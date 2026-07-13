# scripts/local_server/http_server.py
"""Camada HTTP. Única responsabilidade: traduzir requisições em chamadas
para bat_registry (metadados) e bat_runner (execução) — não conhece os
.bat em si nem como eles são disparados."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .bat_registry import list_available_bats, resolve_bat_path
from .bat_runner import run_bat


def make_handler(bat_dir: Path, dashboard_html_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload, status=200):
            body = json.dumps(payload).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path in ('/', '/dashboard'):
                self._serve_dashboard()
            elif parsed.path == '/api/list-bats':
                self._send_json({'bats': list_available_bats(bat_dir)})
            elif parsed.path == '/api/run-bat':
                self._handle_run_bat(parse_qs(parsed.query))
            else:
                self.send_error(404, 'Not found')

        def _serve_dashboard(self):
            if not dashboard_html_path.exists():
                self.send_error(404, 'Dashboard ainda não foi gerado — rode gerar_relatorio.bat primeiro.')
                return
            body = dashboard_html_path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _handle_run_bat(self, query):
            name = (query.get('name') or [''])[0]
            bat_path = resolve_bat_path(bat_dir, name)
            if not bat_path:
                self._send_json({'ok': False, 'error': f"'{name}' não é um script conhecido em bat/."}, status=400)
                return
            run_bat(bat_path)
            self._send_json({'ok': True, 'message': f'{name} iniciado — acompanhe na nova janela do terminal.'})

        def log_message(self, format, *args):
            pass  # silencia o log de acesso padrão no console

    return Handler


def serve(bat_dir: Path, dashboard_html_path: Path, host='127.0.0.1', port=8765):
    handler = make_handler(bat_dir, dashboard_html_path)
    server = ThreadingHTTPServer((host, port), handler)
    print(f'Servidor local do dashboard rodando em http://{host}:{port}/')
    print('Deixe esta janela aberta enquanto usa os botões de extração no dashboard.')
    server.serve_forever()
