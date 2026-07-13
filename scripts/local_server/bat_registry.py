# scripts/local_server/bat_registry.py
"""Registro dos scripts .bat disponíveis para disparo via o painel do
dashboard. Única responsabilidade deste módulo: saber QUAIS .bat existem e
como descrevê-los — não executa nada (isso é bat_runner.py) e não entende
HTTP (isso é http_server.py).
"""
from pathlib import Path

# Metadados conhecidos por nome de arquivo. Um .bat que apareça em bat/ sem
# entrada aqui ainda é listado (com rótulo genérico) em list_available_bats —
# evita que um novo script fique invisível até alguém lembrar de editar isto.
BAT_METADATA = {
    'extrair_logintrack.bat': {
        'label': 'Extrair Logintracking',
        'description': '7 extrações (logintracking x 7 ambientes). Mais rápido — use quando só precisa atualizar login/acesso.',
        'group': 'Extração',
    },
    'extrair_baseline.bat': {
        'label': 'Extrair Baseline Funcional',
        'description': '21 extrações (persongroupview, persongroup, persongroupteam x 7 ambientes).',
        'group': 'Extração',
    },
    'extrair_tudo.bat': {
        'label': 'Extrair TUDO do DB2',
        'description': '98 extrações (14 queries x 7 ambientes). Extração completa — mais lenta.',
        'group': 'Extração',
    },
    'extrair_seguranca.bat': {
        'label': 'Extrair Segurança (Grupos x Permissões)',
        'description': '7 extrações (applicationauth x 7 ambientes) — dados para a auditoria de emissor/aprovador.',
        'group': 'Extração',
    },
    'run_db2cli_all.bat': {
        'label': 'Validar Conexões DB2',
        'description': 'Testa a conectividade com os 7 ambientes, sem extrair dados.',
        'group': 'Diagnóstico',
    },
    'processar_pipeline.bat': {
        'label': 'Rodar Pipeline Completo',
        'description': 'Executa as 13 etapas: extração, consolidação, análises e relatório final.',
        'group': 'Pipeline',
    },
    'gerar_relatorio.bat': {
        'label': 'Regenerar Relatório (HTML + Excel)',
        'description': 'Reprocessa os dados já extraídos e gera o dashboard e o workbook novamente.',
        'group': 'Pipeline',
    },
}


def list_available_bats(bat_dir: Path):
    """Lista os .bat presentes em bat_dir, enriquecidos com metadados quando
    conhecidos."""
    if not bat_dir.exists():
        return []
    bats = []
    for path in sorted(bat_dir.glob('*.bat')):
        meta = BAT_METADATA.get(path.name, {})
        bats.append({
            'name': path.name,
            'label': meta.get('label', path.stem.replace('_', ' ').title()),
            'description': meta.get('description', ''),
            'group': meta.get('group', 'Outros'),
        })
    return bats


def resolve_bat_path(bat_dir: Path, name: str):
    """Resolve um nome de .bat pedido pelo cliente para um Path real,
    validando contra os arquivos de fato presentes em bat_dir. Nunca aceita o
    nome vindo do cliente como caminho — evita path traversal/injeção."""
    available = {b['name'] for b in list_available_bats(bat_dir)}
    if name not in available:
        return None
    return bat_dir / name
