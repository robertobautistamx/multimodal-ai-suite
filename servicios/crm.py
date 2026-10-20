"""CRM de comentarios: repositorio, reglas de negocio y servicio."""
from datetime import date
from pathlib import Path
from typing import NamedTuple

import pandas as pd

import config
from .base_datos import BaseDatos

COLUMNAS_REQUERIDAS = ["producto", "fuente", "autor", "texto"]


class RepositorioComentarios:
    def __init__(self, bd: BaseDatos):
        self.bd = bd

    def insertar(self, producto, fuente, autor, texto, sentimiento, score, temas, fecha):
        with self.bd.conexion() as c:
            c.execute(
                "INSERT INTO comentarios (producto, fuente, autor, texto, sentimiento, score, temas, fecha) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (producto, fuente, autor, texto, sentimiento, score, ",".join(temas), fecha))

    def listar(self) -> pd.DataFrame:
        with self.bd.conexion() as c:
            return pd.read_sql_query("SELECT * FROM comentarios", c)

    def vaciar(self):
        with self.bd.conexion() as c:
            c.execute("DELETE FROM comentarios")


class ReglasCRM:
    """Ranking, alertas, temas y segmentación (sin acceso a datos ni interfaz)."""

    @staticmethod
    def resumen_productos(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        g = df.groupby("producto")
        res = pd.DataFrame({
            "comentarios": g.size(),
            "pct_positivos": g["sentimiento"].apply(lambda s: (s == "positivo").mean()),
            "pct_neutros": g["sentimiento"].apply(lambda s: (s == "neutro").mean()),
            "pct_negativos": g["sentimiento"].apply(lambda s: (s == "negativo").mean()),
            "score_promedio": g["score"].mean(),
        })
        res["destacado"] = ((res["pct_positivos"] >= config.UMBRAL_POSITIVOS)
                            & (res["comentarios"] >= config.MIN_COMENTARIOS))
        res = res.sort_values(["destacado", "pct_positivos", "score_promedio"], ascending=False)
        res.insert(0, "ranking", range(1, len(res) + 1))
        return res.reset_index()

    @staticmethod
    def alertas(resumen: pd.DataFrame) -> pd.DataFrame:
        if resumen.empty:
            return resumen
        return resumen[(resumen["pct_negativos"] >= config.UMBRAL_NEGATIVOS)
                       & (resumen["comentarios"] >= config.MIN_COMENTARIOS)
                       ].sort_values("pct_negativos", ascending=False)

    @staticmethod
    def temas_por_producto(df: pd.DataFrame, sentimiento: str = "negativo", top: int = 3) -> dict:
        out = {}
        for producto, sub in df[df["sentimiento"] == sentimiento].groupby("producto"):
            conteo = {}
            for celda in sub["temas"].fillna(""):
                for t in filter(None, celda.split(",")):
                    conteo[t] = conteo.get(t, 0) + 1
            out[producto] = sorted(conteo.items(), key=lambda x: -x[1])[:top]
        return out

    @staticmethod
    def segmentar_clientes(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        por_autor = (df.groupby("autor")
                     .agg(comentarios=("texto", "size"), score=("score", "mean")).reset_index())
        u = config.UMBRAL_PROMOTOR
        por_autor["segmento"] = por_autor["score"].apply(
            lambda s: "Promotor" if s > u else "Detractor" if s < -u else "Neutro")
        acciones = {
            "Promotor": "Ofrecer cupón de referidos / pedir reseña pública",
            "Neutro": "Enviar encuesta breve y recomendaciones",
            "Detractor": "Contacto de atención al cliente y compensación",
        }
        por_autor["accion_sugerida"] = por_autor["segmento"].map(acciones)
        return por_autor.sort_values("score", ascending=False)


class AnalisisCRM(NamedTuple):
    comentarios: pd.DataFrame
    resumen: pd.DataFrame
    alertas: pd.DataFrame
    temas: dict
    segmentos: pd.DataFrame


class ServicioCRM:
    """Orquesta la entrada de datos (texto, CSV/JSON, audio, video, enlaces) y el análisis."""

    def __init__(self, repositorio, analizador, extractor_temas, transcripcion, descargador):
        self.repo = repositorio
        self.analizador = analizador
        self.extractor = extractor_temas
        self.transcripcion = transcripcion
        self.descargador = descargador

    # ---- entrada de datos ----
    def registrar_texto(self, producto, fuente, autor, texto, fecha=None) -> None:
        texto = str(texto).strip()
        if not texto:
            return
        etiqueta, score = self.analizador.analizar(texto)
        self.repo.insertar(
            str(producto).strip(), str(fuente).strip(), str(autor).strip() or "anónimo", texto,
            etiqueta, score, self.extractor.extraer(texto), str(fecha) if fecha else date.today().isoformat())

    def cargar_archivo(self, ruta, progreso=None) -> int:
        """CSV o JSON con columnas producto, fuente, autor, texto (y fecha opcional)."""
        ruta = Path(ruta)
        df = pd.read_json(ruta) if ruta.suffix.lower() == ".json" else pd.read_csv(ruta)
        faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
        if faltan:
            raise ValueError(f"Faltan columnas: {faltan}. Se requieren: {COLUMNAS_REQUERIDAS}")
        if "fecha" not in df.columns:
            df["fecha"] = date.today().isoformat()
        total = len(df)
        for i, fila in enumerate(df.itertuples(index=False), start=1):
            self.registrar_texto(fila.producto, fila.fuente, fila.autor, fila.texto, fila.fecha)
            if progreso:
                progreso(i, total)
        return total

    def procesar_media(self, ruta, producto: str, autor: str = "cliente (voz)") -> str:
        fuente = self.transcripcion.tipo_archivo(ruta)
        texto = self.transcripcion.transcribir(ruta)
        self.registrar_texto(producto, fuente, autor, texto)
        return texto

    def procesar_enlace(self, url: str, producto: str, autor: str = "cliente (video en línea)") -> str:
        ruta = self.descargador.descargar(url)
        texto = self.transcripcion.transcribir(ruta)
        self.registrar_texto(producto, "Video (enlace)", autor, texto)
        return texto

    # ---- consulta ----
    def productos(self) -> list:
        df = self.repo.listar()
        existentes = set(df["producto"]) if not df.empty else set()
        return sorted(existentes | set(config.PRODUCTOS_DEMO))

    def analisis(self) -> AnalisisCRM:
        df = self.repo.listar()
        if df.empty:
            return AnalisisCRM(df, pd.DataFrame(), pd.DataFrame(), {}, pd.DataFrame())
        resumen = ReglasCRM.resumen_productos(df)
        return AnalisisCRM(df, resumen, ReglasCRM.alertas(resumen),
                           ReglasCRM.temas_por_producto(df), ReglasCRM.segmentar_clientes(df))

    def vaciar(self) -> None:
        self.repo.vaciar()
