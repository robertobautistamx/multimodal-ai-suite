"""Transcripción de audio y video a texto (Whisper)."""
import subprocess
import threading
from pathlib import Path

import numpy as np

import config


class ServicioTranscripcion:
    """Carga Whisper una sola vez y lo comparte entre el Transcriptor y el CRM."""

    EXT_VIDEO = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    EXT_AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}

    def __init__(self, modelo: str = config.MODELO_WHISPER):
        self.nombre_modelo = modelo
        self._modelo = None
        self._backend = None
        self._lock = threading.Lock()

    @classmethod
    def tipo_archivo(cls, ruta) -> str:
        ext = Path(ruta).suffix.lower()
        if ext in cls.EXT_VIDEO:
            return "Video"
        if ext in cls.EXT_AUDIO:
            return "Audio"
        raise ValueError(f"Formato no soportado: {ext}")

    @property
    def cargado(self) -> bool:
        return self._modelo is not None

    def cambiar_modelo(self, nombre: str) -> None:
        with self._lock:
            if nombre != self.nombre_modelo:
                self.nombre_modelo = nombre
                self._modelo = None

    def cargar(self):
        with self._lock:
            if self._modelo is None:
                config.asegurar_ffmpeg()
                try:
                    import whisper
                    self._modelo = whisper.load_model(self.nombre_modelo)
                    self._backend = "whisper"
                except ImportError:
                    try:
                        from faster_whisper import WhisperModel
                    except ImportError:
                        raise RuntimeError("Instala Whisper:  pip install openai-whisper")
                    self._modelo = WhisperModel(self.nombre_modelo, device="cpu", compute_type="int8")
                    self._backend = "faster-whisper"
        return self._modelo

    def transcribir(self, ruta, idioma: str = "es") -> str:
        modelo = self.cargar()
        if self._backend == "whisper":
            return modelo.transcribe(str(ruta), language=idioma, fp16=False)["text"].strip()
        audio = self._decodificar(ruta)
        segmentos, _ = modelo.transcribe(audio, language=idioma)
        return " ".join(s.text.strip() for s in segmentos).strip()

    @staticmethod
    def _decodificar(ruta):
        """Decodifica con ffmpeg a 16 kHz mono (evita problemas de PyAV)."""
        cmd = ["ffmpeg", "-nostdin", "-i", str(ruta), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"]
        try:
            r = subprocess.run(cmd, capture_output=True, check=True)
        except FileNotFoundError:
            raise RuntimeError("ffmpeg no está instalado o no está en el PATH.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError("ffmpeg no pudo leer el archivo: " + e.stderr.decode(errors="ignore")[-300:])
        return np.frombuffer(r.stdout, dtype=np.float32)
