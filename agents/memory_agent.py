from .base_agent import BaseAgent
from services.memory import MemoryClient

class MemoryAgent(BaseAgent):
    def __init__(self, name="Memoria", description="Guarda y busca notas"):
        super().__init__(name, description, tools=["memory"])
        self.mem = MemoryClient()

    def run(self, task: str) -> str:
        # protocolo simple:
        # "recordar: <texto>" -> guarda
        # "buscar: <keyword>" -> busca
        lower = task.lower()
        if lower.startswith("recordar:"):
            content = task.split(":", 1)[1].strip()
            self.mem.save(content)
            self.add_history({"op":"save", "text":content})
            return f"🧠 Guardado en memoria."
        if lower.startswith("buscar:"):
            q = task.split(":", 1)[1].strip()
            results = self.mem.search(q)
            self.add_history({"op":"search", "q":q})
            if not results:
                return "Sin coincidencias en memoria."
            return "Coincidencias:\n- " + "\n- ".join(results)
        # por defecto, guardar como nota
        self.mem.save(task)
        self.add_history({"op":"save", "text":task})
        return "🧠 Guardado (por defecto)."

