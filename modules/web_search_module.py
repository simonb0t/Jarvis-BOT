from __future__ import annotations
import re
import time
from typing import List, Tuple, Dict

from duckduckgo_search import DDGS
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator

DetectorFactory.seed = 0  # resultados deterministas

# ===== Config =====
MAX_TEXT_RESULTS = 8
MAX_SOURCES = 3
CACHE_TTL = 300  # 5 min

_TRUST = (
    "wikipedia.org", "britannica.com", "nasa.gov", "esa.int",
    "mit.edu", "stanford.edu", "harvard.edu",
    "who.int", "nih.gov", "cdc.gov",
    "nature.com", "science.org", "reuters.com", "bbc.com",
    "nationalgeographic.com"
)

_cache: Dict[str, Tuple[float, str]] = {}

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _host(url: str) -> str:
    m = re.match(r"^https?://([^/]+)/?", url or "", re.I)
    return (m.group(1).lower() if m else "").replace("www.", "")

def _is_trusted(url: str) -> bool:
    h = _host(url)
    return any(d in h for d in _TRUST)

def _lang(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "es"

def _to_es(text: str) -> str:
    if not text:
        return ""
    try:
        if _lang(text) != "es":
            return GoogleTranslator(source="auto", target="es").translate(text)
    except Exception:
        pass
    return text

def _ddg_text(q: str, n: int = MAX_TEXT_RESULTS) -> List[Tuple[str, str, str]]:
    out: List[Tuple[str, str, str]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(_clean(q), max_results=n):
                title = r.get("title") or ""
                url = r.get("href") or r.get("url") or ""
                body = r.get("body") or ""
                if url and title:
                    out.append((title, url, body))
    except Exception:
        pass
    return out

def _ddg_images(q: str, n: int = 4) -> List[str]:
    urls: List[str] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.images(_clean(q), max_results=n):
                u = r.get("image") or r.get("thumbnail") or r.get("url")
                if u:
                    urls.append(u)
    except Exception:
        pass
    return urls

def _extractive_bullets(snippets: List[str], k: int = 4) -> List[str]:
    text = " ".join(_clean(s) for s in snippets if s)
    sents = re.split(r"(?<=[.!?])\s+", text)
    sents = [s for s in sents if 30 <= len(s) <= 220]
    if not sents:
        return []
    # frecuencia de términos muy simple
    words = re.findall(r"[a-záéíóúüñ0-9]{3,}", text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    def score(sent: str) -> float:
        toks = re.findall(r"[a-záéíóúüñ0-9]{3,}", sent.lower())
        return sum(freq.get(t, 0) for t in toks) / max(1, len(toks))

    ranked = sorted(sents, key=score, reverse=True)[:k]
    # quitar duplicados manteniendo orden
    seen, bullets = set(), []
    for s in ranked:
        s2 = _clean(s)
        if s2 not in seen:
            seen.add(s2)
            bullets.append("• " + s2)
    return bullets

def web_answer(query: str) -> str:
    q = _clean(query)
    ts_ans = _cache.get(q)
    now = time.time()
    if ts_ans and now - ts_ans[0] < CACHE_TTL:
        return ts_ans[1]

    hits = _ddg_text(q, MAX_TEXT_RESULTS)
    if not hits:
        ans = "No encontré resultados claros en este momento."
        _cache[q] = (now, ans)
        return ans

    # prioriza fuentes confiables
    hits = sorted(hits, key=lambda h: (not _is_trusted(h[1])))
    snippets = [h[2] for h in hits if h[2]]
    bullets = _extractive_bullets(snippets, k=4)
    if bullets:
        summary = "\n".join(bullets)
    else:
        summary = hits[0][2] or hits[0][0]

    # fuentes (máx 3, dominios distintos)
    sources, used = [], set()
    for title, url, _ in hits:
        h = _host(url)
        if h and h not in used:
            used.add(h)
            sources.append(f"• {title}: {url}")
        if len(sources) >= MAX_SOURCES:
            break

    summary = _to_es(summary)
    ans = f"🔎 {_to_es(q)}\n{summary}\n" + ("\n".join(sources) if sources else "")
    _cache[q] = (now, ans)
    return ans

def web_images_answer(topic: str) -> str:
    urls = _ddg_images(topic, 4)
    if not urls:
        return "No pude encontrar imágenes ahora mismo."
    lines = ["🖼️ Imágenes:"]
    for u in urls:
        lines.append(f"• {u}")
    return "\n".join(lines)

def handle_smart_query(text: str) -> str:
    t = _clean(text).lower()

    # Hora (si mencionas "hora")
    if "hora" in t:
        place = re.sub(r"\b(hora|actual|en|de|del|la|el)\b", " ", t).strip()
        q = f"current time in {place or 'my location'}"
        return "⏰ " + web_answer(q)

    # Clima (si mencionas clima/tiempo/temperatura/pronóstico)
    if any(k in t for k in ("clima", "tiempo", "temperatura", "pronóstico", "pronostico", "weather")):
        place = re.sub(r"\b(clima|tiempo|temperatura|pronóstico|pronostico|en|de|del|la|el|actual)\b", " ", t).strip()
        q = f"current weather in {place or 'my city'}"
        return "🌦️ " + web_answer(q)

    # Imágenes
    if any(k in t for k in ("imagen", "imagenes", "imágenes", "foto", "fotos", "image", "picture")):
        topic = re.sub(r"\b(imagen(es)?|foto(s)?|de|del|la|el)\b", " ", t).strip()
        return web_images_answer(topic or text)

    # Pregunta abierta
    return web_answer(text)
