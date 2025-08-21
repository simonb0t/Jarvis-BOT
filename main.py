from modules.whatsapp_module import recibir_mensaje, enviar_respuesta
from modules.voice_module import hablar
from modules.memory_module import guardar_idea, consultar_ideas

def procesar_input(input_text):
    # Guardar la idea automáticamente
    guardar_idea(input_text)
    # Responder con un mensaje
    respuesta = f"Jarvis ha registrado tu idea: {input_text}"
    return respuesta

# Este sería el main loop (simplificado)
if __name__ == "__main__":
    mensaje = recibir_mensaje()
    respuesta = procesar_input(mensaje)
    enviar_respuesta(respuesta)
    hablar(respuesta)
