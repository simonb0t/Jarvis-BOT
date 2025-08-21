import json
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "memory_store.json"

class MemoryClient:
    def __init__(self):
        if not MEMORY_FILE.exists():
            MEMORY_FILE.write_text(json.dumps({"notes": []}, indent=4))

    def load(self):
        return json.loads(MEMORY_FILE.read_text())

    def save(self, text):
        data = self.load()
        data["notes"].append(text)
        MEMORY_FILE.write_text(json.dumps(data, indent=4))

    def search(self, keyword):
        data = self.load()
        return [n for n in data["notes"] if keyword.lower() in n.lower()]

