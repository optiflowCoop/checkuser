# scripts/local_dashboard_server.py (Entry point)
"""Sobe um servidor local que serve o dashboard e permite disparar os .bat
de extração diretamente pelo ícone de engrenagem no HTML — o navegador não
pode executar arquivos locais por conta própria, então este servidor faz a
ponte entre o clique do botão e o processo real.
"""
import sys
import threading
import time
import webbrowser
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_server.http_server import serve

BAT_DIR = ROOT / 'bat'
DASHBOARD_HTML = ROOT / 'output' / 'reports' / 'maximo_unified_dashboard.html'
PORT = 8765


def main():
    server_thread = threading.Thread(
        target=serve, args=(BAT_DIR, DASHBOARD_HTML), kwargs={'port': PORT}, daemon=True,
    )
    server_thread.start()
    time.sleep(0.5)  # dá tempo do bind do socket antes de abrir o navegador
    webbrowser.open(f'http://127.0.0.1:{PORT}/')
    server_thread.join()


if __name__ == '__main__':
    main()
