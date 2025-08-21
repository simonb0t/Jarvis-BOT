import json
from pathlib import Path
from .base_agent import BaseAgent
from .memory_agent import MemoryAgent

AGENTS_REGISTRY = Path(__file__).parent / "registry.json"

def load_agents():
    if AGENTS_REGISTRY.exists():
        return json.loads(AGENTS_REGISTRY.read_text())
    return {}

def save_agents(data):
    AGENTS_REGISTRY.write_text(json.dumps(data, indent=4))

def create_agent(name, description, agent_type="base"):
    agents = load_agents()

    if agent_type == "memory":
        agent = MemoryAgent(name, description)
    else:
        agent = BaseAgent(name, description)

    agents[agent.id] = {
        "name": agent.name,
        "description": agent.description,
        "created_at": agent.created_at,
        "history": agent.history
    }
    save_agents(agents)
    return agent

def list_agents():
    return load_agents()

def run_agent(agent_id, task):
    agents = load_agents()
    agent = agents.get(agent_id)
    if not agent:
        return "Agente no encontrado."
    # Aquí invocas el tipo real según su clase
    return f"Ejecutando tarea '{task}' con agente {agent['name']}"

