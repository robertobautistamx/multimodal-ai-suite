"""Widgets reutilizables: tabla, gráfica de sentimientos, barra de color y caja de texto."""
import tkinter as tk
from tkinter import ttk

from .estilos import (COLOR_BORDE, COLOR_NEGATIVO, COLOR_NEUTRO_BARRA, COLOR_POSITIVO, COLOR_SECUNDARIO,
                      COLOR_TARJETA, COLOR_TEXTO, COLOR_TEXTO_SUAVE, FUENTE)


class TablaDatos(tk.Frame):
    """Treeview con barras de desplazamiento y un método simple para llenarla."""

    def __init__(self, master, altura: int = 8):
        super().__init__(master, bg=COLOR_TARJETA, highlightbackground=COLOR_BORDE, highlightthickness=1)
        self.arbol = ttk.Treeview(self, show="headings", height=altura, style="Moderna.Treeview")
        vertical = ttk.Scrollbar(self, orient="vertical", command=self.arbol.yview,
                                 style="Moderna.Vertical.TScrollbar")
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.arbol.xview)
        self.arbol.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.arbol.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def mostrar(self, columnas, filas, anchos=None):
        anchos = anchos or {}
        self.arbol["columns"] = list(columnas)
        for c in columnas:
            self.arbol.heading(c, text=c)
            self.arbol.column(c, width=anchos.get(c, 110), anchor="w", stretch=True)
        self.arbol.delete(*self.arbol.get_children())
        for fila in filas:
            self.arbol.insert("", "end", values=list(fila))


class CajaTexto(tk.Frame):
    """Texto de solo lectura con barra de desplazamiento."""

    def __init__(self, master, altura: int = 10):
        super().__init__(master, bg=COLOR_TARJETA, highlightbackground=COLOR_BORDE, highlightthickness=1)
        barra = ttk.Scrollbar(self, orient="vertical", style="Moderna.Vertical.TScrollbar")
        barra.pack(side="right", fill="y")
        self.texto = tk.Text(self, height=altura, font=(FUENTE, 11), bg=COLOR_TARJETA, fg=COLOR_TEXTO,
                             selectbackground="#BFD3FA", relief="flat", bd=0, wrap="word",
                             padx=14, pady=12, spacing2=4, yscrollcommand=barra.set)
        self.texto.pack(side="left", fill="both", expand=True)
        barra.config(command=self.texto.yview)

    def poner(self, contenido: str):
        self.texto.delete("1.0", "end")
        self.texto.insert("end", contenido)

    def obtener(self) -> str:
        return self.texto.get("1.0", "end").strip()


class GraficaSentimientos(tk.Canvas):
    """Barras apiladas (positivo / neutro / negativo) por producto."""

    def __init__(self, master, ancho: int = 560):
        super().__init__(master, width=ancho, height=60, bg=COLOR_TARJETA,
                         highlightbackground=COLOR_BORDE, highlightthickness=1)
        self.ancho = ancho

    def dibujar(self, resumen):
        self.delete("all")
        if resumen is None or len(resumen) == 0:
            self.config(height=60)
            self.create_text(self.ancho / 2, 30, text="Sin datos", fill=COLOR_TEXTO_SUAVE, font=(FUENTE, 10))
            return
        self.config(height=44 + len(resumen) * 32)
        x0, largo = 170, self.ancho - 190
        for i, fila in enumerate(resumen.itertuples()):
            y = 14 + i * 32
            self.create_text(10, y + 9, text=fila.producto, anchor="w", fill=COLOR_TEXTO, font=(FUENTE, 9))
            x = x0
            for pct, color in ((fila.pct_positivos, COLOR_POSITIVO), (fila.pct_neutros, COLOR_NEUTRO_BARRA),
                               (fila.pct_negativos, COLOR_NEGATIVO)):
                w = pct * largo
                if w > 0:
                    self.create_rectangle(x, y, x + w, y + 18, fill=color, width=0)
                    if w > 34:
                        self.create_text(x + w / 2, y + 9, text=f"{pct:.0%}", fill="white", font=(FUENTE, 8, "bold"))
                x += w
        base = 20 + len(resumen) * 32
        for j, (nombre, color) in enumerate((("Positivo", COLOR_POSITIVO), ("Neutro", COLOR_NEUTRO_BARRA),
                                             ("Negativo", COLOR_NEGATIVO))):
            xl = x0 + j * 110
            self.create_rectangle(xl, base + 6, xl + 10, base + 16, fill=color, width=0)
            self.create_text(xl + 16, base + 11, text=nombre, anchor="w", fill=COLOR_TEXTO_SUAVE, font=(FUENTE, 8))


class BarraColor(tk.Canvas):
    """Barra horizontal que se llena según un valor de 0 a 255."""

    def __init__(self, master, color: str, ancho: int = 240):
        super().__init__(master, width=ancho, height=8, bg=COLOR_SECUNDARIO, highlightthickness=0)
        self.color = color
        self.ancho = ancho

    def valor(self, v: int):
        self.delete("all")
        self.create_rectangle(0, 0, round(v / 255 * self.ancho), 8, fill=self.color, width=0)
