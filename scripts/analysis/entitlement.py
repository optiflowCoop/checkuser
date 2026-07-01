# analysis/entitlement.py
# CANONICAL MODULE: Entitlement determination and AppPoints calculation
# Single source of truth for cost calculations
from scripts.config import get_app_points_config, get_entitlement_keywords

def determine_user_entitlement(user_groups):
    """
    CANONICAL: Determina o entitlement (nível de licença) com base na regra do "nível mais alto".
    
    Esta função verifica palavras-chave em cada nome de grupo de segurança
    e retorna o nível de licença mais alto detectado.
    
    A ordem de verificação é crucial: do mais caro para o mais barato.
    
    Args:
        user_groups: Lista de nomes de grupos de segurança do usuário
        
    Returns:
        'PREMIUM', 'BASE', 'LIMITED', ou 'SELF FREE'
        
    Reference: docs/SISTEMA_DOCUMENTACAO.md, Section 4.2
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
    CANONICAL: Calcula o custo em AppPoints com base no entitlement e no modelo de licença.
    
    Esta é a ÚNICA função que deve calcular AppPoints no sistema.
    Qualquer mudança aqui afeta todos os cálculos de capacidade e otimização.
    
    Args:
        entitlement: 'PREMIUM', 'BASE', 'LIMITED', ou 'SELF FREE'
        license_model: 'AUTHORIZED' ou 'CONCURRENT'
        
    Returns:
        int: Custo em AppPoints conforme tabela canônica
        
    Reference: docs/SISTEMA_DOCUMENTACAO.md, Section 4.2
    Canonical values defined in: scripts/config.py → get_app_points_config()
    """
    config = get_app_points_config()
    return config.get(entitlement, {}).get(license_model, 0)
