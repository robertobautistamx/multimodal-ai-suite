"""Pestaña de reconocimiento de gestos con MediaPipe."""
import tkinter as tk
from tkinter import messagebox

from .estilos import (BotonModerno, COLOR_AVISO, COLOR_BORDE, COLOR_ERROR, COLOR_FONDO, COLOR_OK, COLOR_PRIMARIO,
                      COLOR_TARJETA, COLOR_TEXTO_SUAVE, FUENTE)
from .pestana_base import PestanaBase


class PestanaGestos(PestanaBase):
    def __init__(self, master, ejecutor, servicio):
        super().__init__(master, ejecutor)
        self.servicio = servicio
        self._construir()

    def _construir(self):
        cont = tk.Frame(self, bg=COLOR_FONDO)
        cont.pack(fill="both", expand=True, padx=24, pady=18)
        self.crear_tarjeta_estado(cont, "Listo. La primera vez se descarga el modelo HandLandmarker.").pack(fill="x")

        botones = tk.Frame(cont, bg=COLOR_FONDO)
        botones.pack(fill="x", pady=14)
        self.btn_iniciar = BotonModerno(botones, "Iniciar cámara", self.iniciar)
        self.btn_iniciar.pack(side="left")
        self.btn_detener = BotonModerno(botones, "Detener", self.detener, primario=False)
        self.btn_detener.pack(side="left", padx=10)
        self.btn_detener.habilitar(False)

        tarjeta = tk.Frame(cont, bg=COLOR_TARJETA, highlightbackground=COLOR_BORDE, highlightthickness=1)
        tarjeta.pack(fill="both", expand=True)
        tk.Label(tarjeta, text="Gesto detectado", font=(FUENTE, 11), bg=COLOR_TARJETA,
                 fg=COLOR_TEXTO_SUAVE).pack(pady=(40, 6))
        self.lbl_gesto = tk.Label(tarjeta, text="—", font=(FUENTE, 40, "bold"), bg=COLOR_TARJETA, fg=COLOR_PRIMARIO)
        self.lbl_gesto.pack()
        tk.Label(tarjeta, text="Se abre una ventana con la cámara. Ciérrala con «q» o Esc.\n"
                 "Gestos: Puño, Uno, Dos / Paz, Tres, Cuatro, Mano abierta y Pulgar arriba.",
                 font=(FUENTE, 10), bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE, justify="center").pack(pady=24)

    def iniciar(self):
        self.servicio.iniciar()
        self.btn_iniciar.habilitar(False)
        self.btn_detener.habilitar(True)
        self.ocupado(True)
        self.estado("Cámara en uso...", COLOR_AVISO)
        self._sondear()

    def detener(self):
        self.servicio.detener()

    def _sondear(self):
        """Lee el estado del hilo de la cámara (Tkinter solo se toca desde este hilo)."""
        if self.servicio.activo:
            self.lbl_gesto.config(text=self.servicio.ultimo_gesto)
            self.after(150, self._sondear)
            return
        self.ocupado(False)
        self.lbl_gesto.config(text="—")
        self.btn_iniciar.habilitar(True)
        self.btn_detener.habilitar(False)
        if self.servicio.error:
            self.estado("No se pudo usar la cámara o MediaPipe.", COLOR_ERROR)
            messagebox.showerror("Gestos", self.servicio.error)
        else:
            self.estado("Cámara detenida.", COLOR_OK)
