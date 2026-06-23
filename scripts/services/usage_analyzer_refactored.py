#!/usr/bin/env python3
"""
STEP 2: Replace Mock Data with Real Analysis

Refactored from: scripts/services/usage_analyzer.py
Changes:
- Remove random.randint() simulation
- Read real consolidated_logintracking.csv
- Calculate: last_login_date, login_frequency, premium_modules_accessed
- No longer generates mock data - uses actual access patterns
"""
import csv
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
IN_DIR = ROOT / 'output' / 'consolidated'


def analyze_usage_real(user_profiles):
    """
    Analyzes REAL usage from consolidated_logintracking.csv for each user profile.
    
    This replaces the mock random.randint() simulation with actual data.
    
    Args:
        user_profiles: List of user dicts with USERID, etc
        
    Returns:
        List of user profiles enriched with real usage metrics
    """
    
    # Load real login tracking data
    logintrack_path = IN_DIR / 'consolidated_logintracking.csv'
    if not logintrack_path.exists():
        print(f"⚠️  WARNING: {logintrack_path} not found. Using fallback empty data.")
        return user_profiles
    
    # Build user usage index
    usage_by_user = defaultdict(lambda: {
        'login_count': 0,
        'last_login': None,
        'apps_accessed': set(),
        'dates': []
    })
    
    try:
        with logintrack_path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                userid = row.get('USERID', '').strip()
                if not userid:
                    continue
                
                usage_by_user[userid]['login_count'] += 1
                
                # Track apps accessed
                app = row.get('APP', '').strip()
                if app:
                    usage_by_user[userid]['apps_accessed'].add(app)
                
                # Track date of login
                date_str = row.get('ATTEMPTDATE', '').strip()
                if date_str:
                    try:
                        login_date = datetime.fromisoformat(date_str.split()[0])
                        usage_by_user[userid]['dates'].append(login_date)
                        
                        if not usage_by_user[userid]['last_login'] or login_date > usage_by_user[userid]['last_login']:
                            usage_by_user[userid]['last_login'] = login_date
                    except (ValueError, IndexError):
                        pass
    except Exception as e:
        print(f"⚠️  Error reading login tracking: {e}")
        return user_profiles
    
    # Enrich profiles with real data
    for profile in user_profiles:
        userid = profile.get('USERID', '')
        
        if userid in usage_by_user:
            usage = usage_by_user[userid]
            
            # Real login count (not random)
            login_count_90d = usage['login_count']
            profile['LOGIN_COUNT_90D'] = login_count_90d
            
            # Real days since last login
            if usage['last_login']:
                days_since_last = (datetime.now() - usage['last_login']).days
            else:
                days_since_last = 999  # No logins = very old
            
            profile['DAYS_SINCE_LAST'] = days_since_last
            
            # Check if used premium apps
            premium_apps_used = False
            if usage['apps_accessed']:
                # Load premium modules from config
                from src.config_loader import load_licensing_rules
                rules = load_licensing_rules()
                premium_mods = rules['premium_modules']['modules'].keys()
                
                for app in usage['apps_accessed']:
                    if any(mod in app.upper() for mod in premium_mods):
                        premium_apps_used = True
                        break
            
            profile['USED_PREMIUM'] = premium_apps_used
            
        else:
            # User not in login tracking = idle
            profile['LOGIN_COUNT_90D'] = 0
            profile['DAYS_SINCE_LAST'] = 999
            profile['USED_PREMIUM'] = False
        
        # Determine optimization recommendation based on REAL data
        recommendation = "OK"
        reason = ""
        
        login_count = profile.get('LOGIN_COUNT_90D', 0)
        days_since = profile.get('DAYS_SINCE_LAST', 999)
        used_premium = profile.get('USED_PREMIUM', False)
        entitlement = profile.get('ENTITLEMENT', '')
        license_model = profile.get('LICENSE_MODEL', '')
        
        # Real rules based on actual usage
        if days_since > 90:
            recommendation = "INATIVO (>90d)"
            reason = "Usuário sem atividade recente. Avaliar bloqueio."
        
        elif entitlement == 'PREMIUM' and not used_premium and login_count > 0:
            recommendation = "DOWNGRADE_CANDIDATE"
            reason = "Possui permissão Premium, mas não utiliza módulos O&G."
        
        elif license_model == 'AUTHORIZED' and login_count < 20 and login_count > 0:
            recommendation = "MOVE_TO_CONCURRENT"
            reason = "Custo Authorized, mas com baixa frequência de acesso."
        
        elif license_model == 'AUTHORIZED' and login_count >= 20:
            recommendation = "CONFIRMED_AUTHORIZED"
            reason = "Alto uso confirmado com padrão consistente."
        
        elif login_count == 0:
            recommendation = "NEVER_USED"
            reason = "Nenhuma atividade registrada no período analisado."
        
        profile['OPTIMIZATION_REC'] = recommendation
        profile['OPTIMIZATION_REASON'] = reason
    
    return user_profiles
