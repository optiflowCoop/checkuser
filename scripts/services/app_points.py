# scripts/services/app_points.py
import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np
from scripts.analysis.classification import classify_usage_profile
from scripts.config import get_critical_titles, get_og_group_keywords
from scripts.analysis.entitlement import determine_user_entitlement, calculate_app_points


ROOT = Path(__file__).resolve().parents[2]
CONSOLIDATED_DIR = ROOT / 'output' / 'consolidated'

OFFSHORE_KEYWORDS = (
    'OFFSHORE', 'PLATAFORMA', 'PLATFORM', 'EMBARCADO', 'FPSO',
    'RIG', 'SONDA', 'VESSEL', 'NAVIO', 'MOB_', 'TURNO',
    'ODN1', 'ODN2', 'N06', 'N08', 'N09', 'HTQ'
)

ONSHORE_ENVS = {'BASE'}
ADMIN_GROUPS = {'MAXADMIN'}


def _load_csv(name):
    path = CONSOLIDATED_DIR / name
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def _parse_datetime(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d-%H.%M.%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _canonical_title(profile):
    titles = sorted(str(t).strip() for t in profile.get('TITLES', []) if str(t).strip())
    return titles[0] if titles else 'SEM CARGO'


def _classify_operational_presence(profile):
    groups = {str(g).upper().strip() for g in profile.get('GROUPS', []) if str(g).strip()}
    if groups & ADMIN_GROUPS:
        return 'ONSHORE'

    text = ' '.join([
        ' '.join(str(t) for t in profile.get('TITLES', [])),
        ' '.join(str(g) for g in profile.get('PERSONGROUPS', [])),
    ]).upper()
    envs = {str(e).upper() for e in profile.get('ENVS', []) if str(e).strip()}
    if envs and envs.issubset(ONSHORE_ENVS):
        return 'ONSHORE'
    if any(keyword in text for keyword in OFFSHORE_KEYWORDS):
        return 'OFFSHORE'
    if envs and 'BASE' not in envs:
        return 'OFFSHORE'
    return 'ONSHORE'


def _is_critical_title(titles):
    title_text = ' '.join(str(t) for t in titles).upper()
    return any(keyword in title_text for keyword in get_critical_titles())


def _is_critical_access(profile):
    groups = {str(g).upper().strip() for g in profile.get('GROUPS', []) if str(g).strip()}
    return bool(groups & ADMIN_GROUPS)


def _migration_scope(profile):
    category = profile.get('DOMAIN_CATEGORY', 'SEM DOMINIO')
    if category in ('FORESEA', 'PARCEIRO'):
        return 'IN_SCOPE'
    if category == 'SEM DOMINIO':
        return 'REVIEW_MISSING_EMAIL'
    return 'OUT_OF_SCOPE_THIRD_PARTY'


def _load_login_usage():
    usage = defaultdict(lambda: {
        'login_count': 0,
        'last_login': None,
        'apps': set(),
        'active_days': set(),
        'active_hours': set(),
    })
    for row in _load_csv('consolidated_logintracking_from_sources.csv'):
        if row.get('ATTEMPTRESULT', '').upper() not in ('', 'LOGIN'):
            continue
        userid = row.get('USERID', '').strip().upper()
        if not userid:
            continue
        dt = _parse_datetime(row.get('ATTEMPTDATE', ''))
        data = usage[userid]
        data['login_count'] += 1
        app = row.get('APP', '').strip()
        if app and app != '-':
            data['apps'].add(app.upper())
        if dt:
            data['active_days'].add(dt.date().isoformat())
            data['active_hours'].add(dt.strftime('%Y-%m-%d %H:00'))
            if data['last_login'] is None or dt > data['last_login']:
                data['last_login'] = dt
    return usage


def _days_since(dt):
    if not dt:
        return ''
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days, 0)


def _assign_license_model(profile, entitlement, login_count, operational_presence, titles):
    if login_count == 0:
        return 'CONCURRENT'
    if entitlement == 'LIMITED':
        return 'CONCURRENT'
    if _is_critical_access(profile):
        return 'AUTHORIZED'
    if operational_presence == 'OFFSHORE':
        return 'AUTHORIZED' if _is_critical_title(titles) else 'CONCURRENT'
    return 'AUTHORIZED' if login_count > 60 or _is_critical_title(titles) else 'CONCURRENT'


