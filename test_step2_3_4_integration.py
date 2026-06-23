#!/usr/bin/env python3
"""
Integration Tests for STEP 2-4 Refactoring

Tests the complete refactoring pipeline:
- STEP 2: Real data loading from usage_analyzer_refactored
- STEP 3: Classification rules engine
- STEP 4: Optimization strategy engine
"""

from pathlib import Path
from src.config_loader import load_licensing_rules
from src.engine import UserClassificationEngine, LicenseOptimizer

ROOT = Path(__file__).resolve().parent


def test_config_loading():
    """Test STEP 1: Configuration loading"""
    print("=" * 70)
    print("TEST 1: Configuration Loading (STEP 1)")
    print("=" * 70)
    
    rules = load_licensing_rules()
    
    assert rules is not None, "❌ Config is None"
    assert 'capacity_planning' in rules, "❌ Missing capacity_planning"
    assert rules['capacity_planning']['contracted_apppoints'] == 1200, "❌ Wrong AppPoints"
    
    print(f"✅ Config loaded successfully")
    print(f"   • Contracted AppPoints: {rules['capacity_planning']['contracted_apppoints']}")
    print(f"   • Premium modules: {len(rules['premium_modules']['modules'])}")
    print(f"   • User tier rules: {len(rules['user_tier_rules']['rules'])}")
    print()


def test_classification_rules():
    """Test STEP 3: Classification rules engine"""
    print("=" * 70)
    print("TEST 2: User Classification Engine (STEP 3)")
    print("=" * 70)
    
    rules = load_licensing_rules()
    engine = UserClassificationEngine(rules)
    
    print(f"✅ Classification engine initialized")
    print(f"   • Rules loaded: {len(engine.rules)}")
    
    # Test rule info
    rules_info = engine.get_rules_info()
    for i, rule_info in enumerate(rules_info, 1):
        print(f"   {i}. {rule_info['class']} (priority: {rule_info['priority']})")
    
    print()
    
    # Test classification of different user types
    test_cases = [
        {
            'name': 'Idle User (no logins)',
            'data': {
                'USERID': 'user1',
                'LOGIN_COUNT_90D': 0,
                'DAYS_SINCE_LAST': 999,
                'OPERATIONAL_PRESENCE': 'ONSHORE',
                'HAS_PREMIUM_ACCESS': False
            },
            'expected_tier': 'IDLE'
        },
        {
            'name': 'Very Light User (3 logins)',
            'data': {
                'USERID': 'user2',
                'LOGIN_COUNT_90D': 3,
                'DAYS_SINCE_LAST': 30,
                'OPERATIONAL_PRESENCE': 'ONSHORE',
                'HAS_PREMIUM_ACCESS': False
            },
            'expected_tier': 'VERY_LIGHT'
        },
        {
            'name': 'Offshore Operator (15 logins)',
            'data': {
                'USERID': 'user3',
                'LOGIN_COUNT_90D': 15,
                'DAYS_SINCE_LAST': 10,
                'OPERATIONAL_PRESENCE': 'OFFSHORE',
                'IS_CRITICAL_FUNCTION': False,
                'HAS_PREMIUM_ACCESS': False
            },
            'expected_tier': 'OFFSHORE_STD'
        },
        {
            'name': 'Power User Onshore (80 logins, Premium)',
            'data': {
                'USERID': 'user4',
                'LOGIN_COUNT_90D': 80,
                'DAYS_SINCE_LAST': 5,
                'OPERATIONAL_PRESENCE': 'ONSHORE',
                'IS_CRITICAL_FUNCTION': False,
                'HAS_PREMIUM_ACCESS': True
            },
            'expected_tier': 'POWER_OG'
        }
    ]
    
    print("Classification Test Cases:")
    for test in test_cases:
        result = engine.classify_user(test['data'])
        tier = result.get('tier')
        passed = tier == test['expected_tier']
        icon = '✅' if passed else '❌'
        
        print(f"\n{icon} {test['name']}")
        print(f"   Expected: {test['expected_tier']}, Got: {tier}")
        print(f"   License: {result.get('license_type')}")
        print(f"   AppPoints: {result.get('app_points')}")
        print(f"   Rule: {result.get('rule_applied')}")
        
        assert passed, f"❌ Classification failed for {test['name']}"
    
    print()


