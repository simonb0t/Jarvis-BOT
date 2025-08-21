from modules.whatsapp_module import app
from modules.automation_module import iniciar_automatizacion
import threading

if __name__ == "__main__":
    print("🚀 Jarvis WhatsApp server corriendo en http://localhost:5000/whatsapp")

    # Hilo paralelo para las automatizaciones
    t = threading.Thread(target=iniciar_automatizacion, daemon=True)
    t.start()

    # Servidor Flask
    app.run(port=5000)
