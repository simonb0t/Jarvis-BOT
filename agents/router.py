import json
from pathlib import Path
from typing import Optional
from .base_agent import BaseAgent
from .memory_agent import MemoryAgent
from services.budget import BudgetGuard
from services.memory import MemoryClient
import re

# Reusa tu buscador web existente
import web_search_module as websearch  # debe exponer una función search(query: str) -> str

REGISTRY = Path(__file__).parent / "registry.json"
if not REGISTRY.exists():
    REGISTRY.write_text("{}")

# Presupuesto
budget = BudgetGuard(monthly_limit=130)

def _load():
    return json.loads(REGISTRY.read_text())

def _save(d):
    REGISTRY.write_text(json.dumps(d, indent=2))

def _instantiate(agent_dict) -> BaseAgent:
    # Por ahora solo MemoryAgent y BaseAgent
    if agent_dict.get("type") == "memory":
        a = MemoryAgent(agent_dict["name"], agent_dict["description"])
    else:
        a = BaseAgent(agent_dict["name"], agent_dict["description"])
        # fallback run:
        a.run = lambda task: f"{a.name} recibió la tarea: {task}"
    # reconstruye historia mínima
    for h in agent_dict.get("history", []):
        a.history.append(h)
    return a

def create_agent(name: str, description: str, agent_type: str = "memory") -> str:
    data = _load()
    if agent_type not in ("memory", "base"):
        agent_type = "base"
    if agent_type == "memory":
        agent = MemoryAgent(name, description)
    else:
        agent = BaseAgent(name, description)
    data[agent.id] = {
        "name": agent.name,
        "description": agent.description,
        "type": agent_type,
        "created_at": agent.created_at,
        "history": agent.history
    }
    _save(data)
    return agent.id

def list_agents() -> str:
    data = _load()
    if not data:
        return "No hay agentes creados. Usa: 'crear agente: <nombre> | <descripcion>'"
    lines = []
    for i, (aid, a) in enumerate(data.items(), start=1):
        lines.append(f"{i}. [{aid}] {a['name']} — {a['description']} (tipo: {a['type']})")
    return "\n".join(lines)

def run_agent(agent_id: str, task: str) -> str:
    data = _load()
    a = data.get(agent_id)
    if not a:
        return "Agente no encontrado."
    inst = _instantiate(a)

    # Política de costos: elegimos “modo” según consumo
    mode = budget.check_mode()
    # aquí podrías branch por modelo si integras OpenAI. De momento solo anotamos:
    inst.add_history({"task": task, "mode": mode})
    out = inst.run(task)
    # persistir historia
    a["history"] = inst.history
    data[agent_id] = a
    _save(data)
    # simulamos costo bajo por operación (ajusta si integras LLM)
    budget.add_usage(0.001)
    return out

def handle_text_command(body: str) -> Optional[str]:
    """
    Detecta comandos desde WhatsApp de forma simple:
    - 'crear agente: <nombre> | <descripcion> [| tipo]'  (tipo opcional: memory | base)
    - 'listar agentes'
    - 'usar agente: <id> | <tarea>'
    - 'buscar: <query>'        -> usa buscador web
    - 'recordar: <texto>'      -> manda al agent por defecto (memoria)
    - 'buscar en memoria: <q>'
    """
    b = body.strip()

    # crear agente
    if b.lower().startswith("crear agente:"):
        rest = b.split(":", 1)[1].strip()
        parts = [p.strip() for p in rest.split("|")]
        if len(parts) >= 2:
            name, desc = parts[0], parts[1]
            a_type = parts[2] if len(parts) >= 3 else "memory"
            aid = create_agent(name, desc, a_type)
            return f"✅ Agente creado [{aid}]: {name} ({a_type})"
        return "Formato: crear agente: <nombre> | <descripcion> [| tipo]"

    if b.lower().startswith("listar agentes"):
        return list_agents()

    if b.lower().startswith("usar agente:"):
        rest = b.split(":", 1)[1].strip()
        parts = [p.strip() for p in rest.split("|")]
        if len(parts) >= 2:
            aid, task = parts[0], parts[1]
            return run_agent(aid, task)
        return "Formato: usar agente: <id> | <tarea>"

    if b.lower().startswith("buscar:"):
        q = b.split(":", 1)[1].strip()
        # Usa tu módulo de búsqueda web
        try:
            result = websearch.search(q)
            budget.add_usage(0.002)
            return f"🔎 Resultado:\n{result}"
        except Exception as e:
            return f"Error en búsqueda: {e}"

    # memoria directa
    if b.lower().startswith("recordar:"):
        # por conveniencia, si no hay agente, creamos uno por defecto y lo usamos
        reply = ensure_default_memory_agent_and_run(f"recordar: {b.split(':',1)[1].strip()}")
        return reply

    if b.lower().startswith("buscar en memoria:"):
        q = b.split(":", 1)[1].strip()
        reply = ensure_default_memory_agent_and_run(f"buscar: {q}")
        return reply

    # No es comando conocido
    return None

def ensure_default_memory_agent_and_run(task: str) -> str:
    data = _load()
    # busca uno de tipo memoria
    for aid, a in data.items():
        if a.get("type") == "memory":
            return run_agent(aid, task)
    # si no existe, crea uno
    new_id = create_agent("Memoria", "Notas y búsqueda interna", "memory")
    return run_agent(new_id, task)

def handle_agent_task(task: str) -> str:
    """
    Fallback: si el usuario escribe texto libre, lo tomamos como
    input para el agente de memoria por defecto (guarda idea).
    """
    return ensure_default_memory_agent_and_run(task)
