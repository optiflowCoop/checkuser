#!/usr/bin/env python3
"""
Fase 3: Análise de Uso Real - LOGINTRACKING

Consolida histórico de acesso por usuário (últimos 90 dias) e classifica:
- Módulos O&G Premium vs Standard
- Perfil de uso (Power/Medium/Light)
- Usuários ociosos (sem login recente)
"""
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'consolidated'

# Módulos O&G que REQUEREM licença PREMIUM
OG_PREMIUM_MODULES = {
    'WOTRACK': ['PETROLEUM', 'OILGAS', 'OG_'],  # WO com contexto O&G
    'ASSET': ['PETROLEUM', 'OILGAS', 'OG_'],
    'PFWORKTRACK': [],  # PetroField Work Tracking
    'PFASSIGNMENT': [],  # Field Operations Assignment
    'LOCREC': [],  # Location Records
    'COMPLIANCE': [],  # Compliance Management
    'HSE': [],  # Health Safety Environment
    'DRILLING': [],  # Drilling Operations
}

# Domínios prioritários (usuários permanentes Foresea)
PRIORITY_DOMAINS = ['@foresea.com', '@foresea-partner.com']

# Keywords para identificar OFFSHORE (turnista)
OFFSHORE_KEYWORDS = [
    'offshore', 'plataforma', 'platform', 'embarcado', 'fpso',
    'rig', 'sonda', 'vessel', 'navio', 'mob_', 'turno'
]

# Módulos BASE (não requerem Premium)
STANDARD_MODULES = {
    'STARTCNTR', 'ASSET', 'WORKORDER', 'PM', 'INVENTORY',
    'JOBPLAN', 'SR', 'PURCHASING', 'RECEIVING', 'MATRECTRANS'
}


def classify_operational_presence(persongroup, title):
    """
    Identifica se usuário é OFFSHORE (turnista) ou ONSHORE (administrativo)

    OFFSHORE = revezamento 12h, baixa simultaneidade → CONCURRENT
    ONSHORE = administrativo, alta simultaneidade → pode ser AUTHORIZED

    Returns:
        str: 'OFFSHORE' ou 'ONSHORE'
    """
    text = f"{persongroup} {title}".lower()
    if any(keyword in text for keyword in OFFSHORE_KEYWORDS):
        return 'OFFSHORE'
    return 'ONSHORE'


def classify_user_by_domain(email):
    """
    Classifica usuário por domínio de email

    Returns:
        str: 'FORESEA' (permanente) ou 'TEMPORARY' (contratado)
    """
    if not email:
        return 'UNKNOWN'

    email_lower = email.lower()
    for domain in PRIORITY_DOMAINS:
        if domain.lower() in email_lower:
            return 'FORESEA'

    return 'TEMPORARY'


def load_csv(filename):
    """Carrega CSV com encoding seguro"""
    path = IN_DIR / filename
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def is_premium_app(app_name):
    """
    Identifica se app requer licença PREMIUM (contexto O&G)

    Regra IBM: Qualquer módulo com contexto Petroleum/OilGas requer Premium
    """
    app_upper = app_name.upper()

    # Check explicit O&G modules
    for module_base, og_suffixes in OG_PREMIUM_MODULES.items():
        if isinstance(og_suffixes, list):
            if any(suffix in app_upper for suffix in og_suffixes):
                return True
        elif module_base in app_upper:
            return True

    return False


def detect_premium_from_groups(groups_list):
    """
    Detecta se usuário precisa Premium baseado em grupos de segurança O&G.

    LOGINTRACKING tem apenas IDs numéricos de apps, sem mapeamento disponível.
    Solução: usar GROUPS de consolidated_user_access que identificam acesso O&G.

    Args:
        groups_list: Lista ou string delimitada por ; com nomes de grupos

    Returns:
        bool: True se encontrar grupos O&G que requerem Premium
    """
    if not groups_list:
        return False

    # Parse groups se for string
    if isinstance(groups_list, str):
        groups = [g.strip().upper() for g in groups_list.split(';') if g.strip()]
    else:
        groups = [str(g).upper() for g in groups_list if g]

    # Keywords O&G em nomes de grupos
    OG_GROUP_KEYWORDS = [
        'OG_', 'O&G', 'OILGAS', 'PETROLEUM', 'PETRO',
        'HSE', 'DRILLING', 'DRILL', 'RIG', 'FPSO',
        'PFWORK', 'LOCREC', 'COMPLIANCE', 'WELL'
    ]

    for group in groups:
        if any(keyword in group for keyword in OG_GROUP_KEYWORDS):
            return True

    return False


# Funções críticas que precisam AUTHORIZED mesmo offshore (sempre disponíveis)
CRITICAL_TITLES = [
    'almoxarife', 'almox', 'supply', 'suprimento',
    'supervisor', 'coord', 'lider', 'gerente', 'gestor',
    'planejador', 'planner', 'programador', 'scheduler',
    'engenheiro', 'engineer', 'inspetor', 'inspector'
]


def is_critical_function(title):
    """Identifica funções críticas que precisam authorized mesmo offshore."""
    if not title:
        return False
    title_lower = title.lower()
    return any(crit in title_lower for crit in CRITICAL_TITLES)


