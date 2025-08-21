# modules/transcribe_module.py
import os
import io
import requests
from openai import OpenAI

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

client = OpenAI(api_key=OPENAI_API_KEY)

def descargar_media_twilio(media_url: str) -> bytes:
    """
    Descarga el binario del audio desde Twilio (requiere auth básica).
    media_url viene del webhook: MediaUrl0
    """
    # Auth básica con SID y TOKEN de Twilio
    resp = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=30)
    resp.raise_for_status()
    return resp.content

def transcribir_audio_bytes(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    """
    Envía los bytes a Whisper (OpenAI) y devuelve el texto.
    Acepta ogg/opus, m4a, mp3, wav, etc.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("Falta OPENAI_API_KEY en Config Vars")

    # Pasamos los bytes como archivo in-memory
    file_like = io.BytesIO(audio_bytes)
    file_like.name = filename  # sugerir extensión ayuda al decoder

    # Modelo de transcripción
    # whisper-1 es el endpoint estándar de OpenAI para STT
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=file_like,
        language="es"  # forzar español si prefieres
    )
    return result.text.strip() if hasattr(result, "text") else str(result)
