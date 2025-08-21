from __future__ import annotations
import re
from typing import List, Tuple
from duckduckgo_search import DDGS

# -------- utilidades --------
def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", _clean(text))
    return [p for p in parts if 30 <= len(p) <= 220]

def _top_bullets(snippets: List[str], max_items: int = 5) -> List[str]:
    text = " ".join(_clean(s) for s in snippets if s)
    if not text:
        return []
    sents = _sentences(text)
    # scoring ligero por frecuencia
    words = re.findall(r"[a-záéíóúüñ0-9]{3,}", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    def score(sent: str) -> float:
        toks = re.findall(r"[a-záéíóúüñ0-9]{3,}", sent.lower())
        return sum(freq.get(t, 0) for t in toks) / max(1, len(toks))
    ranked = sorted(sents, key=score, reverse=True)
    out, seen = [], set()
    for s in ranked:
        key = s.lower()[:60]
        if key in seen: 
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= max_items:
            break
    return out

def _host(url: str) -> str:
    return re.sub(r"^www\.", "", re.sub(r"^https?://", "", url)).split("/")[0]

# -------- searchers --------
def _ddg_text(query: str, max_results: int = 10) -> List[Tuple[str, str, str]]:
    q = _clean(query)
    out: List[Tuple[str, str, str]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=max_results, region="es-es", safesearch="moderate"):
                title = r.get("title") or ""
                href  = r.get("href") or r.get("url") or ""
                body  = r.get("body") or ""
                if href and (title or body):
                    out.append((title, href, body))
    except Exception:
        pass
    return out

def _ddg_images(query: str, max_results: int = 4) -> List[str]:
    q = _clean(query)
    urls: List[str] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.images(q, max_results=max_results, region="es-es", safesearch="moderate"):
                u = r.get("image") or r.get("thumbnail") or r.get("url")
                if u:
                    urls.append(u)
    except Exception:
        pass
    return urls

# -------- respuestas --------
def web_images_answer(topic: str) -> str:
    urls = _ddg_images(topic or "imagen", 4)
    if not urls:
        return "No pude encontrar imágenes ahora mismo."
    return "🖼️ Imágenes:\n" + "\n".join(f"• {u}" for u in urls)

def web_answer(query: str) -> str:
    hits = _ddg_text(query, 10)
    if not hits:
        return "No encontré resultados claros ahora mismo."

    snippets = [h[2] for h in hits if h[2]]
    bullets = _top_bullets(snippets, max_items=5)

    # fuentes: 3 dominios distintos
    seen, fuentes = set(), []
    for title, url, _ in hits:
        h = _host(url)
        if h and h not in seen:
            seen.add(h)
            fuentes.append(f"• {title or h}: {url}")
        if len(fuentes) >= 3:
            break

    header = f"🔎 {_clean(query)}"
    body = "\n".join(f"• {b}" for b in bullets) if bullets else "\n".join(f"• {t or u}" for t, u, _ in hits[:3])
    tail = "\n".join(fuentes) if fuentes else ""
    return "\n".join([header, body, tail]).strip()

def handle_smart_query(text: str) -> str:
    """Router simple: hora, clima, imágenes o pregunta general (todo vía web)."""
    t = _clean(text).lower()

    # Hora
    if "hora" in t:
        place = re.sub(r"\b(hora|actual|en|de|del|la|el)\b", " ", t).strip()
        q = f"current time in {place or 'my city'}"
        return "⏰ " + web_answer(q)

    # Clima
    if any(k in t for k in ("clima", "tiempo", "temperatura", "pronóstico", "pronostico", "weather")):
        place = re.sub(r"\b(clima|tiempo|temperatura|pronóstico|pronostico|en|de|del|la|el|actual)\b", " ", t).strip()
        q = f"current weather in {place or 'my city'}"
        return "🌦️ " + web_answer(q)

    # Imágenes (si llegara aquí)
    if any(k in t for k in ("imagen", "imagenes", "imágenes", "foto", "fotos", "image", "picture")):
        topic = re.sub(r"\b(imagen(es)?|foto(s)?|de|del|la|el)\b", " ", t).strip()
        return web_images_answer(topic or text)

    # General
    return web_answer(text)