def classify_user_tier(app_list, login_count_90d, operational_presence, title='', groups=''):
    """
    Classifica usuário em tiers para otimização

    LÓGICA FORESEA ASSERTIVA:
    - OFFSHORE + Função Crítica (almoxarife, supervisor) = AUTHORIZED (precisa disponibilidade 24/7)
    - OFFSHORE + Função Operacional (técnico, operador) = CONCURRENT (revezamento turno)
    - ONSHORE + uso intenso (>60 logins) = AUTHORIZED
    - Demais = CONCURRENT
    """
    has_premium = detect_premium_from_groups(groups)
    is_critical = is_critical_function(title)

    # REGRA 1: Ociosos (0 logins)
    if login_count_90d == 0:
        return ('IDLE', 'NONE', 0)

    # REGRA 2: Uso extremamente baixo
    if login_count_90d < 5:
        return ('VERY_LIGHT', 'LIMITED', 5)

    # REGRA 3: OFFSHORE - dividir entre Críticos (AUTHORIZED) e Operacionais (CONCURRENT)
    if operational_presence == 'OFFSHORE':
        if is_critical:
            if has_premium:
                return ('CRITICAL_OFFSHORE_OG', 'PREMIUM_AUTHORIZED', 5)
            else:
                return ('CRITICAL_OFFSHORE_STD', 'BASE_AUTHORIZED', 2)
        else:
            if has_premium:
                return ('OFFSHORE_OG', 'PREMIUM_CONCURRENT', 15)
            else:
                return ('OFFSHORE_STD', 'BASE_CONCURRENT', 10)

    # REGRA 4: ONSHORE - Authorized = exceção (não regra)
    if has_premium:
        if login_count_90d > 60:
            return ('POWER_OG', 'PREMIUM_AUTHORIZED', 5)
        else:
            return ('MEDIUM_OG', 'PREMIUM_CONCURRENT', 15)
    else:
        if login_count_90d > 60:
            return ('POWER_STD', 'BASE_AUTHORIZED', 2)
        else:
            return ('MEDIUM_STD', 'BASE_CONCURRENT', 10)


