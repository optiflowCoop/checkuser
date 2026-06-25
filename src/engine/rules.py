# src/engine/rules.py
from abc import ABC, abstractmethod
from typing import Dict, Optional, List


class ClassificationRule(ABC):
    def __init__(self, config: Dict = None):
        self.config = config or {}

    @abstractmethod
    def evaluate(self, user_data: Dict) -> Optional[Dict]: pass

    @abstractmethod
    def priority(self) -> int: pass


class IdleUserRule(ClassificationRule):
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        days_since = user_data.get('DAYS_SINCE_LAST', 999)
        if login_count == 0 or days_since > 90:
            return {'tier': 'IDLE', 'license_type': 'NONE', 'app_points': 0}
        return None

    def priority(self) -> int: return 0


class VeryLightUsageRule(ClassificationRule):
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        if 0 < login_count < 5:
            return {'tier': 'VERY_LIGHT', 'license_type': 'LIMITED', 'app_points': 5}
        return None

    def priority(self) -> int: return 1


class OffshoreAnalysisRule(ClassificationRule):
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        operational_presence = user_data.get('OPERATIONAL_PRESENCE', 'UNKNOWN')
        if operational_presence not in ['OFFSHORE', 'ONSHORE']: return None
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        if login_count < 5: return None

        is_critical = user_data.get('IS_CRITICAL_FUNCTION', False)
        has_premium = user_data.get('HAS_PREMIUM_ACCESS', False)

        if operational_presence == 'OFFSHORE':
            if is_critical:
                return {'tier': 'CRITICAL_OFFSHORE_OG', 'license_type': 'PREMIUM_AUTHORIZED',
                        'app_points': 5} if has_premium else {'tier': 'CRITICAL_OFFSHORE_STD',
                                                              'license_type': 'BASE_AUTHORIZED', 'app_points': 2}
            else:
                return {'tier': 'OFFSHORE_OG', 'license_type': 'PREMIUM_CONCURRENT',
                        'app_points': 15} if has_premium else {'tier': 'OFFSHORE_STD',
                                                               'license_type': 'BASE_CONCURRENT', 'app_points': 10}
        return None

    def priority(self) -> int:
        return 2


class OnshoreUsageRule(ClassificationRule):
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        operational_presence = user_data.get('OPERATIONAL_PRESENCE', 'UNKNOWN')
        if operational_presence != 'ONSHORE': return None
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        if login_count < 5: return None

        has_premium = user_data.get('HAS_PREMIUM_ACCESS', False)
        power_user_threshold = self.config.get('usage_analysis_parameters', {}).get('power_user_threshold', 60)

        if has_premium:
            return {'tier': 'POWER_OG', 'license_type': 'PREMIUM_AUTHORIZED',
                    'app_points': 5} if login_count > power_user_threshold else {'tier': 'MEDIUM_OG',
                                                                                 'license_type': 'PREMIUM_CONCURRENT',
                                                                                 'app_points': 15}
        else:
            return {'tier': 'POWER_STD', 'license_type': 'BASE_AUTHORIZED',
                    'app_points': 2} if login_count > power_user_threshold else {'tier': 'MEDIUM_STD',
                                                                                 'license_type': 'BASE_CONCURRENT',
                                                                                 'app_points': 10}

    def priority(self) -> int:
        return 3


class PremiumDowngradeRule(ClassificationRule):
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        has_premium = user_data.get('HAS_PREMIUM_ACCESS', False)
        used_premium = user_data.get('USED_PREMIUM', False)
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        if has_premium and not used_premium and login_count > 0:
            return {'tier': 'DOWNGRADE_CANDIDATE', 'license_type': 'BASE_CONCURRENT', 'app_points': 10}
        return None

    def priority(self) -> int: return 4


class AuthorizedLowUsageRule(ClassificationRule):
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        license_model = user_data.get('LICENSE_MODEL', '')
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        auth_threshold = self.config.get('optimization_thresholds', {}).get('authorized_low_usage', {}).get(
            'max_logins', 30) if self.config else 30
        if license_model == 'AUTHORIZED' and 0 < login_count < auth_threshold:
            return {'tier': 'CONCURRENT_CANDIDATE', 'license_type': 'CONCURRENT', 'app_points': 0}
        return None

    def priority(self) -> int: return 5


class UserClassificationEngine:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.rules = [
            IdleUserRule(self.config),
            VeryLightUsageRule(self.config),
            OffshoreAnalysisRule(self.config),
            OnshoreUsageRule(self.config),
            PremiumDowngradeRule(self.config),
            AuthorizedLowUsageRule(self.config)
        ]
        self.rules.sort(key=lambda r: r.priority())

    def classify_user(self, user_data: Dict) -> Dict:
        for rule in self.rules:
            result = rule.evaluate(user_data)
            if result:
                result['rule_applied'] = rule.__class__.__name__
                return result
        return {'tier': 'UNCLASSIFIED', 'license_type': 'UNKNOWN', 'app_points': 0, 'rule_applied': 'NONE'}