# -*- coding: utf-8 -*-

"""
Módulo do Motor de Entitlement

Responsável por determinar o nível de licença requerido por um usuário
com base nas aplicações que ele tem permissão para acessar.
"""

from ..config import get_entitlement_app_map

def determine_user_entitlement(user_apps):
    """
    Determina o entitlement (nível de licença) com base na regra do "nível mais alto".

    Args:
        user_apps (set): Um conjunto de strings com os nomes das aplicações
                         que o usuário pode acessar.

    Returns:
        str: O nível de entitlement requerido ('PREMIUM', 'BASE', 'LIMITED', 'SELF FREE').
    """
    app_map = get_entitlement_app_map()

    # A ordem de verificação é crucial: do mais caro para o mais barato.
    if any(app in user_apps for app in app_map['PREMIUM']):
        return 'PREMIUM'
    
    if any(app in user_apps for app in app_map['BASE']):
        return 'BASE'
    
    if any(app in user_apps for app in app_map['LIMITED']):
        return 'LIMITED'
    
    return 'SELF FREE'
