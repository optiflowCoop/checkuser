"""scripts/domain/env_normalizer.py

Utilitário compartilhado para normalizar nomes de ambientes do Maximo.
Mapeia NORBE06 -> N06, NORBE08 -> N08, NORBE09 -> N09, etc.
Isso garante consistência em todas as abas do relatório.
"""


# Mapeamento de normalização de ambientes
ENV_MAPPING = {
    'NORBE06': 'N06',
    'NORBE08': 'N08',
    'NORBE09': 'N09',
    'BASE-UNP': 'BASE',
    'OP-BASE': 'BASE',
    'ODRL-SP': 'BASE',
}


def normalize_env(env):
    """Normaliza nome de ambiente para o padrão curto (N06, N08, N09, etc.)."""
    if not env:
        return env
    e = env.upper().strip()
    return ENV_MAPPING.get(e, e)


def normalize_env_list(envs):
    """Normaliza uma lista/set de ambientes."""
    if isinstance(envs, str):
        return ' | '.join(sorted({normalize_env(e.strip()) for e in envs.split('|') if e.strip()}))
    elif isinstance(envs, (set, list)):
        return sorted({normalize_env(e) for e in envs if e})
    return envs