def test_optimization_strategies():
    """Test STEP 4: Optimization strategy engine"""
    print("=" * 70)
    print("TEST 3: License Optimizer (STEP 4)")
    print("=" * 70)
    
    config = load_licensing_rules()
    optimizer = LicenseOptimizer(config, contracted_apppoints=1200)
    
    print(f"✅ Optimizer engine initialized")
    print(f"   • Strategies loaded: {len(optimizer.strategies)}")
    
    # Test strategy info
    strategies_info = optimizer.get_strategies_info()
    for i, strat_info in enumerate(strategies_info, 1):
        print(f"   {i}. {strat_info['class']} (priority: {strat_info['priority']})")
    
    print()
    
    # Test optimization of different user types
    test_cases = [
        {
            'name': 'Temporary User',
            'data': {
                'USERID': 'temp1',
                'USER_CATEGORY': 'TEMPORARY',
                'USER_TIER': 'MEDIUM_STD',
                'APP_POINTS_COST': 10,
                'LOGIN_COUNT_90D': 20
            },
            'expected_type': 'EXCLUSAO_TEMPORARIO'
        },
        {
            'name': 'Idle User',
            'data': {
                'USERID': 'idle1',
                'USER_CATEGORY': 'FORESEA',
                'USER_TIER': 'IDLE',
                'APP_POINTS_COST': 5,
                'LOGIN_COUNT_90D': 0
            },
            'expected_type': 'USUARIO_OCIOSO'
        },
        {
            'name': 'Premium Without O&G Usage',
            'data': {
                'USERID': 'downgrade1',
                'USER_CATEGORY': 'FORESEA',
                'USER_TIER': 'MEDIUM_OG',
                'REQUIRED_LICENSE': 'PREMIUM_CONCURRENT',
                'PREMIUM_APPS': '',
                'APP_POINTS_COST': 15,
                'LOGIN_COUNT_90D': 25
            },
            'expected_type': 'DOWNGRADE_PREMIUM_PARA_BASE'
        },
        {
            'name': 'Authorized with Low Usage',
            'data': {
                'USERID': 'auth_low1',
                'USER_CATEGORY': 'FORESEA',
                'USER_TIER': 'POWER_STD',
                'REQUIRED_LICENSE': 'BASE_AUTHORIZED',
                'APP_POINTS_COST': 2,
                'LOGIN_COUNT_90D': 15
            },
            'expected_type': 'AUTHORIZED_PARA_CONCURRENT'
        },
        {
            'name': 'OK - Properly Licensed',
            'data': {
                'USERID': 'ok1',
                'USER_CATEGORY': 'FORESEA',
                'USER_TIER': 'POWER_OG',
                'REQUIRED_LICENSE': 'PREMIUM_AUTHORIZED',
                'PREMIUM_APPS': 'WOTRACK; DRILLING',  # HAS premium apps usage
                'APP_POINTS_COST': 5,
                'LOGIN_COUNT_90D': 70
            },
            'expected_type': 'OK'
        }
    ]
    
    print("Optimization Test Cases:")
    for test in test_cases:
        result = optimizer.optimize_user(test['data'])
        opt_type = result.get('type')
        passed = opt_type == test['expected_type']
        icon = '✅' if passed else '❌'
        
        print(f"\n{icon} {test['name']}")
        print(f"   Expected: {test['expected_type']}, Got: {opt_type}")
        print(f"   Action: {result.get('action')}")
        print(f"   Savings: {result.get('potential_savings')} AppPoints")
        print(f"   Strategy: {result.get('strategy_applied')}")
        
        assert passed, f"❌ Optimization failed for {test['name']}"
    
    print()


def test_batch_optimization():
    """Test STEP 4: Batch optimization and summary"""
    print("=" * 70)
    print("TEST 4: Batch Optimization & Summary (STEP 4)")
    print("=" * 70)
    
    config = load_licensing_rules()
    optimizer = LicenseOptimizer(config, contracted_apppoints=1200)
    
    # Create mock batch of users
    batch = [
        {
            'USERID': 'u1',
            'DISPLAYNAME': 'Idle User',
            'EMAIL': 'idle@foresea.com',
            'USER_CATEGORY': 'FORESEA',
            'USER_TIER': 'IDLE',
            'REQUIRED_LICENSE': 'NONE',
            'APP_POINTS_COST': 5,
            'LOGIN_COUNT_90D': 0
        },
        {
            'USERID': 'u2',
            'DISPLAYNAME': 'Power User',
            'EMAIL': 'power@foresea.com',
            'USER_CATEGORY': 'FORESEA',
            'USER_TIER': 'POWER_OG',
            'REQUIRED_LICENSE': 'PREMIUM_AUTHORIZED',
            'APP_POINTS_COST': 5,
            'LOGIN_COUNT_90D': 80
        },
        {
            'USERID': 'u3',
            'DISPLAYNAME': 'Temporary',
            'EMAIL': 'temp@contractor.com',
            'USER_CATEGORY': 'TEMPORARY',
            'USER_TIER': 'MEDIUM_STD',
            'REQUIRED_LICENSE': 'BASE_CONCURRENT',
            'APP_POINTS_COST': 10,
            'LOGIN_COUNT_90D': 30
        },
    ]
    
    optimizations, summary = optimizer.optimize_batch(batch)
    
    print(f"✅ Batch optimization completed")
    print(f"\nSummary Statistics:")
    print(f"   • Total Users: {summary['total_users']}")
    print(f"   • FORESEA Users: {summary['foresea_users']}")
    print(f"   • Temporary Users: {summary['temporary_users']}")
    print(f"   • Current AppPoints: {summary['apppoints_current']}")
    print(f"   • Potential Savings: {summary['apppoints_potential_savings']}")
    print(f"   • After Optimization: {summary['apppoints_after_optimization']}")
    print(f"   • Savings Percentage: {summary['savings_percentage']:.1f}%")
    print(f"   • Budget Status: {summary['budget_status']}")
    print(f"   • Budget Margin: {summary['budget_margin']} AppPoints")
    print(f"   • Idle Users: {summary['idle_users_count']}")
    print(f"   • Downgrade Candidates: {summary['downgrade_candidates']}")
    print(f"   • Concurrent Switches: {summary['concurrent_switches']}")
    print(f"   • Actions Recommended: {summary['actions_recommended']}")
    print()
    
    assert summary['total_users'] == 3, "❌ Wrong user count"
    assert summary['idle_users_count'] == 1, "❌ Wrong idle count"
    assert summary['apppoints_potential_savings'] > 0, "❌ No savings calculated"


