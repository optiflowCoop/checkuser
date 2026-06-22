# config.py
def get_app_points_config():
    return {
        'SELF FREE': {'CONCURRENT': 0, 'AUTHORIZED': 0},
        'LIMITED': {'CONCURRENT': 5, 'AUTHORIZED': 2},
        'BASE': {'CONCURRENT': 10, 'AUTHORIZED': 2},
        'PREMIUM': {'CONCURRENT': 15, 'AUTHORIZED': 5},
    }

def get_entitlement_keywords():
    return {
        'PREMIUM': ['O&G', 'HSE', 'DRILLING', 'OIL'],
        'BASE': ['WOTRACK', 'ASSET', 'SCHEDULER', 'PLANNING', 'JOBPLAN'],
        'LIMITED': ['INVENTORY', 'PO', 'RECEIVING', 'SR', 'REQUEST'],
    }

def get_critical_titles():
    return ['ALMOXARIFE', 'SUPERVISOR', 'COORDENADOR', 'GERENTE', 'LIDER', 'ENCARREGADO']

def get_foresea_domains():
    return ['foresea.com', 'foresea-partner.com']
