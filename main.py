from modules.whatsapp_module import app
from modules.automation_module import iniciar_automatizacion
import threading

if __name__ == "__main__":
    print("🚀 Jarvis WhatsApp server en /whatsapp")

    # Automatizaciones en hilo aparte
    t = threading.Thread(target=iniciar_automatizacion, daemon=True)
    t.start()

    # Flask sirve /static para los MP3 de voz
    app.run(port=5000)
