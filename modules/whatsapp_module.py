from __future__ import annotations
import re
from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.web_search_module import handle_smart_query, web_images_answer
from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes

whatsapp_bp = Blueprint("whatsapp", __name__)

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _as_int(s: str, default: int = 0) -> int:
    try:
        return int(s or default)
    except Exception:
        return default

def _is_audio(ct: str, url: str) -> tuple[bool, str]:
    """Devuelve (es_audio, ext_hint)."""
    ct = (ct or "").lower()
    u  = (url or "").lower()
    if ct.startswith("audio") or ct == "application/ogg":
        if "ogg" in ct or "opus" in ct: return True, "ogg"
        if "mp3" in ct: return True, "mp3"
        if "aac" in ct: return True, "aac"
        if "m4a" in ct or "mp4" in ct: return True, "m4a"
        return True, "ogg"
    for ext in ("ogg", "mp3", "aac", "m4a"):
        if u.endswith(f".{ext}"):
            return True, ext
    return False, "ogg"

@whatsapp_bp.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    body = _clean(request.form.get("Body", ""))
    num_media = _as_int(request.form.get("NumMedia", "0"), 0)

    resp = MessagingResponse()
    msg = resp.message()

    try:
        low = body.lower()

        # ===== TRANSCRIPCIÓN BAJO DEMANDA =====
        wants_transcribe = any(k in low for k in ("transcribe", "transcribir", "transcripción", "transcripcion"))
        if wants_transcribe:
            if num_media == 0:
                msg.body("Ok. Envíame una *nota de voz* (o reenvíala) junto con la palabra *transcribe* en el pie del audio.")
                return str(resp)

            # Tomamos el primer media que parezca audio
            for i in range(num_media):
                ct = request.form.get(f"MediaContentType{i}", "") or ""
                url = request.form.get(f"MediaUrl{i}", "") or ""
                es_audio, ext = _is_audio(ct, url)
                if es_audio and url:
                    try:
                        raw = descargar_media_twilio(url)
                        texto = transcribir_audio_bytes(raw, ext_hint=ext) or "(no entendí el audio)"
                        msg.body(f"📝 Transcripción: {texto}")
                        return str(resp)
                    except Exception as e:
                        msg.body(f"No pude transcribir ahora. Tip: asegúrate de hablar claro y que el audio sea de WhatsApp.\nError: {e}")
                        return str(resp)

            msg.body("No detecté audio en tu mensaje. Reenvíalo con *transcribe*.")
            return str(resp)

        # ===== SI HAY AUDIO PERO NO LO PEDISTE → NO TRANSCRIBO =====
        if num_media > 0:
            # Respuesta discreta para no consumir STT si no lo pediste.
            msg.body("Audio recibido. Si quieres que lo *transcriba*, envíalo con la palabra *transcribe* en el pie del audio.")
            return str(resp)

        # ===== BÚSQUEDA WEB / IMÁGENES / HORA / CLIMA / PREGUNTAS =====
        if not body:
            msg.body("No recibí mensaje.")
            return str(resp)

        # Imagen explícita: atajo (“imagen de X”)
        if any(k in low for k in ("imagen", "imagenes", "imágenes", "foto", "fotos")):
            topic = re.sub(r"\b(imagen(es)?|foto(s)?|de|del|la|el)\b", " ", low).strip()
            msg.body(web_images_answer(topic or body))
            return str(resp)

        # Resto: router inteligente
        msg.body(handle_smart_query(body))
        return str(resp)

    except Exception as e:
        msg.body(f"⚠️ Ocurrió un error procesando tu mensaje: {e}")
        return str(resp)
