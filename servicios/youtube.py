"""Análisis de emociones en comentarios de YouTube con un LLM local (Ollama)."""
import json

import pandas as pd
import requests

import config


class ExtractorYouTube:
    """Obtiene datos del video y sus comentarios (scraping, sin API key)."""

    def info_video(self, url: str):
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError("Instala yt-dlp:  pip install yt-dlp")
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        return info.get("title", ""), (info.get("description") or "")[:1500]

    def comentarios(self, url: str, limite: int = 50):
        try:
            from youtube_comment_downloader import SORT_BY_POPULAR, YoutubeCommentDownloader
        except ImportError:
            raise RuntimeError("Instala:  pip install youtube-comment-downloader")
        resultado = []
        for c in YoutubeCommentDownloader().get_comments_from_url(url, sort_by=SORT_BY_POPULAR):
            resultado.append({"autor": c.get("author", ""), "texto": c.get("text", "")})
            if len(resultado) >= limite:
                break
        return resultado


class AnalizadorEmociones:
    """Pide a Ollama la relación del comentario con el video y su emoción dominante."""

    def __init__(self, modelo=config.OLLAMA_MODELO, base=config.OLLAMA_BASE, emociones=None):
        self.modelo = modelo
        self.base = base
        self.emociones = emociones or config.EMOCIONES

    def verificar(self) -> None:
        try:
            requests.get(f"{self.base}/api/tags", timeout=3).raise_for_status()
        except Exception:
            raise ConnectionError(
                f"No se pudo conectar con Ollama. Ábrelo y ejecuta:  ollama pull {self.modelo}")

    def analizar(self, titulo: str, descripcion: str, comentario: str) -> dict:
        sistema = (
            "Analizas comentarios de YouTube sobre un video. Responde SOLO con JSON con las claves: "
            '"relacion" (alta, media, baja o ninguna: qué tanto se relaciona el comentario con el video), '
            f'"emocion" (una de: {", ".join(self.emociones)}, neutral) y '
            '"justificacion" (máximo 15 palabras, en español).')
        usuario = f"Video: {titulo}\nDescripción: {descripcion}\n\nComentario: {comentario}"
        r = requests.post(f"{self.base}/api/chat", json={
            "model": self.modelo, "stream": False, "format": "json", "options": {"temperature": 0},
            "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
        }, timeout=180)
        r.raise_for_status()
        try:
            datos = json.loads(r.json()["message"]["content"])
        except (ValueError, KeyError):
            datos = {}
        emocion = str(datos.get("emocion", "neutral")).lower().strip()
        if emocion not in self.emociones:
            emocion = "neutral"
        return {"relacion": str(datos.get("relacion", "ninguna")).lower().strip(),
                "emocion": emocion,
                "justificacion": str(datos.get("justificacion", "")).strip()}


class ServicioYouTube:
    def __init__(self, extractor: ExtractorYouTube, analizador: AnalizadorEmociones):
        self.extractor = extractor
        self.analizador = analizador

    def analizar_video(self, url: str, limite: int = 50, progreso=None) -> pd.DataFrame:
        self.analizador.verificar()
        titulo, descripcion = self.extractor.info_video(url)
        comentarios = self.extractor.comentarios(url, limite)
        if not comentarios:
            raise ValueError("No se encontraron comentarios (¿están desactivados?).")
        filas = []
        for i, c in enumerate(comentarios, start=1):
            filas.append({**c, **self.analizador.analizar(titulo, descripcion, c["texto"])})
            if progreso:
                progreso(i, len(comentarios))
        return pd.DataFrame(filas)

    @staticmethod
    def resumen(df: pd.DataFrame):
        """Devuelve (emoción dominante, conteo por emoción)."""
        if df.empty:
            return "—", {}
        conteo = df["emocion"].value_counts()
        return conteo.index[0], conteo.to_dict()

    @staticmethod
    def exportar_csv(df: pd.DataFrame, ruta) -> None:
        df.to_csv(ruta, index=False, encoding="utf-8-sig")
