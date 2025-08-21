import speech_recognition as sr

def audio_to_text(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="es-ES")
    except sr.UnknownValueError:
        return "No se entendió el audio."
    except sr.RequestError:
        return "Error con el servicio de reconocimiento."

