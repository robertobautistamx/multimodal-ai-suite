"""Ventana principal: crea los servicios una sola vez y los reparte a cada pestaña."""
import tkinter as tk
from tkinter import ttk

import config
from servicios.base_datos import BaseDatos
from servicios.crm import RepositorioComentarios, ServicioCRM
from servicios.descarga import DescargadorAudio
from servicios.gestos import ServicioGestos
from servicios.rgb import RepositorioRGB, ServicioRGB
from servicios.sentimiento import AnalizadorSentimiento, ExtractorTemas
from servicios.transcripcion import ServicioTranscripcion
from servicios.youtube import AnalizadorEmociones, ExtractorYouTube, ServicioYouTube
from .estilos import (COLOR_ENCABEZADO, COLOR_ENCABEZADO_SUB, COLOR_ENCABEZADO_TEXTO, COLOR_FONDO, FUENTE,
                      configurar_estilos)
from .pestana_crm import PestanaCRM
from .pestana_gestos import PestanaGestos
from .pestana_rgb import PestanaRGB
from .pestana_transcriptor import PestanaTranscriptor
from .pestana_youtube import PestanaYouTube
from .utilidades import EjecutorAsincrono


class AplicacionIntegradora(tk.Tk):
    def __init__(self):
        super().__init__()
        config.asegurar_directorios()
        self.title("Producto Integrador")
        self.geometry("1120x800")
        self.minsize(980, 700)
        self.configure(bg=COLOR_FONDO)
        configurar_estilos(self)
        self.ejecutor = EjecutorAsincrono(self)
        self._crear_servicios()
        self._crear_encabezado()
        self._crear_pestanas()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _crear_servicios(self):
        bd = BaseDatos(config.DB_PATH)
        self.transcripcion = ServicioTranscripcion()
        self.crm = ServicioCRM(RepositorioComentarios(bd), AnalizadorSentimiento(), ExtractorTemas(),
                               self.transcripcion, DescargadorAudio())
        self.rgb = ServicioRGB(RepositorioRGB(bd, config.CARPETA_IMAGENES))
        self.youtube = ServicioYouTube(ExtractorYouTube(), AnalizadorEmociones())
        self.gestos = ServicioGestos()

    def _crear_encabezado(self):
        marco = tk.Frame(self, bg=COLOR_ENCABEZADO)
        marco.pack(fill="x")
        tk.Label(marco, text="Producto Integrador", font=(FUENTE, 20, "bold"), bg=COLOR_ENCABEZADO,
                 fg=COLOR_ENCABEZADO_TEXTO).pack(anchor="w", padx=28, pady=(18, 0))
        tk.Label(marco, text="CRM con IA · Emociones de YouTube · Gestos · Transcriptor · Clasificador RGB",
                 font=(FUENTE, 10), bg=COLOR_ENCABEZADO, fg=COLOR_ENCABEZADO_SUB).pack(anchor="w", padx=28, pady=(2, 16))

    def _crear_pestanas(self):
        cuaderno = ttk.Notebook(self)
        cuaderno.pack(fill="both", expand=True, padx=12, pady=(12, 12))
        pestanas = (
            ("CRM", PestanaCRM(cuaderno, self.ejecutor, self.crm)),
            ("Emociones YouTube", PestanaYouTube(cuaderno, self.ejecutor, self.youtube)),
            ("Gestos", PestanaGestos(cuaderno, self.ejecutor, self.gestos)),
            ("Transcriptor", PestanaTranscriptor(cuaderno, self.ejecutor, self.transcripcion)),
            ("Clasificador RGB", PestanaRGB(cuaderno, self.ejecutor, self.rgb)),
        )
        for titulo, pestana in pestanas:
            cuaderno.add(pestana, text=titulo)

    def _cerrar(self):
        self.gestos.detener()
        self.destroy()
