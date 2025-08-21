from gtts import gTTS
import os
import speech_recognition as sr

def hablar(texto, archivo="respuesta.mp3"):
    """Convierte texto en audio y lo reproduce"""
    tts = gTTS(text=texto, lang='es')
    tts.save(archivo)
    os.system(f"start {archivo}")  # Windows; en Linux/Mac usar "afplay" o "mpg123"

def escuchar():
    """Escucha desde micrófono y convierte a texto"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Jarvis escuchando...")
        audio = r.listen(source)
        try:
            return r.recognize_google(audio, language="es-ES")
        except sr.UnknownValueError:
            return "No entendí lo que dijiste"
        except sr.RequestError:
            return "Error al conectar con el servicio de voz"
