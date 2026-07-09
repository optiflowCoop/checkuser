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


def _detect_delimiter(path: Path) -> str:
    """
    Detecta delimiter mais provável entre ',', ';' e '\t' lendo algumas linhas do arquivo.
    Objetivo: evitar CSVs 'colados' onde o cabeçalho vem como "A;B;C" (delimiter=','),
    mas o código tentava ler como delimiter=','.
    """
    candidates = [',', ';', '\t']
    if not path.exists():
        return ','

    # Lê poucas linhas para não pesar (arquivos podem ser grandes).
    sample_lines = []
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        for _ in range(25):
            line = handle.readline()
            if not line:
                break
            line = line.strip('\n\r')
            if line.strip():
                sample_lines.append(line)

    if not sample_lines:
        return ','

    best = ','
    best_score = -1

    for delim in candidates:
        score = 0
        for i, line in enumerate(sample_lines[:10]):
            # Conta "campos" aproximado; o cabeçalho normalmente guia melhor.
            parts = line.split(delim)
            if len(parts) <= 1:
                continue
            # Pontua mais a linha 0/1 (cabeçalho).
            weight = 3 if i == 0 else 2 if i == 1 else 1
            score += weight * len(parts)
        if score > best_score:
            best_score = score
            best = delim

    return best


def _load_csv(name):
    path = CONSOLIDATED_DIR / name
    if not path.exists():
        return []
    delimiter = _detect_delimiter(path)
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


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


def _normalize_titles(raw_titles):
    """
    Normaliza TITLES vindos do consolidado/engenharia (pode vir como:
    - lista de strings
    - set (stringified)
    - string tipo "SET()" / "N/A"
    - string com separadores ; , 
    """
    if raw_titles is None:
        return []

    # Caso set/list
    if isinstance(raw_titles, (list, set, tuple)):
        out = []
        for t in raw_titles:
            if t is None:
                continue
            s = str(t).strip()
            if not s:
                continue
            if s.upper() in ('N/A', 'NA', 'NONE', 'NULL', 'SET()'):
                continue
            out.append(s)
        return sorted(set(out))

    # Caso string
    s = str(raw_titles).strip()
    if not s:
        return []
    if s.upper() in ('N/A', 'NA', 'NONE', 'NULL', 'SET()', '{}'):
        return []

    # Remove wrapper de "set()" / "{...}" se vier stringified
    s_up = s.upper()
    if s_up.startswith('SET(') and s_up.endswith(')'):
        s = s[4:-1].strip()
    if s.startswith('{') and s.endswith('}'):
        s = s[1:-1].strip()

    # Divide por separadores comuns
    parts = []
    for sep in [';', ',', '|']:
        if sep in s:
            parts = [p.strip() for p in s.split(sep)]
            break
    if not parts:
        parts = [s.strip()]

    cleaned = []
    for p in parts:
        if not p:
            continue
        p = p.strip().strip("'").strip('"').strip()
        if not p:
            continue
        if p.upper() in ('N/A', 'NA', 'NONE', 'NULL', 'SET()'):
            continue
        cleaned.append(p)

    return sorted(set(cleaned))


