"""Clasificador RGB (puerto del proyecto en C#): promedios, KNN y almacenamiento."""
import math
import shutil
import uuid
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

import numpy as np
from PIL import Image

import config
from .base_datos import BaseDatos

EPSILON = 1e-6


class MuestraRGB(NamedTuple):
    nombre: str
    r: int
    g: int
    b: int


class ProcesadorImagenRGB:
    @staticmethod
    def calcular_promedios(ruta_imagen):
        """Promedio de los canales R, G y B de toda la imagen (enteros)."""
        with Image.open(ruta_imagen) as img:
            pixeles = np.asarray(img.convert("RGB"), dtype=np.float64)
        r, g, b = pixeles.reshape(-1, 3).mean(axis=0)
        return round(r), round(g), round(b)


class ClasificadorKNN:
    """KNN con distancia euclidiana en RGB y voto ponderado por 1/distancia."""

    def __init__(self, k=config.K_POR_DEFECTO, umbral=config.UMBRAL_DISTANCIA_RGB):
        self.k = k
        self.umbral = umbral

    def clasificar(self, muestras, r, g, b):
        if not muestras:
            return "Desconocido", -1.0
        vecinos = sorted(
            ((m.nombre, math.dist((m.r, m.g, m.b), (r, g, b))) for m in muestras),
            key=lambda v: v[1])[: min(self.k, len(muestras))]
        votos = defaultdict(float)
        for nombre, distancia in vecinos:
            votos[nombre] += 1.0 / (distancia + EPSILON)
        ganador = max(votos, key=votos.get)
        distancia_ganador = min(d for n, d in vecinos if n == ganador)
        if distancia_ganador > self.umbral:
            return "Desconocido", distancia_ganador
        return ganador, distancia_ganador


class RepositorioRGB:
    def __init__(self, bd: BaseDatos, carpeta_imagenes):
        self.bd = bd
        self.carpeta_imagenes = Path(carpeta_imagenes)
        self.carpeta_imagenes.mkdir(parents=True, exist_ok=True)

    def siguiente_identificador(self) -> str:
        with self.bd.conexion() as c:
            numeros = [int(i) for (i,) in c.execute("SELECT Identificador FROM Persona") if i.isdigit()]
        return f"{max(numeros, default=0) + 1:04d}"

    def cantidad_imagenes(self, identificador) -> int:
        with self.bd.conexion() as c:
            return c.execute(
                """SELECT COUNT(*) FROM ImagenRGB i JOIN Persona p ON p.Id = i.PersonaId
                   WHERE p.Identificador = ?""", (identificador,)).fetchone()[0]

    def guardar(self, nombre, identificador, ruta_original, r, g, b) -> None:
        """Copia la imagen y registra persona + imagen en una transacción."""
        extension = Path(ruta_original).suffix or ".jpg"
        destino = self.carpeta_imagenes / f"{uuid.uuid4().hex}{extension}"
        shutil.copy2(ruta_original, destino)
        try:
            with self.bd.conexion() as c:
                fila = c.execute("SELECT Id FROM Persona WHERE Identificador = ?", (identificador,)).fetchone()
                persona_id = fila[0] if fila else c.execute(
                    "INSERT INTO Persona (Nombre, Identificador) VALUES (?, ?)",
                    (nombre, identificador)).lastrowid
                c.execute(
                    """INSERT INTO ImagenRGB (PersonaId, NombreImagen, RutaImagen, PromedioR, PromedioG, PromedioB)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (persona_id, Path(ruta_original).name, str(destino), r, g, b))
        except Exception:
            destino.unlink(missing_ok=True)
            raise

    def muestras(self):
        with self.bd.conexion() as c:
            filas = c.execute(
                """SELECT p.Nombre, i.PromedioR, i.PromedioG, i.PromedioB
                   FROM ImagenRGB i JOIN Persona p ON i.PersonaId = p.Id""").fetchall()
        return [MuestraRGB(*f) for f in filas]


class ServicioRGB:
    """Fachada que usa la interfaz."""

    def __init__(self, repositorio: RepositorioRGB, clasificador: ClasificadorKNN = None):
        self.repo = repositorio
        self.clasificador = clasificador or ClasificadorKNN()

    def analizar_imagen(self, ruta):
        return ProcesadorImagenRGB.calcular_promedios(ruta)

    def siguiente_identificador(self) -> str:
        return self.repo.siguiente_identificador()

    def clasificar(self, r, g, b):
        return self.clasificador.clasificar(self.repo.muestras(), r, g, b)

    def guardar(self, nombre, identificador, ruta, r, g, b) -> int:
        """Guarda la muestra y devuelve cuántas imágenes tiene ya esa persona."""
        if self.repo.cantidad_imagenes(identificador) >= config.MAX_IMAGENES_POR_PERSONA:
            raise ValueError(f"Esta persona ya tiene el máximo de {config.MAX_IMAGENES_POR_PERSONA} imágenes.")
        self.repo.guardar(nombre, identificador, ruta, r, g, b)
        return self.repo.cantidad_imagenes(identificador)
