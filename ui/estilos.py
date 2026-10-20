"""Paleta, botón moderno y estilos ttk compartidos por toda la interfaz."""
import tkinter as tk
from tkinter import ttk

COLOR_FONDO = "#EDF1F7"
COLOR_TARJETA = "#FFFFFF"
COLOR_ENCABEZADO = "#24344D"
COLOR_ENCABEZADO_TEXTO = "#FFFFFF"
COLOR_ENCABEZADO_SUB = "#A9B8D0"
COLOR_PRIMARIO = "#2563EB"
COLOR_PRIMARIO_HOVER = "#1D4ED8"
COLOR_SECUNDARIO = "#E3E9F3"
COLOR_SECUNDARIO_HOVER = "#D3DCEB"
COLOR_TEXTO = "#1F2A3C"
COLOR_TEXTO_SUAVE = "#6B778C"
COLOR_BORDE = "#D5DDEA"
COLOR_DESACTIVADO_BG = "#E6EAF1"
COLOR_DESACTIVADO_FG = "#9AA5B8"

COLOR_INFO = "#2563EB"
COLOR_OK = "#15803D"
COLOR_AVISO = "#B45309"
COLOR_ERROR = "#B91C1C"
COLOR_NEUTRO = "#1F2A3C"

COLOR_POSITIVO = "#16A34A"
COLOR_NEUTRO_BARRA = "#9CA3AF"
COLOR_NEGATIVO = "#DC2626"

FUENTE = "Segoe UI"


class BotonModerno(tk.Button):
    """Botón plano con efecto hover y estilo para estado deshabilitado."""

    def __init__(self, master, texto, comando, primario=True, **kwargs):
        self.bg = COLOR_PRIMARIO if primario else COLOR_SECUNDARIO
        self.bg_hover = COLOR_PRIMARIO_HOVER if primario else COLOR_SECUNDARIO_HOVER
        self.fg = "#FFFFFF" if primario else COLOR_TEXTO
        super().__init__(
            master, text=texto, command=comando, font=(FUENTE, 10, "bold"),
            bg=self.bg, fg=self.fg, activebackground=self.bg_hover, activeforeground=self.fg,
            disabledforeground=COLOR_DESACTIVADO_FG, relief="flat", bd=0,
            padx=18, pady=9, cursor="hand2", **kwargs)
        self.bind("<Enter>", self._al_entrar)
        self.bind("<Leave>", self._al_salir)

    def _al_entrar(self, _):
        if str(self["state"]) != "disabled":
            tk.Button.config(self, bg=self.bg_hover)

    def _al_salir(self, _):
        if str(self["state"]) != "disabled":
            tk.Button.config(self, bg=self.bg)

    def habilitar(self, activo: bool = True):
        if activo:
            tk.Button.config(self, state=tk.NORMAL, bg=self.bg, cursor="hand2")
        else:
            tk.Button.config(self, state=tk.DISABLED, bg=COLOR_DESACTIVADO_BG, cursor="arrow")


def configurar_estilos(raiz) -> None:
    estilo = ttk.Style(raiz)
    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass
    estilo.configure("Moderna.Horizontal.TProgressbar", troughcolor=COLOR_SECUNDARIO,
                     background=COLOR_PRIMARIO, bordercolor=COLOR_SECUNDARIO,
                     lightcolor=COLOR_PRIMARIO, darkcolor=COLOR_PRIMARIO, thickness=6)
    estilo.configure("Moderna.Vertical.TScrollbar", troughcolor=COLOR_TARJETA,
                     background=COLOR_SECUNDARIO, bordercolor=COLOR_TARJETA,
                     arrowcolor=COLOR_TEXTO_SUAVE, relief="flat")
    estilo.map("Moderna.Vertical.TScrollbar", background=[("active", COLOR_SECUNDARIO_HOVER)])
    estilo.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
    estilo.configure("TNotebook.Tab", font=(FUENTE, 10, "bold"), padding=(18, 9),
                     background=COLOR_SECUNDARIO, foreground=COLOR_TEXTO_SUAVE, borderwidth=0)
    estilo.map("TNotebook.Tab", background=[("selected", COLOR_TARJETA)],
               foreground=[("selected", COLOR_PRIMARIO)])
    estilo.configure("Moderna.Treeview", font=(FUENTE, 10), rowheight=26, background=COLOR_TARJETA,
                     fieldbackground=COLOR_TARJETA, foreground=COLOR_TEXTO, borderwidth=0)
    estilo.configure("Moderna.Treeview.Heading", font=(FUENTE, 10, "bold"),
                     background=COLOR_SECUNDARIO, foreground=COLOR_TEXTO, relief="flat")
    estilo.map("Moderna.Treeview", background=[("selected", "#BFD3FA")],
               foreground=[("selected", COLOR_TEXTO)])
