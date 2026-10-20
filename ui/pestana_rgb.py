"""Pestaña del Clasificador RGB."""
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from PIL import Image, ImageTk

import config
from .estilos import (BotonModerno, COLOR_BORDE, COLOR_ERROR, COLOR_FONDO, COLOR_OK, COLOR_TARJETA,
                      COLOR_TEXTO, COLOR_TEXTO_SUAVE, FUENTE)
from .pestana_base import PestanaBase
from .widgets import BarraColor

TIPOS = [("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")]


class PestanaRGB(PestanaBase):
    def __init__(self, master, ejecutor, servicio):
        super().__init__(master, ejecutor)
        self.servicio = servicio
        self.ruta = None
        self.promedios = None
        self._foto = None
        self._construir()
        self.nueva_persona()

    # ---------- construcción ----------
    def _construir(self):
        cont = tk.Frame(self, bg=COLOR_FONDO)
        cont.pack(fill="both", expand=True, padx=24, pady=18)

        datos = tk.Frame(cont, bg=COLOR_TARJETA, highlightbackground=COLOR_BORDE, highlightthickness=1)
        datos.pack(fill="x")
        self.var_id, self.var_nombre = tk.StringVar(), tk.StringVar()
        self.var_k = tk.IntVar(value=config.K_POR_DEFECTO)
        for col, (texto, ancho, var, solo_lectura) in enumerate((
                ("CÓDIGO", 12, self.var_id, True), ("NOMBRE", 34, self.var_nombre, False))):
            bloque = tk.Frame(datos, bg=COLOR_TARJETA)
            bloque.grid(row=0, column=col, padx=16, pady=12, sticky="w")
            tk.Label(bloque, text=texto, font=(FUENTE, 8, "bold"), bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE).pack(anchor="w")
            tk.Entry(bloque, textvariable=var, width=ancho, font=(FUENTE, 11), relief="solid", bd=1,
                     state="readonly" if solo_lectura else "normal").pack(anchor="w")
        bloque_k = tk.Frame(datos, bg=COLOR_TARJETA)
        bloque_k.grid(row=0, column=2, padx=16, pady=12, sticky="w")
        tk.Label(bloque_k, text="K (VECINOS)", font=(FUENTE, 8, "bold"), bg=COLOR_TARJETA,
                 fg=COLOR_TEXTO_SUAVE).pack(anchor="w")
        tk.Spinbox(bloque_k, from_=1, to=15, width=5, textvariable=self.var_k, font=(FUENTE, 11),
                   command=self._cambiar_k).pack(anchor="w")

        medio = tk.Frame(cont, bg=COLOR_FONDO)
        medio.pack(fill="both", expand=True, pady=14)

        marco_img = tk.Frame(medio, bg=COLOR_TARJETA, highlightbackground=COLOR_BORDE, highlightthickness=1)
        marco_img.pack(side="left", fill="both", expand=True)
        self.lienzo_img = tk.Label(marco_img, bg="#F6F7F9", text="Carga una imagen para analizar su color",
                                   fg=COLOR_TEXTO_SUAVE, font=(FUENTE, 10), width=60, height=16)
        self.lienzo_img.pack(padx=14, pady=14, fill="both", expand=True)

        panel = tk.Frame(medio, bg=COLOR_TARJETA, highlightbackground=COLOR_BORDE, highlightthickness=1, width=290)
        panel.pack(side="left", fill="y", padx=(14, 0))
        panel.pack_propagate(False)
        tk.Label(panel, text="Análisis de color", font=(FUENTE, 13, "bold"), bg=COLOR_TARJETA,
                 fg=COLOR_TEXTO).pack(anchor="w", padx=20, pady=(16, 8))
        self.muestra = tk.Frame(panel, bg="#F6F7F9", height=50, highlightbackground=COLOR_BORDE, highlightthickness=1)
        self.muestra.pack(fill="x", padx=20)
        self.labels, self.barras = {}, {}
        for clave, texto, color in (("r", "Rojo (R)", "#DC2626"), ("g", "Verde (G)", "#16A34A"), ("b", "Azul (B)", "#2563EB")):
            lbl = tk.Label(panel, text=f"{texto}: 0", font=(FUENTE, 10, "bold"), bg=COLOR_TARJETA, fg=color)
            lbl.pack(anchor="w", padx=20, pady=(12, 2))
            barra = BarraColor(panel, color)
            barra.pack(anchor="w", padx=20)
            barra.valor(0)
            self.labels[clave], self.barras[clave] = (lbl, texto), barra
        self.lbl_promedio = tk.Label(panel, text="Promedio: 0", font=(FUENTE, 10, "bold"), bg=COLOR_TARJETA,
                                     fg=COLOR_TEXTO_SUAVE)
        self.lbl_promedio.pack(anchor="w", padx=20, pady=(16, 0))
        self.lbl_resultado = tk.Label(panel, text="", font=(FUENTE, 10, "italic"), bg=COLOR_TARJETA,
                                      fg=COLOR_OK, wraplength=250, justify="left")
        self.lbl_resultado.pack(anchor="w", padx=20, pady=(8, 0))

        botones = tk.Frame(cont, bg=COLOR_FONDO)
        botones.pack(fill="x")
        for texto, cmd, prim in (("Cargar imagen", self.cargar_imagen, True), ("Clasificar imagen", self.clasificar, True),
                                 ("Guardar datos", self.guardar, True), ("Nueva persona", self.nueva_persona, False),
                                 ("Limpiar imagen", self.limpiar_imagen, False)):
            BotonModerno(botones, texto, cmd, primario=prim).pack(side="left", padx=(0, 10))

    # ---------- acciones ----------
    def _cambiar_k(self):
        try:
            self.servicio.clasificador.k = max(1, int(self.var_k.get()))
        except (ValueError, tk.TclError):
            pass

    def _mostrar_promedios(self, r, g, b):
        for clave, valor in (("r", r), ("g", g), ("b", b)):
            lbl, texto = self.labels[clave]
            lbl.config(text=f"{texto}: {valor}")
            self.barras[clave].valor(valor)
        self.muestra.config(bg=f"#{r:02x}{g:02x}{b:02x}")
        self.lbl_promedio.config(text=f"Promedio: {round((r + g + b) / 3)}")
        self.lbl_resultado.config(text="")

    def cargar_imagen(self):
        ruta = filedialog.askopenfilename(title="Selecciona una imagen", filetypes=TIPOS)
        if not ruta:
            return
        try:
            with Image.open(ruta) as img:
                vista = img.convert("RGB")
            vista.thumbnail((520, 300))
            self._foto = ImageTk.PhotoImage(vista)
            self.lienzo_img.config(image=self._foto, text="", width=0, height=0)
            self.ruta = ruta
            self.promedios = self.servicio.analizar_imagen(ruta)
            self._mostrar_promedios(*self.promedios)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def clasificar(self):
        if not self.promedios:
            messagebox.showinfo("Clasificador", "Carga una imagen nueva primero.")
            return
        try:
            nombre, distancia = self.servicio.clasificar(*self.promedios)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo clasificar la imagen:\n{e}")
            return
        if nombre == "Desconocido":
            sin_datos = distancia < 0
            self.lbl_resultado.config(fg=COLOR_ERROR, text="Sin datos en la base de datos." if sin_datos
                                      else f"Sin coincidencia cercana (dist. {distancia:.2f})")
            messagebox.showinfo("Clasificador", "No hay imágenes guardadas en la base de datos." if sin_datos
                                else f"No se encontró una coincidencia suficientemente cercana.\n\nDistancia: {distancia:.2f}")
            return
        self.lbl_resultado.config(fg=COLOR_OK, text=f"Coincide con: {nombre}")
        messagebox.showinfo("Clasificador", f"La imagen tiene más coincidencias con:\n\n{nombre}\n\n"
                            f"Distancia RGB: {distancia:.2f} (K={self.servicio.clasificador.k})")

    def guardar(self):
        if not self.ruta or not self.promedios:
            messagebox.showwarning("Guardar", "Primero debes cargar una imagen.")
            return
        nombre, codigo = self.var_nombre.get().strip(), self.var_id.get().strip()
        if not nombre or not codigo:
            messagebox.showwarning("Guardar", "Debes llenar el Nombre y el Código.")
            return
        try:
            cantidad = self.servicio.guardar(nombre, codigo, self.ruta, *self.promedios)
        except ValueError as e:
            messagebox.showwarning("Guardar", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")
            return
        messagebox.showinfo("Guardar", f"¡Imagen guardada correctamente!\n\nPersona: {nombre} ({codigo})\n"
                            f"Imagen: {Path(self.ruta).name}\nImágenes de esta persona: "
                            f"{cantidad}/{config.MAX_IMAGENES_POR_PERSONA}\n\n"
                            "Puedes cargar otra imagen de la misma persona o pulsar «Nueva persona».")
        self.limpiar_imagen()

    def limpiar_imagen(self):
        self.ruta, self.promedios, self._foto = None, None, None
        self.lienzo_img.config(image="", text="Carga una imagen para analizar su color", width=60, height=16)
        self._mostrar_promedios(0, 0, 0)
        self.muestra.config(bg="#F6F7F9")

    def nueva_persona(self):
        self.limpiar_imagen()
        self.var_nombre.set("")
        self.var_id.set(self.servicio.siguiente_identificador())
