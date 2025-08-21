import schedule
import time
from modules.memory_module import consultar_ideas

def enviar_resumen():
    ideas = consultar_ideas()
    if not ideas:
        resumen = "No tienes ideas registradas hoy."
    else:
        resumen = "Resumen de tus últimas ideas:\n"
        for id_, texto, fecha in ideas:
            resumen += f"- {texto} ({fecha})\n"
    print(resumen)  # aquí luego lo mandaremos por WhatsApp

def iniciar_automatizacion():
    schedule.every().day.at("20:00").do(enviar_resumen)
    while True:
        schedule.run_pending()
        time.sleep(60)
