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

    # 1. Deduplicação Inteligente de Usuários
    unique_users = {}
    for user in users:
        loginid = user.get('LOGINID', '').strip().upper()
        personid = user.get('PERSONID', '').strip().upper()
        email = user.get('PRIMARYEMAIL', '').strip().lower()
        status = user.get('STATUS', '').upper()

        # Define a chave de unicidade com uma hierarquia de prioridade
        unique_key = None
        if loginid and loginid not in ('NULL', 'NONE'):
            unique_key = f"LOGINID|{loginid}"
        elif personid and personid not in ('NULL', 'NONE'):
            unique_key = f"PERSONID|{personid}"
        elif email:
            unique_key = f"EMAIL|{email}"
        
        if not unique_key:
            continue # Ignora registros sem chave de identificação

        # Lógica de atualização: um novo registro só substitui um antigo se
        # o novo for 'ACTIVE' e o antigo não, ou se a chave ainda não existir.
        if unique_key not in unique_users or (status == 'ACTIVE' and unique_users[unique_key].get('STATUS') != 'ACTIVE'):
            unique_users[unique_key] = user

    deduplicated_list = list(unique_users.values())

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

    # 3. Montagem do Dicionário de Resultados
    return {
        "total_registrations": len(users),
        "total_unique_users": len(deduplicated_list),
        "status_counts": status_counts,
        "domain_counts": domain_counts,
        "total_active_unique": status_counts.get('ACTIVE', 0)
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