# -*- coding: utf-8 -*-

"""
Módulo de Configuração

Centraliza todas as regras de negócio, mapeamentos e configurações
para a análise de AppPoints do Maximo.
"""

def get_app_points_config():
    """
    Retorna a matriz de custo de AppPoints por tipo de licença.
    Estes são os valores oficiais para cálculo.
    """
    return {
        'SELF FREE': {'CONCURRENT': 0, 'AUTHORIZED': 0},
        'LIMITED': {'CONCURRENT': 5, 'AUTHORIZED': 2},
        'BASE': {'CONCURRENT': 10, 'AUTHORIZED': 2},
        'PREMIUM': {'CONCURRENT': 15, 'AUTHORIZED': 5},
    }

def get_entitlement_app_map():
    """
    Mapeia nomes de aplicações (ou parte deles) para o nível de entitlement.
    A lógica de análise sempre usará o nível mais alto encontrado.
    
    Esta configuração é crucial e deve ser alimentada com os dados
    da tabela APPLICATIONAUTH do Maximo.
    """
    return {
        'PREMIUM': [
            'WOTRACK_O&G', 'ASSET_O&G', 'DRILLING', 'HSE', 'OIL', 
            # Adicionar outros apps O&G ou Premium aqui
        ],
        'BASE': [
            'WOTRACK', 'ASSET', 'SCHEDULER', 'PLANNING', 'JOBPLAN',
            # Adicionar outros apps de nível Base aqui
        ],
        'LIMITED': [
            'INVENTORY', 'PO', 'RECEIVING', 'SR', 'REQUEST',
            # Adicionar outros apps de nível Limited aqui
        ],
    }

def get_operational_presence_keywords():
    """
    Retorna as palavras-chave para identificar um usuário como 'OFFSHORE'.
    """
    return ['offshore', 'platform', 'sonda', 'rig', 'fpso']

def get_usage_profile_thresholds():
    """
    Retorna os limites (número de grupos) para classificar o perfil de uso.
    """
    return {
        'POWER': 8,
        'MEDIUM': 4,
    }
