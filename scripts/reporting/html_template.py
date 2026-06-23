# scripts/reporting/html_template.py
from datetime import datetime
import json
from .html_helpers import fmt_br, render_table

def render_html(data):
    analytics = data['analytics']
    gov_tables = data['gov_tables']
    app_points_rows = data['app_points_rows']
    summary = data['summary']
    domains = data['domains']
    
    inativos_count = analytics['inativos_count']
    downgrade_count = analytics['downgrade_count']
    concurrent_count = analytics['concurrent_count']
    scenarios_data = analytics['scenarios_data']
    avg_f_p50 = analytics['avg_f_p50']
    avg_f_p95 = analytics['avg_f_p95']
    avg_f_p100 = analytics['avg_f_p100']

    scenarios_json = json.dumps(scenarios_data)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Maximo Unificado - Foresea</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{ --primary: #0f172a; --secondary: #1e293b; --accent: #2563eb; --bg: #f8fafc; --card-bg: #ffffff; --text: #334155; --border: #e2e8f0; --danger: #ef4444; --warning: #f59e0b; --success: #10b981; --neutral:#64748b}}
        * {{ box-sizing: border-box; }}
        body {{ font-family: "Segoe UI", system-ui, -apple-system, sans-serif; margin: 0; background-color: var(--bg); color: var(--text); line-height: 1.5; }}
        .topbar {{ background: var(--primary); color: white; padding: 1.5rem 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center;}}
        .topbar h1 {{ margin: 0; font-size: 1.8rem; font-weight: 600; letter-spacing: -0.5px; }}
        .topbar p {{ margin: 0; color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem; }}
        .tabs {{ background: var(--secondary); padding: 0 2rem; display: flex; gap: 1rem; overflow-x: auto; white-space: nowrap;}}
        .tab-button {{ background: none; border: none; color: #cbd5e1; padding: 1rem 1.5rem; cursor: pointer; font-size: 1rem; border-bottom: 3px solid transparent; font-weight: 600; transition: all 0.2s;}}
        .tab-button:hover {{ color: white; }}
        .tab-button.active {{ color: white; border-bottom-color: var(--accent); }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; animation: fadeIn 0.3s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

        .alert-box {{ background-color: #eff6ff; border-left: 4px solid var(--accent); padding: 1rem 1.5rem; border-radius: 6px; margin-bottom: 2rem; display: flex; flex-direction: column; gap: 0.5rem; }}
        .alert-box strong {{ color: #1e3a8a; font-size: 1.1rem; }}
        .alert-box p {{ margin: 0; color: #1e40af; }}

        .card {{ background: var(--card-bg); border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid var(--border); padding: 1.8rem; margin-bottom: 2rem; }}
        .card-header {{ margin-top: 0; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border); padding-bottom: 0.75rem; color: var(--secondary); font-size: 1.4rem; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }}

        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; }}
        .stat-card {{ background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; text-align: center; transition: transform 0.2s; position: relative; }}
        .stat-value {{ font-size: 2.2rem; font-weight: 700; color: var(--primary); margin-bottom: 0.2rem; }}
        .stat-title {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #1e293b; font-weight: 700; margin-bottom: 0.5rem; }}
        .stat-subtitle {{ font-size: 0.75rem; color: #64748b; line-height: 1.2; }}

        .border-danger {{ border-bottom: 4px solid var(--danger); }}
        .border-warning {{ border-bottom: 4px solid var(--warning); }}
        .border-accent {{ border-bottom: 4px solid var(--accent); }}
        .border-success {{ border-bottom: 4px solid var(--success); }}
        .border-neutral {{ border-bottom: 4px solid var(--neutral); }}

        .charts-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 2rem; margin-top: 2rem; }}
        .chart-box {{ height: 320px; display: flex; justify-content: center; align-items: center; background: #ffffff; border-radius: 8px; border: 1px solid var(--border); padding: 1rem; }}

        .table-responsive {{ overflow-x: auto; border-radius: 8px; border: 1px solid var(--border); max-height: 500px; overflow-y: auto; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 14px 16px; border-bottom: 1px solid var(--border); vertical-align: top; font-size: 0.9rem; }}
        th {{ background-color: #f1f5f9; color: #334155; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; position: sticky; top: 0; z-index: 10; }}
        tbody tr:hover {{ background-color: #f8fafc; }}

        .badge {{ padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: inline-block; text-align: center; color: white; }}
        .badge-critical {{ background-color: var(--danger); }}
        .badge-high {{ background-color: var(--warning); }}
        .badge-medium {{ background-color: var(--accent); }}
        .badge-success {{ background-color: var(--success); }}
        .badge-neutral {{ background-color: var(--neutral); }}

        .search-container {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #f1f5f9; padding: 1.5rem; border-radius: 8px; align-items: center; }}
        .search-bar {{ flex-grow: 1; padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; min-width: 250px; }}
        .filter-select {{ padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; background: white; min-width: 180px; }}
        .btn-export {{ background-color: #10b981; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-size: 0.95rem; font-weight: bold; cursor: pointer; transition: background 0.2s; }}
        .btn-export:hover {{ background-color: #059669; }}

        /* Analysis Grid CSS (Tab 2) */
        .type-analysis-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }}
        .type-card {{ background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; }}
        .type-card h4 {{ margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }}
        .env-divergence {{ margin-bottom: 0.8rem; padding: 0.8rem; background: #f8fafc; border-left: 3px solid var(--warning); border-radius: 4px; }}
        .env-header {{ font-weight: 700; color: var(--primary); margin-bottom: 0.4rem; font-size: 0.9rem; }}

        /* Simulator & Scenarios CSS (Tab 3) */
        .preset-btn {{ background: white; border: 1px solid var(--border); padding: 8px 16px; border-radius: 6px; font-size: 0.9rem; font-weight: 600; cursor: pointer; color: var(--secondary); transition: all 0.2s; }}
        .preset-btn:hover {{ background: #f1f5f9; }}
        .preset-btn.active {{ background: var(--accent); color: white; border-color: var(--accent); }}

        .calc-input-group {{ margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed var(--border); padding-bottom: 0.5rem; }}
        .calc-input-group label {{ font-weight: 600; color: var(--text); font-size: 0.95rem; }}
        .calc-input-group input {{ width: 100px; padding: 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 1.1rem; text-align: center; color: var(--primary); font-weight: bold; }}
        .calc-badge-pts {{ font-size: 0.75rem; background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; margin-left: 8px; }}

        .legend-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
        .legend-box {{ background: #f8fafc; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); }}
        .legend-box h3 {{ margin-top: 0; color: var(--primary); font-size: 1.05rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; margin-bottom: 1rem; }}
        .legend-list {{ padding-left: 1.2rem; margin-bottom: 0; font-size: 0.88rem; color: var(--text); }}
        .legend-list li {{ margin-bottom: 0.6rem; }}

        /* Event Simulator CSS (Tab 4) */
        .event-card {{ background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid var(--warning); padding: 1.2rem; border-radius: 8px; margin-bottom: 1rem; cursor: pointer; transition: background 0.2s; }}
        .event-card:hover {{ background: #fef08a; }}
        .event-card h4 {{ margin: 0 0 0.4rem 0; color: #92400e; font-size: 1.1rem; }}
        .event-card p {{ margin: 0; font-size: 0.85rem; color: #b45309; }}
    </style>
</head>
<body>
    <div class="topbar">
        <div>
            <h1>Dashboard Gerencial MAS 9.1 | Foresea</h1>
            <p>Capacity Planning Avançado, Saneamento e Simulação de ROI</p>
        </div>
        <div>
            <p style="text-align: right; color: #cbd5e1;">Gerado em:<br><strong>{datetime.now().strftime("%d/%m/%Y %H:%M")}</strong></p>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-button active" onclick="openTab(event, 'tab-painel')">1. Painel Operacional</button>
        <button class="tab-button" onclick="openTab(event, 'tab-gov')">2. Governança & Saneamento</button>
        <button class="tab-button" onclick="openTab(event, 'tab-apppoints')" style="color:#60a5fa;">3. Cenários & ROI</button>
        <button class="tab-button" onclick="openTab(event, 'tab-eventos')" style="color:var(--warning);">4. Eventos Críticos</button>
        <button class="tab-button" onclick="openTab(event, 'tab-tabela')">5. Plano de Ação</button>
    </div>

    <div id="tab-painel" class="container tab-content active">
        <div class="alert-box">
            <strong>🎯 Resumo Consolidador (Base de Dados Real)</strong>
            <p>A inteligência mapeou as 7 instâncias. Detetamos {fmt_br(inativos_count)} inativos e {fmt_br(downgrade_count + concurrent_count)} elegíveis para partilha de turnos/downgrade de licenças.</p>
        </div>
        <div class="card">
            <h2 class="card-header">Radar Operacional (As-Is)</h2>
            <div class="stats-grid">
                <div class="stat-card border-success"><div class="stat-value" style="color: var(--success);">{fmt_br(summary['active_profiles_count'])}</div><div class="stat-title">Pessoas Únicas</div></div>
                <div class="stat-card border-neutral"><div class="stat-value" style="color: var(--neutral);">{fmt_br(inativos_count)}</div><div class="stat-title">Contas Zumbi</div><div class="stat-subtitle">Sem login há > 90d</div></div>
                <div class="stat-card border-warning"><div class="stat-value" style="color: var(--warning);">{fmt_br(downgrade_count)}</div><div class="stat-title">Elegíveis Downgrade</div></div>
                <div class="stat-card border-accent"><div class="stat-value" style="color: var(--accent);">{fmt_br(concurrent_count)}</div><div class="stat-title">Migração Offshore</div></div>
            </div>
            <div class="charts-container" style="grid-template-columns: 1fr 2fr;">
                <div class="chart-box" style="flex-direction: column;">
                    <h3 style="margin-top:0; font-size: 1rem; color: var(--primary);">Distribuição Contratual (Domínio)</h3>
                    <canvas id="domainChart"></canvas>
                </div>
                <div class="chart-box" style="align-items: flex-start; padding: 2rem;">
                    <div style="width: 100%;">
                        <h3 style="margin-top:0; font-size: 1rem; color: var(--primary);">Segregação Operacional</h3>
                        <p style="font-size: 0.9rem; color: var(--text); margin-bottom: 1rem;">
                            Terceiros representam passivo. Recomenda-se migrar acessos esporádicos de parceiros para integrações via API, otimizando AppPoints.
                        </p>
                        <div style="display: flex; justify-content: space-between; padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border);">
                            <div style="text-align:center"><strong style="color: #10b981; font-size: 1.4rem;">{fmt_br(domains.get('FORESEA', 0))}</strong> <br><span style="font-size: 0.8rem; font-weight:bold; color: #64748b;">FORESEA</span></div>
                            <div style="text-align:center"><strong style="color: #2563eb; font-size: 1.4rem;">{fmt_br(domains.get('PARCEIRO', 0))}</strong> <br><span style="font-size: 0.8rem; font-weight:bold; color: #64748b;">PARCEIROS</span></div>
                            <div style="text-align:center"><strong style="color: #f59e0b; font-size: 1.4rem;">{fmt_br(domains.get('TERCEIRO', 0))}</strong> <br><span style="font-size: 0.8rem; font-weight:bold; color: #64748b;">TERCEIROS</span></div>
                            <div style="text-align:center"><strong style="color: #ef4444; font-size: 1.4rem;">{fmt_br(domains.get('SEM DOMINIO', 0))}</strong> <br><span style="font-size: 0.8rem; font-weight:bold; color: #64748b;">S/ DOMÍNIO</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

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

    <div id="tab-apppoints" class="container tab-content">
        <div class="card" style="border-left: 4px solid var(--success); background-image: linear-gradient(to right, #ffffff, #f8fafc);">
            <div class="card-header" style="border:none; margin-bottom:0.5rem;">
                <div>
                    <h2 style="margin:0; color:var(--success);">🧮 Simulador Financeiro (Comparativo de ROI)</h2>
                    <p style="font-size: 0.9rem; color: #64748b; font-weight: normal; margin-top: 4px;">Utilize os filtros abaixo para comprovar a poupança gerada pela inteligência de dados perante a Diretoria.</p>
                </div>
            </div>

            <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; padding: 1rem; background: #f1f5f9; border-radius: 8px; flex-wrap:wrap;">
                <button class="preset-btn" id="btnAsIs" onclick="loadScenario('asis', this)">1. Migração Cega (As-Is)</button>
                <button class="preset-btn" id="btnSaneado" onclick="loadScenario('saneado', this)">2. Saneamento (Remove >90d)</button>
                <button class="preset-btn active" id="btnOtimizado" onclick="loadScenario('otimizado', this)">3. Otimizado (IA: Escalas + Downgrades)</button>
            </div>

            <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 300px; background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border);">
                    <div style="margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom:1rem;">
                        <label style="font-weight: bold; color: var(--primary);">💵 Custo Estimado por AppPoint/Ano:</label>
                        <input type="number" id="inpCustoUnitario" value="500" min="0" oninput="updateCalculator()" style="width: 100%; padding: 8px; margin-top: 4px; font-weight: bold; border: 1px solid var(--border); border-radius: 6px;">
                    </div>
                    <div class="calc-input-group"><label>Premium Auth <span class="calc-badge-pts">5 pts</span></label><input type="number" id="inpPremAuth" oninput="updateCalculator()"></div>
                    <div class="calc-input-group"><label>Premium Conc <span class="calc-badge-pts">15 pts</span></label><input type="number" id="inpPremConc" oninput="updateCalculator()"></div>
                    <div class="calc-input-group"><label>Base Auth <span class="calc-badge-pts">3 pts</span></label><input type="number" id="inpBaseAuth" oninput="updateCalculator()"></div>
                    <div class="calc-input-group" style="border:none; margin:0; padding:0;"><label>Base Conc <span class="calc-badge-pts">10 pts</span></label><input type="number" id="inpBaseConc" oninput="updateCalculator()"></div>
                </div>
                <div style="flex: 1; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                    <h3 style="margin: 0; font-size: 1rem; color: var(--secondary);">AppPoints Requeridos</h3>
                    <div id="calcTotalDisplay" style="font-size: 4.5rem; font-weight: 800; color: var(--success); line-height:1;">0</div>
                    <div style="margin-top: 1.5rem; padding: 1rem; background:#ecfdf5; border: 1px solid #a7f3d0; border-radius:8px;">
                        <div style="font-size: 0.85rem; font-weight: bold; color: #065f46; text-transform:uppercase;">Custo Anual Contratual</div>
                        <div id="calcFinancialTotal" style="font-size: 1.8rem; font-weight: 800; color: #047857;">$ 0</div>
                    </div>
                    <div id="calcAlertBox" style="margin-top: 1rem; padding: 0.75rem; background: var(--danger); color:white; font-weight:bold; border-radius:6px; display:none; font-size:1.1rem;">⚠️ TETO EXCEDIDO (>1200)</div>
                </div>
                <div style="flex: 1; min-width: 300px; height: 260px;"><canvas id="simChart"></canvas></div>
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

    <div id="tab-eventos" class="container tab-content">
        <div class="alert-box" style="border-left-color: var(--warning); background-color: #fffbeb;">
            <strong style="color: #b45309;">📊 Simulador de Teto Orçamentário Diário (Eventos de Sonda)</strong>
            <p style="color: #92400e;">Teste a resistência da arquitetura. O que acontece com o consumo se houver um evento atípico na Foresea?</p>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem;">
            <div>
                <div class="card">
                    <h3 style="margin-top:0; font-size:1.1rem; color:var(--primary);">🚀 Disparadores de Cenário</h3>
                    <div class="event-card" onclick="triggerEventScenario('normal')">
                        <h4>🟢 Cenário Cotidiano (Mediana - P50)</h4>
                        <p>Simula um dia comum. Consome aprox. {avg_f_p50 * 100:.0f}% das licenças partilháveis.</p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('p95')" style="border-left-color: var(--warning);">
                        <h4>🟡 Pico Seguro (Percentil 95)</h4>
                        <p>O teto projetado pela máquina. Absorve trocas de turnos com {avg_f_p95 * 100:.0f}% de taxa real.</p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('crisis')" style="border-left-color: var(--danger);">
                        <h4>🔴 Emergência Operacional (P100)</h4>
                        <p>Pico máximo histórico ({avg_f_p100 * 100:.0f}% simultâneos). Teste o limite do orçamento.</p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('blackout')" style="border-left-color: #7c3aed; background: #faf5ff; border-color:#e9d5ff">
                        <h4>⚡ Blackout Total (100% de Acessos)</h4>
                        <p>Cenário extremo e improvável: Todas as sondas caem e todos tentam logar juntos.</p>
                    </div>
                </div>
            </div>

            <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <h3 style="margin-top:0; font-size:1.2rem; color:var(--secondary);">Termômetro de Impacto Orçamental (Limite: 1.200)</h3>
                <div style="height: 280px; position: relative;">
                    <canvas id="eventChart"></canvas>
                </div>
                <div id="eventOutputBox" style="padding: 1rem; text-align: center; font-weight: bold; border-radius: 6px; font-size: 1.1rem; margin-top: 1rem; background: #ecfdf5; color:#047857;">
                    Selecione um cenário ao lado...
                </div>
            </div>
        </div>
    </div>

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

    <script>
        const rawScenarios = {scenarios_json};

        function openTab(evt, tabName) {{
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{ tabcontent[i].style.display = "none"; tabcontent[i].classList.remove("active"); }}
            tablinks = document.getElementsByClassName("tab-button");
            for (i = 0; i < tablinks.length; i++) {{ tablinks[i].classList.remove("active"); }}

            var target = document.getElementById(tabName);
            target.style.display = "block";
            setTimeout(() => target.classList.add("active"), 10);
            evt.currentTarget.classList.add("active");
        }}

        // Gráfico Domínio
        const domainLabels = {list(domains.keys())};
        const domainValues = {list(domains.values())};
        new Chart(document.getElementById('domainChart'), {{
            type: 'doughnut',
            data: {{
                labels: domainLabels,
                datasets: [{{ data: domainValues, backgroundColor: ['#10b981', '#2563eb', '#f59e0b', '#ef4444'], borderWidth: 2, borderColor: '#ffffff' }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: {{ legend: {{ position: 'right' }} }} }}
        }});

        // Lógica Aba 3: ROI e Simulador Financeiro
        function loadScenario(scenarioKey, btnElement) {{
            document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
            if(btnElement) btnElement.classList.add('active');

            const data = rawScenarios[scenarioKey];
            document.getElementById('inpPremAuth').value = Math.round(data.pA);
            document.getElementById('inpPremConc').value = Math.round(data.pC);
            document.getElementById('inpBaseAuth').value = Math.round(data.bA);
            document.getElementById('inpBaseConc').value = Math.round(data.bC);

            updateCalculator();
        }}

        let simChartInstance = null;
        function updateCalculator() {{
            const pAuth = parseInt(document.getElementById('inpPremAuth').value) || 0;
            const pConc = parseInt(document.getElementById('inpPremConc').value) || 0;
            const bAuth = parseInt(document.getElementById('inpBaseAuth').value) || 0;
            const bConc = parseInt(document.getElementById('inpBaseConc').value) || 0;
            const unitCost = parseFloat(document.getElementById('inpCustoUnitario').value) || 0;

            const costPAuth = pAuth * 5;
            const costPConc = pConc * 15;
            const costBAuth = bAuth * 3;
            const costBConc = bConc * 10;

            const totalPoints = costPAuth + costPConc + costBAuth + costBConc;
            document.getElementById('calcTotalDisplay').innerText = totalPoints.toLocaleString('pt-BR');
            document.getElementById('calcFinancialTotal').innerText = "$" + (totalPoints * unitCost).toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});

            const alertEl = document.getElementById('calcAlertBox');
            if (totalPoints > 1200) {{
                document.getElementById('calcTotalDisplay').style.color = 'var(--danger)';
                alertEl.style.display = 'block';
            }} else {{
                document.getElementById('calcTotalDisplay').style.color = 'var(--success)';
                alertEl.style.display = 'none';
            }}

            const ctxSim = document.getElementById('simChart').getContext('2d');
            if (simChartInstance) {{
                simChartInstance.data.datasets[0].data = [costPAuth, costPConc, costBAuth, costBConc];
                simChartInstance.update();
            }} else {{
                simChartInstance = new Chart(ctxSim, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Prem Auth', 'Prem Conc', 'Base Auth', 'Base Conc'],
                        datasets: [{{ data: [costPAuth, costPConc, costBAuth, costBConc], backgroundColor: ['#1e3a8a', '#3b82f6', '#047857', '#10b981'] }}]
                    }},
                    options: {{ responsive: true, maintainAspectRatio: false, cutout: '50%', plugins: {{ legend: {{ position: 'right' }} }} }}
                }});
            }}
        }}

        // Lógica Aba 4: Eventos de Estresse
        let eventChartInstance = null;
        function triggerEventScenario(type) {{
            let factor = 0;
            let titleText = ""; let description = "";

            if (type === 'normal') {{
                factor = {avg_f_p50}; titleText = "🟢 Cotidiano (Mediana)"; description = "Operação normal e fluida.";
            }} else if (type === 'p95') {{
                factor = {avg_f_p95}; titleText = "🟡 Pico Seguro (P95)"; description = "Handovers de turno comportados na meta.";
            }} else if (type === 'crisis') {{
                factor = {avg_f_p100}; titleText = "🔴 Emergência (P100)"; description = "Risco moderado. Acesso simultâneo alto registrado no log.";
            }} else if (type === 'blackout') {{
                factor = 1.0; titleText = "⚡ Blackout (100%)"; description = "Cenário fatal: Sondas paradas. Possível travamento do MAS 9.";
            }}

            // Usa os totais físicos do cenário otimizado
            const dataOpt = rawScenarios['otimizado'];
            // A matemática aqui reverte o fator embutido no cenário otimizado para reaplicar o fator do evento
            const physPremConc = dataOpt.pC / {avg_f_p95}; 
            const physBaseConc = dataOpt.bC / {avg_f_p95};

            const ptsAuth = (dataOpt.pA * 5) + (dataOpt.bA * 3);
            const ptsConc = ((physPremConc * 15) + (physBaseConc * 10)) * factor;
            const totalPoints = Math.round(ptsAuth + ptsConc);

            const outBox = document.getElementById('eventOutputBox');
            outBox.innerText = titleText + ": " + totalPoints.toLocaleString('pt-BR') + " AppPoints. " + description;

            if (totalPoints > 1200) {{
                outBox.style.background = '#fef2f2'; outBox.style.color = 'var(--danger)';
            }} else {{
                outBox.style.background = '#ecfdf5'; outBox.style.color = '#047857';
            }}

            const ctxEvent = document.getElementById('eventChart').getContext('2d');
            if (eventChartInstance) {{
                eventChartInstance.data.datasets[0].data = [totalPoints];
                if(totalPoints > 1200) eventChartInstance.data.datasets[0].backgroundColor = '#ef4444';
                else eventChartInstance.data.datasets[0].backgroundColor = '#2563eb';
                eventChartInstance.update();
            }} else {{
                eventChartInstance = new Chart(ctxEvent, {{
                    type: 'bar',
                    data: {{
                        labels: ['Consumo Simulado'],
                        datasets: [{{ label: 'AppPoints Requeridos', data: [totalPoints], backgroundColor: '#2563eb', barThickness: 60 }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        responsive: true, maintainAspectRatio: false,
                        scales: {{ x: {{ max: 2000, beginAtZero: true }} }},
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}
        }}

        // Filtros (Aba 2: Governança)
        function filterGovTable() {{
            var input = document.getElementById("searchGov").value.toUpperCase();
            var decFilter = document.getElementById("selGovDec").value.toUpperCase();
            var tables = document.querySelectorAll("#tab-gov .gov-table");
            tables.forEach(function(table) {{
                var tr = table.getElementsByTagName("tr");
                for (var i = 1; i < tr.length; i++) {{
                    var rowText = tr[i].textContent || tr[i].innerText;
                    var matchInput = input === "" || rowText.toUpperCase().indexOf(input) > -1;
                    var matchDec = decFilter === "" || rowText.toUpperCase().indexOf(decFilter) > -1;
                    tr[i].style.display = (matchInput && matchDec) ? "" : "none";
                }}
            }});
        }}

        // Filtros (Aba 5: AppPoints)
        function filterAppPoints() {{
            var input = document.getElementById("searchAppPoints").value.toUpperCase();
            var recFilter = document.getElementById("filterRec").value.toUpperCase();
            var entFilter = document.getElementById("filterEnt").value.toUpperCase();

            var table = document.getElementById("table-apppoints");
            if(!table) return;
            var tr = table.getElementsByTagName("tr");
            for (var i = 1; i < tr.length; i++) {{
                var tdNameTitle = tr[i].cells[0].textContent + " " + tr[i].cells[1].textContent + " " + tr[i].cells[8].textContent;
                var tdRec = tr[i].cells[2].textContent.toUpperCase();
                var tdEnt = tr[i].cells[3].textContent.toUpperCase();

                var matchSearch = input === "" || tdNameTitle.toUpperCase().indexOf(input) > -1;
                var matchRec = recFilter === "" || tdRec.indexOf(recFilter) > -1;
                var matchEnt = entFilter === "" || tdEnt.indexOf(entFilter) > -1;
                tr[i].style.display = (matchSearch && matchRec && matchEnt) ? "" : "none";
            }}
        }}

        // Exportador Master
        function downloadCSV(csv, filename) {{
            var csvFile = new Blob(["\\uFEFF" + csv], {{type: "text/csv;charset=utf-8;"}});
            var link = document.createElement("a");
            link.download = filename; link.href = window.URL.createObjectURL(csvFile);
            link.style.display = "none"; document.body.appendChild(link); link.click();
        }}

        function exportTableToCSV(tableId, filename) {{
            var csv = [], table = document.getElementById(tableId), rows = table.querySelectorAll("tr");
            for (var i = 0; i < rows.length; i++) {{
                if(rows[i].style.display === "none") continue;
                var row = [], cols = rows[i].querySelectorAll("td, th");
                for (var j = 0; j < cols.length; j++) row.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');
                csv.push(row.join(";"));
            }}
            downloadCSV(csv.join("\\n"), filename);
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            loadScenario('otimizado');
            triggerEventScenario('p95');
        }});
    </script>
</body>
</html>"""
