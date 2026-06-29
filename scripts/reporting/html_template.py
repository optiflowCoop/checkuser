# scripts/reporting/html_template.py
from datetime import datetime
import json

try:
    from .html_helpers import fmt_br, render_table
except ImportError:
    from html_helpers import fmt_br, render_table


# --- Private Component Functions ---

def _render_styles():
    """Returns the CSS styles for the report."""
    return """
    <style>
        :root { --primary: #0f172a; --secondary: #1e293b; --accent: #2563eb; --bg: #f8fafc; --card-bg: #ffffff; --text: #334155; --border: #e2e8f0; --danger: #ef4444; --warning: #f59e0b; --success: #10b981; --neutral:#64748b}
        * { box-sizing: border-box; }
        body { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; margin: 0; background-color: var(--bg); color: var(--text); line-height: 1.5; }
        .topbar { background: var(--primary); color: white; padding: 1.5rem 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center;}
        .topbar h1 { margin: 0; font-size: 1.8rem; font-weight: 600; letter-spacing: -0.5px; }
        .topbar p { margin: 0; color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem; }
        .tabs { background: var(--secondary); padding: 0 2rem; display: flex; gap: 1rem; overflow-x: auto; white-space: nowrap;}
        .tab-button { background: none; border: none; color: #cbd5e1; padding: 1rem 1.5rem; cursor: pointer; font-size: 1rem; border-bottom: 3px solid transparent; font-weight: 600; transition: all 0.2s;}
        .tab-button:hover { color: white; }
        .tab-button.active { color: white; border-bottom-color: var(--accent); }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .alert-box { background-color: #eff6ff; border-left: 4px solid var(--accent); padding: 1rem 1.5rem; border-radius: 6px; margin-bottom: 2rem; display: flex; flex-direction: column; gap: 0.5rem; }
        .alert-box strong { color: #1e3a8a; font-size: 1.1rem; }
        .alert-box p { margin: 0; color: #1e40af; }
        .card { background: var(--card-bg); border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid var(--border); padding: 1.8rem; margin-bottom: 2rem; }
        .card-header { margin-top: 0; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border); padding-bottom: 0.75rem; color: var(--secondary); font-size: 1.4rem; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; }
        .stat-card { background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; text-align: center; transition: transform 0.2s; position: relative; }
        .stat-value { font-size: 2.2rem; font-weight: 700; color: var(--primary); margin-bottom: 0.2rem; }
        .stat-title { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #1e293b; font-weight: 700; margin-bottom: 0.5rem; }
        .stat-subtitle { font-size: 0.75rem; color: #64748b; line-height: 1.2; }
        .border-danger { border-bottom: 4px solid var(--danger); }
        .border-warning { border-bottom: 4px solid var(--warning); }
        .border-accent { border-bottom: 4px solid var(--accent); }
        .border-success { border-bottom: 4px solid var(--success); }
        .border-neutral { border-bottom: 4px solid var(--neutral); }
        .charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 2rem; margin-top: 2rem; }
        .chart-box { height: 320px; display: flex; justify-content: center; align-items: center; background: #ffffff; border-radius: 8px; border: 1px solid var(--border); padding: 1rem; }
        .table-responsive { overflow-x: auto; border-radius: 8px; border: 1px solid var(--border); max-height: 500px; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th, td { padding: 14px 16px; border-bottom: 1px solid var(--border); vertical-align: top; font-size: 0.9rem; }
        th { background-color: #f1f5f9; color: #334155; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; position: sticky; top: 0; z-index: 10; }
        tbody tr:hover { background-color: #f8fafc; }
        .badge { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: inline-block; text-align: center; color: white; }
        .badge-critical { background-color: var(--danger); }
        .badge-high { background-color: var(--warning); }
        .badge-medium { background-color: var(--accent); }
        .badge-success { background-color: var(--success); }
        .badge-neutral { background-color: var(--neutral); }
        .search-container { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #f1f5f9; padding: 1.5rem; border-radius: 8px; align-items: center; }
        .search-bar { flex-grow: 1; padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; min-width: 250px; }
        .filter-select { padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; background: white; min-width: 180px; }
        .btn-export { background-color: #10b981; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-size: 0.95rem; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        .btn-export:hover { background-color: #059669; }
        .type-analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }
        .type-card { background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; }
        .type-card h4 { margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
        .env-divergence { margin-bottom: 0.8rem; padding: 0.8rem; background: #f8fafc; border-left: 3px solid var(--warning); border-radius: 4px; }
        .env-header { font-weight: 700; color: var(--primary); margin-bottom: 0.4rem; font-size: 0.9rem; }
        .preset-btn-group { display: flex; flex-direction: column; }
        .preset-btn { background: white; border: 1px solid var(--border); padding: 8px 16px; border-radius: 6px; font-size: 0.9rem; font-weight: 600; cursor: pointer; color: var(--secondary); transition: all 0.2s; text-align: left; }
        .preset-btn:hover { background: #f1f5f9; }
        .preset-btn.active { background: var(--accent); color: white; border-color: var(--accent); }
        .preset-btn p { margin: 2px 0 0 0; font-size: 0.8rem; font-weight: normal; opacity: 0.8; }
        .calc-input-group { margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed var(--border); padding-bottom: 0.5rem; }
        .calc-input-group label { font-weight: 600; color: var(--text); font-size: 0.95rem; }
        .calc-input-group input { width: 100px; padding: 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 1.1rem; text-align: center; color: var(--primary); font-weight: bold; }
        .calc-badge-pts { font-size: 0.75rem; background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; margin-left: 8px; }
        .legend-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
        .legend-box { background: #f8fafc; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); }
        .legend-box h3 { margin-top: 0; color: var(--primary); font-size: 1.05rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; margin-bottom: 1rem; }
        .legend-list { padding-left: 1.2rem; margin-bottom: 0; font-size: 0.88rem; color: var(--text); }
        .legend-list li { margin-bottom: 0.6rem; }
        .event-card { background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid var(--warning); padding: 1.2rem; border-radius: 8px; margin-bottom: 1rem; cursor: pointer; transition: background 0.2s; }
        .event-card:hover { background: #fef08a; }
        .event-card h4 { margin: 0 0 0.4rem 0; color: #92400e; font-size: 1.1rem; }
        .event-card p { margin: 0; font-size: 0.85rem; color: #b45309; }
    </style>
    """