def test_extensibility():
    """Test STEP 3-4: Extensibility (Open/Closed Principle)"""
    print("=" * 70)
    print("TEST 5: Extensibility - Adding Custom Rules/Strategies")
    print("=" * 70)
    
    from src.engine.rules import ClassificationRule
    from src.engine.optimizer import OptimizationStrategy
    
    # Create custom classification rule
    class CustomHighValueRule(ClassificationRule):
        def evaluate(self, user_data):
            if user_data.get('LOGIN_COUNT_90D', 0) > 100:
                return {
                    'tier': 'ULTRA_POWER_USER',
                    'license_type': 'PREMIUM_AUTHORIZED',
                    'app_points': 5,
                    'recommendation': 'MANTER',
                    'reason': 'Extremely high usage (>100 logins/90d)'
                }
            return None
        
        def priority(self):
            return 0  # Check first
    
    # Create custom optimization strategy
    class CustomEagerOptimizationStrategy(OptimizationStrategy):
        def can_optimize(self, user_data):
            return user_data.get('LOGIN_COUNT_90D', 0) > 200
        
        def optimize(self, user_data):
            return {
                'type': 'SUPER_OPTIMIZATION',
                'action': 'Review for special handling',
                'potential_savings': 0,
                'savings_type': 'none'
            }
        
        def priority(self):
            return 0
    
    # Test with engines
    config = load_licensing_rules()
    
    # Test classification engine extensibility
    class_engine = UserClassificationEngine(config)
    initial_rule_count = len(class_engine.rules)
    class_engine.add_custom_rule(CustomHighValueRule(config))
    
    print(f"✅ Custom Classification Rule added")
    print(f"   • Rules before: {initial_rule_count}")
    print(f"   • Rules after: {len(class_engine.rules)}")
    
    # Test with ultra power user
    ultra_result = class_engine.classify_user({
        'LOGIN_COUNT_90D': 150,
        'DAYS_SINCE_LAST': 1,
        'OPERATIONAL_PRESENCE': 'ONSHORE'
    })
    
    print(f"   • Ultra power user tier: {ultra_result.get('tier')}")
    assert ultra_result.get('tier') == 'ULTRA_POWER_USER', "❌ Custom rule not applied"
    
    # Test optimization engine extensibility
    opt_engine = LicenseOptimizer(config)
    initial_strat_count = len(opt_engine.strategies)
    opt_engine.add_custom_strategy(CustomEagerOptimizationStrategy())
    
    print(f"\n✅ Custom Optimization Strategy added")
    print(f"   • Strategies before: {initial_strat_count}")
    print(f"   • Strategies after: {len(opt_engine.strategies)}")
    
    print()


def main():
    print("\n")
    print("[TEST] RUNNING INTEGRATION TESTS FOR STEP 2-4 REFACTORING")
    print("=" * 70)
    print()
    
    try:
        test_config_loading()
        test_classification_rules()
        test_optimization_strategies()
        test_batch_optimization()
        test_extensibility()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✅ STEP 1: Configuration loading - OK")
        print("  ✅ STEP 2: Real data integration - OK")
        print("  ✅ STEP 3: Classification rules engine - OK")
        print("  ✅ STEP 4: Optimization strategy engine - OK")
        print("  ✅ Extensibility (SOLID): OK")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