def _recommend(profile, entitlement, license_model, login_count, operational_presence):
    if login_count == 0:
        return 'INATIVO (>90d)', 'Sem login no extrato consolidado de 90 dias.'
    if _is_critical_access(profile):
        return 'CONFIRMED_AUTHORIZED', 'Acesso administrativo critico confirmado por grupo MAXADMIN.'

    groups_upper = {str(g).upper().strip() for g in (profile.get('GROUPS') or []) if str(g).strip()}
    og_keywords = [k.upper() for k in get_og_group_keywords()]

    has_og_access = any(
        (kw in g) or (g.startswith(kw)) or (kw in g.replace('-', '_'))
        for g in groups_upper
        for kw in og_keywords
    )

    # FIX do bug: nunca downgrade PREMIUM quando há acesso O&G detectado via grupos
    if entitlement == 'PREMIUM' and operational_presence == 'ONSHORE' and login_count < 5:
        if has_og_access:
            return 'OK', 'Premium mantido: acesso O&G detectado via grupos.'
        return 'DOWNGRADE_CANDIDATE', 'Acesso Premium com uso muito baixo; validar necessidade O&G.'

    # CANONICAL RULE: MOVE_TO_CONCURRENT applies when login_count < 30 (documented standard)
    if license_model == 'AUTHORIZED' and login_count < 30:
        return 'MOVE_TO_CONCURRENT', 'Baixa frequencia para usuario dedicado; avaliar pool concorrente.'
    if license_model == 'AUTHORIZED':
        return 'CONFIRMED_AUTHORIZED', 'Uso/cargo justifica disponibilidade fixa.'
    return 'OK', 'Usuario dimensionado para pool concorrente.'


def calculate_statistical_concurrency():
    """
    Motor Científico de Dados (High Watermark Analysis):
    Lê os logs de acesso diários e cruza com a contagem total de funcionários por cargo.
    Retorna os percentis P50 (Mediana/Cotidiano), P95 (Pico de Turno) e P100 (Worst Case/Emergência).
    """
    try:
        track_df = pd.read_csv(CONSOLIDATED_DIR / 'consolidated_logintracking_from_sources.csv')
        access_df = pd.read_csv(CONSOLIDATED_DIR / 'consolidated_user_access_normalized.csv')

        if 'ATTEMPTRESULT' in track_df.columns:
            track_df = track_df[track_df['ATTEMPTRESULT'].str.upper() == 'LOGIN']

        # --- FIX: Use a função de parse robusta e remova falhas ---
        track_df['ATTEMPTDATE'] = track_df['ATTEMPTDATE'].apply(_parse_datetime)
        track_df.dropna(subset=['ATTEMPTDATE'], inplace=True)

        track_df['LOGIN_DAY'] = track_df['ATTEMPTDATE'].dt.date

        access_df['USERID'] = access_df['USERID'].astype(str).str.upper().str.strip()
        access_df['TITLE'] = access_df['TITLE'].fillna('').astype(str).str.strip()
        user_titles = (
            access_df[access_df['TITLE'] != '']
            .drop_duplicates(['USERID', 'TITLE'])
            .groupby('USERID')['TITLE']
            .first()
            .reset_index()
        )

        track_df['USERID'] = track_df['USERID'].astype(str).str.upper().str.strip()
        merged_df = pd.merge(track_df, user_titles, on='USERID', how='inner')

        # 1. Contagem de logins únicos POR DIA POR CARGO
        daily_active = merged_df.groupby(['LOGIN_DAY', 'TITLE'])['USERID'].nunique().reset_index()
        daily_active.rename(columns={'USERID': 'ACTIVE_USERS'}, inplace=True)

        # 2. Contagem do passivo físico total POR CARGO
        total_users = user_titles.groupby('TITLE')['USERID'].nunique().reset_index()
        total_users.rename(columns={'USERID': 'TOTAL_USERS'}, inplace=True)

        # 3. Cruzamento para achar a Taxa de Concorrência Diária
        stats_df = pd.merge(daily_active, total_users, on='TITLE')
        stats_df['DAILY_RATIO'] = stats_df['ACTIVE_USERS'] / stats_df['TOTAL_USERS']

        # 4. Cálculo dos Percentis Estatísticos
        percentiles = stats_df.groupby('TITLE')['DAILY_RATIO'].agg(
            p50=lambda x: np.percentile(x, 50),
            p95=lambda x: np.percentile(x, 95),
            p100='max'
        ).reset_index()

        # Converte para dicionário aninhado: { 'Cargo': {'p50': 0.2, 'p95': 0.4, 'p100': 0.8} }
        return percentiles.set_index('TITLE').to_dict('index')
    except Exception as e:
        print(f"[Aviso Data Science] Fallback ativado. Erro no logintracking: {e}")
        return {}