def _render_header_and_tabs():
    """Returns the top bar and tab buttons."""
    return f"""
    <div class="topbar">
        <div>
            <h1>Dashboard Gerencial MAS 9.1 | Foresea</h1>
            <p>Capacity Planning Avançado e Saneamento de Identidades</p>
        </div>
        <div>
            <p style="text-align: right; color: #cbd5e1;">Gerado em:<br><strong>{datetime.now().strftime("%d/%m/%Y %H:%M")}</strong></p>
        </div>
    </div>
    <div class="tabs">
        <button class="tab-button active" onclick="openTab(event, 'tab-painel')">1. Painel Operacional</button>
        <button class="tab-button" onclick="openTab(event, 'tab-gov')">2. Governança & Saneamento</button>
        <button class="tab-button" onclick="openTab(event, 'tab-apppoints')" style="color:#60a5fa;">3. Cenários de AppPoints</button>
        <button class="tab-button" onclick="openTab(event, 'tab-eventos')" style="color:var(--warning);">4. Eventos Críticos</button>
        <button class="tab-button" onclick="openTab(event, 'tab-tabela')">5. Plano de Ação</button>
        <button class="tab-button" onclick="openTab(event, 'tab-peak')" style="color:#7c3aed;">6. Peak Contributors</button>
    </div>
    """


# ==========================================================
# ABA 1 – Painel Operacional (VERSÃO FINAL CORRIGIDA)
# ==========================================================

def _render_tab_painel(analytics, identity_analytics):

    painel = analytics.get('painel_data', {})

    return f"""
<div id="tab-painel" class="container tab-content active">

<div class="card">
<h2 class="card-header">📊 Visão Executiva (Alinhado ao Excel)</h2>

<div class="stats-grid">

<div class="stat-card border-success">
<div class="stat-value" style="color: var(--success);">
{fmt_br(painel.get('usuarios_ativos', 0))}
</div>
<div class="stat-title">Usuários Ativos Analisados</div>
</div>

<div class="stat-card border-primary">
<div class="stat-value">
{fmt_br(painel.get('usuarios_plano', 0))}
</div>
<div class="stat-title">Usuários no Plano de Licença</div>
</div>

<div class="stat-card border-warning">
<div class="stat-value">
{fmt_br(painel.get('authorized', 0))}
</div>
<div class="stat-title">Authorized</div>
</div>

<div class="stat-card border-accent">
<div class="stat-value">
{fmt_br(painel.get('concurrent', 0))}
</div>
<div class="stat-title">Concurrent</div>
</div>

<div class="stat-card border-secondary">
<div class="stat-value">
{fmt_br(painel.get('premium', 0))}
</div>
<div class="stat-title">Premium</div>
</div>

</div>
</div>

<div class="card" style="border-left: 4px solid var(--danger);">
<h2 class="card-header">⚡ Capacidade NEM vs Contrato</h2>

<div class="stats-grid">

<div class="stat-card">
<div class="stat-value" style="color: var(--danger);">
{fmt_br(painel.get('true_peak', 0))}
</div>
<div class="stat-title">Pico Real (P100)</div>
</div>

<div class="stat-card">
<div class="stat-value" style="color: var(--warning);">
{fmt_br(painel.get('p95', 0))}
</div>
<div class="stat-title">Pico Seguro (P95)</div>
</div>

<div class="stat-card">
<div class="stat-value">
{fmt_br(painel.get('contratado', 0))}
</div>
<div class="stat-title">Capacidade Contratada</div>
</div>

<div class="stat-card">
<div class="stat-value" style="color: {'var(--success)' if painel.get('folga', 0) >= 0 else 'var(--danger)'};">
{fmt_br(painel.get('folga', 0))}
</div>
<div class="stat-title">Folga / Déficit</div>
</div>

<div class="stat-card">
<div class="stat-value">
{painel.get('percentual_uso', 0)}%
</div>
<div class="stat-title">% Uso do Contrato (P95)</div>
</div>

</div>
</div>

</div>
"""

