"""Clase base de todas las pestañas: tarjeta de estado con barra de progreso."""
import tkinter as tk
from tkinter import ttk

from .estilos import (COLOR_BORDE, COLOR_FONDO, COLOR_INFO, COLOR_NEUTRO, COLOR_TARJETA, FUENTE)


class PestanaBase(tk.Frame):
    def __init__(self, master, ejecutor):
        super().__init__(master, bg=COLOR_FONDO)
        self.ejecutor = ejecutor
        self.label_estado = None
        self.barra = None

    def crear_tarjeta_estado(self, padre, texto_inicial: str = ""):
        tarjeta = tk.Frame(padre, bg=COLOR_TARJETA, highlightbackground=COLOR_BORDE, highlightthickness=1)
        self.label_estado = tk.Label(tarjeta, text=texto_inicial, font=(FUENTE, 10, "bold"), bg=COLOR_TARJETA,
                                     fg=COLOR_INFO, anchor="w", wraplength=900, justify="left")
        self.label_estado.pack(fill="x", padx=16, pady=(12, 6))
        self.barra = ttk.Progressbar(tarjeta, mode="indeterminate", style="Moderna.Horizontal.TProgressbar")
        self.barra.pack(fill="x", padx=16, pady=(0, 12))
        return tarjeta

    def estado(self, texto: str, color: str = COLOR_NEUTRO):
        self.label_estado.config(text=texto, fg=color)

    def ocupado(self, activo: bool):
        if activo:
            self.barra.start(12)
        else:
            self.barra.stop()

    @staticmethod
    def titulo(padre, texto: str):
        return tk.Label(padre, text=texto, font=(FUENTE, 11, "bold"), bg=COLOR_FONDO, fg="#1F2A3C", anchor="w")
