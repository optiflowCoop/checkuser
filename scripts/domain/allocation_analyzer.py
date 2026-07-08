"""
scripts/domain/allocation_analyzer.py

Saneamento de Alocação para migração ao Maximo 9 (até 9 ambientes).

Para cada usuário do Maximo (inclusive INACTIVOS), calcula:
  - Histórico de logins dos últimos 90 dias por ambiente (inferido do CLIENTHOST)
  - Alocação real (onde o usuário está baseado) -> persongroupview.locationsite / DEFSITE
  - Ambiente principal de uso (maior volume de logins)
  - Ambientes secundários (>= MIN_SECUNDARIO acessos nos últimos 90d)
  - Sugestão de em quais ambientes criar a conta do usuário no Maximo 9

Esta análise é ADITIVA e NÃO altera o cálculo de AppPoints.
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'

# Regra de negócio: ambiente secundário exige no mínimo este número de acessos (90d)
MIN_SECUNDARIO = 5
LOOKBACK_DAYS = 90

# Ambientes conhecidos (para colunas individuais)
KNOWN_ENVS = ['BASE', 'ODN1', 'ODN2', 'ODN3', 'ODN4', 'N06', 'N08', 'N09', 'HTQ', 'POL', 'PGA', 'PGB', 'PGC']


def detect_delimiter(path: Path):
    with path.open('r', encoding='utf-8-sig') as f:
        first_line = f.readline()
    return ';' if ';' in first_line else ','


def load_csv(path: Path):
    if not path.exists():
        return []
    delim = detect_delimiter(path)
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delim))


def _is_junk(value):
    """Filtra linhas de cabeçalho/copyright que por vezes poluem os CSVs."""
    v = (value or '').upper()
    return any(k in v for k in ('COPYRIGHT', 'RESTRICTED', 'DUPLICATION', 'IBM CORP'))


def parse_date_safe(date_str):
    if not date_str:
        return None
    text = str(date_str).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d-%H.%M.%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def normalize_env(env):
    """Normaliza nomes de ambiente: NORBE06 -> N06, NORBE08 -> N08, NORBE09 -> N09, OP-BASE -> BASE, BASE-UNP -> BASE."""
    if not env:
        return env
    e = env.upper().strip()
    mapping = {'NORBE06': 'N06', 'NORBE08': 'N08', 'NORBE09': 'N09',
               'BASE-UNP': 'BASE', 'OP-BASE': 'BASE', 'ODRL-SP': 'BASE'}
    return mapping.get(e, e)


def infer_env_from_clienthost(clienthost):
    """Infere o ambiente a partir do CLIENTHOST (hostname ou IP).
    Retorna (env, is_shared). Baseado em analyze_usage.py / generate_risk_report.py."""
    if not clienthost:
        return None, False
    host = clienthost.strip().upper()

    IP_TO_ENV = {
        '10.119.240.73': 'BASE',
        '10.120.216.81': 'ODN1',
        '10.118.6.88': 'ODN2',
        '10.120.148.67': 'N06',
        '10.120.148.143': 'N08',
        '10.120.149.83': 'N09',
        '10.119.58.21': 'HTQ',
    }

    if host.replace('.', '').isdigit():
        return IP_TO_ENV.get(host), False

    if 'ODRL-SP-SV' in host:
        return None, True  # servidor compartilhado

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


def analyze_allocation():
    """Analisa alocação real e sugere ambientes para criação de conta no Maximo 9."""
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    logintrack = load_csv(IN_DIR / 'consolidated_logintracking_from_sources.csv')
    pgv = load_csv(IN_DIR / 'consolidated_persongroupview.csv')

    print(f"📥 Alocação: identities={len(identities)} logintrack={len(logintrack)} pgv={len(pgv)}")

    # ---- 1. Mapa de alocação real (persongroupview) ----
    pgv_locations = defaultdict(set)
    pgv_env = defaultdict(set)
    for r in pgv:
        pid = (r.get('personid') or '').strip().upper()
        if not pid or _is_junk(pid):
            continue
        loc = normalize_env((r.get('locationsite') or '').strip().upper())
        env = normalize_env((r.get('ENVIRONMENT') or '').strip().upper())
        if loc and loc != '0':
            pgv_locations[pid].add(loc)
        if env:
            pgv_env[pid].add(env)

    # ---- 2. Janela de 90 dias (referência = data máxima do logintracking) ----
    max_dt = None
    for rec in logintrack:
        dt = parse_date_safe(rec.get('ATTEMPTDATE'))
        if dt and (max_dt is None or dt > max_dt):
            max_dt = dt
    if max_dt is None:
        max_dt = datetime.now()
    cutoff = max_dt - timedelta(days=LOOKBACK_DAYS)
    print(f"   Janela 90d: de {cutoff.date()} até {max_dt.date()}")

    # ---- 3. Logins por usuário/ambiente (últimos 90d) ----
    user_env_counts = defaultdict(lambda: defaultdict(int))   # userid -> env -> count
    user_last_login = {}
    for rec in logintrack:
        if (rec.get('ATTEMPTRESULT') or '').strip().upper() != 'LOGIN':
            continue
        userid = (rec.get('USERID') or '').strip().upper()
        if not userid or _is_junk(userid):
            continue
        dt = parse_date_safe(rec.get('ATTEMPTDATE'))
        if not dt or dt < cutoff:
            continue
        env, is_shared = infer_env_from_clienthost(rec.get('CLIENTHOST', ''))
        if not env:
            continue
        user_env_counts[userid][env] += 1
        if userid not in user_last_login or dt > user_last_login[userid]:
            user_last_login[userid] = dt

    # ---- 4. Processar cada usuário da identidade (DEDUP por USERID) ----
    user_rows = {}
    for r in identities:
        userid = (r.get('USERID') or '').strip().upper()
        if not userid or _is_junk(userid):
            continue
        if userid not in user_rows:
            user_rows[userid] = r
        else:
            if (user_rows[userid].get('STATUS') or '').strip().upper() != 'ACTIVE' and \
               (r.get('STATUS') or '').strip().upper() == 'ACTIVE':
                user_rows[userid] = r

    analises = []
    for userid, r in user_rows.items():
        status = (r.get('STATUS') or '').strip().upper() or 'ACTIVE'
        displayname = (r.get('DISPLAYNAME') or '').strip()
        email = (r.get('PRIMARYEMAIL') or '').strip().lower()
        defsite = normalize_env((r.get('DEFSITE') or '').strip().upper())
        env_db = normalize_env((r.get('ENV_DB') or '').strip().upper())

        # Alocação real: locationsite (pgv) > DEFSITE > ENV_DB
        locs = pgv_locations.get(userid, set())
        allocation_primary = ''
        if locs:
            allocation_primary = sorted(locs)[0]
        elif defsite:
            allocation_primary = defsite
        elif env_db:
            allocation_primary = env_db

        raw_env_counts = dict(user_env_counts.get(userid, {}))
        total_logins = sum(raw_env_counts.values())
        last_login = user_last_login.get(userid)

        # Preencher contagens por ambiente conhecido (para colunas individuais)
        env_logins_detail = {}
        for e in KNOWN_ENVS:
            env_logins_detail[e] = raw_env_counts.get(e, 0)
        # Ambientes não-listados são incluídos como "OUTROS"
        outros = {e: c for e, c in raw_env_counts.items() if e not in KNOWN_ENVS}
        if outros:
            env_logins_detail['OUTROS'] = sum(outros.values())

        # Ambiente principal de USO (maior volume)
        if raw_env_counts:
            primary_env = max(raw_env_counts.items(), key=lambda kv: kv[1])[0]
        else:
            primary_env = allocation_primary

        # Secundários: >= MIN_SECUNDARIO acessos e diferentes da alocação principal
        secondary = sorted(
            [e for e, c in raw_env_counts.items() if c >= MIN_SECUNDARIO and e != allocation_primary],
            key=lambda e: raw_env_counts[e], reverse=True
        )

        # Sugestão de ambientes para criar a conta
        base = allocation_primary or primary_env
        suggested = []
        if base:
            suggested.append(base)
        for e in secondary:
            if e not in suggested:
                suggested.append(e)
        if not suggested and not raw_env_counts:
            suggested = [allocation_primary] if allocation_primary else []

        # Motivo / razão
        if raw_env_counts:
            detalhe = ', '.join(f"{e} ({c})" for e, c in sorted(raw_env_counts.items(), key=lambda kv: kv[1], reverse=True))
            if secondary:
                razao = f"Alocado em {allocation_primary or 'N/A'}; acessou secundarios (>= {MIN_SECUNDARIO}): {', '.join(secondary)}. Criar conta tambem nestes."
            else:
                razao = f"Alocado em {allocation_primary or 'N/A'}; uso concentrado em {primary_env}. Criar conta no ambiente de alocacao."
        else:
            detalhe = 'Sem logins nos ultimos 90d'
            razao = f"Sem logins recentes. Manter na alocacao ({allocation_primary or 'N/A'})."

        analises.append({
            'userid': userid,
            'displayname': displayname,
            'status': status,
            'email': email,
            'allocation_primary': allocation_primary,
            'env_counts': raw_env_counts,
            'env_logins_detail': env_logins_detail,
            'total_logins_90d': total_logins,
            'last_login': last_login.strftime('%Y-%m-%d') if last_login else '',
            'primary_env': primary_env,
            'secondary_envs': secondary,
            'suggested_accounts': suggested,
            'reason': razao,
            'detail': detalhe,
        })

    def _sort_key(a):
        return (0 if a['status'] == 'ACTIVE' else 1, -a['total_logins_90d'])
    analises.sort(key=_sort_key)

    # ---- 5. Estatísticas ----
    total_users = len(analises)
    with_logins = sum(1 for a in analises if a['total_logins_90d'] > 0)
    inactive = sum(1 for a in analises if a['status'] != 'ACTIVE')
    multi = sum(1 for a in analises if len(a['suggested_accounts']) > 1)
    total_suggested = sum(len(a['suggested_accounts']) for a in analises)

    stats = {
        'total_users': total_users,
        'users_with_logins_90d': with_logins,
        'users_inactive': inactive,
        'users_multi_env': multi,
        'total_suggested_accounts': total_suggested,
        'min_secundario': MIN_SECUNDARIO,
        'window_start': cutoff.strftime('%Y-%m-%d'),
        'window_end': max_dt.strftime('%Y-%m-%d'),
    }

    print(f"📊 Alocacao: users={total_users} com_logins={with_logins} inativos={inactive} multi_env={multi}")
    return {'stats': stats, 'analises': analises}


if __name__ == '__main__':
    res = analyze_allocation()
    print("\n=== STATS ===")
    for k, v in res['stats'].items():
        print(f"  {k}: {v}")
    print("\n=== AMOSTRA (top 5) ===")
    for a in res['analises'][:5]:
        print(f"  {a['userid']} | status={a['status']} | aloc={a['allocation_primary']} | "
              f"logins={a['total_logins_90d']} | sugeridos={a['suggested_accounts']}")