def _render_tab_gov(gov_tables):
    """Renders the 'Governança & Saneamento' tab content."""
    return f"""
    <div id="tab-gov" class="container tab-content">
        <div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">
            <h3 style="margin-top: 0; color: var(--primary);">🔍 Filtro Interativo de Risco Lógico</h3>
            <div class="search-container">
                <input type="text" id="searchGov" class="search-bar" onkeyup="filterGovTable()" placeholder="Pesquisar por ID, Nome, Email...">
                <select id="selGovDec" class="filter-select" onchange="filterGovTable()">
                    <option value="">⚖️ Todas as Decisões</option>
                    <option value="PESSOAS DIFERENTES">🔴 ALTO - PESSOAS DIFERENTES</option>
                    <option value="REQUER REVISÃO">🟡 MÉDIO - REQUER REVISÃO</option>
                    <option value="POSSÍVEL MESMA PESSOA">🟢 BAIXO - POSSÍVEL MESMA PESSOA</option>
                </select>
            </div>
        </div>
        <div class="card">
            <h2 class="card-header">Top Divergências de Segurança (Matriz Base vs Sonda)</h2>
            <div class="type-analysis-grid">{gov_tables['title_divergence_html']}</div>
        </div>
        <div class="card">
            <h2 class="card-header">Conflitos de Multi-Ambiente (Cross-Env)</h2>
            {render_table(['USERID', 'Bases Encontradas', 'Nomes de Exibição', 'Conclusão'], gov_tables['cross_env_rows'], 'table-cross-env', 'gov-table')}
        </div>
        <div class="card">
            <h2 class="card-header">Colisões de Active Directory (LOGINID)</h2>
            {render_table(['LOGINID AD', 'Bases', 'USERIDs', 'Nomes Cadastrados'], gov_tables['login_conflicts_rows'], 'table-login-conflicts', 'gov-table')}
        </div>
        <div class="card">
            <div style="display:flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); margin-bottom: 1.5rem; padding-bottom: 0.75rem;">
                <h2 style="margin:0; color: var(--secondary); font-size: 1.4rem; font-weight: 600;">Fila de Resolução Consolidada</h2>
                <button class="btn-export" style="background-color: var(--secondary);" onclick="exportTableToCSV('table-worklist', 'Backlog_Governanca.csv')">Exportar Backlog</button>
            </div>
            {render_table(['ID Bruto', 'Nome', 'Hipótese Sistêmica', 'Decisão / Ação'], gov_tables['worklist_rows'], 'table-worklist', 'gov-table')}
        </div>
    </div>
    """


