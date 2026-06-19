import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / 'config'

def load_environments():
    path = CONFIG_DIR / 'config.json'
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    return cfg.get('connections', [])

def load_query_catalog():
    path = CONFIG_DIR / 'query_catalog.json'
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_identity_rules():
    path = CONFIG_DIR / 'rules.identity.json'
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)