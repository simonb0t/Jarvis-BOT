# modules/voice_module.py
import os
import time
from elevenlabs import ElevenLabs

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")  # tu dominio público (Heroku)
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "")

# ID de una voz española profunda creada con Voice Design (o usa uno de los presets españoles).
# Si aún no tienes una voz, ElevenLabs permite "Voice Design" para crearla y te da un voice_id.
VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "")  # opcional, si ya tienes uno

client = ElevenLabs(api_key=ELEVEN_API_KEY)

def synth_voice_filename(prefix="jarvis"):
    ts = int(time.time())
    return f"{prefix}_{ts}.mp3"

def hablar_epico(texto: str) -> str:
    """
    Convierte texto a voz (narrador grave en español), guarda en /static y
    devuelve la URL pública para enviarla por WhatsApp.
    """
    filename = synth_voice_filename()
    out_path = os.path.join("static", filename)

    # Si no tienes un VOICE_ID, usa 'voice_design' con parámetros en español.
    # Aquí usamos TTS normal indicando language y una voz grave si está disponible.
    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID or "Rachel",  # reemplaza por tu voz española si ya la creaste
        optimize_streaming_latency="0",
        output_format="mp3_44100_128",
        text=texto,
        model_id="eleven_multilingual_v2",  # soporte español
    )

    with open(out_path, "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)

    # URL pública al MP3 (Heroku sirve /static automáticamente en Flask si configuras static_folder)
    return f"{BASE_URL}/static/{filename}"