def _render_tab_apppoints(analytics):
    """Renders the 'Cenários de AppPoints' tab content."""
    return f"""
    <div id="tab-apppoints" class="container tab-content">
        <div class="card" style="border-left: 4px solid var(--success); background-image: linear-gradient(to right, #ffffff, #f8fafc);">
            <div class="card-header" style="border:none; margin-bottom:0.5rem;">
                <div>
                    <h2 style="margin:0; color:var(--success);">🧮 Simulador de Cenários de AppPoints</h2>
                    <p style="font-size: 0.9rem; color: #64748b; font-weight: normal; margin-top: 4px;">Selecione um cenário para ver o impacto no consumo de AppPoints ou edite os campos para uma simulação manual.</p>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem; align-items: start;">
                <div class="preset-btn-group">
                    <button class="preset-btn" id="btnAsIs" onclick="loadScenario('asis', this)">
                        <strong>1. Cenário Atual (As-Is)</strong>
                        <p>Simula o consumo se todos os usuários atuais fossem migrados sem nenhuma otimização.</p>
                    </button>
                    <button class="preset-btn" id="btnSaneado" onclick="loadScenario('saneado', this)">
                        <strong>2. Pós-Saneamento</strong>
                        <p>Simula o consumo após a desativação de usuários inativos (> 90 dias).</p>
                    </button>
                    <button class="preset-btn active" id="btnOtimizado" onclick="loadScenario('otimizado_p95', this)">
                        <strong>3. Otimizado (Pico P95)</strong>
                        <p>Aplica todas as otimizações (inativos, downgrades, concorrência) usando o fator de pico (P95).</p>
                    </button>
                    <button class="preset-btn" id="btnOtimizadoP50" onclick="loadScenario('otimizado_p50', this)">
                        <strong>4. Otimizado (Mediana P50)</strong>
                        <p>Aplica todas as otimizações usando o fator de uso mediano (P50) para um dia comum.</p>
                    </button>
                </div>
                <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                    <div style="flex: 2; min-width: 300px; background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border);">
                        <div class="calc-input-group"><label>Premium Auth <span class="calc-badge-pts">5 pts</span></label><input type="number" id="inpPremAuth" oninput="updateCalculator()"></div>
                        <div class="calc-input-group"><label>Premium Conc <span class="calc-badge-pts">15 pts</span></label><input type="number" id="inpPremConc" oninput="updateCalculator()"></div>
                        <div class="calc-input-group"><label>Base Auth <span class="calc-badge-pts">3 pts</span></label><input type="number" id="inpBaseAuth" oninput="updateCalculator()"></div>
                        <div class="calc-input-group" style="border:none; margin:0; padding:0;"><label>Base Conc <span class="calc-badge-pts">10 pts</span></label><input type="number" id="inpBaseConc" oninput="updateCalculator()"></div>
                    </div>
                    <div style="flex: 1; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                        <h3 style="margin: 0; font-size: 1rem; color: var(--secondary);">AppPoints Requeridos</h3>
                        <div id="calcTotalDisplay" style="font-size: 4.5rem; font-weight: 800; color: var(--success); line-height:1;">0</div>
                        <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #475569;">Soma bruta (XLSX): <strong id="rawSumDisplay">0</strong></div>
                        <div id="calcAlertBox" style="margin-top: 1rem; padding: 0.75rem; background: var(--danger); color:white; font-weight:bold; border-radius:6px; display:none; font-size:1.1rem;">⚠️ TETO EXCEDIDO</div>
                    </div>
                    <div style="flex: 2; min-width: 300px; height: 260px;"><canvas id="simChart"></canvas></div>
                </div>
            </div>
        </div>
        <div class="card" style="border-top: 4px solid var(--primary);">
            <h2 class="card-header" style="border:none; margin-bottom:0.5rem;">🧠 Quadro de Regras de Negócio O&G</h2>
            <div class="legend-grid">
                <div class="legend-box" style="border-left: 3px solid #1e3a8a;">
                    <h3>🔰 Entitlement (Módulos)</h3>
                    <ul class="legend-list">
                        <li><strong>PREMIUM:</strong> Obrigatório para usuários Foresea com acesso a Permissão de Trabalho (PTW) e módulos HSE.</li>
                        <li><strong>BASE:</strong> Mapeado para equipes de retaguarda (Compras, PCM, O.S padrão).</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid #f59e0b;">
                    <h3>🔑 Licença (Acesso)</h3>
                    <ul class="legend-list">
                        <li><strong>AUTHORIZED:</strong> Cargos críticos (ex: Supervisores). Acesso garantido 100% do tempo.</li>
                        <li><strong>CONCURRENT:</strong> Aplicado nas Sondas. Partilha o *pool* com base no cálculo do pico real do logintracking.</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid #10b981;">
                    <h3>📊 Fator de Escala (Data-Driven)</h3>
                    <ul class="legend-list">
                        <li>A máquina abandonou a média de 33%.</li>
                        <li>O <strong>Fator Real</strong> é calculado dinamicamente encontrando o dia em que cada cargo registrou o maior pico simultâneo de logins.</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """


def _render_tab_eventos(analytics):
    """Renders the 'Eventos Críticos' tab content."""
    scenario_points = analytics['scenario_points']
    return f"""
    <div id="tab-eventos" class="container tab-content">
        <div class="alert-box" style="border-left-color: var(--warning); background-color: #fffbeb;">
            <strong style="color: #b45309;">📊 Simulador de Teto de AppPoints (Eventos de Sonda)</strong>
            <p style="color: #92400e;">Teste a resistência da arquitetura de licenciamento. O que acontece com o consumo se houver um evento atípico na Foresea?</p>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem;">
            <div>
                <div class="card">
                    <h3 style="margin-top:0; font-size:1.1rem; color:var(--primary);">🚀 Disparadores de Cenário</h3>
                    <div class="event-card" onclick="triggerEventScenario('p50')">
                        <h4>🟢 Cenário Cotidiano (Mediana - P50)</h4>
                        <p>Simula um dia comum. Consome aprox. {fmt_br(scenario_points['p50'])} AppPoints. <small style="color:#64748b;">(Soma bruta: {fmt_br(analytics.get('scenario_points_total', {}).get('p50', 0))})</small></p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('p95')" style="border-left-color: var(--warning);">
                        <h4>🟡 Pico Seguro (Percentil 95)</h4>
                        <p>O teto projetado pela máquina. Consome aprox. {fmt_br(scenario_points['p95'])} AppPoints. <small style="color:#64748b;">(Soma bruta: {fmt_br(analytics.get('scenario_points_total', {}).get('p95', 0))})</small></p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('p100')" style="border-left-color: var(--danger);">
                        <h4>🔴 Emergência Operacional (P100)</h4>
                        <p>Pico máximo histórico. Consome aprox. {fmt_br(scenario_points['p100'])} AppPoints. <small style="color:#64748b;">(Soma bruta: {fmt_br(analytics.get('scenario_points_total', {}).get('p100', 0))})</small></p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('blackout')" style="border-left-color: #7c3aed; background: #faf5ff; border-color:#e9d5ff">
                        <h4>⚡ Blackout Total (100% de Acessos)</h4>
                        <p>Cenário extremo: Todos os usuários simultâneos. Consome aprox. {fmt_br(scenario_points['blackout'])} AppPoints. <small style="color:#64748b;">(Soma bruta: {fmt_br(analytics.get('scenario_points_total', {}).get('blackout', 0))})</small></p>
                    </div>
                </div>
            </div>
            <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <h3 id="eventCeilingLabel" style="margin-top:0; font-size:1.2rem; color:var(--secondary);">Termômetro de Impacto (Limite)</h3>
                <div style="height: 280px; position: relative;">
                    <canvas id="eventChart"></canvas>
                </div>
                <div id="eventOutputBox" style="padding: 1rem; text-align: center; font-weight: bold; border-radius: 6px; font-size: 1.1rem; margin-top: 1rem; background: #ecfdf5; color:#047857;">
                    Selecione um cenário ao lado...
                </div>
            </div>
        </div>
    </div>
    """


