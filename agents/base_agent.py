import uuid
from datetime import datetime

class BaseAgent:
    def __init__(self, name, description, tools=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.created_at = datetime.utcnow().isoformat()
        self.tools = tools or []
        self.history = []

    def add_history(self, entry):
        self.history.append({
            "t": datetime.utcnow().isoformat(),
            "entry": entry
        })

    def run(self, task: str) -> str:
        raise NotImplementedError("Implementar en subclase")
