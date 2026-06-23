#!/usr/bin/env python3
"""
STEP 4: Optimization Engine - SOLID Design Pattern (Strategy)

Replaces hardcoded if/elif blocks in license_optimizer.py with extensible Strategy classes.
Each optimization strategy is independent, testable, and easy to extend.

This eliminates the need to modify core code when adding new optimization rules.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class OptimizationStrategy(ABC):
    """Abstract base class for license optimization strategies"""
    
    @abstractmethod
    def can_optimize(self, user_data: Dict) -> bool:
        """
        Check if this strategy applies to the user.
        
        Args:
            user_data: User profile dict with all attributes
            
        Returns:
            True if this strategy can optimize this user
        """
        pass
    
    @abstractmethod
    def optimize(self, user_data: Dict) -> Dict:
        """
        Apply optimization strategy and return recommendation.
        
        Args:
            user_data: User profile dict
            
        Returns:
            Dict with optimization type, action, and potential savings
        """
        pass
    
    @abstractmethod
    def priority(self) -> int:
        """
        Priority for strategy evaluation (0 = highest priority).
        Strategies are evaluated in order of priority.
        """
        pass


class ExcludeTemporaryStrategy(OptimizationStrategy):
    """
    Excludes temporary/contractor users from migration.
    
    These users should NOT be migrated to new platform.
    Their licenses should be excluded from optimization.
    """
    
    def can_optimize(self, user_data: Dict) -> bool:
        return user_data.get('USER_CATEGORY') == 'TEMPORARY'
    
    def optimize(self, user_data: Dict) -> Dict:
        app_points = user_data.get('APP_POINTS_COST', 0)
        return {
            'type': 'EXCLUSAO_TEMPORARIO',
            'action': 'Excluir da migração',
            'icon': '🔵',
            'description': 'Usuário temporário/contratado - não migrar',
            'potential_savings': app_points,
            'savings_type': 'exclusion',
            'priority': 'CRITICAL'
        }
    
    def priority(self) -> int:
        return 0  # Check first


class DisableIdleUserStrategy(OptimizationStrategy):
    """
    Identifies and disables idle users (no login in 90+ days).
    
    These users represent pure waste and should be deactivated.
    Full cost can be saved.
    """
    
    def can_optimize(self, user_data: Dict) -> bool:
        return user_data.get('USER_TIER') == 'IDLE'
    
    def optimize(self, user_data: Dict) -> Dict:
        app_points = user_data.get('APP_POINTS_COST', 0)
        return {
            'type': 'USUARIO_OCIOSO',
            'action': 'Desativar',
            'icon': '🔴',
            'description': 'Sem uso há 90 dias',
            'potential_savings': app_points,
            'savings_type': 'idle',
            'priority': 'HIGH'
        }
    
    def priority(self) -> int:
        return 1


class EvaluateVeryLowUsageStrategy(OptimizationStrategy):
    """
    Flags users with very low usage for manual evaluation.
    
    These might be deactivated, but require HR/business validation first.
    Potential partial savings (70% confidence).
    """
    
    def can_optimize(self, user_data: Dict) -> bool:
        tier = user_data.get('USER_TIER', '')
        logins = user_data.get('LOGIN_COUNT_90D', 0)
        return tier == 'VERY_LIGHT' and logins < 5
    
    def optimize(self, user_data: Dict) -> Dict:
        app_points = user_data.get('APP_POINTS_COST', 0)
        potential_savings = app_points * 0.7  # 70% confidence
        
        return {
            'type': 'USO_MUITO_BAIXO',
            'action': 'Avaliar desativação',
            'icon': '🟠',
            'description': f'Uso extremamente baixo ({user_data.get("LOGIN_COUNT_90D", 0)} logins/90d)',
            'potential_savings': int(potential_savings),
            'savings_type': 'conditional',
            'priority': 'MEDIUM',
            'validation_required': 'HR'
        }
    
    def priority(self) -> int:
        return 2


class DowngradePremiumStrategy(OptimizationStrategy):
    """
    Downgrades PREMIUM licenses to BASE when no O&G apps are accessed.
    
    Condition: has_premium_access == True BUT premium_apps_used == False
    Savings: 10 AppPoints (PREMIUM_CONCURRENT 15 → BASE_CONCURRENT 10)
    """
    
    def can_optimize(self, user_data: Dict) -> bool:
        required_license = user_data.get('REQUIRED_LICENSE', '')
        premium_apps = user_data.get('PREMIUM_APPS', '')
        logins = user_data.get('LOGIN_COUNT_90D', 0)
        
        return (
            'PREMIUM' in required_license
            and not premium_apps
            and logins > 0
        )
    
    def optimize(self, user_data: Dict) -> Dict:
        return {
            'type': 'DOWNGRADE_PREMIUM_PARA_BASE',
            'action': 'Mudar para BASE',
            'icon': '🟡',
            'description': 'Licença Premium sem uso de módulos O&G',
            'potential_savings': 5,
            'apppoints_current': 15,
            'apppoints_new': 10,
            'savings_type': 'downgrade',
            'priority': 'MEDIUM'
        }
    
    def priority(self) -> int:
        return 3


class MoveAuthorizedToConcurrentStrategy(OptimizationStrategy):
    """
    Moves AUTHORIZED users with low usage to CONCURRENT model.
    
    Condition: license_model == AUTHORIZED AND login_count < 30 AND login_count > 0
    Savings: 3 AppPoints (AUTHORIZED → CONCURRENT)
    """
    
    def can_optimize(self, user_data: Dict) -> bool:
        required_license = user_data.get('REQUIRED_LICENSE', '')
        logins = user_data.get('LOGIN_COUNT_90D', 0)
        
        return (
            'AUTHORIZED' in required_license
            and 0 < logins < 30
        )
    
    def optimize(self, user_data: Dict) -> Dict:
        return {
            'type': 'AUTHORIZED_PARA_CONCURRENT',
            'action': 'Mudar para CONCURRENT',
            'icon': '🟡',
            'description': f'Uso baixo não justifica Authorized ({user_data.get("LOGIN_COUNT_90D", 0)} logins/90d)',
            'potential_savings': 3,
            'apppoints_current': 5,
            'apppoints_new': 2,
            'savings_type': 'optimization',
            'priority': 'MEDIUM'
        }
    
    def priority(self) -> int:
        return 4


class ValidateOkStrategy(OptimizationStrategy):
    """
    Validates that users with adequate usage are correctly licensed.
    
    No optimization needed - license is correctly aligned with usage.
    Serves as positive confirmation.
    """
    
    def can_optimize(self, user_data: Dict) -> bool:
        # Match all users not caught by other strategies
        return True
    
    def optimize(self, user_data: Dict) -> Dict:
        return {
            'type': 'OK',
            'action': 'Manter',
            'icon': '🟢',
            'description': 'Licença alinhada com padrão de uso',
            'potential_savings': 0,
            'savings_type': 'none',
            'priority': 'LOW'
        }
    
    def priority(self) -> int:
        return 999  # Last resort - always matches


class LicenseOptimizer:
    """
    Main optimization engine using Strategy pattern.
    
    Orchestrates multiple optimization strategies and applies them in priority order.
    New strategies can be added without modifying existing code (Open/Closed Principle).
    
    This replaces the hardcoded if/elif blocks in the original license_optimizer.py
    """
    
    def __init__(self, config: Dict = None, contracted_apppoints: int = 1200):
        """
        Initialize optimizer with strategies and configuration.
        
        Args:
            config: Dict from config/licensing_rules.json
            contracted_apppoints: Total AppPoints contracted (default: 1200)
        """
        self.config = config or {}
        self.contracted_apppoints = contracted_apppoints
        self.strategies: List[OptimizationStrategy] = []
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize all optimization strategy classes"""
        self.strategies = [
            ExcludeTemporaryStrategy(),
            DisableIdleUserStrategy(),
            EvaluateVeryLowUsageStrategy(),
            DowngradePremiumStrategy(),
            MoveAuthorizedToConcurrentStrategy(),
            ValidateOkStrategy(),
        ]
        # Sort by priority
        self.strategies.sort(key=lambda s: s.priority())
    
    def optimize_user(self, user_data: Dict) -> Dict:
        """
        Optimize a user's license by applying all strategies in priority order.
        
        Returns the first matching strategy's optimization.
        
        Args:
            user_data: User profile dict
            
        Returns:
            Dict with optimization type, action, and potential savings
        """
        for strategy in self.strategies:
            if strategy.can_optimize(user_data):
                result = strategy.optimize(user_data)
                result['strategy_applied'] = strategy.__class__.__name__
                return result
        
        # Fallback (should not reach here due to ValidateOkStrategy)
        return {
            'type': 'REVISAR_MANUALMENTE',
            'action': 'Revisar',
            'icon': '⚠️',
            'description': 'Perfil não corresponde a estratégias conhecidas',
            'potential_savings': 0,
            'savings_type': 'unknown',
            'priority': 'LOW',
            'strategy_applied': 'NONE'
        }
    
    def optimize_batch(self, user_list: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Optimize a batch of users and calculate totals.
        
        Args:
            user_list: List of user dicts
            
        Returns:
            Tuple of (optimizations list, summary dict)
        """
        optimizations = []
        
        for user in user_list:
            optimization = self.optimize_user(user)
            optimization.update({
                'USERID': user.get('USERID'),
                'DISPLAYNAME': user.get('DISPLAYNAME'),
                'EMAIL': user.get('EMAIL'),
                'USER_CATEGORY': user.get('USER_CATEGORY'),
                'CURRENT_TIER': user.get('USER_TIER'),
                'REQUIRED_LICENSE': user.get('REQUIRED_LICENSE'),
                'APP_POINTS_COST': user.get('APP_POINTS_COST', 0),
                'LOGIN_COUNT_90D': user.get('LOGIN_COUNT_90D', 0),
            })
            optimizations.append(optimization)
        
        # Calculate summary statistics
        summary = self._calculate_summary(user_list, optimizations)
        
        return optimizations, summary
    
    def _calculate_summary(self, user_list: List[Dict], optimizations: List[Dict]) -> Dict:
        """Calculate summary statistics from optimizations"""
        
        total_users = len(user_list)
        foresea_users = sum(1 for u in user_list if u.get('USER_CATEGORY') == 'FORESEA')
        temp_users = sum(1 for u in user_list if u.get('USER_CATEGORY') == 'TEMPORARY')
        
        total_current_apppoints = sum(u.get('APP_POINTS_COST', 0) for u in user_list if u.get('USER_CATEGORY') == 'FORESEA')
        total_savings = sum(o.get('potential_savings', 0) for o in optimizations)
        total_after_optimization = total_current_apppoints - total_savings
        
        idle_count = sum(1 for o in optimizations if o.get('type') == 'USUARIO_OCIOSO')
        downgrade_count = sum(1 for o in optimizations if 'DOWNGRADE' in o.get('type', ''))
        concurrent_switch = sum(1 for o in optimizations if 'CONCURRENT' in o.get('type', ''))
        temp_exclusion = temp_users
        
        within_budget = total_after_optimization <= self.contracted_apppoints
        budget_status = 'DENTRO' if within_budget else 'ACIMA'
        margin = abs(self.contracted_apppoints - total_after_optimization)
        
        return {
            'total_users': total_users,
            'foresea_users': foresea_users,
            'temporary_users': temp_users,
            'apppoints_contracted': self.contracted_apppoints,
            'apppoints_current': total_current_apppoints,
            'apppoints_potential_savings': int(total_savings),
            'apppoints_after_optimization': int(total_after_optimization),
            'savings_percentage': (total_savings / total_current_apppoints * 100) if total_current_apppoints > 0 else 0,
            'budget_status': budget_status,
            'budget_margin': int(margin),
            'idle_users_count': idle_count,
            'downgrade_candidates': downgrade_count,
            'concurrent_switches': concurrent_switch,
            'temporary_exclusions': temp_exclusion,
            'actions_recommended': idle_count + downgrade_count + concurrent_switch
        }
    
    def add_custom_strategy(self, strategy: OptimizationStrategy):
        """
        Add a custom optimization strategy (Open/Closed Principle).
        
        Args:
            strategy: Instance of a class extending OptimizationStrategy
        """
        self.strategies.append(strategy)
        self.strategies.sort(key=lambda s: s.priority())
    
    def remove_strategy(self, strategy_class_name: str):
        """Remove a strategy by class name"""
        self.strategies = [s for s in self.strategies if s.__class__.__name__ != strategy_class_name]
    
    def get_strategies_info(self) -> List[Dict]:
        """Get information about all loaded strategies"""
        return [
            {
                'class': s.__class__.__name__,
                'priority': s.priority(),
                'description': s.__doc__
            }
            for s in self.strategies
        ]