def _render_tab_peak(analytics):
    """Renders the Peak tab with aligned hourly series."""

    def rows_to_map(rows, value_keys):
        if isinstance(rows, dict):
            return {str(k): v for k, v in rows.items() if k}

        mapped = {}
        if isinstance(rows, list):
            for entry in rows:
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    mapped[str(entry[0])] = entry[1]
                elif isinstance(entry, dict):
                    hour = entry.get('hour') or entry.get('ts') or entry.get('time')
                    value = None
                    for key in value_keys:
                        if entry.get(key) is not None:
                            value = entry.get(key)
                            break
                    if hour:
                        mapped[str(hour)] = value
        return mapped

    users_by_hour = rows_to_map(
        analytics.get('concurrency_hourly', {}) or analytics.get('concurrency_peak_users_hours', []),
        ('users', 'count', 'value'),
    )
    points_by_hour = rows_to_map(
        analytics.get('concurrency_hourly_app_points', {}) or analytics.get('concurrency_peak_hours', []),
        ('app_points', 'points', 'count', 'value'),
    )
    nem_by_hour = rows_to_map(
        analytics.get('concurrency_hourly_app_points_nem', {}),
        ('app_points_nem', 'app_points', 'points', 'count', 'value'),
    )

    if not nem_by_hour:
        nem_by_hour = points_by_hour.copy()

    all_hours = set(users_by_hour) | set(points_by_hour) | set(nem_by_hour)
    peak_hours = sorted(
        all_hours,
        key=lambda hour: max(
            float(points_by_hour.get(hour) or 0),
            float(nem_by_hour.get(hour) or 0),
            float(users_by_hour.get(hour) or 0),
        ),
        reverse=True,
    )[:24]
    labels = sorted(peak_hours)

    def series_values(source):
        values = []
        for hour in labels:
            try:
                values.append(round(float(source.get(hour) or 0), 2))
            except (TypeError, ValueError):
                values.append(0)
        return values

    labels_json = json.dumps(labels, ensure_ascii=False)
    users_data_json = json.dumps(series_values(users_by_hour), ensure_ascii=False)
    points_data_json = json.dumps(series_values(points_by_hour), ensure_ascii=False)
    nem_data_json = json.dumps(series_values(nem_by_hour), ensure_ascii=False)

    return f"""
    <div id="tab-peak" class="container tab-content">
        <div class="card">
            <h2 class="card-header">⛰️ Peak Hours (High-Water Mark) - Ecocardiograma</h2>
            <p style="color:#475569;">Passe o mouse para ver usuários simultâneos e consumo de AppPoints no mesmo horário.</p>

            <div class="chart-box" style="height: 380px; align-items: stretch; padding: 1.5rem;">
                <canvas id="peakLineChart"
                        data-labels='{labels_json}'
                        data-users-data='{users_data_json}'
                        data-points-data='{points_data_json}'
                        data-nem-data='{nem_data_json}'></canvas>
            </div>
        </div>
    </div>
    """


def _render_tab_tabela(app_points_rows):
    """Renders the 'Plano de Ação' tab content."""
    return f"""
    <div id="tab-tabela" class="container tab-content">
        <div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">
            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: var(--primary);">📋 Plano de Ação Mestre e Fatores de Escala</h3>
                <button class="btn-export" onclick="exportTableToCSV('table-apppoints', 'Planejamento_Capacity_Maximo.csv')">
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 4px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                    Exportar para Excel (CSV)
                </button>
            </div>
            <div class="search-container">
                <input type="text" id="searchAppPoints" class="search-bar" onkeyup="filterAppPoints()" placeholder="Pesquisar por ID, Nome, Cargo...">
                <select id="filterRec" class="filter-select" onchange="filterAppPoints()">
                    <option value="">💡 Filtro de Ação</option>
                    <option value="INATIVO">🔴 Inativos (>90d)</option>
                    <option value="DOWNGRADE">🟡 Requer Downgrade (Premium p/ Base)</option>
                    <option value="P/ CONCURRENT">🔵 Escala Offshore (Concurrent)</option>
                    <option value="CONFIRMADO">🟢 Autorizado Fixo (Authorized)</option>
                </select>
                <select id="filterEnt" class="filter-select" onchange="filterAppPoints()">
                    <option value="">🔰 Todos Níveis (Entitlement)</option>
                    <option value="PREMIUM">Premium</option>
                    <option value="BASE">Base</option>
                </select>
            </div>
            {render_table(['USERID', 'Nome', 'Recomendação', 'Entitlement', 'Licença To-Be', 'AppPoints Ref.', 'Fator Analytics', 'Logins 90d', 'Cargo'], app_points_rows, 'table-apppoints', 'filterable-app-table')}
        </div>
    </div>
    """


