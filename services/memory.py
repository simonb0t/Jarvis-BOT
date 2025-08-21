import json
from pathlib import Path

STORE = Path(__file__).parent / "memory_store.json"
if not STORE.exists():
    STORE.write_text(json.dumps({"notes": []}, indent=2))

class MemoryClient:
    def load(self):
        return json.loads(STORE.read_text())

    def save(self, text: str):
        data = self.load()
        data["notes"].append(text)
        STORE.write_text(json.dumps(data, indent=2))

    def search(self, keyword: str):
        data = self.load()
        k = keyword.lower()
        return [n for n in data["notes"] if k in n.lower()]
