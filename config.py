"""Configuración central del producto integrador."""
import os
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "datos"
MODELOS = RAIZ / "modelos"
DB_PATH = DATOS / "integrador.db"
CARPETA_IMAGENES = DATOS / "Imagenes"
CSV_EJEMPLO = DATOS / "comentarios_ejemplo.csv"

# ---- Transcriptor ----
MODELO_WHISPER = "base"          # tiny, base, small, medium, large

# ---- CRM ----
UMBRAL_POSITIVOS = 0.30          # >= 30% positivos => producto destacado
UMBRAL_NEGATIVOS = 0.30          # >= 30% negativos => alerta
MIN_COMENTARIOS = 3              # mínimo de comentarios para que cuente el porcentaje
UMBRAL_PROMOTOR = 0.25           # score promedio > 0.25 promotor, < -0.25 detractor
PRODUCTOS_DEMO = ["Audífonos Pulse X", "Cargador Rápido 65W", "Smartwatch Orbit", "Bocina Boom Mini"]

# ---- Clasificador RGB ----
K_POR_DEFECTO = 3
UMBRAL_DISTANCIA_RGB = 100.0
MAX_IMAGENES_POR_PERSONA = 7

# ---- Emociones de YouTube (Ollama) ----
OLLAMA_BASE = "http://localhost:11434"
OLLAMA_MODELO = "llama3.1"
EMOCIONES = ["alegría", "tristeza", "enojo", "miedo", "desagrado"]

# ---- MediaPipe (gestos) ----
MEDIAPIPE_MODELO = MODELOS / "hand_landmarker.task"
MEDIAPIPE_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
                 "hand_landmarker/float16/1/hand_landmarker.task")
CAMARA = 0


def asegurar_directorios() -> None:
    for carpeta in (DATOS, MODELOS, CARPETA_IMAGENES):
        carpeta.mkdir(parents=True, exist_ok=True)


def asegurar_ffmpeg() -> bool:
    """Si ffmpeg no está en el PATH, lo busca donde lo instala winget y lo agrega."""
    if shutil.which("ffmpeg"):
        return True
    base = os.environ.get("LOCALAPPDATA")
    if base:
        for exe in Path(base, "Microsoft", "WinGet").rglob("ffmpeg.exe"):
            os.environ["PATH"] += os.pathsep + str(exe.parent)
            return True
    return False