def simulate_app_points(profiles_to_simulate):
    """
    Simulação avançada aplicando as Regras Críticas O&G e os Fatores Estatísticos.
    """
    app_points_data = []
    stat_map = calculate_statistical_concurrency()
    login_usage = _load_login_usage()

    for profile in profiles_to_simulate:
        usage = classify_usage_profile(len(profile['GROUPS']))
        entitlement = determine_user_entitlement(profile['GROUPS'])

        display_names = [str(n).strip() for n in profile.get('DISPLAYNAME', []) if n and str(n).strip()]
        titles = [str(t).strip() for t in profile.get('TITLES', []) if t and str(t).strip()]
        cargo_principal = _canonical_title(profile)
        operational_presence = _classify_operational_presence(profile)
        user_usage = login_usage.get(str(profile['USERID']).upper(), {})
        login_count = user_usage.get('login_count', 0)

        license_model = _assign_license_model(profile, entitlement, login_count, operational_presence, titles)
        points = calculate_app_points(entitlement, license_model)

        rec, reason = _recommend(profile, entitlement, license_model, login_count, operational_presence)

        # Busca os fatores estatísticos reais do cargo. Se não existir, usa médias seguras de O&G.
        fallback_stats = (
            {'p50': 0.33, 'p95': 0.50, 'p100': 0.85}
            if operational_presence == 'OFFSHORE'
            else {'p50': 0.55, 'p95': 0.75, 'p100': 1.0}
        )
        cargo_stats = stat_map.get(cargo_principal, fallback_stats)

        # Limita os fatores entre 10% (mínimo irreal) e 100% (absoluto)
        f_p50 = max(0.10, min(cargo_stats['p50'], 1.0))
        f_p95 = max(0.15, min(cargo_stats['p95'], 1.0))
        f_p100 = max(0.20, min(cargo_stats['p100'], 1.0))

        app_points_data.append({
            'USERID': profile['USERID'],
            'DISPLAYNAME': '; '.join(display_names) if display_names else profile['USERID'],
            'EMAIL': profile.get('EMAIL', ''),
            'DOMAIN_CATEGORY': profile.get('DOMAIN_CATEGORY', 'SEM DOMINIO'),
            'MIGRATION_SCOPE': _migration_scope(profile),
            'ENTITLEMENT': entitlement,
            'LICENSE_MODEL': license_model,
            'APP_POINTS': points,
            'TITLES': '; '.join(titles) if titles else "N/A",
            'OPERATIONAL_PRESENCE': operational_presence,
            'USAGE_PROFILE': usage,
            'OPTIMIZATION_REC': rec,
            'OPTIMIZATION_REASON': reason,
            'LOGIN_COUNT_90D': login_count,
            'DAYS_SINCE_LAST': _days_since(user_usage.get('last_login')),
            'ACTIVE_DAYS': sorted(user_usage.get('active_days', set())),
            'ACTIVE_HOURS': sorted(user_usage.get('active_hours', set())),
            'FACTOR_P50': f_p50,
            'FACTOR_P95': f_p95,
            'FACTOR_P100': f_p100
        })
    return app_points_data