def _render_scripts(analytics, identity_analytics):
    """Renders the JavaScript for the report."""
    scenarios_json = json.dumps(analytics['scenarios_data'])
    points_json = json.dumps(analytics['scenario_points'])
    total_points_json = json.dumps(analytics.get('scenario_points_total', {}))
    ceiling_limit = analytics.get('ceiling_limit', 1200)

    domain_keys = json.dumps(list(identity_analytics['domain_counts'].keys()))
    domain_values = json.dumps(list(identity_analytics['domain_counts'].values()))

    return f"""
    <script>
        const rawScenarios = {scenarios_json};
        const scenarioPoints = {points_json};
        const scenarioPointsTotal = {total_points_json};
        const ceilingLimit = {ceiling_limit};

        function openTab(evt, tabName) {{
            let i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{ tabcontent[i].style.display = "none"; tabcontent[i].classList.remove("active"); }}
            tablinks = document.getElementsByClassName("tab-button");
            for (i = 0; i < tablinks.length; i++) {{ tablinks[i].classList.remove("active"); }}
            const target = document.getElementById(tabName);
            target.style.display = "block";
            setTimeout(() => target.classList.add("active"), 10);
            evt.currentTarget.classList.add("active");
        }}

        new Chart(document.getElementById('domainChart'), {{
            type: 'doughnut',
            data: {{
                labels: {domain_keys},
                datasets: [{{ data: {domain_values}, backgroundColor: ['#10b981', '#2563eb', '#f59e0b', '#ef4444'], borderWidth: 2, borderColor: '#ffffff' }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: {{ legend: {{ position: 'right' }} }} }}
        }});

        function loadScenario(scenarioKey, btnElement) {{
            document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
            if(btnElement) btnElement.classList.add('active');

            const isFactoredScenario = scenarioKey === 'otimizado_p95' || scenarioKey === 'otimizado_p50';
            const physicalCountsKey = isFactoredScenario ? 'otimizado' : scenarioKey;
            const data = rawScenarios[physicalCountsKey];

            document.getElementById('inpPremAuth').value = data.pA;
            document.getElementById('inpPremConc').value = data.pC;
            document.getElementById('inpBaseAuth').value = data.bA;
            document.getElementById('inpBaseConc').value = data.bC;

            let totalPoints = 0;
            if (scenarioKey === 'otimizado_p95') {{
                totalPoints = Math.round(scenarioPoints.p95);
            }} else if (scenarioKey === 'otimizado_p50') {{
                totalPoints = Math.round(scenarioPoints.p50);
            }} else {{
                totalPoints = (data.pA * 5) + (data.pC * 15) + (data.bA * 3) + (data.bC * 10);
            }}

            document.getElementById('calcTotalDisplay').innerText = totalPoints.toLocaleString('pt-BR');
            updateCalculatorDisplay(totalPoints);
            updateChartFromInputs(); // Agora isso reflete os valores dos inputs, que são consistentes
        }}

        let simChartInstance = null;
        function updateCalculator() {{
            // Quando o usuário edita manualmente, desativa qualquer preset
            document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));

            const pAuth = parseInt(document.getElementById('inpPremAuth').value) || 0;
            const pConc = parseInt(document.getElementById('inpPremConc').value) || 0;
            const bAuth = parseInt(document.getElementById('inpBaseAuth').value) || 0;
            const bConc = parseInt(document.getElementById('inpBaseConc').value) || 0;
            const totalPoints = Math.round((pAuth * 5) + (pConc * 15) + (bAuth * 3) + (bConc * 10));

            document.getElementById('calcTotalDisplay').innerText = totalPoints.toLocaleString('pt-BR');
            updateCalculatorDisplay(totalPoints);
            updateChartFromInputs();
        }}

        function updateCalculatorDisplay(totalPoints) {{
            const alertEl = document.getElementById('calcAlertBox');
            const rawSumEl = document.getElementById('rawSumDisplay');
            try {{
                if (rawSumEl && scenarioPointsTotal && scenarioPointsTotal.p95) {{
                    rawSumEl.innerText = Number(scenarioPointsTotal.p95).toLocaleString('pt-BR');
                }}
            }} catch(e) {{ console.warn('raw sum display error', e); }}

            if (totalPoints > ceilingLimit) {{
                document.getElementById('calcTotalDisplay').style.color = 'var(--danger)';
                alertEl.style.display = 'block';
                alertEl.innerText = `⚠️ TETO EXCEDIDO (>${{ceilingLimit.toLocaleString('pt-BR')}})`;
            }} else {{
                document.getElementById('calcTotalDisplay').style.color = 'var(--success)';
                alertEl.style.display = 'none';
            }}
        }}

        function updateChartFromInputs() {{
            const pAuth = parseInt(document.getElementById('inpPremAuth').value) || 0;
            const pConc = parseInt(document.getElementById('inpPremConc').value) || 0;
            const bAuth = parseInt(document.getElementById('inpBaseAuth').value) || 0;
            const bConc = parseInt(document.getElementById('inpBaseConc').value) || 0;
            const data = [(pAuth * 5), (pConc * 15), (bAuth * 3), (bConc * 10)];
            const ctxSim = document.getElementById('simChart').getContext('2d');
            if (simChartInstance) {{
                simChartInstance.data.datasets[0].data = data;
                simChartInstance.update();
            }} else {{
                simChartInstance = new Chart(ctxSim, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Prem Auth', 'Prem Conc', 'Base Auth', 'Base Conc'],
                        datasets: [{{ data: data, backgroundColor: ['#1e3a8a', '#3b82f6', '#047857', '#10b981'] }}]
                    }},
                    options: {{ responsive: true, maintainAspectRatio: false, cutout: '50%', plugins: {{ legend: {{ position: 'right' }} }} }}
                }});
            }}
        }}

        let eventChartInstance = null;
        function triggerEventScenario(type) {{
            let totalPoints = Math.round(scenarioPoints[type] || 0);
            let titleText = "", description = "";

            if (type === 'p50') {{ titleText = "🟢 Cotidiano (Mediana)"; description = "Operação normal e fluida."; }} 
            else if (type === 'p95') {{ titleText = "🟡 Pico Seguro (P95)"; description = "Handovers de turno comportados na meta."; }}
            else if (type === 'p100') {{ titleText = "🔴 Emergência (P100)"; description = "Risco moderado. Acesso simultâneo alto registrado no log."; }}
            else if (type === 'blackout') {{ titleText = "⚡ Blackout (100%)"; description = "Cenário fatal: Sondas paradas. Possível travamento do MAS 9."; }}

            const outBox = document.getElementById('eventOutputBox');
            outBox.innerText = `${{titleText}}: ${{totalPoints.toLocaleString('pt-BR')}} AppPoints. ${{description}}`;
            outBox.style.background = totalPoints > ceilingLimit ? '#fef2f2' : '#ecfdf5';
            outBox.style.color = totalPoints > ceilingLimit ? 'var(--danger)' : '#047857';

            const ctxEvent = document.getElementById('eventChart').getContext('2d');
            if (eventChartInstance) {{
                eventChartInstance.data.datasets[0].data = [totalPoints];
                eventChartInstance.data.datasets[0].backgroundColor = totalPoints > 1200 ? '#ef4444' : '#2563eb';
                eventChartInstance.update();
            }} else {{
                eventChartInstance = new Chart(ctxEvent, {{
                    type: 'bar',
                    data: {{
                        labels: ['Consumo Simulado'],
                        datasets: [{{ label: 'AppPoints Requeridos', data: [totalPoints], backgroundColor: '#2563eb', barThickness: 60 }}]
                    }},
                    options: {{
                        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                        scales: {{ x: {{ max: 2000, beginAtZero: true }} }},
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}
        }}

        function filterGovTable() {{
            const input = document.getElementById("searchGov").value.toUpperCase();
            const decFilter = document.getElementById("selGovDec").value.toUpperCase();
            document.querySelectorAll("#tab-gov .gov-table").forEach(table => {{
                for (let i = 1; i < table.rows.length; i++) {{
                    const rowText = table.rows[i].textContent.toUpperCase();
                    const matchInput = input === "" || rowText.includes(input);
                    const matchDec = decFilter === "" || rowText.includes(decFilter);
                    table.rows[i].style.display = (matchInput && matchDec) ? "" : "none";
                }}
            }});
        }}

        function filterAppPoints() {{
            const input = document.getElementById("searchAppPoints").value.toUpperCase();
            const recFilter = document.getElementById("filterRec").value.toUpperCase();
            const entFilter = document.getElementById("filterEnt").value.toUpperCase();
            const table = document.getElementById("table-apppoints");
            if(!table) return;
            for (let i = 1; i < table.rows.length; i++) {{
                const row = table.rows[i];
                const matchSearch = row.cells[0].textContent.toUpperCase().includes(input) || row.cells[1].textContent.toUpperCase().includes(input) || row.cells[8].textContent.toUpperCase().includes(input);
                const matchRec = recFilter === "" || row.cells[2].textContent.toUpperCase().includes(recFilter);
                const matchEnt = entFilter === "" || row.cells[3].textContent.toUpperCase().includes(entFilter);
                row.style.display = (matchSearch && matchRec && matchEnt) ? "" : "none";
            }}
        }}

        function downloadCSV(csv, filename) {{
            const csvFile = new Blob(["\\uFEFF" + csv], {{type: "text/csv;charset=utf-8;"}});
            const link = document.createElement("a");
            link.download = filename;
            link.href = window.URL.createObjectURL(csvFile);
            link.style.display = "none";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}

        function exportTableToCSV(tableId, filename) {{
            const csv = [];
            const table = document.getElementById(tableId);
            const rows = table.querySelectorAll("tr");
            for (let i = 0; i < rows.length; i++) {{
                if(rows[i].style.display === "none") continue;
                const row = [], cols = rows[i].querySelectorAll("td, th");
                for (let j = 0; j < cols.length; j++) {{
                    row.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');
                }}
                csv.push(row.join(";"));
            }}
            downloadCSV(csv.join("\\n"), filename);
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            // ---- Peak Line Chart (ecocardiograma-like) ----
            try {{
                const canvasEl = document.getElementById('peakLineChart');
                if (canvasEl) {{
                    const labels = JSON.parse(canvasEl.getAttribute('data-labels') || '[]');
                    const usersData = JSON.parse(canvasEl.getAttribute('data-users-data') || '[]');
                    const pointsData = JSON.parse(canvasEl.getAttribute('data-points-data') || '[]');
                    const nemData = JSON.parse(canvasEl.getAttribute('data-nem-data') || '[]');

                    const ctxPeak = canvasEl.getContext('2d');
                    new Chart(ctxPeak, {{
                        type: 'line',
                        data: {{
                            labels: labels,
                            datasets: [{{
                                label: 'Usuários Simultâneos',
                                data: usersData,
                                borderColor: '#7c3aed',
                                backgroundColor: 'rgba(124, 58, 237, 0.1)',
                                yAxisID: 'y-users',
                                borderWidth: 3,
                                tension: 0.3,
                                unit: 'usuarios'
                            }}, {{
                                label: 'Consumo de AppPoints',
                                data: pointsData,
                                borderColor: '#f59e0b',
                                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                                yAxisID: 'y-points',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                tension: 0.3,
                                unit: 'AppPoints'
                            }}, {{
                                label: 'AppPoints NEM',
                                data: nemData,
                                borderColor: '#ef4444',
                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                yAxisID: 'y-points',
                                borderWidth: 2,
                                tension: 0.3,
                                unit: 'AppPoints'
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {{
                                mode: 'index',
                                intersect: false,
                            }},
                            plugins: {{
                                legend: {{ position: 'bottom' }},
                                tooltip: {{
                                    position: 'nearest',
                                    padding: 10,
                                    titleFont: {{ weight: 'bold' }},
                                    bodySpacing: 5,
                                    callbacks: {{
                                        label: function(ctx) {{
                                            const label = ctx.dataset.label || '';
                                            const unit = ctx.dataset.unit || '';
                                            const rawValue = ctx.parsed.y;
                                            const value = Number(rawValue || 0).toLocaleString('pt-BR');
                                            return `${{label}}: ${{value}} ${{unit}}`.trim();
                                        }}
                                    }}
                                }}
                            }},
                            scales: {{
                                x: {{
                                    title: {{ display: true, text: 'Hora do Dia' }}
                                }},
                                'y-users': {{
                                    type: 'linear',
                                    position: 'left',
                                    beginAtZero: true,
                                    title: {{ display: true, text: 'Nº de Usuários Simultâneos', color: '#7c3aed' }}
                                }},
                                'y-points': {{
                                    type: 'linear',
                                    position: 'right',
                                    beginAtZero: true,
                                    title: {{ display: true, text: 'AppPoints Consumidos', color: '#f59e0b' }},
                                    grid: {{
                                        drawOnChartArea: false, // Só desenha o grid para o eixo Y da esquerda
                                    }},
                                }}
                            }}
                        }}
                    }});
                }}
            }} catch(e) {{
                console.error('peakLineChart init failed', e);
            }}

            // Force correct initialization with the pre-calculated scenario points
            const initialPoints = Math.round(scenarioPoints.p95);
            document.getElementById('calcTotalDisplay').innerText = initialPoints.toLocaleString('pt-BR');
            // Populate raw sum display if available
            try {{
                const rawSumEl = document.getElementById('rawSumDisplay');
                if (rawSumEl && scenarioPointsTotal && scenarioPointsTotal.p95) {{
                    rawSumEl.innerText = Number(scenarioPointsTotal.p95).toLocaleString('pt-BR');
                }}
            }} catch(e) {{ console.warn('raw sum init error', e); }}

            // Set ceiling label dynamically
            try {{
                const ceilLabel = document.getElementById('eventCeilingLabel');
                if (ceilLabel) ceilLabel.innerText = `Termômetro de Impacto (Limite: ${{ceilingLimit.toLocaleString('pt-BR')}})`;
            }} catch(e) {{ }}

            loadScenario('otimizado_p95', document.getElementById('btnOtimizado'));
            triggerEventScenario('p95'); // Initial trigger for the event chart
        }});
    </script>
    """


# --- Main Orchestrator Function ---

def render_html(data):
    """
    Orchestrates the rendering of the full HTML report by assembling its components.
    """
    analytics = data['analytics']
    gov_tables = data['gov_tables']
    app_points_rows = data['app_points_rows']
    identity_analytics = data['identity_analytics']

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Maximo Unificado - Foresea</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {_render_styles()}
</head>
<body>
    {_render_header_and_tabs()}
    {_render_tab_painel(analytics, identity_analytics)}
    {_render_tab_gov(gov_tables)}
    {_render_tab_apppoints(analytics)}
    {_render_tab_eventos(analytics)}
    {_render_tab_peak(analytics)}
    {_render_tab_tabela(app_points_rows)}
    {_render_scripts(analytics, identity_analytics)}
</body>
</html>"""
