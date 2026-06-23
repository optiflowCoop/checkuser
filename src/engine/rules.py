#!/usr/bin/env python3
"""
STEP 3: Rule Engine - SOLID Design Pattern (Strategy)

Replaces hardcoded if/elif blocks with extensible Rule classes.
Each rule is independent, testable, and easy to extend.

Based on config/licensing_rules.json
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from datetime import datetime


class ClassificationRule(ABC):
    """Abstract base class for user classification rules"""
    
    def __init__(self, config: Dict = None):
        """Initialize rule with configuration from licensing_rules.json"""
        self.config = config or {}
    
    @abstractmethod
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        """
        Evaluate if this rule applies to the user.
        
        Args:
            user_data: User profile dict with all attributes
            
        Returns:
            Dict with classification result or None if rule doesn't apply
        """
        pass
    
    @abstractmethod
    def priority(self) -> int:
        """
        Priority for rule evaluation (0 = highest priority).
        Rules are evaluated in order of priority.
        """
        pass


class IdleUserRule(ClassificationRule):
    """
    Identifies users with no login activity in the last 90 days.
    
    Condition: login_count_90d == 0 OR days_since_last_login > 90
    """
    
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        days_since = user_data.get('DAYS_SINCE_LAST', 999)
        
        if login_count == 0 or days_since > 90:
            return {
                'tier': 'IDLE',
                'license_type': 'NONE',
                'app_points': 0,
                'recommendation': 'DESATIVAR',
                'reason': 'Usuário sem atividade nos últimos 90 dias'
            }
        return None
    
    def priority(self) -> int:
        return 0  # Check first - highest priority


class VeryLightUsageRule(ClassificationRule):
    """
    Identifies users with extremely low usage (< 5 logins in 90 days).
    
    Condition: 0 < login_count_90d < 5
    """
    
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        
        if 0 < login_count < 5:
            return {
                'tier': 'VERY_LIGHT',
                'license_type': 'LIMITED',
                'app_points': 5,
                'recommendation': 'AVALIAR_DESATIVACAO',
                'reason': f'Uso extremamente baixo ({login_count} logins/90d)'
            }
        return None
    
    def priority(self) -> int:
        return 1


class OffshoreAnalysisRule(ClassificationRule):
    """
    Analyzes offshore vs onshore users with different license models.
    
    OFFSHORE = 12h shifts, low simultaneity → CONCURRENT
    ONSHORE = administrative, high simultaneity → can be AUTHORIZED
    """
    
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        operational_presence = user_data.get('OPERATIONAL_PRESENCE', 'UNKNOWN')
        
        if operational_presence not in ['OFFSHORE', 'ONSHORE']:
            return None
        
        # Only process if not idle or very light
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        if login_count < 5:
            return None
        
        is_critical = user_data.get('IS_CRITICAL_FUNCTION', False)
        has_premium = user_data.get('HAS_PREMIUM_ACCESS', False)
        
        if operational_presence == 'OFFSHORE':
            if is_critical:
                if has_premium:
                    return {
                        'tier': 'CRITICAL_OFFSHORE_OG',
                        'license_type': 'PREMIUM_AUTHORIZED',
                        'app_points': 5,
                        'recommendation': 'MANTER',
                        'reason': 'Função crítica offshore com acesso O&G (requer disponibilidade 24/7)'
                    }
                else:
                    return {
                        'tier': 'CRITICAL_OFFSHORE_STD',
                        'license_type': 'BASE_AUTHORIZED',
                        'app_points': 2,
                        'recommendation': 'MANTER',
                        'reason': 'Função crítica offshore (requer disponibilidade 24/7)'
                    }
            else:
                # Operational offshore workers use CONCURRENT
                if has_premium:
                    return {
                        'tier': 'OFFSHORE_OG',
                        'license_type': 'PREMIUM_CONCURRENT',
                        'app_points': 15,
                        'recommendation': 'MANTER',
                        'reason': 'Offshore com acesso O&G (revezamento de turnos)'
                    }
                else:
                    return {
                        'tier': 'OFFSHORE_STD',
                        'license_type': 'BASE_CONCURRENT',
                        'app_points': 10,
                        'recommendation': 'MANTER',
                        'reason': 'Offshore operacional (revezamento de turnos)'
                    }
        
        return None
    
    def priority(self) -> int:
        return 2


class OnshoreUsageRule(ClassificationRule):
    """
    Analyzes onshore users based on usage intensity.
    
    High usage (>60 logins) → can justify AUTHORIZED
    Medium usage → typically CONCURRENT
    """
    
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        operational_presence = user_data.get('OPERATIONAL_PRESENCE', 'UNKNOWN')
        
        if operational_presence != 'ONSHORE':
            return None
        
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        if login_count < 5:
            return None
        
        has_premium = user_data.get('HAS_PREMIUM_ACCESS', False)
        power_user_threshold = self.config.get('usage_analysis_parameters', {}).get('power_user_threshold', 60)
        
        if has_premium:
            if login_count > power_user_threshold:
                return {
                    'tier': 'POWER_OG',
                    'license_type': 'PREMIUM_AUTHORIZED',
                    'app_points': 5,
                    'recommendation': 'MANTER',
                    'reason': f'Power user com acesso O&G ({login_count} logins/90d)'
                }
            else:
                return {
                    'tier': 'MEDIUM_OG',
                    'license_type': 'PREMIUM_CONCURRENT',
                    'app_points': 15,
                    'recommendation': 'MANTER',
                    'reason': f'Uso médio com acesso O&G ({login_count} logins/90d)'
                }
        else:
            if login_count > power_user_threshold:
                return {
                    'tier': 'POWER_STD',
                    'license_type': 'BASE_AUTHORIZED',
                    'app_points': 2,
                    'recommendation': 'MANTER',
                    'reason': f'Power user BASE ({login_count} logins/90d)'
                }
            else:
                return {
                    'tier': 'MEDIUM_STD',
                    'license_type': 'BASE_CONCURRENT',
                    'app_points': 10,
                    'recommendation': 'MANTER',
                    'reason': f'Uso médio BASE ({login_count} logins/90d)'
                }
        
        return None
    
    def priority(self) -> int:
        return 3


class PremiumDowngradeRule(ClassificationRule):
    """
    Identifies users with PREMIUM license but ZERO O&G usage.
    
    Condition: has_premium_access == True AND premium_apps_used == False AND login_count > 0
    """
    
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        has_premium = user_data.get('HAS_PREMIUM_ACCESS', False)
        used_premium = user_data.get('USED_PREMIUM', False)
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        
        if has_premium and not used_premium and login_count > 0:
            return {
                'tier': 'DOWNGRADE_CANDIDATE',
                'license_type': 'BASE_CONCURRENT',
                'app_points': 10,
                'recommendation': 'DOWNGRADE_PREMIUM_TO_BASE',
                'reason': 'Licença Premium sem uso de módulos O&G',
                'potential_savings': 5  # PREMIUM_CONCURRENT (15) - BASE_CONCURRENT (10)
            }
        return None
    
    def priority(self) -> int:
        return 4


class AuthorizedLowUsageRule(ClassificationRule):
    """
    Identifies AUTHORIZED users with low usage patterns.
    
    Condition: license_model == AUTHORIZED AND login_count < 30 AND login_count > 0
    Action: Switch to CONCURRENT to reduce costs
    """
    
    def evaluate(self, user_data: Dict) -> Optional[Dict]:
        license_model = user_data.get('LICENSE_MODEL', '')
        login_count = user_data.get('LOGIN_COUNT_90D', 0)
        
        authorized_threshold = self.config.get('optimization_thresholds', {}).get('authorized_low_usage', {}).get('max_logins', 30)
        
        if license_model == 'AUTHORIZED' and 0 < login_count < authorized_threshold:
            return {
                'tier': 'CONCURRENT_CANDIDATE',
                'license_type': 'CONCURRENT',
                'app_points': None,  # Will be recalculated
                'recommendation': 'MOVE_AUTHORIZED_TO_CONCURRENT',
                'reason': f'Uso baixo não justifica modelo Authorized ({login_count} logins/90d)',
                'potential_savings': 3  # AUTHORIZED - CONCURRENT difference
            }
        return None
    
    def priority(self) -> int:
        return 5


class UserClassificationEngine:
    """
    Main classification engine using Strategy pattern.
    
    Orchestrates multiple rules and applies them in priority order.
    New rules can be added without modifying existing code (Open/Closed Principle).
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize engine with configuration rules.
        
        Args:
            config: Dict from config/licensing_rules.json
        """
        self.config = config or {}
        self.rules: List[ClassificationRule] = []
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize all rule classes"""
        self.rules = [
            IdleUserRule(self.config),
            VeryLightUsageRule(self.config),
            OffshoreAnalysisRule(self.config),
            OnshoreUsageRule(self.config),
            PremiumDowngradeRule(self.config),
            AuthorizedLowUsageRule(self.config),
        ]
        # Sort by priority
        self.rules.sort(key=lambda r: r.priority())
    
    def classify_user(self, user_data: Dict) -> Dict:
        """
        Classify a user by applying all rules in priority order.
        
        Returns the first matching rule's result.
        
        Args:
            user_data: User profile dict
            
        Returns:
            Dict with classification, tier, license type, and recommendation
        """
        for rule in self.rules:
            result = rule.evaluate(user_data)
            if result:
                result['rule_applied'] = rule.__class__.__name__
                return result
        
        # Fallback if no rule matched
        return {
            'tier': 'UNCLASSIFIED',
            'license_type': 'UNKNOWN',
            'app_points': 0,
            'recommendation': 'REVISAR_MANUALMENTE',
            'reason': 'Perfil de usuário não corresponde a nenhuma regra padrão',
            'rule_applied': 'NONE'
        }
    
    def add_custom_rule(self, rule: ClassificationRule):
        """
        Add a custom rule to the engine (Open/Closed Principle).
        
        Args:
            rule: Instance of a class extending ClassificationRule
        """
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority())
    
    def remove_rule(self, rule_class_name: str):
        """Remove a rule by class name"""
        self.rules = [r for r in self.rules if r.__class__.__name__ != rule_class_name]
    
    def get_rules_info(self) -> List[Dict]:
        """Get information about all loaded rules"""
        return [
            {
                'class': r.__class__.__name__,
                'priority': r.priority(),
                'description': r.__doc__
            }
            for r in self.rules
        ]
