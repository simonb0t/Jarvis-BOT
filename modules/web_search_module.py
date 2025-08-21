import requests
import os
from datetime import datetime

# Usa Tavily si quieres, pero por defecto metemos búsqueda web gratuita
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def search_web(query: str) -> str:
    """
    Realiza una búsqueda en internet y devuelve un resumen limpio.
    """
    try:
        if not TAVILY_API_KEY:
            # fallback simple con DuckDuckGo si no hay API key
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1"
            res = requests.get(url, timeout=10)
            data = res.json()
            if "AbstractText" in data and data["AbstractText"]:
                return data["AbstractText"]
            elif "RelatedTopics" in data and data["RelatedTopics"]:
                return data["RelatedTopics"][0].get("Text", "No encontré nada concreto.")
            else:
                return "No encontré resultados claros en la búsqueda."
        else:
            url = "https://api.tavily.com/search"
            headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
            res = requests.post(url, json={"query": query, "max_results": 3}, headers=headers, timeout=10)
            data = res.json()
            results = [r["content"] for r in data.get("results", [])]
            return "\n".join(results) if results else "No encontré nada concreto."
    except Exception as e:
        return f"Error al buscar en la web: {e}"


def handle_smart_query(text: str) -> str:
    """
    Analiza el texto y decide si es hora, clima, imágenes o pregunta general.
    """
    lower = text.lower()

    # --- Hora ---
    if "hora" in lower:
        place = lower.replace("hora", "").replace("actual", "").strip()
        if not place:
            place = "mi ciudad actual"
        return f"⏰ {search_web(f'current time in {place}')}"
    
    # --- Clima ---
    if "clima" in lower or "tiempo" in lower:
        place = lower.replace("clima", "").replace("tiempo", "").replace("actual", "").strip()
        if not place:
            place = "mi ciudad actual"
        return f"🌦️ {search_web(f'current weather in {place}')}"
    
    # --- Imagen ---
    if "imagen" in lower or "foto" in lower:
        topic = lower.replace("imagen", "").replace("foto", "").strip()
        return f"🖼️ Aquí tienes imágenes relacionadas: {search_web(f'image of {topic}')}"
    
    # --- Preguntas generales ---
    return f"🔎 {search_web(text)}"
