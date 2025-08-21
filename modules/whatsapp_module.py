from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.web_search_module import handle_smart_query

whatsapp_bp = Blueprint("whatsapp", __name__)

@whatsapp_bp.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    resp = MessagingResponse()
    msg = resp.message()

    if not incoming_msg:
        msg.body("No recibí ningún mensaje 📭")
        return str(resp)

    try:
        respuesta = handle_smart_query(incoming_msg)
        msg.body(respuesta)
    except Exception as e:
        msg.body(f"⚠️ Error procesando tu mensaje: {e}")

    return str(resp)
