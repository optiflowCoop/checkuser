# -*- coding: utf-8 -*-

"""
Módulo de Classificação de Perfis de Usuário

Responsável por aplicar regras de negócio para categorizar usuários
com base em seus atributos, como grupos de segurança e PersonGroups.
"""

from ..config import get_usage_profile_thresholds, get_operational_presence_keywords

def classify_usage_profile(group_count):
    """
    Classifica o perfil de uso (POWER, MEDIUM, LIGHT) com base na contagem de grupos.
    
    Args:
        group_count (int): O número de grupos de segurança aos quais um usuário pertence.
        
    Returns:
        str: A classificação do perfil ('POWER', 'MEDIUM', ou 'LIGHT').
    """
    thresholds = get_usage_profile_thresholds()
    if group_count > thresholds['POWER']:
        return "POWER"
    elif group_count > thresholds['MEDIUM']:
        return "MEDIUM"
    else:
        return "LIGHT"

def classify_operational_presence(person_groups):
    """
    Classifica a presença operacional do usuário (OFFSHORE ou ONSHORE).
    
    Args:
        person_groups (set): Um conjunto de strings contendo os PersonGroups do usuário.
        
    Returns:
        str: A classificação da presença ('OFFSHORE' ou 'ONSHORE').
    """
    keywords = get_operational_presence_keywords()
    for pg in person_groups:
        if any(keyword in pg.lower() for keyword in keywords):
            return "OFFSHORE"
    return "ONSHORE"
