from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]

def resource(path: str) -> Path:
    return ROOT / path

def read_data(name: str):
    return json.loads(resource(f"data/{name}.json").read_text(encoding="utf-8"))
