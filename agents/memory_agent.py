from .base_agent import BaseAgent
from services.memory import MemoryClient

class MemoryAgent(BaseAgent):
    def __init__(self, name, description):
        super().__init__(name, description, tools=["memory"])
        self.memory = MemoryClient()

    def run(self, task):
        self.add_history(task)
        self.memory.save(task)
        return f"Guardado en memoria: {task}"

