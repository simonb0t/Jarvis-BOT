# modules/web_search_module.py
from __future__ import annotations
from typing import List, Tuple, Optional, Dict
import re
import time
import requests
from urllib.parse import urlparse
from duckduckgo_search import DDGS

# ====== Config ======
MAX_RESULTS = 6
MAX_SOURCES_TO_SHOW = 3
WIKI_LANGS = ("es", "en")  # intenta español y luego inglés
TIMEOUT = 10
CACHE_TTL_SEC = 300  # 5 minutos

# Whitelist básica de dominios más confiables
TRUSTED_DOMAINS = (
    "wikipedia.org", "britannica.com", "khanacademy.org", "nasa.gov",
    "esa.int", "mit.edu", "stanford.edu", "harvard.edu", "who.int",
    "nih.gov", "cdc.gov", "unesco.org", "nature.com", "science.org",
    "bbc.com", "reuters.com", "nationalgeographic.com", "esa.int", "esawebb.org"
)

_cache: Dict[str, Tuple[float, str]] = {}  # query -> (timestamp, answer)

def _now() -> float:
    return time.time()

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def _is_trusted(url: str) -> bool:
    h = _host(url)
    return any(d in h for d in TRUSTED_DOMAINS)

def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen, out = set(), []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out

# ---------- Wikipedia ----------
def wiki_summary(query: str, sentences: int = 2) -> Optional[str]:
    q = _clean(query)
    for lang in WIKI_LANGS:
        try:
            # Buscar título aproximado
            s = requests.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": q,
                    "limit": 1,
                    "namespace": 0,
                    "format": "json",
                },
                timeout=TIMEOUT,
            )
            s.raise_for_status()
            data = s.json()
            if not data or len(data) < 2 or not data[1]:
                continue
            title = data[1][0]
            # Summary
            p = requests.get(
                f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}",
                timeout=TIMEOUT,
            )
            p.raise_for_status()
            j = p.json()
            extract = j.get("extract")
            if not extract:
                continue
            # Recorta a N oraciones
            parts = re.split(r"(?<=[.!?])\s+", extract)
            return " ".join(parts[:sentences])
        except Exception:
            continue
    return None

# ---------- DuckDuckGo ----------
def search_duckduckgo(query: str, max_results: int = MAX_RESULTS) -> List[Tuple[str, str, str]]:
    """
    Devuelve lista de (title, url, snippet).
    """
    q = _clean(query)
    results: List[Tuple[str, str, str]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=max_results):
                title = r.get("title") or ""
                href = r.get("href") or r.get("url") or ""
                body = r.get("body") or ""
                if href and title:
                    results.append((title, href, body))
    except Exception:
        pass
    return results

# ---------- Resumen híbrido ----------
def _extractive_summary(snippets: List[str], max_sentences: int = 3) -> Optional[str]:
    """
    Resumen extractivo muy simple: toma las oraciones más
    “centrales” por longitud/ocurrencia de términos (heurística suave).
    Sin librerías externas para mantenerlo ligero.
    """
    text = " ".join(_clean(s) for s in snippets if s)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s for s in sentences if 30 <= len(s) <= 220]
    if not sentences:
        return None

    # Ponderación simple por frecuencia de palabras (sin stopwords)
    words = re.findall(r"[a-záéíóúüñ0-9]{3,}", text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    def score(sent: str) -> float:
        tokens = re.findall(r"[a-záéíóúüñ0-9]{3,}", sent.lower())
        if not tokens:
            return 0.0
        return sum(freq.get(t, 0) for t in tokens) / len(tokens)

    ranked = sorted(sentences, key=score, reverse=True)
    summary = " ".join(_dedupe_keep_order(ranked)[:max_sentences])
    return summary or None

# ---------- Orquestador ----------
def web_answer(query: str, max_results: int = MAX_RESULTS) -> str:
    q = _clean(query)
    # cache
    if q in _cache:
        ts, ans = _cache[q]
        if _now() - ts < CACHE_TTL_SEC:
            return ans

    resumen_wiki = wiki_summary(q)
    hits = search_duckduckgo(q, max_results=max_results)

    # Filtrar y ordenar: preferimos dominios confiables primero
    trusted, others = [], []
    for title, url, snippet in hits:
        (trusted if _is_trusted(url) else others).append((title, url, snippet))
    hits_sorted = trusted + others

    # Construir resumen extractivo a partir de snippets
    snippets = [s for _, _, s in hits_sorted[:max_results] if s]
    resumen_extr = _extractive_summary(snippets, max_sentences=3)

    # Armar respuesta final
    parts: List[str] = []
    if resumen_wiki:
        parts.append(resumen_wiki)
    if resumen_extr and (not resumen_wiki or resumen_extr not in resumen_wiki):
        parts.append(resumen_extr)

    # Fuentes (máx 3, deduplicadas por host)
    shown = 0
    used_hosts = set()
    for title, url, snippet in hits_sorted:
        h = _host(url)
        if not h or h in used_hosts:
            continue
        parts.append(f"• {title}: {url}")
        used_hosts.add(h)
        shown += 1
        if shown >= MAX_SOURCES_TO_SHOW:
            break

    if not parts:
        answer = "No encontré resultados claros ahora mismo."
    else:
        answer = "🔎 " + q + "\n" + "\n".join(parts)

    _cache[q] = (_now(), answer)
    return answer
