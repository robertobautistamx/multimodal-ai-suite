# Producto Integrador

Aplicación de escritorio (Tkinter) que reúne cinco programas en una sola ventana, una pestaña por módulo:

| Pestaña | Qué hace |
|---|---|
| CRM | Comentarios (CSV/JSON), audios, videos y enlaces → transcripción, sentimiento, ranking, alertas y segmentación de clientes |
| Emociones YouTube | Descarga comentarios de un video y un LLM local (Ollama) clasifica su relación con el video y su emoción |
| Gestos | Cámara + MediaPipe HandLandmarker: reconoce Puño, Uno, Dos, Tres, Cuatro, Mano abierta y Pulgar arriba |
| Transcriptor | Convierte audio o video en texto con Whisper (local) |
| Clasificador RGB | Promedio RGB de imágenes y clasificación KNN contra las personas guardadas (puerto del proyecto en C#) |

## Ejecutar
1. `py -m pip install -r requirements.txt`
2. ffmpeg instalado (si no está en el PATH, la app intenta encontrarlo en la carpeta de winget).
3. Para la pestaña de YouTube: Ollama abierto y `ollama pull llama3.1`.
4. `py main.py`

Cada dependencia pesada se importa solo al usar su módulo: si algo no está instalado (por ejemplo mediapipe), solo esa pestaña muestra un error y el resto sigue funcionando.

## Estructura (una clase por responsabilidad)
```
main.py                     punto de entrada
config.py                   rutas, umbrales y parámetros (todo ajustable en un solo lugar)
servicios/                  lógica, sin interfaz
  base_datos.py             BaseDatos            SQLite compartido
  transcripcion.py          ServicioTranscripcion  Whisper (se carga una vez y se comparte)
  descarga.py               DescargadorAudio       yt-dlp
  sentimiento.py            AnalizadorSentimiento, ExtractorTemas
  crm.py                    RepositorioComentarios, ReglasCRM, ServicioCRM
  rgb.py                    ProcesadorImagenRGB, ClasificadorKNN, RepositorioRGB, ServicioRGB
  youtube.py                ExtractorYouTube, AnalizadorEmociones, ServicioYouTube
  gestos.py                 ClasificadorGestos, ServicioGestos
ui/                         interfaz
  estilos.py                paleta, BotonModerno, estilos ttk
  widgets.py                TablaDatos, CajaTexto, GraficaSentimientos, BarraColor
  utilidades.py             EjecutorAsincrono (tareas largas sin congelar la ventana)
  pestana_base.py           PestanaBase (tarjeta de estado + barra de progreso)
  pestana_*.py              una clase por pestaña
  ventana_principal.py      AplicacionIntegradora (crea los servicios y los reparte)
datos/                      base de datos, imágenes y CSV de ejemplo
modelos/                    modelo de MediaPipe (se descarga solo)
```

## Cómo agregar otro módulo
1. Crea la lógica en `servicios/mi_modulo.py` (sin importar tkinter).
2. Crea `ui/pestana_mi_modulo.py` con una clase que herede de `PestanaBase`.
3. Registra el servicio y la pestaña en `ui/ventana_principal.py`.

## Ajustes comunes (config.py)
- `MODELO_WHISPER`: tiny, base, small o medium (más grande = más preciso y más lento).
- `OLLAMA_MODELO` y `EMOCIONES`: modelo y lista de emociones de la pestaña de YouTube.
- `UMBRAL_POSITIVOS`, `UMBRAL_NEGATIVOS`, `MIN_COMENTARIOS`: reglas del CRM.
- `K_POR_DEFECTO`, `UMBRAL_DISTANCIA_RGB`, `MAX_IMAGENES_POR_PERSONA`: clasificador RGB.
- `CAMARA`: índice de la cámara para los gestos.
