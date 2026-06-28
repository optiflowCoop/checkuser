# src/rules_manager.py
import json
from pathlib import Path


class RulesManager:
    """Singleton responsável por carregar as regras de negócio."""
    _instance = None
    _rules = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RulesManager, cls).__new__(cls)
            cls._instance._load_rules()
        return cls._instance

    def _load_rules(self):
        root_dir = Path(__file__).resolve().parent.parent
        rules_path = root_dir / 'config' / 'licensing_rules.json'

        if not rules_path.exists():
            # Fallback seguro caso o JSON não exista ainda
            self._rules = {'capacity_planning': {'contracted_apppoints': 1200}}
            return

        with open(rules_path, 'r', encoding='utf-8') as f:
            self._rules = json.load(f)

    @property
    def rules(self):
        return self._rules

    @property
    def capacity(self) -> dict:
        return self._rules.get('capacity_planning', {'contracted_apppoints': 1200})


# Instância global
rules_manager = RulesManager()