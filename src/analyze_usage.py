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
            'USER_TIER': classification.get('tier', 'UNKNOWN'),
            'AUTH_SCORE': auth_score,
            'REQUIRED_LICENSE': required_license,
            'APP_POINTS_COST': app_points,
            'CLASSIFICATION_RULE': 'SCORE_MODEL'
        })

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