# scripts/local_server/bat_runner.py
"""Execução dos .bat. Única responsabilidade: abrir o script numa nova
janela de terminal visível, para o usuário acompanhar o progresso — o
mesmo comportamento de dar duplo-clique manualmente no arquivo."""
import subprocess
from pathlib import Path


def run_bat(bat_path: Path) -> None:
    subprocess.Popen(
        ['cmd', '/c', str(bat_path)],
        cwd=str(bat_path.parent),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
