import csv
from pathlib import Path
from collections import Counter

# Define o caminho para o arquivo de identidade consolidado
# Assumimos que o ROOT para este script é o diretório do projeto
# e o arquivo de identidade está em 'output/consolidated/'
ROOT = Path(__file__).resolve().parent.parent.parent # Vai para CHECKUSER
IDENTITY_FILE = ROOT / 'output' / 'consolidated' / 'consolidated_user_identity.csv'

def get_unique_users_data():
    """
    Lê o arquivo de identidade consolidado, executa uma deduplicação inteligente
    e retorna um dicionário com métricas agregadas para o dashboard.
    """
    if not IDENTITY_FILE.exists():
        # Retorna dados vazios se o arquivo não for encontrado, para evitar quebrar o pipeline.
        # Imprime um aviso para o usuário.
        print(f"AVISO: Arquivo de identidade não encontrado em: {IDENTITY_FILE}")
        return {
            "total_registrations": 0,
            "total_unique_users": 0,
            "status_counts": Counter(),
            "domain_counts": Counter(),
            "total_active_unique": 0
        }

    with IDENTITY_FILE.open('r', encoding='utf-8-sig') as f:
        users = list(csv.DictReader(f))

    # 1. Deduplicação Inteligente de Usuários (priorizar EMAIL -> PERSONID -> LOGINID)
    unique_by_email = {}
    unique_by_person = {}
    unique_by_login = {}

    for user in users:
        loginid = user.get('LOGINID', '').strip().upper()
        personid = user.get('PERSONID', '').strip().upper()
        email = user.get('PRIMARYEMAIL', '').strip().lower()
        status = user.get('STATUS', '').upper()

        # Prefer email as primary key when available
        if email:
            key = email
            existing = unique_by_email.get(key)
            if not existing or (status == 'ACTIVE' and existing.get('STATUS', '').upper() != 'ACTIVE'):
                unique_by_email[key] = user
            continue

        # If no email, fallback to PERSONID
        if personid and personid not in ('NULL', 'NONE'):
            key = personid
            existing = unique_by_person.get(key)
            if not existing or (status == 'ACTIVE' and existing.get('STATUS', '').upper() != 'ACTIVE'):
                unique_by_person[key] = user
            continue

        # Finally fallback to LOGINID
        if loginid and loginid not in ('NULL', 'NONE'):
            key = loginid
            existing = unique_by_login.get(key)
            if not existing or (status == 'ACTIVE' and existing.get('STATUS', '').upper() != 'ACTIVE'):
                unique_by_login[key] = user
            continue

    # Merge deduplicated users preferring email records, then person, then login
    deduplicated_list = list(unique_by_email.values())

    # Add persons that are not already represented by email
    emails_seen = set(k for k in unique_by_email.keys())
    for pid, u in unique_by_person.items():
        email = u.get('PRIMARYEMAIL', '').strip().lower()
        if not email or email not in emails_seen:
            deduplicated_list.append(u)

    # Add logins that are not represented by email or person
    persons_seen = {u.get('PERSONID', '').upper() for u in deduplicated_list if u.get('PERSONID')}
    for lid, u in unique_by_login.items():
        email = u.get('PRIMARYEMAIL', '').strip().lower()
        personid = u.get('PERSONID', '').strip().upper()
        if (not email or email not in emails_seen) and (not personid or personid not in persons_seen):
            deduplicated_list.append(u)

    # 2. Cálculo de Métricas com `Counter`
    status_counts = Counter(u.get('STATUS', 'UNKNOWN').upper() for u in deduplicated_list)
    
    domain_counts = Counter()
    active_users = [u for u in deduplicated_list if u.get('STATUS', '').upper() == 'ACTIVE']
    
    for user in active_users:
        email = user.get('PRIMARYEMAIL', '').lower()
        if '@foresea.com' in email:
            domain_counts['foresea'] += 1
        elif '@foresea-partner.com' in email:
            domain_counts['foresea_partner'] += 1
        elif email:
            domain_counts['other'] += 1
        else:
            domain_counts['no_domain'] += 1

    # Define in-scope heuristics: email domain OR known operational sites
    IN_SCOPE_SITES = {'OP-BASE', 'N06', 'N08', 'N09', 'HTQ', 'ODN1', 'ODN2', 'BASE'}
    in_scope = []
    in_scope_active = []
    for u in deduplicated_list:
        email = u.get('PRIMARYEMAIL', '').strip().lower()
        site = u.get('DEFSITE', '').strip().upper()
        if (email and ('@foresea.com' in email or '@foresea-partner.com' in email)) or (site and site in IN_SCOPE_SITES):
            in_scope.append(u)
            if u.get('STATUS','').upper() == 'ACTIVE':
                in_scope_active.append(u)

    # 3. Montagem do Dicionário de Resultados
    return {
        "total_registrations": len(users),
        "total_unique_users": len(deduplicated_list),
        "total_active_unique": status_counts.get('ACTIVE', 0),
        "in_scope_total_unique": len(in_scope),
        "in_scope_active_unique": len(in_scope_active),
        "status_counts": status_counts,
        "domain_counts": domain_counts
    }

if __name__ == '__main__':
    # Para testes diretos
    try:
        data = get_unique_users_data()
        import json
        # Counter não é serializável em JSON por padrão, então convertemos para dict
        data['status_counts'] = dict(data['status_counts'])
        data['domain_counts'] = dict(data['domain_counts'])
        print(json.dumps(data, indent=2))
    except FileNotFoundError as e:
        print(e)