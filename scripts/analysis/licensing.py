# -*- coding: utf-8 -*-

"""
Módulo do Motor de Licenciamento

Responsável por atribuir o modelo de licença (Authorized/Concurrent)
e calcular o custo final em AppPoints.
"""

from ..config import get_app_points_config

def assign_license_model(usage_profile, operational_presence):
    """
    Atribui o modelo de licença (Authorized ou Concurrent) com base no perfil do usuário.

    A regra de negócio é:
    - Usuários 'POWER' que são 'ONSHORE' são candidatos a 'AUTHORIZED'.
    - Todos os outros são 'CONCURRENT'.

    Args:
        usage_profile (str): O perfil de uso ('POWER', 'MEDIUM', 'LIGHT').
        operational_presence (str): A presença operacional ('ONSHORE', 'OFFSHORE').

    Returns:
        str: O modelo de licença ('AUTHORIZED' ou 'CONCURRENT').
    """
    if usage_profile == "POWER" and operational_presence == "ONSHORE":
        return "AUTHORIZED"
    
    return "CONCURRENT"

def calculate_app_points(entitlement, license_model):
    """
    Calcula o custo em AppPoints com base no entitlement e no modelo de licença.

    Args:
        entitlement (str): O nível de licença ('PREMIUM', 'BASE', etc.).
        license_model (str): O modelo de licença ('AUTHORIZED', 'CONCURRENT').

    Returns:
        int: O custo em AppPoints.
    """
    config = get_app_points_config()
    return config.get(entitlement, {}).get(license_model, 0)
