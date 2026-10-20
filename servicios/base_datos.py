"""Acceso a SQLite compartido por todos los módulos."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class BaseDatos:
    """Una sola base de datos con las tablas del CRM y del clasificador RGB."""

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self._crear_tablas()

    @contextmanager
    def conexion(self):
        conn = sqlite3.connect(self.ruta)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _crear_tablas(self):
        with self.conexion() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS comentarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto TEXT NOT NULL, fuente TEXT NOT NULL, autor TEXT NOT NULL,
                texto TEXT NOT NULL, sentimiento TEXT NOT NULL, score REAL NOT NULL,
                temas TEXT, fecha TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS Persona (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Nombre TEXT NOT NULL,
                Identificador TEXT UNIQUE NOT NULL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS ImagenRGB (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                PersonaId INTEGER NOT NULL,
                NombreImagen TEXT NOT NULL,
                RutaImagen TEXT NOT NULL DEFAULT '',
                PromedioR INTEGER NOT NULL, PromedioG INTEGER NOT NULL, PromedioB INTEGER NOT NULL,
                FOREIGN KEY(PersonaId) REFERENCES Persona(Id) ON DELETE CASCADE)""")
