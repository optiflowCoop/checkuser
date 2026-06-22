# -*- coding: utf-8 -*-

"""
Módulo de Geração de Relatório HTML

Responsável por construir o dashboard HTML com os resultados da análise.
"""

from datetime import datetime

def fmt_br(num):
    """Formata um número para o padrão brasileiro."""
    return f"{num:,}".replace(",", ".")

def render_table(headers, rows, table_id="", extra_class=""):
    """Renderiza uma tabela HTML a partir de uma lista de cabeçalhos e linhas."""
    html = f'<div class="table-responsive"><table id="{table_id}" class="{extra_class}">\n'
    html += '  <thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead>\n'
    html += '  <tbody>\n'
    for row in rows:
        html += '    <tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>\n'
    html += '  </tbody>\n'
    html += '</table></div>\n'
    return html

def build_html_report(summary_data, simulation_data):
    """
    Constrói o conteúdo completo do arquivo HTML.

    Args:
        summary_data (dict): Um dicionário com as métricas executivas.
        simulation_data (list): Uma lista de dicionários, onde cada um representa
                                um usuário na simulação de AppPoints.

    Returns:
        str: A string completa do conteúdo HTML.
    """
    
    # --- Extrair dados para os cards ---
    unique_active_logins = summary_data.get('unique_active_logins', 0)
    active_records = summary_data.get('active_records', 0)
    total_reused_active = summary_data.get('total_reused_active', 0)
    critical_diff_active = summary_data.get('critical_diff_active', 0)
    
    total_authorized_points = summary_data.get('total_authorized_points', 0)
    authorized_users = summary_data.get('authorized_users', 0)
    total_concurrent_points = summary_data.get('total_concurrent_points', 0)
    concurrent_users = summary_data.get('concurrent_users', 0)
    
    # --- Início do Documento HTML ---
    html = [
        '<!DOCTYPE html>',
        '<html lang="pt-BR">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<title>Maximo MAS 9 - Análise de AppPoints</title>',
        '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
        '<style>',
        ':root { --primary: #0f172a; --secondary: #1e293b; --accent: #2563eb; --bg: #f8fafc; --card-bg: #ffffff; --text: #334155; --border: #e2e8f0; --danger: #ef4444; --warning: #f59e0b; --success: #10b981;}',
        'body { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; margin: 0; background-color: var(--bg); color: var(--text); line-height: 1.5; }',
        '.topbar { background: var(--primary); color: white; padding: 1.5rem 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center;}',
        '.topbar h1 { margin: 0; font-size: 1.8rem; font-weight: 600; }',
        '.topbar p { margin: 0; color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem; }',
        '.container { max-width: 1600px; margin: 0 auto; padding: 2rem; }',
        '.card { background: var(--card-bg); border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid var(--border); padding: 1.8rem; margin-bottom: 2rem; }',
        '.card-header { margin-top: 0; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border); padding-bottom: 0.75rem; font-size: 1.4rem; font-weight: 600; }',
        '.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; }',
        '.stat-card { background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; text-align: center; }',
        '.stat-value { font-size: 2.2rem; font-weight: 700; color: var(--primary); margin-bottom: 0.2rem; }',
        '.stat-title { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; margin-bottom: 0.5rem; }',
        '.stat-subtitle { font-size: 0.75rem; color: #64748b; }',
        '.border-danger { border-bottom: 4px solid var(--danger); }',
        '.border-warning { border-bottom: 4px solid var(--warning); }',
        '.border-accent { border-bottom: 4px solid var(--accent); }',
        '.border-success { border-bottom: 4px solid var(--success); }',
        '.table-responsive { overflow-x: auto; border-radius: 8px; border: 1px solid var(--border); max-height: 600px; overflow-y: auto; }',
        'table { width: 100%; border-collapse: collapse; } th, td { padding: 14px 16px; border-bottom: 1px solid var(--border); text-align: left; white-space: nowrap; } th { background-color: #f1f5f9; font-weight: 600; position: sticky; top: 0; }',
        '</style>',
        '</head>',
        '<body>',
        '<div class="topbar">',
        '<div><h1>Dashboard de Análise de AppPoints</h1><p>Fase 4: Análise de Entitlement e Otimização de Licenciamento</p></div>',
        f'<div><p style="text-align: right; color: #cbd5e1;">Atualizado em:<br><strong>{datetime.now().strftime("%d/%m/%Y %H:%M")}</strong></p></div>',
        '</div>',
        '<div class="container">',
    ]
    
    # --- Bloco 1: Resumo de Identidades ---
    html.append('<div class="card"><h2 class="card-header">1. Resumo Executivo de Identidades</h2><div class="stats-grid">')
    html.append(f'<div class="stat-card border-success"><div class="stat-value" style="color: var(--success);">{fmt_br(unique_active_logins)}</div><div class="stat-title">Pessoas Únicas (Ativas)</div><div class="stat-subtitle">Base para licenciamento</div></div>')
    html.append(f'<div class="stat-card border-accent"><div class="stat-value">{fmt_br(active_records)}</div><div class="stat-title">Registros Ativos</div><div class="stat-subtitle">Contas logáveis no sistema</div></div>')
    html.append(f'<div class="stat-card border-warning"><div class="stat-value" style="color: var(--warning);">{fmt_br(total_reused_active)}</div><div class="stat-title">Riscos de Reuso</div><div class="stat-subtitle">Logins repetidos entre bases</div></div>')
    html.append(f'<div class="stat-card border-danger"><div class="stat-value" style="color: var(--danger);">{fmt_br(critical_diff_active)}</div><div class="stat-title">Colisões Críticas</div><div class="stat-subtitle">Mesmo login, pessoas diferentes</div></div>')
    html.append('</div></div>')

    # --- Bloco 2: Simulação de AppPoints ---
    html.append('<div class="card"><h2 class="card-header">2. 💰 Simulação de AppPoints (Baseado em Entitlement)</h2>')
    html.append('<div class="stats-grid">')
    html.append(f'<div class="stat-card border-accent"><div class="stat-value">{fmt_br(total_authorized_points)}</div><div class="stat-title">Total AppPoints (Authorized)</div><div class="stat-subtitle">{fmt_br(authorized_users)} usuários</div></div>')
    html.append(f'<div class="stat-card border-success"><div class="stat-value">{fmt_br(total_concurrent_points)}</div><div class="stat-title">Total AppPoints (Concurrent Pool)</div><div class="stat-subtitle">{fmt_br(concurrent_users)} usuários</div></div>')
    html.append(f'<div class="stat-card border-warning"><div class="stat-value">{fmt_br(int(total_concurrent_points * 0.3))}</div><div class="stat-title">Estimativa Concorrência (30%)</div><div class="stat-subtitle">Simulação de pico de uso</div></div>')
    html.append(f'<div class="stat-card border-danger"><div class="stat-value">{fmt_br(total_authorized_points + int(total_concurrent_points * 0.3))}</div><div class="stat-title">Custo Total Estimado</div><div class="stat-subtitle">Authorized + Pico Concurrent</div></div>')
    html.append('</div>')
    
    html.append('<h3 style="margin-top: 2rem; border-top: 1px solid var(--border); padding-top: 1.5rem;">Detalhamento por Usuário (Top 500 por custo)</h3>')
    app_points_rows = []
    # Ordena os dados pela pontuação para mostrar os mais caros primeiro
    for entry in sorted(simulation_data, key=lambda x: x['APP_POINTS'], reverse=True):
        app_points_rows.append([
            entry['USERID'],
            entry['DISPLAYNAME'],
            entry['ENTITLEMENT'],
            entry['OPERATIONAL_PRESENCE'],
            entry['LICENSE_MODEL'],
            entry['APP_POINTS'],
            entry['USAGE_PROFILE'],
            entry['GROUP_COUNT'],
            entry['APPS_COUNT'],
        ])
    
    headers = ['USERID', 'Nome', 'Entitlement', 'Presença', 'Licença', 'AppPoints', 'Perfil de Uso', 'Grupos', 'Aplicações']
    html.append(render_table(headers, app_points_rows[:500], "appPointsTable"))
    html.append('</div>')

    # --- Fim do Documento HTML ---
    html.append('</div></body></html>')
    return '\n'.join(html)
