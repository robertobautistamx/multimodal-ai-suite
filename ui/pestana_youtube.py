"""Pestaña de análisis de emociones en comentarios de YouTube (Ollama)."""
import tkinter as tk
from tkinter import filedialog, messagebox

from .estilos import (BotonModerno, COLOR_AVISO, COLOR_ERROR, COLOR_FONDO, COLOR_OK, COLOR_TEXTO_SUAVE, FUENTE)
from .pestana_base import PestanaBase
from .widgets import TablaDatos


class PestanaYouTube(PestanaBase):
    def __init__(self, master, ejecutor, servicio):
        super().__init__(master, ejecutor)
        self.servicio = servicio
        self.df = None
        self._construir()

    def _construir(self):
        cont = tk.Frame(self, bg=COLOR_FONDO)
        cont.pack(fill="both", expand=True, padx=24, pady=18)

        fila = tk.Frame(cont, bg=COLOR_FONDO)
        fila.pack(fill="x")
        tk.Label(fila, text="Enlace del video:", font=(FUENTE, 10), bg=COLOR_FONDO).pack(side="left")
        self.var_url = tk.StringVar()
        tk.Entry(fila, textvariable=self.var_url, width=52, font=(FUENTE, 10), relief="solid",
                 bd=1).pack(side="left", padx=8)
        tk.Label(fila, text="Comentarios:", font=(FUENTE, 10), bg=COLOR_FONDO).pack(side="left")
        self.var_limite = tk.IntVar(value=30)
        tk.Spinbox(fila, from_=5, to=500, increment=5, width=5, textvariable=self.var_limite,
                   font=(FUENTE, 10)).pack(side="left", padx=8)

        botones = tk.Frame(cont, bg=COLOR_FONDO)
        botones.pack(fill="x", pady=12)
        self.btn_analizar = BotonModerno(botones, "Analizar emociones", self.analizar)
        self.btn_analizar.pack(side="left")
        self.btn_exportar = BotonModerno(botones, "Exportar CSV", self.exportar, primario=False)
        self.btn_exportar.pack(side="left", padx=10)
        self.btn_exportar.habilitar(False)

        self.crear_tarjeta_estado(cont, "Pega el enlace de un video de YouTube. Requiere Ollama abierto.").pack(fill="x")
        self.lbl_resumen = tk.Label(cont, text="", font=(FUENTE, 11, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE,
                                    anchor="w", justify="left", wraplength=900)
        self.lbl_resumen.pack(fill="x", pady=10)
        self.tabla = TablaDatos(cont, altura=12)
        self.tabla.pack(fill="both", expand=True)

    def analizar(self):
        url = self.var_url.get().strip()
        if not url:
            messagebox.showwarning("Enlace", "Pega el enlace de un video de YouTube.")
            return
        try:
            limite = max(1, int(self.var_limite.get()))
        except (ValueError, tk.TclError):
            limite = 30
        self.btn_analizar.habilitar(False)
        self.btn_exportar.habilitar(False)
        self.ocupado(True)
        self.estado("Descargando comentarios y consultando a Ollama...", COLOR_AVISO)
        self.ejecutor.ejecutar(lambda rep: self.servicio.analizar_video(url, limite, rep), self._listo,
                               self._fallo, lambda i, t: self.estado(f"Analizando comentario {i}/{t}", COLOR_AVISO))

    def _listo(self, df):
        self.df = df
        self.ocupado(False)
        self.btn_analizar.habilitar(True)
        self.btn_exportar.habilitar(True)
        dominante, conteo = self.servicio.resumen(df)
        self.estado(f"Análisis completado: {len(df)} comentarios.", COLOR_OK)
        self.lbl_resumen.config(text=f"Emoción dominante: {dominante}    |    " +
                                "   ".join(f"{e}: {n}" for e, n in conteo.items()))
        self.tabla.mostrar(["autor", "relacion", "emocion", "justificacion", "texto"],
                           df[["autor", "relacion", "emocion", "justificacion", "texto"]].values.tolist(),
                           {"autor": 120, "relacion": 80, "emocion": 90, "justificacion": 260, "texto": 420})

    def _fallo(self, error):
        self.ocupado(False)
        self.btn_analizar.habilitar(True)
        self.estado("Ocurrió un error.", COLOR_ERROR)
        messagebox.showerror("Error", str(error))

    def exportar(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile="emociones_youtube.csv")
        if ruta:
            self.servicio.exportar_csv(self.df, ruta)
            self.estado(f"Exportado a {ruta}", COLOR_OK)
