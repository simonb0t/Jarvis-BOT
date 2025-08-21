from __future__ import annotations
import re
from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.web_search_module import handle_smart_query, web_images_answer

whatsapp_bp = Blueprint("whatsapp", __name__)

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

@whatsapp_bp.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    body = _clean(request.form.get("Body", ""))
    resp = MessagingResponse()
    msg = resp.message()

    if not body:
        msg.body("No recibí mensaje.")
        return str(resp)

    low = body.lower()

    # atajo explícito a imágenes
    if any(k in low for k in ("imagen", "imagenes", "imágenes", "foto", "fotos", "image", "picture")):
        topic = re.sub(r"\b(imagen(es)?|foto(s)?|de|del|la|el)\b", " ", low).strip()
        msg.body(web_images_answer(topic or body))
        return str(resp)

    # resto: router inteligente (hora, clima, preguntas abiertas)
    msg.body(handle_smart_query(body))
    return str(resp)
