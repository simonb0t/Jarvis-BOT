"""
memory_module.py
Módulo simple de memoria basado en archivo JSON.

Funciones principales:
- init_store()              -> garantiza que el archivo existe
- save_note(text, tags=[])  -> guarda una nota
- list_notes(limit=None)    -> lista notas (opcionalmente limitado)
- search_notes(keyword)     -> busca por palabra clave (texto/tags)
- delete_note(index)        -> borra por índice (lista visible)
- clear_notes()             -> borra todas las notas (¡cuidado!)

El archivo de almacenamiento por defecto es 'memory_store.json'
en la misma carpeta de este módulo. Puedes cambiar MEMORY_PATH.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# === Config ===
# Archivo donde se guardan las notas
MEMORY_PATH = Path(__file__).parent / "memory_store.json"


def init_store() -> None:
    """Crea el archivo JSON si no existe."""
    if not MEMORY_PATH.exists():
        data = {
            "created_at": datetime.utcnow().isoformat(),
            "notes": []
        }
        MEMORY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _load() -> Dict[str, Any]:
    """Carga el JSON de memoria."""
    init_store()
    return json.loads(MEMORY_PATH.read_text())


def _save(data: Dict[str, Any]) -> None:
    """Guarda el JSON de memoria."""
    MEMORY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def save_note(text: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Guarda una nota con texto y tags opcionales.
    Retorna la nota guardada.
    """
    tags = tags or []
    data = _load()
    note = {
        "timestamp": datetime.utcnow().isoformat(),
        "text": text.strip(),
        "tags": [t.strip().lower() for t in tags if t.strip()]
    }
    data["notes"].append(note)
    _save(data)
    return note


def list_notes(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Lista notas en orden de inserción (las más antiguas primero).
    Si limit está definido, corta la lista a ese número.
    """
    data = _load()
    notes = data.get("notes", [])
    if limit is not None:
        notes = notes[:limit]
    return notes


def search_notes(keyword: str) -> List[Dict[str, Any]]:
    """
    Busca keyword en el texto o en los tags de las notas (case-insensitive).
    Retorna lista de notas coincidentes.
    """
    k = (keyword or "").strip().lower()
    if not k:
        return []
    data = _load()
    results = []
    for note in data.get("notes", []):
        text_hit = k in note.get("text", "").lower()
        tags = note.get("tags", [])
        tag_hit = any(k in t for t in tags)
        if text_hit or tag_hit:
            results.append(note)
    return results


def delete_note(index: int) -> bool:
    """
    Borra una nota por índice de la lista (usa list_notes() para ver orden/índices).
    Retorna True si borró, False si el índice no existe.
    """
    data = _load()
    notes = data.get("notes", [])
    if 0 <= index < len(notes):
        notes.pop(index)
        data["notes"] = notes
        _save(data)
        return True
    return False


def clear_notes() -> None:
    """BORRA TODAS LAS NOTAS. Úsalo con cuidado."""
    data = _load()
    data["notes"] = []
    _save(data)


# ---- Helpers de presentación (opcional) ----

def pretty_list(limit: Optional[int] = None) -> str:
    """
    Representación legible de las notas (para enviar por WhatsApp).
    """
    notes = list_notes(limit=limit)
    if not notes:
        return "No hay notas."
    lines = []
    for i, n in enumerate(notes):
        ts = n.get("timestamp", "")
        text = n.get("text", "")
        tags = ", ".join(n.get("tags", [])) if n.get("tags") else "-"
        lines.append(f"{i}. [{ts}] {text}  (tags: {tags})")
    return "\n".join(lines)


def pretty_search(keyword: str) -> str:
    """
    Representación legible de resultados de búsqueda.
    """
    results = search_notes(keyword)
    if not results:
        return f"Sin coincidencias para: {keyword}"
    lines = [f"Resultados para '{keyword}':"]
    for i, n in enumerate(results):
        ts = n.get("timestamp", "")
        text = n.get("text", "")
        tags = ", ".join(n.get("tags", [])) if n.get("tags") else "-"
        lines.append(f"- [{ts}] {text}  (tags: {tags})")
    return "\n".join(lines)
