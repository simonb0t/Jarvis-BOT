from __future__ import annotations
import requests
import re
from duckduckgo_search import DDGS

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _ddg_text(query: str, max_results: int = 6):
    out = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(_clean(query), max_results=max_results):
                out.append((r.get("title") or "", r.get("href") or r.get("url") or "", r.get("body") or ""))
    except Exception:
        pass
    return out

def _ddg_images(query: str, max_results: int = 4):
    urls = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.images(_clean(query), max_results=max_results):
                u = r.get("image") or r.get("thumbnail") or r.get("url")
                if u:
                    urls.append(u)
    except Exception:
        pass
    return urls

def web_answer(query: str) -> str:
    """Resumen breve + 3 fuentes."""
    hits = _ddg_text(query, 6)
    if not hits:
        return "No encontré resultados claros ahora."
    # resumen extractivo simple
    snippets = " ".join([h[2] for h in hits if h[2]]) or ""
    sents = re.split(r"(?<=[.!?])\s+", snippets)
    sents = [s for s in sents if 30 <= len(s) <= 220][:3]
    summary = " ".join(sents) if sents else (hits[0][2] or hits[0][0])
    # 3 fuentes
    seen_hosts, sources = set(), []
    for title, url, _ in hits:
        host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", url)).split("/")[0]
        if host and host not in seen_hosts:
            seen_hosts.add(host)
            sources.append(f"• {title}: {url}")
        if len(sources) == 3:
            break
    return f"🔎 {_clean(query)}\n{summary}\n" + ("\n".join(sources) if sources else "")

def web_images_answer(topic: str) -> str:
    urls = _ddg_images(topic, 4)
    if not urls:
        return "No pude encontrar imágenes ahora mismo."
    lines = ["🖼️ Imágenes:"]
    for u in urls:
        lines.append(f"• {u}")
    return "\n".join(lines)

def handle_smart_query(text: str) -> str:
    """Router: hora, clima, imágenes o pregunta abierta (todo vía web)."""
    t = _clean(text).lower()

    # Hora
    if "hora" in t:
        place = re.sub(r"\b(hora|actual|en|de|del|la|el)\b", " ", t).strip()
        q = f"current time in {place or 'my location'}"
        return "⏰ " + web_answer(q)

    # Clima
    if any(k in t for k in ("clima", "tiempo", "temperatura", "pronóstico", "pronostico", "weather")):
        place = re.sub(r"\b(clima|tiempo|temperatura|pronóstico|pronostico|en|de|del|la|el|actual)\b", " ", t).strip()
        q = f"current weather in {place or 'my city'}"
        return "🌦️ " + web_answer(q)

    # Imágenes
    if any(k in t for k in ("imagen", "imagenes", "imágenes", "foto", "fotos", "image", "picture")):
        topic = re.sub(r"\b(imagen(es)?|foto(s)?|de|del|la|el)\b", " ", t).strip()
        return web_images_answer(topic or text)

    # Pregunta general
    return web_answer(text)
