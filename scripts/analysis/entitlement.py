# analysis/entitlement.py
from scripts.config import get_app_points_config, get_entitlement_keywords

def determine_user_entitlement(user_groups):
    """
    Determina o entitlement (nível de licença) com base na regra do "nível mais alto",
    verificando palavras-chave em cada nome de grupo.
    """
    keywords = get_entitlement_keywords()
    
    # A ordem de verificação é crucial: do mais caro para o mais barato.
    for group in user_groups:
        group_upper = group.upper()
        if any(keyword in group_upper for keyword in keywords['PREMIUM']):
            return 'PREMIUM'
    
    for group in user_groups:
        group_upper = group.upper()
        if any(keyword in group_upper for keyword in keywords['BASE']):
            return 'BASE'

    for group in user_groups:
        group_upper = group.upper()
        if any(keyword in group_upper for keyword in keywords['LIMITED']):
            return 'LIMITED'
            
    return 'SELF FREE'

def calculate_app_points(entitlement, license_model):
    """
    Calcula o custo em AppPoints com base no entitlement e no modelo de licença.
    """
    config = get_app_points_config()
    return config.get(entitlement, {}).get(license_model, 0)
