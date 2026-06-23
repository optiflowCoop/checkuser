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

def load_licensing_rules():
    """
    Load centralized business rules for license optimization and user classification.
    
    This file contains all previously hardcoded rules from:
    - analyze_usage.py (OG_PREMIUM_MODULES, PRIORITY_DOMAINS, OFFSHORE_KEYWORDS, etc.)
    - license_optimizer.py (CONTRACTED_APPPOINTS, optimization thresholds)
    - usage_analyzer.py (mock data simulation parameters)
    
    Returns:
        dict: Licensing rules configuration
    """
    path = CONFIG_DIR / 'licensing_rules.json'
    if not path.exists():
        raise FileNotFoundError(
            f"Licensing rules not found at {path}. "
            "Run: python src/config_loader.py to generate template."
        )
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)