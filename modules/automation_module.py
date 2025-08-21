import schedule
import time
from modules.memory_module import consultar_ideas

def resumen_texto():
    ideas = consultar_ideas()
    if not ideas:
        return "No tienes ideas registradas aún."
    out = ["Resumen de tus últimas ideas:"]
    for _, texto, fecha in ideas:
        out.append(f"- {texto} ({fecha})")
    return "\n".join(out)

def enviar_resumen():
    # Por ahora imprime; si quieres, puedes integrarlo a WhatsApp con Twilio REST.
    print(resumen_texto())

def iniciar_automatizacion():
    schedule.every().day.at("20:00").do(enviar_resumen)
    while True:
        schedule.run_pending()
        time.sleep(60)
