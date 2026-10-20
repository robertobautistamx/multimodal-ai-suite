"""Descarga del audio de videos en línea (YouTube, TikTok, Facebook público)."""
import tempfile
from pathlib import Path

import config


class DescargadorAudio:
    def descargar(self, url: str) -> Path:
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError("Instala yt-dlp:  pip install yt-dlp")
        config.asegurar_ffmpeg()
        carpeta = tempfile.mkdtemp()
        opciones = {
            "format": "bestaudio/best",
            "outtmpl": f"{carpeta}/audio.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        }
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.extract_info(url, download=True)
        return Path(carpeta) / "audio.wav"
