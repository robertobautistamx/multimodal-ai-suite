"""Ejecución de tareas largas en segundo plano sin congelar la interfaz."""
import queue
import threading


class EjecutorAsincrono:
    """Corre una función en un hilo y entrega sus resultados en el hilo de Tkinter."""

    def __init__(self, raiz, intervalo_ms: int = 100):
        self.raiz = raiz
        self.intervalo = intervalo_ms
        self._cola = queue.Queue()
        self.raiz.after(self.intervalo, self._procesar)

    def ejecutar(self, tarea, al_terminar=None, al_error=None, al_progreso=None):
        """tarea(reportar) -> resultado. `reportar(a, b)` llama a al_progreso(a, b) en la interfaz."""
        def reportar(*args):
            if al_progreso:
                self._cola.put(("progreso", al_progreso, args))

        def trabajo():
            try:
                resultado = tarea(reportar)
                self._cola.put(("ok", al_terminar, (resultado,)))
            except Exception as e:
                self._cola.put(("error", al_error, (e,)))

        threading.Thread(target=trabajo, daemon=True).start()

    def _procesar(self):
        try:
            while True:
                _, callback, args = self._cola.get_nowait()
                if callback:
                    callback(*args)
        except queue.Empty:
            pass
        self.raiz.after(self.intervalo, self._procesar)
