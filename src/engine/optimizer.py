# src/engine/optimizer.py
from abc import ABC, abstractmethod

class OptimizationRule(ABC):
    @abstractmethod
    def evaluate(self, user_data: dict) -> dict: pass

class TemporaryUserRule(OptimizationRule):
    def evaluate(self, user_data: dict):
        if user_data.get('USER_CATEGORY') == 'TEMPORARY':
            return {'type': 'Exclusão Temporário', 'recommendation': '🔵 NÃO MIGRAR - Usuário temporário', 'savings': int(user_data.get('APP_POINTS_COST', 0))}
        return None

class IdleUserOptimization(OptimizationRule):
    def evaluate(self, user_data: dict):
        if user_data.get('USER_TIER') == 'IDLE':
            return {'type': 'Usuário Ocioso', 'recommendation': '🔴 DESATIVAR - Sem uso há 90 dias', 'savings': int(user_data.get('APP_POINTS_COST', 0))}
        return None

class VeryLightUsageOptimization(OptimizationRule):
    def evaluate(self, user_data: dict):
        logins = int(user_data.get('LOGIN_COUNT_90D', 0))
        cost = int(user_data.get('APP_POINTS_COST', 0))
        if user_data.get('USER_TIER') == 'VERY_LIGHT' and logins < 5:
            return {'type': 'Uso Muito Baixo', 'recommendation': '🟠 AVALIAR DESATIVAÇÃO - Uso baixo', 'savings': int(cost * 0.7)}
        return None

class PremiumDowngradeOptimization(OptimizationRule):
    def evaluate(self, user_data: dict):
        req_lic = user_data.get('REQUIRED_LICENSE', '')
        premium_apps = user_data.get('PREMIUM_APPS', '')
        if 'PREMIUM' in req_lic and not premium_apps:
            return {'type': 'Premium sem uso O&G', 'recommendation': '🟡 DOWNGRADE para BASE', 'savings': 10}
        return None

class ConcurrentSwitchOptimization(OptimizationRule):
    def evaluate(self, user_data: dict):
        req_lic = user_data.get('REQUIRED_LICENSE', '')
        logins = int(user_data.get('LOGIN_COUNT_90D', 0))
        if 'AUTHORIZED' in req_lic and logins < 30:
            return {'type': 'Authorized → Concurrent', 'recommendation': '🟡 MUDAR para CONCURRENT', 'savings': 3}
        return None

class LicenseOptimizerEngine:
    def __init__(self):
        self.rules = [
            TemporaryUserRule(),
            IdleUserOptimization(),
            VeryLightUsageOptimization(),
            PremiumDowngradeOptimization(),
            ConcurrentSwitchOptimization()
        ]

    def process_user(self, user_data: dict) -> dict:
        for rule in self.rules:
            result = rule.evaluate(user_data)
            if result:
                return result
        return {'type': 'OK', 'recommendation': '🟢 OK - Licença alinhada com uso', 'savings': 0}