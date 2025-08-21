import os
from twilio.rest import Client

_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
_from = os.getenv("TWILIO_WHATSAPP_FROM")

_client = Client(_account_sid, _auth_token)

def send_whatsapp_reply(message: str, to_number: str):
    """
    to_number llega como 'whatsapp:+<pais><numero>' desde Twilio.
    """
    _client.messages.create(
        body=message,
        from_=_from,
        to=to_number
    )
