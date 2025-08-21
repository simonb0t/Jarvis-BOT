import os
import tempfile
import requests
from twilio.http.http_client import TwilioHttpClient
from pydub import AudioSegment
import speech_recognition as sr

# Descarga media de Twilio con auth básica
_TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
_TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

def _download_media_to_wav(media_url: str) -> str:
    # Twilio media puede venir como .ogg - convertimos a .wav para SpeechRecognition
    with requests.get(media_url, auth=( _TWILIO_SID, _TWILIO_TOKEN ), stream=True) as r:
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp_in:
            for chunk in r.iter_content(chunk_size=8192):
                tmp_in.write(chunk)
            in_path = tmp_in.name

    # Detecta por contenido; pydub lee automáticamente
    audio = AudioSegment.from_file(in_path)
    out_fd = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    out_path = out_fd.name
    out_fd.close()
    audio.export(out_path, format="wav")
    return out_path

def transcribe_twilio_media(media_url: str) -> str:
    try:
        wav_path = _download_media_to_wav(media_url)
        rec = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = rec.record(source)
        text = rec.recognize_google(audio, language="es-ES")
        return text
    except sr.UnknownValueError:
        return ""
    except Exception:
        return ""

