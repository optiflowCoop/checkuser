import csv
from pathlib import Path
from collections import Counter

# Define o caminho para o arquivo de decisão de licença (já processado e consolidado)
ROOT = Path(__file__).resolve().parent.parent.parent # Vai para CHECKUSER
LICENSE_PLAN_FILE = ROOT / 'output' / 'consolidated' / 'license_decision_plan.csv'

def get_unique_users_data():
    """
    Lê o arquivo license_decision_plan.csv (já processado pelo pipeline)
    e retorna um dicionário com métricas agregadas para o dashboard.
    
    Este arquivo já contém os dados consolidados e corretos de:
    - Domínio (FORESEA, PARCEIRO, TERCEIRO, SEM DOMINIO)
    - Modelo de licença (AUTHORIZED, CONCURRENT)
    - Entitlement (PREMIUM, BASE)
    """
    if not LICENSE_PLAN_FILE.exists():
        print(f"AVISO: Arquivo de licença não encontrado em: {LICENSE_PLAN_FILE}")
        return {
            "total_registrations": 0,
            "total_unique_users": 0,
            "status_counts": Counter(),
            "domain_counts": Counter(),
            "total_active_unique": 0
        }

    with LICENSE_PLAN_FILE.open('r', encoding='utf-8-sig') as f:
        users = list(csv.DictReader(f))

    # Cálculo de Métricas diretamente do license_decision_plan.csv
    domain_counts = Counter()
    for user in users:
        domain = user.get('DOMAIN_CATEGORY', 'SEM DOMINIO').strip().upper()
        if domain == 'FORESEA':
            domain_counts['foresea'] += 1
        elif domain == 'PARCEIRO':
            domain_counts['foresea_partner'] += 1
        elif domain == 'INTEGRACAO':
            domain_counts['integracao'] += 1
        elif domain == 'TERCEIRO':
            domain_counts['other'] += 1
        else:
            domain_counts['no_domain'] += 1

    # Status counts (todos são ativos no license_decision_plan)
    status_counts = Counter()
    status_counts['ACTIVE'] = len(users)

    return {
        "total_registrations": len(users),
        "total_unique_users": len(users),
        "total_active_unique": len(users),
        "in_scope_total_unique": domain_counts.get('foresea', 0) + domain_counts.get('foresea_partner', 0),
        "in_scope_active_unique": domain_counts.get('foresea', 0) + domain_counts.get('foresea_partner', 0),
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