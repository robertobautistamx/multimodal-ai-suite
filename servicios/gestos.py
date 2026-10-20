"""Reconocimiento de gestos de la mano con MediaPipe HandLandmarker."""
import math
import threading
import time
import urllib.request

import config

CONEXIONES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11),
              (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]
NOMBRES = {0: "Puño", 1: "Uno", 2: "Dos / Paz", 3: "Tres", 4: "Cuatro", 5: "Mano abierta"}


class ClasificadorGestos:
    """Cuenta dedos extendidos con distancias (no depende de la orientación de la mano)."""

    PUNTAS = (8, 12, 16, 20)
    ARTICULACIONES = (6, 10, 14, 18)

    @staticmethod
    def _dist(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    @classmethod
    def dedos_extendidos(cls, pts):
        """Lista [pulgar, índice, medio, anular, meñique] con True si está extendido."""
        pulgar = cls._dist(pts[4], pts[17]) > cls._dist(pts[3], pts[17])
        otros = [cls._dist(pts[p], pts[0]) > cls._dist(pts[a], pts[0])
                 for p, a in zip(cls.PUNTAS, cls.ARTICULACIONES)]
        return [pulgar] + otros

    @classmethod
    def nombre(cls, pts) -> str:
        dedos = cls.dedos_extendidos(pts)
        if dedos == [True, False, False, False, False] and pts[4].y < pts[0].y:
            return "Pulgar arriba"
        return NOMBRES[sum(dedos)]


class ServicioGestos:
    """Abre la cámara en un hilo y publica el último gesto detectado."""

    VENTANA = "Gestos MediaPipe (q o Esc para cerrar)"

    def __init__(self):
        self.ultimo_gesto = "—"
        self.error = None
        self._activo = False
        self._hilo = None

    @property
    def activo(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive()

    def iniciar(self):
        if self.activo:
            return
        self.error = None
        self._activo = True
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def detener(self):
        self._activo = False

    @staticmethod
    def _asegurar_modelo():
        ruta = config.MEDIAPIPE_MODELO
        if not ruta.exists():
            ruta.parent.mkdir(parents=True, exist_ok=True)
            try:
                urllib.request.urlretrieve(config.MEDIAPIPE_URL, ruta)
            except Exception:
                ruta.unlink(missing_ok=True)
                raise RuntimeError(
                    "No se pudo descargar el modelo de MediaPipe. Descárgalo de:\n"
                    f"{config.MEDIAPIPE_URL}\ny guárdalo como:\n{ruta}")
        return ruta

    @staticmethod
    def _dibujar(cv2, frame, pts):
        alto, ancho = frame.shape[:2]
        xy = [(int(p.x * ancho), int(p.y * alto)) for p in pts]
        for a, b in CONEXIONES:
            cv2.line(frame, xy[a], xy[b], (255, 140, 40), 2)
        for punto in xy:
            cv2.circle(frame, punto, 4, (40, 200, 60), -1)

    def _bucle(self):
        camara = None
        cv2 = None
        try:
            import cv2
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision

            ruta = self._asegurar_modelo()
            opciones = vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(ruta)),
                running_mode=vision.RunningMode.VIDEO, num_hands=1)
            camara = cv2.VideoCapture(config.CAMARA)
            if not camara.isOpened():
                raise RuntimeError("No se pudo abrir la cámara.")
            inicio = time.time()
            with vision.HandLandmarker.create_from_options(opciones) as detector:
                while self._activo:
                    ok, frame = camara.read()
                    if not ok:
                        break
                    frame = cv2.flip(frame, 1)
                    imagen = mp.Image(image_format=mp.ImageFormat.SRGB,
                                      data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    resultado = detector.detect_for_video(imagen, int((time.time() - inicio) * 1000))
                    gesto = "Sin mano"
                    if resultado.hand_landmarks:
                        pts = resultado.hand_landmarks[0]
                        gesto = ClasificadorGestos.nombre(pts)
                        self._dibujar(cv2, frame, pts)
                    self.ultimo_gesto = gesto
                    cv2.putText(frame, gesto, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 4)
                    cv2.putText(frame, gesto, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (37, 99, 235), 2)
                    cv2.imshow(self.VENTANA, frame)
                    if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                        break
                    if cv2.getWindowProperty(self.VENTANA, cv2.WND_PROP_VISIBLE) < 1:
                        break
        except Exception as e:
            self.error = str(e)
        finally:
            self._activo = False
            self.ultimo_gesto = "—"
            if camara is not None:
                camara.release()
            if cv2 is not None:
                try:
                    cv2.destroyAllWindows()
                except Exception:
                    pass
