# main.py
import os
import threading
from modules.whatsapp_module import app
from modules.automation_module import iniciar_automatizacion

# --- Healthchecks útiles para probar en el navegador ---
@app.get("/")
def home():
    return "Jarvis WhatsApp OK"

@app.get("/health")
def health():
    return {"status": "ok", "service": "jarvis-whatsapp"}

def run_schedulers():
    """
    Arranca las automatizaciones (resumen diario, etc.)
    En un hilo daemon para no bloquear el servidor Flask.
    """
    try:
        iniciar_automatizacion()
    except Exception as e:
        # Nunca tumbes el proceso por un fallo de scheduler
        print(f"[scheduler] error: {e}")

if __name__ == "__main__":
