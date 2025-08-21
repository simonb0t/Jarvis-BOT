import uuid
import datetime

class BaseAgent:
    def __init__(self, name, description, tools=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.created_at = datetime.datetime.utcnow().isoformat()
        self.tools = tools or []
        self.history = []

    def add_history(self, entry):
        self.history.append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "entry": entry
        })

    def run(self, task):
        raise NotImplementedError("Cada agente debe implementar run()")

