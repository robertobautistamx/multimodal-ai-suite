"""Pestaña del CRM de comentarios, audios y videos."""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import config
from .estilos import (BotonModerno, COLOR_AVISO, COLOR_ERROR, COLOR_FONDO, COLOR_INFO, COLOR_OK, COLOR_TARJETA,
                      COLOR_TEXTO, COLOR_TEXTO_SUAVE, COLOR_BORDE, FUENTE)
from .pestana_base import PestanaBase
from .widgets import CajaTexto, GraficaSentimientos, TablaDatos

TIPOS_COMENTARIOS = [("CSV o JSON", "*.csv *.json")]
TIPOS_MEDIA = [("Audio y video", "*.mp3 *.wav *.m4a *.ogg *.flac *.mp4 *.mov *.mkv *.webm")]


class PestanaCRM(PestanaBase):
    def __init__(self, master, ejecutor, servicio):
        super().__init__(master, ejecutor)
        self.servicio = servicio
        self.botones = []
        self._analisis = None
        self._construir()
        self.refrescar()

    # ---------- construcción ----------
    def _construir(self):
        cont = tk.Frame(self, bg=COLOR_FONDO)
        cont.pack(fill="both", expand=True, padx=24, pady=14)

        acciones = tk.Frame(cont, bg=COLOR_FONDO)
        acciones.pack(fill="x")
        for texto, cmd, prim in (("Datos de ejemplo", self.cargar_ejemplo, True),
                                 ("Cargar CSV / JSON", self.cargar_comentarios, False),
                                 ("Audio o video", self.cargar_media, False),
                                 ("Enlace de video", self.cargar_enlace, False),
                                 ("Vaciar datos", self.vaciar, False)):
            boton = BotonModerno(acciones, texto, cmd, primario=prim)
            boton.pack(side="left", padx=(0, 8))
            self.botones.append(boton)

        datos = tk.Frame(cont, bg=COLOR_FONDO)
        datos.pack(fill="x", pady=(10, 8))
        tk.Label(datos, text="Producto (para audio, video y enlaces):", font=(FUENTE, 9), bg=COLOR_FONDO,
                 fg=COLOR_TEXTO_SUAVE).pack(side="left")
        self.var_producto = tk.StringVar()
        self.combo_producto = ttk.Combobox(datos, textvariable=self.var_producto, width=26,
                                           values=self.servicio.productos())
        self.combo_producto.pack(side="left", padx=(6, 18))
        tk.Label(datos, text="Cliente:", font=(FUENTE, 9), bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE).pack(side="left")
        self.var_autor = tk.StringVar(value="Cliente (voz)")
        tk.Entry(datos, textvariable=self.var_autor, width=22, font=(FUENTE, 10), relief="solid",
                 bd=1).pack(side="left", padx=6)

        self.crear_tarjeta_estado(cont, "Carga los datos de ejemplo o tus propios archivos para empezar.").pack(fill="x")

        self.metricas = {}
        fila_m = tk.Frame(cont, bg=COLOR_FONDO)
        fila_m.pack(fill="x", pady=10)
        for clave, texto in (("total", "Comentarios"), ("pos", "% positivos"), ("neg", "% negativos"),
                             ("dest", "Destacados")):
            tarjeta = tk.Frame(fila_m, bg=COLOR_TARJETA, highlightbackground=COLOR_BORDE, highlightthickness=1)
            tarjeta.pack(side="left", expand=True, fill="x", padx=(0, 8))
            tk.Label(tarjeta, text=texto, font=(FUENTE, 9), bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE).pack(pady=(8, 0))
            lbl = tk.Label(tarjeta, text="0", font=(FUENTE, 18, "bold"), bg=COLOR_TARJETA, fg=COLOR_TEXTO)
            lbl.pack(pady=(0, 8))
            self.metricas[clave] = lbl

        sub = ttk.Notebook(cont)
        sub.pack(fill="both", expand=True)
        self.tabla_ranking = self._sub_tabla(sub, "Ranking", extra=True)
        self.tabla_alertas = self._sub_tabla(sub, "Alertas")
        self.tabla_clientes = self._sub_tabla(sub, "Clientes")
        self._crear_subtab_comentarios(sub)

    def _sub_frame(self, sub, titulo):
        marco = tk.Frame(sub, bg=COLOR_FONDO)
        sub.add(marco, text=titulo)
        return marco

    def _sub_tabla(self, sub, titulo, extra=False):
        marco = self._sub_frame(sub, titulo)
        if extra:
            self.grafica = GraficaSentimientos(marco)
            self.grafica.pack(fill="x", padx=8, pady=(10, 4))
        tabla = TablaDatos(marco, altura=7)
        tabla.pack(fill="both", expand=True, padx=8, pady=8)
        return tabla

    def _crear_subtab_comentarios(self, sub):
        marco = self._sub_frame(sub, "Comentarios")
        filtros = tk.Frame(marco, bg=COLOR_FONDO)
        filtros.pack(fill="x", padx=8, pady=(10, 0))
        self.var_f_producto, self.var_f_sent = tk.StringVar(value="Todos"), tk.StringVar(value="Todos")
        for texto, var, valores in (("Producto:", self.var_f_producto, ["Todos"]),
                                    ("Sentimiento:", self.var_f_sent, ["Todos", "positivo", "neutro", "negativo"])):
            tk.Label(filtros, text=texto, font=(FUENTE, 9), bg=COLOR_FONDO).pack(side="left", padx=(0, 4))
            combo = ttk.Combobox(filtros, textvariable=var, values=valores, state="readonly", width=22)
            combo.pack(side="left", padx=(0, 14))
            combo.bind("<<ComboboxSelected>>", lambda _: self._llenar_comentarios())
            if texto == "Producto:":
                self.combo_f_producto = combo
        self.tabla_comentarios = TablaDatos(marco, altura=7)
        self.tabla_comentarios.pack(fill="both", expand=True, padx=8, pady=8)

    # ---------- carga de datos ----------
    def _bloquear(self, bloquear: bool):
        for b in self.botones:
            b.habilitar(not bloquear)
        self.ocupado(bloquear)

    def _lanzar(self, tarea, mensaje, al_terminar):
        self._bloquear(True)
        self.estado(mensaje, COLOR_AVISO)

        def ok(resultado):
            self._bloquear(False)
            al_terminar(resultado)
            self.refrescar()

        def fallo(error):
            self._bloquear(False)
            self.estado("Ocurrió un error.", COLOR_ERROR)
            messagebox.showerror("Error", str(error))

        self.ejecutor.ejecutar(tarea, ok, fallo, lambda i, t: self.estado(f"Analizando comentarios: {i}/{t}", COLOR_AVISO))

    def _cargar_archivo(self, ruta):
        self._lanzar(lambda rep: self.servicio.cargar_archivo(ruta, rep), "Analizando comentarios...",
                     lambda n: self.estado(f"{n} comentarios procesados. Motor: {self.servicio.analizador.motor}", COLOR_OK))

    def cargar_ejemplo(self):
        if not config.CSV_EJEMPLO.exists():
            messagebox.showerror("Error", f"No se encontró {config.CSV_EJEMPLO}")
            return
        self._cargar_archivo(config.CSV_EJEMPLO)

    def cargar_comentarios(self):
        ruta = filedialog.askopenfilename(title="CSV o JSON con comentarios", filetypes=TIPOS_COMENTARIOS)
        if ruta:
            self._cargar_archivo(ruta)

    def _producto(self):
        producto = self.var_producto.get().strip()
        if not producto:
            messagebox.showwarning("Producto", "Escribe o elige el producto al que se refiere el audio o video.")
        return producto

    def _mostrar_transcripcion(self, texto):
        self.estado("Procesado correctamente.", COLOR_OK)
        messagebox.showinfo("Transcripción", texto or "(sin texto)")

    def cargar_media(self):
        producto = self._producto()
        ruta = producto and filedialog.askopenfilename(title="Audio o video", filetypes=TIPOS_MEDIA)
        if ruta:
            autor = self.var_autor.get()
            self._lanzar(lambda _: self.servicio.procesar_media(ruta, producto, autor),
                         "Transcribiendo con Whisper... (la primera vez descarga el modelo)", self._mostrar_transcripcion)

    def cargar_enlace(self):
        producto = self._producto()
        url = producto and simpledialog.askstring("Enlace de video", "Pega el enlace (YouTube, TikTok, Facebook público):")
        if url:
            autor = self.var_autor.get()
            self._lanzar(lambda _: self.servicio.procesar_enlace(url.strip(), producto, autor),
                         "Descargando audio y transcribiendo...", self._mostrar_transcripcion)

    def vaciar(self):
        if messagebox.askyesno("Vaciar datos", "¿Borrar todos los comentarios del CRM?"):
            self.servicio.vaciar()
            self.estado("Datos borrados.", COLOR_INFO)
            self.refrescar()

    # ---------- presentación ----------
    def refrescar(self):
        self._analisis = a = self.servicio.analisis()
        self.combo_producto["values"] = self.servicio.productos()
        df = a.comentarios
        if df.empty:
            for lbl in self.metricas.values():
                lbl.config(text="0")
            for tabla in (self.tabla_ranking, self.tabla_alertas, self.tabla_clientes, self.tabla_comentarios):
                tabla.mostrar(["Sin datos"], [])
            self.grafica.dibujar(None)
            return
        self.metricas["total"].config(text=str(len(df)))
        self.metricas["pos"].config(text=f"{(df['sentimiento'] == 'positivo').mean():.0%}")
        self.metricas["neg"].config(text=f"{(df['sentimiento'] == 'negativo').mean():.0%}")
        self.metricas["dest"].config(text=str(int(a.resumen['destacado'].sum())))

        self.tabla_ranking.mostrar(
            ["#", "Producto", "Comentarios", "% positivos", "% neutros", "% negativos", "Score", "Destacado"],
            [(f.ranking, f.producto, f.comentarios, f"{f.pct_positivos:.0%}", f"{f.pct_neutros:.0%}",
              f"{f.pct_negativos:.0%}", f"{f.score_promedio:.2f}", "★ Sí" if f.destacado else "—")
             for f in a.resumen.itertuples()], {"#": 40, "Producto": 200})
        self.grafica.dibujar(a.resumen)

        filas = [(f.producto, f"{f.pct_negativos:.0%}",
                  ", ".join(f"{t} ({n})" for t, n in a.temas.get(f.producto, [])) or "sin tema claro")
                 for f in a.alertas.itertuples()]
        self.tabla_alertas.mostrar(["Producto", "% negativos", "Temas principales de queja"],
                                   filas or [("Sin alertas", "—", "Ningún producto supera el umbral")],
                                   {"Producto": 200, "Temas principales de queja": 380})

        self.tabla_clientes.mostrar(
            ["Cliente", "Comentarios", "Score", "Segmento", "Acción sugerida"],
            [(f.autor, f.comentarios, f"{f.score:.2f}", f.segmento, f.accion_sugerida)
             for f in a.segmentos.itertuples()], {"Cliente": 170, "Acción sugerida": 360})

        self.combo_f_producto["values"] = ["Todos"] + sorted(df["producto"].unique())
        self._llenar_comentarios()

    def _llenar_comentarios(self):
        if self._analisis is None or self._analisis.comentarios.empty:
            return
        df = self._analisis.comentarios
        if self.var_f_producto.get() != "Todos":
            df = df[df["producto"] == self.var_f_producto.get()]
        if self.var_f_sent.get() != "Todos":
            df = df[df["sentimiento"] == self.var_f_sent.get()]
        self.tabla_comentarios.mostrar(
            ["Producto", "Fuente", "Autor", "Sentimiento", "Texto"],
            [(f.producto, f.fuente, f.autor, f.sentimiento, f.texto) for f in df.itertuples()],
            {"Producto": 150, "Texto": 420})
