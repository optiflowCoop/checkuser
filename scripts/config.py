# config.py
# CANONICAL AppPoints Configuration - Single Source of Truth
# Based on IBM Maximo 9.1 licensing model for Foresea
def get_app_points_config():
    """
    Returns the canonical AppPoints cost table.
    
    CRITICAL: These values directly impact capacity planning and cost calculations.
    Any changes must be validated against documentation and contract terms.
    
    Reference: docs/SISTEMA_DOCUMENTACAO.md, Section 4.2
    """
    return {
        'SELF FREE': {'CONCURRENT': 0, 'AUTHORIZED': 0},
        'LIMITED': {'CONCURRENT': 5, 'AUTHORIZED': 2},
        'BASE': {'CONCURRENT': 10, 'AUTHORIZED': 3},  # FIX: Was 2, canonical is 3
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

def get_og_group_keywords():
    """
    Security group name patterns that indicate O&G access requiring PREMIUM licensing.
    Must be aligned with config/licensing_rules.json user_classification.og_group_keywords.
    """
    return [
        'OG_', 'OOG_', 'OOG_PTW_ISSUER', 'O&G', 'OILGAS', 'PETROLEUM', 'PETRO',
        'HSE', 'DRILLING', 'DRILL', 'RIG', 'FPSO', 'PFWORK', 'LOCREC',
        'COMPLIANCE', 'WELL'
    ]
