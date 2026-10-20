"""Análisis de sentimiento y extracción de temas."""
import re
import unicodedata


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9\s]", " ", texto)


class AnalizadorSentimiento:
    """Usa pysentimiento (IA en español); si no está, usa un lexicón de respaldo."""

    POSITIVAS = {
        "excelente", "bueno", "buena", "buenisimo", "genial", "recomiendo", "recomendado", "perfecto",
        "increible", "encanta", "encanto", "rapido", "util", "calidad", "satisfecho", "funciona",
        "barato", "mejor", "feliz", "contento", "contenta", "vale", "duradero", "comodo", "cumple",
        "espectacular", "lindo", "bonito", "fantastico", "agradecido", "buen",
    }
    NEGATIVAS = {
        "malo", "mala", "pesimo", "pesima", "terrible", "horrible", "defectuoso", "roto", "rompio",
        "tarde", "lento", "caro", "decepcion", "decepcionado", "decepcionante", "fraude", "estafa",
        "basura", "falla", "fallo", "devolver", "devolucion", "queja", "peor", "nunca", "garantia",
        "dejo", "inservible", "mal", "incomodo", "sucio", "falso", "enganoso",
    }
    NEGADORES = {"no", "nunca", "ni", "tampoco", "sin"}

    def __init__(self):
        self._modelo = None
        self._intentado = False

    def _cargar_modelo(self):
        if not self._intentado:
            self._intentado = True
            try:
                from pysentimiento import create_analyzer
                self._modelo = create_analyzer(task="sentiment", lang="es")
            except Exception:
                self._modelo = None
        return self._modelo

    @property
    def motor(self) -> str:
        if not self._intentado:
            return "sin cargar"
        return "pysentimiento (IA)" if self._modelo is not None else "lexicón de respaldo"

    def analizar(self, texto: str):
        """Devuelve (etiqueta, score) con score en [-1, 1]."""
        modelo = self._cargar_modelo()
        if modelo is not None:
            try:
                r = modelo.predict(texto)
                etiqueta = {"POS": "positivo", "NEG": "negativo", "NEU": "neutro"}[r.output]
                return etiqueta, float(r.probas["POS"] - r.probas["NEG"])
            except Exception:
                pass
        return self._por_lexicon(texto)

    def _por_lexicon(self, texto: str):
        tokens = normalizar(texto).split()
        puntos = 0
        for i, t in enumerate(tokens):
            signo = 1 if t in self.POSITIVAS else -1 if t in self.NEGATIVAS else 0
            if signo == 0:
                continue
            if any(p in self.NEGADORES for p in tokens[max(0, i - 2):i]):
                signo = -signo
            puntos += signo
        score = max(-1.0, min(1.0, puntos / 3))
        if score > 0.1:
            return "positivo", score
        if score < -0.1:
            return "negativo", score
        return "neutro", 0.0


class ExtractorTemas:
    TEMAS = {
        "batería": ["bateria", "carga", "dura", "autonomia"],
        "envío": ["envio", "llego", "entrega", "paqueteria", "tarde", "paquete"],
        "precio": ["precio", "caro", "barato", "costo", "vale", "oferta"],
        "calidad": ["calidad", "material", "roto", "rompio", "defectuoso", "duradero", "resistente"],
        "sonido": ["sonido", "audio", "bajos", "volumen", "ruido", "microfono"],
        "atención al cliente": ["atencion", "servicio", "garantia", "soporte", "devolucion", "devolver"],
        "diseño": ["diseno", "color", "bonito", "lindo", "comodo", "incomodo", "tamano"],
    }

    def extraer(self, texto: str):
        tokens = set(normalizar(texto).split())
        return [tema for tema, palabras in self.TEMAS.items() if any(p in tokens for p in palabras)]