def _canonical_title(profile):
    titles = _normalize_titles(profile.get('TITLES', []))
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
    normalized = _normalize_titles(titles)
    title_text = ' '.join(normalized).upper()
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
    usage = defaultdict(
        lambda: {
            'login_count': 0,
            'last_login': None,
            'apps': set(),
            'active_days': set(),
            'active_hours': set(),
        }
    )

    logintracking_rows = _load_csv('consolidated_logintracking_from_sources.csv')
    if not logintracking_rows:
        return usage

    # ATTEMPTDATE pode vir com nomes diferentes dependendo da origem.
    possible_date_cols = [
        'ATTEMPTDATE',
        'ATTEMPTDATETIME',
        'ATTEMPT_DT',
        'ATTEMPTDT',
        'EVENTDATE',
        'LOGIN_DATE',
    ]
    first_row_keys = set((logintracking_rows[0] or {}).keys())
    date_col = next((c for c in possible_date_cols if c in first_row_keys), None)

    # ATTEMPTRESULT: historicamente pode vir vazio/constante.
    # Se existir evidência de que "LOGIN" aparece, aplicamos filtro.
    # Caso contrário, contamos qualquer linha com USERID (fallback quando ATTEMPTDATE/ATTEMPTRESULT não são confiáveis).
    attempt_values = set()
    for r in logintracking_rows[:5000]:
        v = str((r or {}).get('ATTEMPTRESULT', '')).strip().upper()
        if v:
            attempt_values.add(v)
        if len(attempt_values) >= 10:
            break
    attempt_has_login = 'LOGIN' in attempt_values

    for row in logintracking_rows:
        userid = str(row.get('USERID', '')).strip().upper()
        if not userid:
            continue

        if attempt_has_login:
            v = str(row.get('ATTEMPTRESULT', '')).strip().upper()
            if v not in ('', 'LOGIN'):
                continue

        dt_raw = row.get(date_col, '') if date_col else ''
        dt = _parse_datetime(dt_raw)

        data = usage[userid]
        data['login_count'] += 1

        app = str(row.get('APP', '')).strip()
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
    # Preservar AUTHORIZED para títulos críticos mesmo quando o login_count veio 0
    # (evita zerar Aba 1/3 e cards de Authorized-as-is).
    if login_count == 0:
        if _is_critical_access(profile) or _is_critical_title(titles):
            return 'AUTHORIZED'
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
        logintrack_path = CONSOLIDATED_DIR / 'consolidated_logintracking_from_sources.csv'
        access_path = CONSOLIDATED_DIR / 'consolidated_user_access_normalized.csv'

        logintrack_delim = _detect_delimiter(logintrack_path)
        access_delim = _detect_delimiter(access_path)

        track_df = pd.read_csv(
            logintrack_path,
            delimiter=logintrack_delim
        )
        access_df = pd.read_csv(
            access_path,
            delimiter=access_delim
        )

        if 'ATTEMPTRESULT' in track_df.columns:
            track_df = track_df[track_df['ATTEMPTRESULT'].str.upper() == 'LOGIN']

        # ATTEMPTDATE pode não existir; detectar alternativa.
        possible_date_cols = ['ATTEMPTDATE', 'ATTEMPTDATETIME', 'ATTEMPT_DT', 'ATTEMPTDT', 'EVENTDATE', 'LOGIN_DATE']
        date_col = next((c for c in possible_date_cols if c in track_df.columns), None)

        # Se não existir coluna de data, não dá para calcular P50/P95/P100 por dia.
        # Retorna vazio para disparar fallback controlado em simulate_app_points().
        if not date_col:
            return {}

        # --- FIX: Use a função de parse robusta e remova falhas ---
        track_df['_PARSED_ATTEMPTDATE'] = track_df[date_col].apply(_parse_datetime)
        track_df.dropna(subset=['_PARSED_ATTEMPTDATE'], inplace=True)

        track_df['LOGIN_DAY'] = track_df['_PARSED_ATTEMPTDATE'].dt.date

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


def simulate_app_points(profiles_to_simulate, user_real_env=None):
    """
    Simulação avançada aplicando as Regras Críticas O&G e os Fatores Estatísticos.
    
    Args:
        profiles_to_simulate: lista de perfis de usuário
        user_real_env: dicionário {userid: env} com ambiente real inferido do logintracking
    """
    app_points_data = []
    stat_map = calculate_statistical_concurrency()
    login_usage = _load_login_usage()
    
    if user_real_env is None:
        user_real_env = {}

    for profile in profiles_to_simulate:
        usage = classify_usage_profile(len(profile['GROUPS']))
        entitlement = determine_user_entitlement(profile['GROUPS'])

        display_names = [str(n).strip() for n in profile.get('DISPLAYNAME', []) if n and str(n).strip()]
        titles = _normalize_titles(profile.get('TITLES', []))
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

        # Determina LOCAL_SITE: prioriza ambiente real do logintracking
        local_site = user_real_env.get(str(profile['USERID']).upper(), '')
        if not local_site:
            local_site = profile.get('LOCATION_SITE', '')
        
        app_points_data.append({
            'USERID': profile['USERID'],
            'DISPLAYNAME': '; '.join(display_names) if display_names else profile['USERID'],
            'EMAIL': profile.get('EMAIL', ''),
            'DOMAIN_CATEGORY': profile.get('DOMAIN_CATEGORY', 'SEM DOMINIO'),
            'MIGRATION_SCOPE': _migration_scope(profile),
            'ENTITLEMENT': entitlement,
            'LICENSE_MODEL': license_model,
            'APP_POINTS': points,
            'LOCATION_SITE': local_site,
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
