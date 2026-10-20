"""Pestaña del Transcriptor de audio y video."""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .estilos import (BotonModerno, COLOR_AVISO, COLOR_ERROR, COLOR_FONDO, COLOR_INFO, COLOR_NEUTRO, COLOR_OK,
                      FUENTE)
from .pestana_base import PestanaBase
from .widgets import CajaTexto

TIPOS = [("Audio y video", "*.mp3 *.wav *.m4a *.ogg *.flac *.mp4 *.mov *.mkv *.webm"), ("Todos", "*.*")]


class PestanaTranscriptor(PestanaBase):
    def __init__(self, master, ejecutor, transcripcion):
        super().__init__(master, ejecutor)
        self.transcripcion = transcripcion
        self.ruta = None
        self._construir()

    def _construir(self):
        cont = tk.Frame(self, bg=COLOR_FONDO)
        cont.pack(fill="both", expand=True, padx=24, pady=18)

        self.crear_tarjeta_estado(cont, "El modelo de IA se carga la primera vez que transcribas.").pack(fill="x")

        fila = tk.Frame(cont, bg=COLOR_FONDO)
        fila.pack(fill="x", pady=14)
        self.btn_seleccionar = BotonModerno(fila, "Seleccionar audio o video", self.seleccionar, primario=False)
        self.btn_seleccionar.pack(side="left")
        self.btn_transcribir = BotonModerno(fila, "Transcribir", self.transcribir)
        self.btn_transcribir.pack(side="left", padx=(10, 0))
        self.btn_transcribir.habilitar(False)
        self.btn_copiar = BotonModerno(fila, "Copiar texto", self.copiar, primario=False)
        self.btn_copiar.pack(side="left", padx=(10, 0))

        tk.Label(fila, text="Modelo:", font=(FUENTE, 10), bg=COLOR_FONDO).pack(side="left", padx=(24, 6))
        self.var_modelo = tk.StringVar(value=self.transcripcion.nombre_modelo)
        combo = ttk.Combobox(fila, textvariable=self.var_modelo, state="readonly", width=9,
                             values=["tiny", "base", "small", "medium"])
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _: self.transcripcion.cambiar_modelo(self.var_modelo.get()))

        self.titulo(cont, "Transcripción").pack(fill="x", pady=(0, 6))
        self.caja = CajaTexto(cont, altura=16)
        self.caja.pack(fill="both", expand=True)

    def seleccionar(self):
        ruta = filedialog.askopenfilename(title="Selecciona un archivo de audio o video", filetypes=TIPOS)
        if ruta:
            self.ruta = ruta
            self.estado(f"Archivo cargado: {Path(ruta).name}", COLOR_NEUTRO)
            self.btn_transcribir.habilitar(True)

    def transcribir(self):
        self.btn_transcribir.habilitar(False)
        self.estado("Transcribiendo... (la primera vez también se carga el modelo)", COLOR_AVISO)
        self.ocupado(True)
        self.caja.poner("")
        self.ejecutor.ejecutar(lambda _: self.transcripcion.transcribir(self.ruta), self._listo, self._fallo)

    def _listo(self, texto):
        self.ocupado(False)
        self.caja.poner(texto)
        self.estado("Transcripción completada.", COLOR_OK)
        self.btn_transcribir.habilitar(True)

    def _fallo(self, error):
        self.ocupado(False)
        self.estado("Error en la transcripción.", COLOR_ERROR)
        self.btn_transcribir.habilitar(True)
        messagebox.showerror("Error", f"Ocurrió un error: {error}")

    def copiar(self):
        self.clipboard_clear()
        self.clipboard_append(self.caja.obtener())
        self.estado("Texto copiado al portapapeles.", COLOR_INFO)