def main():
    print("🔍 Fase 3: Analisando Histórico de Uso (LOGINTRACKING)")

    # Carregar dados base
    identities = load_csv('consolidated_user_identity.csv')
    access_data = load_csv('consolidated_user_access_normalized.csv')

    # Carregar emails
    email_data = load_csv('consolidated_email.csv')
    email_map = {}
    for e in email_data:
        # CORREÇÃO APLICADA: Ler PERSONID em vez de apenas USERID
        userid = e.get('PERSONID', '').strip() or e.get('USERID', '').strip()
        email = e.get('EMAILADDRESS', '').strip() or e.get('PRIMARYEMAIL', '').strip()
        if userid and email:
            email_map[userid] = email

    print(f"✓ Carregados {len(email_map)} emails reais da base")

    # Carregar LOGINTRACKING consolidado
    logintrack_path = IN_DIR / 'consolidated_logintracking.csv'
    if not logintrack_path.exists():
        print(f"⚠️  AVISO: {logintrack_path.name} não encontrado. Execute extração primeiro.")
        return

    logintrack = load_csv('consolidated_logintracking.csv')
    print(f"✓ Carregado {len(logintrack)} registros de acesso (últimos 90 dias)")

    # Agregar uso por usuário
    usage_by_user = defaultdict(lambda: {
        'apps': set(),
        'login_count': 0,
        'last_login': None,
        'environments': set()
    })

    for rec in logintrack:
        env = rec.get('ENVIRONMENT', '').strip() or rec.get('ENV_DB', '').strip()
        userid = rec.get('USERID', '').strip()
        app = rec.get('APP', '').strip()
        date_str = rec.get('ATTEMPTDATE', '').strip()

        if not (env and userid):
            continue

        key = f"{env}|{userid}"
        usage_by_user[key]['apps'].add(app)
        usage_by_user[key]['login_count'] += 1
        usage_by_user[key]['environments'].add(env)

        if date_str:
            try:
                login_date = datetime.fromisoformat(date_str.split()[0])
                if not usage_by_user[key]['last_login'] or login_date > usage_by_user[key]['last_login']:
                    usage_by_user[key]['last_login'] = login_date
            except:
                pass

    print(f"✓ Processados {len(usage_by_user)} usuários únicos com histórico")

    # Gerar análise detalhada
    output_rows = []

    for identity in identities:
        userid = identity.get('USERID', '').strip()
        status = identity.get('STATUS', '').strip().upper()

        if status != 'ACTIVE':
            continue

        user_access = [a for a in access_data if a.get('USERID', '').strip() == userid]

        groups = set()
        title = ''
        persongroup = ''
        env_list = set()

        for acc in user_access:
            env_list.add(acc.get('ENV_DB', ''))
            if acc.get('GROUPNAME'):
                groups.add(acc.get('GROUPNAME', '').strip())
            if not title and acc.get('TITLE'):
                title = acc.get('TITLE', '').strip()
            if not persongroup and acc.get('PERSONGROUP'):
                persongroup = acc.get('PERSONGROUP', '').strip()

        total_logins = 0
        all_apps = set()
        last_login_overall = None

        for env in env_list:
            key = f"{env}|{userid}"
            if key in usage_by_user:
                usage = usage_by_user[key]
                total_logins += usage['login_count']
                all_apps.update(usage['apps'])
                if usage['last_login']:
                    if not last_login_overall or usage['last_login'] > last_login_overall:
                        last_login_overall = usage['last_login']

        operational_presence = classify_operational_presence(persongroup, title)

        tier, required_license, app_points = classify_user_tier(
            list(all_apps), total_logins, operational_presence, title, groups
        )

        # Mapeando email com o email_map corrigido
        email = email_map.get(userid, '') or identity.get('PRIMARYEMAIL', '') or identity.get('EMAILADDRESS', '')
        user_category = classify_user_by_domain(email)

        premium_apps = [app for app in all_apps if is_premium_app(app)]
        standard_apps = [app for app in all_apps if not is_premium_app(app)]

        output_rows.append({
            'USERID': userid,
            'DISPLAYNAME': identity.get('DISPLAYNAME', ''),
            'EMAIL': email,
            'USER_CATEGORY': user_category,
            'OPERATIONAL_PRESENCE': operational_presence,
            'STATUS': status,
            'TITLE': title,
            'PERSONGROUP': persongroup,
            'ENV_COUNT': len(env_list),
            'SECURITY_GROUPS_COUNT': len(groups),
            'LOGIN_COUNT_90D': total_logins,
            'LAST_LOGIN': last_login_overall.strftime('%Y-%m-%d') if last_login_overall else '',
            'APPS_USED': len(all_apps),
            'PREMIUM_APPS': '; '.join(sorted(premium_apps)[:5]),
            'STANDARD_APPS': '; '.join(sorted(standard_apps)[:5]),
            'USER_TIER': tier,
            'REQUIRED_LICENSE': required_license,
            'APP_POINTS_COST': app_points,
            'MIGRATION_PRIORITY': 'HIGH' if user_category == 'FORESEA' else 'LOW'
        })

    out_path = OUT_DIR / 'usage_analysis_phase3.csv'
    if output_rows:
        with out_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
            writer.writeheader()
            writer.writerows(output_rows)

        print(f"✅ ESCRITO: {out_path.name} ({len(output_rows)} usuários ativos analisados)")

        foresea_users = [r for r in output_rows if r['USER_CATEGORY'] == 'FORESEA']
        temp_users = [r for r in output_rows if r['USER_CATEGORY'] == 'TEMPORARY']

        offshore_users = [r for r in foresea_users if r['OPERATIONAL_PRESENCE'] == 'OFFSHORE']
        onshore_users = [r for r in foresea_users if r['OPERATIONAL_PRESENCE'] == 'ONSHORE']

        idle = sum(1 for r in output_rows if r['USER_TIER'] == 'IDLE')
        premium_needed = sum(1 for r in output_rows if 'PREMIUM' in r['REQUIRED_LICENSE'])
        authorized_count = sum(1 for r in foresea_users if 'AUTHORIZED' in r['REQUIRED_LICENSE'])
        concurrent_count = sum(1 for r in foresea_users if 'CONCURRENT' in r['REQUIRED_LICENSE'])

        foresea_cost = sum(r['APP_POINTS_COST'] for r in foresea_users)
        temp_cost = sum(r['APP_POINTS_COST'] for r in temp_users)

        print(f"\n📊 RESUMO EXECUTIVO:")
        print(f"   • Usuários Ativos: {len(output_rows)}")
        print(f"   • 🏢 FORESEA (Permanentes): {len(foresea_users)} ({foresea_cost:.0f} AppPoints)")
        print(f"       ⛵ OFFSHORE: {len(offshore_users)} (sempre Concurrent)")
        print(f"       🏢 ONSHORE: {len(onshore_users)}")
        print(f"   • 👷 TEMPORÁRIOS (Contratados): {len(temp_users)} ({temp_cost:.0f} AppPoints - não migrar)")
        print(f"   • 💤 Ociosos (0 logins 90d): {idle}")
        print(f"   • 🛢️  Requerem Premium O&G: {premium_needed}")
        print(f"\n🎯 DISTRIBUIÇÃO DE LICENÇAS (FORESEA):")
        if foresea_users:
            print(f"   • 🔑 AUTHORIZED: {authorized_count} ({authorized_count / len(foresea_users) * 100:.1f}%)")
            print(f"   • 🔄 CONCURRENT: {concurrent_count} ({concurrent_count / len(foresea_users) * 100:.1f}%)")
        print(f"   • Custo Total AppPoints FORESEA: {foresea_cost:,.0f}")
        print(f"   • Capacidade Contratada: 1,200")
        print(f"   • {'✅ DENTRO DO LIMITE' if foresea_cost <= 1200 else '⚠️  ACIMA DO CONTRATADO'}")
    else:
        print("⚠️  Nenhum usuário ativo encontrado para análise")


if __name__ == '__main__':
    main()