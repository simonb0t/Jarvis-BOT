from __future__ import annotations
import os
import io
import requests
from pydub import AudioSegment
import speech_recognition as sr

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")

def descargar_media_twilio(media_url: str) -> bytes:
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None
    r = requests.get(media_url, stream=True, timeout=20, auth=auth)
    r.raise_for_status()
    return r.content

def _to_wav_bytes(data: bytes, content_hint: str = "ogg") -> bytes:
    buf_in = io.BytesIO(data)
    audio = AudioSegment.from_file(buf_in, format=content_hint)
    buf_out = io.BytesIO()
    audio.export(buf_out, format="wav")
    return buf_out.getvalue()

def transcribir_audio_bytes(data: bytes, ext_hint: str = "ogg") -> str:
    wav = _to_wav_bytes(data, content_hint=ext_hint)
    r = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(wav)) as source:
        audio = r.record(source)
    try:
        return r.recognize_google(audio, language="es-ES")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        raise RuntimeError(f"STT error: {e}")
