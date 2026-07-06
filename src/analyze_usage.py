#!/usr/bin/env python3
"""
Fase 3: Análise de Uso Real - MODELO POR SCORE

Implementa:
- AUTH por pontuação acumulada (não binário)
- Regime Offshore 14x14
- Regime Onshore seg–sex
- Compatível com LicenseOptimizer e TrueCapacity
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'consolidated'

try:
    from src.engine import UserClassificationEngine
    from src.config_loader import load_licensing_rules
except ImportError as e:
    print(f"[ERRO] Falha ao importar modules SOLID: {e}")
    sys.exit(1)


LOOKBACK_DAYS = 90
OFFSHORE_MIN_DAYS_IN_14 = 12
ONSHORE_MIN_RATIO = 0.7
AUTH_THRESHOLD = 70


def load_csv(filename):
    path = IN_DIR / filename
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def parse_date_safe(date_str):
    if not date_str:
        return None

    text = str(date_str).strip()

    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def evaluate_offshore_pattern(login_dates):
    if len(login_dates) < OFFSHORE_MIN_DAYS_IN_14:
        return False

    login_dates = sorted(set(d.date() for d in login_dates))

    for i in range(len(login_dates)):
        start = login_dates[i]
        window_end = start + timedelta(days=13)
        count = sum(1 for d in login_dates if start <= d <= window_end)
        if count >= OFFSHORE_MIN_DAYS_IN_14:
            return True
    return False


def evaluate_onshore_pattern(login_dates):
    if not login_dates:
        return False

    unique_days = set(d.date() for d in login_dates)
    weekdays = [d for d in unique_days if d.weekday() < 5]

    if not unique_days:
        return False

    ratio = len(weekdays) / len(unique_days)
    return ratio >= ONSHORE_MIN_RATIO


def infer_env_from_clienthost(clienthost):
    """
    Infer environment from CLIENTHOST hostname or IP.
    Returns: (env, is_shared) - env is the inferred environment or None, is_shared indicates IP/shared server
    """
    if not clienthost:
        return None, False
    
    host = clienthost.strip().upper()
    
    # Mapeamento de IPs dos servidores Maximo para ambientes (Produção)
    IP_TO_ENV = {
        '10.119.240.73': 'BASE',      # ODRL-SP-MX01
        '10.120.216.81': 'ODN1',      # ODRL-ODN1-MX01
        '10.118.6.88': 'ODN2',        # ODRL-ODN2-MX01
        '10.120.148.67': 'N06',       # ODRL-N06-MX01
        '10.120.148.143': 'N08',      # ODRL-N08-MX01
        '10.120.149.83': 'N09',       # ODRL-N09-MX01
        '10.119.58.21': 'HTQ',        # ODRL-HTQ-MX05
    }
    
    # IP addresses - mapear para ambiente
    if host.replace('.', '').isdigit():
        return IP_TO_ENV.get(host), False
    
    # Padrão odrl-sp-sv013.foresea.com - SERVIDOR COMPARTILHADO
    if 'ODRL-SP-SV' in host:
        return None, True
    
    # Servidores específicos de ambiente
    if 'ODRL-ODN2-SV' in host:
        return 'ODN2', False
    if 'ODRL-ODN1-SV' in host:
        return 'ODN1', False
    if 'ODRL-ODN3-SV' in host:
        return 'ODN3', False
    if 'ODRL-ODN4-SV' in host:
        return 'ODN4', False
    
    if 'ODRL-N06-SV' in host:
        return 'N06', False
    if 'ODRL-N08-SV' in host:
        return 'N08', False
    if 'ODRL-N09-SV' in host:
        return 'N09', False
    
    if 'ODRL-HTQ-SV' in host:
        return 'HTQ', False
    if 'ODRL-POL-SV' in host:
        return 'POL', False
    if 'ODRL-PGA-SV' in host:
        return 'PGA', False
    if 'ODRL-PGB-SV' in host:
        return 'PGB', False
    
    # Padrão OD2-, OD1-, ON06- (máquinas específicas)
    if host.startswith('OD2-') or '-OD2-' in host:
        return 'ODN2', False
    if host.startswith('OD1-') or '-OD1-' in host:
        return 'ODN1', False
    if host.startswith('ON06-') or '-N06-' in host:
        return 'N06', False
    if host.startswith('ON08-') or '-N08-' in host:
        return 'N08', False
    if host.startswith('ON09-') or '-N09-' in host:
        return 'N09', False
    
    return None, False


def get_user_login_env(logintrack):
    """
    Get the environment of the last login for each user.
    Uses CLIENTHOST to infer environment when ENVIRONMENT is BASE or shared.
    Returns: {userid: {'env': environment, 'last_login': datetime, 'login_count': int}}
    """
    user_logins = defaultdict(list)
    
    for rec in logintrack:
        result = (rec.get('ATTEMPTRESULT') or '').strip().upper()
        if result != 'LOGIN':
            continue
        userid = rec.get('USERID', '').strip().upper()
        env = (rec.get('ENVIRONMENT') or '').strip()
        clienthost = rec.get('CLIENTHOST', '').strip()
        dt = parse_date_safe(rec.get('ATTEMPTDATE'))
        
        if userid and dt:
            # Infer environment from CLIENTHOST if ENVIRONMENT is BASE or shared
            actual_env, is_shared = infer_env_from_clienthost(clienthost)
            if actual_env:
                env = actual_env
            elif not is_shared:
                env = env  # Use ENVIRONMENT as-is
            else:
                env = None  # Shared server - cannot determine environment
            
            if env:
                user_logins[userid].append({
                    'env': env,
                    'datetime': dt
                })
    
    # For each user, get the most recent login environment
    result = {}
    for userid, logins in user_logins.items():
        if logins:
            logins_sorted = sorted(logins, key=lambda x: x['datetime'], reverse=True)
            most_recent = logins_sorted[0]
            result[userid] = {
                'env': most_recent['env'],
                'last_login': most_recent['datetime'],
                'login_count': len(logins)
            }
    
    return result


def main():

    print("\n" + "=" * 80)
    print("[FASE 3] Análise por SCORE - AUTH vs CONCURRENT")
    print("=" * 80)

    start = time.time()

    rules = load_licensing_rules()
    engine = UserClassificationEngine(rules)

    priority_domains = rules['user_classification']['priority_domains']['domains']
    offshore_keywords = rules['user_classification']['offshore_keywords']['keywords']
    critical_keywords = rules['user_classification']['critical_functions']['keywords']

    identities = load_csv('consolidated_user_identity.csv')
    logintrack = load_csv('consolidated_logintracking_from_sources.csv')

    # Get login environment per user
    user_login_env = get_user_login_env(logintrack)

    usage_by_user = defaultdict(list)

    for rec in logintrack:
        result = (rec.get('ATTEMPTRESULT') or '').strip().upper()
        if result != 'LOGIN':
            continue
        userid = rec.get('USERID', '').strip().upper()
        dt = parse_date_safe(rec.get('ATTEMPTDATE'))
        if userid and dt:
            usage_by_user[userid].append(dt)

    output_rows = []

    for identity in identities:

        userid = identity.get('USERID', '').strip().upper()
        status = identity.get('STATUS', '').strip().upper()

        # Se STATUS estiver vazio, assume como ACTIVE (comum em sistemas)
        if not status:
            status = 'ACTIVE'
        
        if status != 'ACTIVE':
            continue

        login_dates = usage_by_user.get(userid, [])
        total_logins = len(login_dates)

        last_login = max(login_dates) if login_dates else None
        days_since_last = 999

        if last_login:
            days_since_last = (datetime.now() - last_login).days

        # Domínio
        email = identity.get('PRIMARYEMAIL', '') or ''
        is_foresea = any(d in email.lower() for d in priority_domains)
        user_category = 'FORESEA' if is_foresea else 'TEMPORARY'

        # Operacional
        title = identity.get('TITLE', '') or ''
        persongroup = identity.get('PERSONGROUP', '') or ''
        text = f"{title} {persongroup}".lower()

        offshore = any(k in text for k in offshore_keywords)
        operational_presence = 'OFFSHORE' if offshore else 'ONSHORE'

        is_critical = any(k.lower() in title.lower() for k in critical_keywords)

        # Uso intenso
        if offshore:
            intense_use = evaluate_offshore_pattern(login_dates)
        else:
            intense_use = evaluate_onshore_pattern(login_dates)

        # Score
        auth_score = 0

        if is_critical:
            auth_score += 40

        if offshore:
            auth_score += 20

        if intense_use:
            auth_score += 30

        if total_logins >= 60:
            auth_score += 20

        if total_logins >= 90:
            auth_score += 30

        if days_since_last <= 7:
            auth_score += 10

        if is_foresea:
            auth_score += 20

        # Get LOCAL_SITE from last login environment
        login_env_info = user_login_env.get(userid, {})
        local_site = login_env_info.get('env', '')
        
        # If no login found, use DEFSITE from identity as fallback
        if not local_site:
            local_site = identity.get('DEFSITE', '')

        # Engine decide entitlement (Premium/Base)
        user_data = {
            'USERID': userid,
            'LOGIN_COUNT_90D': total_logins,
            'DAYS_SINCE_LAST': days_since_last,
            'OPERATIONAL_PRESENCE': operational_presence,
            'IS_CRITICAL_FUNCTION': is_critical,
            'USED_PREMIUM': False,
            'HAS_PREMIUM_ACCESS': False,
            'LICENSE_MODEL': 'CONCURRENT'
        }

        classification = engine.classify_user(user_data)
        required_license = classification.get('license_type', 'BASE_CONCURRENT')
        app_points = classification.get('app_points', 5)

        # Aplicação do Score
        if auth_score >= AUTH_THRESHOLD:
            if 'PREMIUM' in required_license:
                required_license = 'PREMIUM_AUTHORIZED'
                app_points = 15
            else:
                required_license = 'BASE_AUTHORIZED'
                app_points = 5
        else:
            if 'PREMIUM' in required_license:
                required_license = 'PREMIUM_CONCURRENT'
                app_points = 15
            else:
                required_license = 'BASE_CONCURRENT'
                app_points = 5

        output_rows.append({
            'USERID': userid,
            'DISPLAYNAME': identity.get('DISPLAYNAME', ''),
            'EMAIL': email,
            'USER_CATEGORY': user_category,
            'OPERATIONAL_PRESENCE': operational_presence,
            'STATUS': status,
            'TITLE': title,
            'LOGIN_COUNT_90D': total_logins,
            'LAST_LOGIN': last_login.strftime('%Y-%m-%d') if last_login else '',
            'LOCAL_SITE': local_site,
            'USER_TIER': classification.get('tier', 'UNKNOWN'),
            'AUTH_SCORE': auth_score,
            'REQUIRED_LICENSE': required_license,
            'APP_POINTS_COST': app_points,
            'CLASSIFICATION_RULE': 'SCORE_MODEL'
        })

    # Verificação de segurança para evitar IndexError
    if not output_rows:
        print("\n⚠️  AVISO: Nenhum usuário ativo encontrado para análise.")
        print("   Verifique se o arquivo consolidated_user_identity.csv contém dados.")
        print("   Criando arquivo vazio com cabeçalho.\n")
        out_path = OUT_DIR / 'usage_analysis_phase3.csv'
        with out_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['USERID', 'DISPLAYNAME', 'EMAIL', 'USER_CATEGORY', 
                                                   'OPERATIONAL_PRESENCE', 'STATUS', 'TITLE', 
                                                   'LOGIN_COUNT_90D', 'LAST_LOGIN', 'LOCAL_SITE',
                                                   'USER_TIER', 
                                                   'AUTH_SCORE', 'REQUIRED_LICENSE', 
                                                   'APP_POINTS_COST', 'CLASSIFICATION_RULE'])
            writer.writeheader()
        return
    
    out_path = OUT_DIR / 'usage_analysis_phase3.csv'
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"\n✅ usage_analysis_phase3.csv atualizado ({len(output_rows)} usuários)")
    print("✅ Modelo por SCORE aplicado.")
    print(f"[LOG] Concluído em {time.time() - start:.2f}s\n")


if __name__ == '__main__':
    main()