# modules/whatsapp_module.py
import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.memory_module import guardar_idea, consultar_ideas
from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes

app = Flask(__name__)

@app.get("/")
def home():
    return "Jarvis WhatsApp OK"

@app.get("/whatsapp")
def whatsapp_get():
    return "Endpoint WhatsApp OK (usa POST desde Twilio)"

# ---------- Utilidades de respuesta ----------

def mejorar_texto_rapido(texto: str) -> str:
    base = texto.strip()
    if len(base) < 10:
        return "Idea registrada. Siguiente paso: define objetivo y una acción concreta para hoy."
    return f"{base}\n\nSiguiente paso: prioriza, define un resultado medible y un primer bloque de 25 minutos."

def listar_ultimas_ideas(n=5) -> str:
    filas = consultar_ideas(limit=n)
    if not filas:
        return "Aún no tienes ideas registradas."
    out = ["🗂️ Últimas ideas:"]
    for _id, txt, fecha in filas:
        out.append(f"• {txt}  ({fecha})")
    return "\n".join(out)

def respuesta_inteligente(texto: str) -> str:
    """
    Responde menos hermético: reconoce, refleja y propone acción concreta.
    Comandos:
      - 'idea ...'
      - 'opina: ...'
      - 'listar ideas' / 'resume
