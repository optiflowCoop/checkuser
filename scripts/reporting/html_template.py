# scripts/reporting/html_template.py - Orquestrador de Abas
from datetime import datetime
import json

from .html_helpers import fmt_br, render_table
from .ab0_extracao_modal import render_gear_icon, render_bat_modal, render_bat_modal_scripts
from .ab1_painel import render_tab_painel
from .ab2_governanca import render_tab_gov, render_allocation_summary
from .ab3_cenarios import render_tab_apppoints
from .ab5_plano_acao import render_tab_tabela
from .ab6_peak import render_tab_peak
from .ab7_saneamento import render_tab_saneamento, render_tab_saneamento_scripts
from .ab8_migracao import render_tab_migracao, render_tab_migracao_scripts, render_allocation_detail
from .ab9_seguranca import render_tab_seguranca, render_tab_seguranca_scripts


def _render_styles():
    """Returns the CSS styles for the report."""
    return """
    <style>
        /* ============================================================
           DESIGN SYSTEM - Variáveis Globais
           ============================================================ */
        :root {
            --primary: #0f172a;
            --secondary: #1e293b;
            --accent: #2563eb;
            --bg: #f1f5f9;
            --card-bg: #ffffff;
            --text: #334155;
            --text-light: #64748b;
            --border: #e2e8f0;
            --danger: #dc2626;
            --danger-bg: #fef2f2;
            --warning: #d97706;
            --warning-bg: #fffbeb;
            --success: #059669;
            --success-bg: #f0fdf4;
            --neutral: #64748b;
            --neutral-bg: #f8fafc;
            --radius: 8px;
            --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-lg: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1);
        }

        * { box-sizing: border-box; }

        body {
            font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
            margin: 0;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            font-size: 14px;
        }

        /* ============================================================
           TOPBAR & TABS
           ============================================================ */
        .topbar {
            background: var(--primary);
            color: white;
            padding: 1.25rem 2rem;
            box-shadow: var(--shadow-lg);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .topbar h1 { margin: 0; font-size: 1.5rem; font-weight: 600; letter-spacing: -0.3px; }
        .topbar p { margin: 0.15rem 0 0; color: #94a3b8; font-size: 0.85rem; }

        .tabs {
            background: var(--secondary);
            padding: 0 2rem;
            display: flex;
            gap: 0.25rem;
            overflow-x: auto;
            white-space: nowrap;
        }
        .tab-button {
            background: none;
            border: none;
            color: #94a3b8;
            padding: 0.85rem 1.25rem;
            cursor: pointer;
            font-size: 0.9rem;
            border-bottom: 3px solid transparent;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .tab-button:hover { color: #e2e8f0; background: rgba(255,255,255,0.05); }
        .tab-button.active { color: white; border-bottom-color: var(--accent); }

        /* ============================================================
           LAYOUT
           ============================================================ */
        .container { max-width: 1400px; margin: 0 auto; padding: 1.5rem; }
        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.25s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

        /* ============================================================
           CARDS
           ============================================================ */
        .card {
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .card-header {
            margin: 0 0 1rem;
            border-bottom: 2px solid var(--border);
            padding-bottom: 0.75rem;
            color: var(--secondary);
            font-size: 1.2rem;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* ============================================================
           STATS GRID
           ============================================================ */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .stat-card {
            background: var(--neutral-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.25rem 1rem;
            text-align: center;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
        .stat-value { font-size: 2rem; font-weight: 700; color: var(--primary); margin-bottom: 0.15rem; }
        .stat-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--secondary); font-weight: 700; margin-bottom: 0.25rem; }
        .stat-subtitle { font-size: 0.7rem; color: var(--text-light); line-height: 1.3; }

        .border-danger { border-bottom: 3px solid var(--danger); }
        .border-warning { border-bottom: 3px solid var(--warning); }
        .border-accent { border-bottom: 3px solid var(--accent); }
        .border-success { border-bottom: 3px solid var(--success); }
        .border-neutral { border-bottom: 3px solid var(--neutral); }
        .border-primary { border-bottom: 3px solid var(--primary); }
        .border-secondary { border-bottom: 3px solid var(--secondary); }
        .stat-card-warning { border-bottom: 3px solid var(--warning); }
        .stat-card-danger { border-bottom: 3px solid var(--danger); }

        /* ============================================================
           TEXTO DE APOIO EM CARDS (descrição breve / rodapé)
           ============================================================ */
        .card-desc { color: var(--text-light); font-size: 0.85rem; margin: 0 0 1rem; line-height: 1.5; }
        .card-footnote { color: var(--text-light); font-size: 0.78rem; margin: 0.75rem 0 0; }

        /* ============================================================
           FILTROS DE ESCOPO (radio) — usados em várias abas
           ============================================================ */
        .filter-bar {
            display: flex; gap: 1.25rem; flex-wrap: wrap; align-items: center;
            padding: 0.65rem 1rem; background: var(--neutral-bg); border: 1px solid var(--border);
            border-radius: var(--radius); margin-bottom: 1rem;
        }
        .filter-bar-label { font-weight: 600; color: var(--secondary); font-size: 0.85rem; }
        .radio-label { display: flex; align-items: center; gap: 0.4rem; cursor: pointer; font-size: 0.85rem; color: var(--text); }

        .alert-inline {
            margin-top: 1rem; padding: 0.6rem; background: var(--danger-bg); color: var(--danger);
            font-weight: 600; border: 1px solid var(--danger); border-radius: 6px; font-size: 0.9rem; text-align: center;
        }

        /* ============================================================
           TABLES
           ============================================================ */
        .table-responsive {
            overflow-x: auto;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            max-height: 480px;
            overflow-y: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.85rem;
        }
        th {
            background: #f1f5f9;
            color: var(--secondary);
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            padding: 12px 14px;
            border-bottom: 2px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 10;
            white-space: nowrap;
        }
        td {
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }
        tbody tr:hover { background: #f8fafc; }
        tbody tr:last-child td { border-bottom: none; }

        /* ============================================================
           BADGES - Design System Unificado
           ============================================================ */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 5px;
            font-size: 0.7rem;
            font-weight: 700;
            text-align: center;
            color: #ffffff;
            min-width: 70px;
            letter-spacing: 0.2px;
            line-height: 1.4;
        }
        .badge-danger { background: var(--danger); }
        .badge-warning { background: var(--warning); }
        .badge-medium { background: var(--accent); }
        .badge-success { background: var(--success); }
        .badge-neutral { background: var(--neutral); }
        .badge-critical { background: #b91c1c; }

        /* ============================================================
           SEARCH & FILTERS
           ============================================================ */
        .search-container {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
            background: #f8fafc;
            padding: 1rem 1.25rem;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            align-items: center;
        }
        .search-bar {
            flex: 1;
            min-width: 200px;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.9rem;
            background: white;
            transition: border-color 0.2s;
        }
        .search-bar:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
        .filter-select {
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.9rem;
            background: white;
            min-width: 160px;
            cursor: pointer;
        }
        .btn-export {
            background: var(--success);
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-export:hover { background: #047857; }

        /* ============================================================
           CHARTS
           ============================================================ */
        .charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }
        .chart-box { height: 300px; display: flex; justify-content: center; align-items: center; background: white; border-radius: var(--radius); border: 1px solid var(--border); padding: 1rem; }

        /* ============================================================
           SIMULATOR (Aba 3)
           ============================================================ */
        .simulator-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.25rem; align-items: stretch; }
        .simulator-inputs { background: white; padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); }
        .simulator-total { background: white; padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); text-align: center; display: flex; flex-direction: column; justify-content: center; }
        .simulator-chart { background: white; padding: 1rem; border-radius: var(--radius); border: 1px solid var(--border); height: 280px; }

        .preset-btn-group { display: flex; flex-direction: column; gap: 0.5rem; }
        .preset-btn {
            background: white;
            border: 1px solid var(--border);
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            color: var(--secondary);
            transition: all 0.2s;
            text-align: left;
        }
        .preset-btn:hover { background: #f1f5f9; border-color: var(--accent); }
        .preset-btn.active { background: var(--accent); color: white; border-color: var(--accent); }
        .preset-btn p { margin: 2px 0 0; font-size: 0.75rem; font-weight: normal; opacity: 0.8; }

        .calc-input-group {
            margin-bottom: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 0.5rem;
        }
        .calc-input-group label { font-weight: 600; color: var(--text); font-size: 0.9rem; }
        .calc-input-group input {
            width: 100px;
            padding: 6px 8px;
            border: 1px solid var(--border);
            border-radius: 5px;
            font-size: 1rem;
            text-align: center;
            color: var(--primary);
            font-weight: 600;
        }
        .calc-badge-pts { font-size: 0.7rem; background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; margin-left: 6px; }

        /* ============================================================
           TYPE ANALYSIS (Aba 2)
           ============================================================ */
        .type-analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.25rem; margin-top: 1.25rem; }
        .type-card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; }
        .type-card h4 { margin: 0 0 0.75rem; font-size: 1rem; color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
        .env-divergence { margin-bottom: 0.75rem; padding: 0.75rem; background: #f8fafc; border-left: 3px solid var(--warning); border-radius: 4px; }
        .env-header { font-weight: 700; color: var(--primary); margin-bottom: 0.3rem; font-size: 0.85rem; }

        /* ============================================================
           LEGEND / REGRAS
           ============================================================ */
        .legend-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.25rem; }
        .legend-box { background: #f8fafc; padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); }
        .legend-box h3 { margin: 0 0 0.75rem; color: var(--primary); font-size: 0.95rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.4rem; }
        .legend-list { padding-left: 1.1rem; margin: 0; font-size: 0.82rem; color: var(--text); }
        .legend-list li { margin-bottom: 0.4rem; }

        /* ============================================================
           EVENT CARDS (Aba 4)
           ============================================================ */
        .event-card {
            background: var(--warning-bg);
            border: 1px solid #fde68a;
            border-left: 4px solid var(--warning);
            padding: 1rem 1.25rem;
            border-radius: var(--radius);
            margin-bottom: 0.75rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        .event-card:hover { background: #fef3c7; }
        .event-card h4 { margin: 0 0 0.3rem; color: #92400e; font-size: 1rem; }
        .event-card p { margin: 0; font-size: 0.8rem; color: #b45309; }

        /* ============================================================
           ALERT BOX
           ============================================================ */
        .alert-box {
            background: #eff6ff;
            border-left: 4px solid var(--accent);
            padding: 0.75rem 1.25rem;
            border-radius: 6px;
            margin-bottom: 1.5rem;
        }
        .alert-box strong { color: #1e3a8a; font-size: 1rem; }
        .alert-box p { margin: 0; color: #1e40af; }

        /* ============================================================
           ABA 3 - APP POINTS (Override específico)
           ============================================================ */
        #tab-apppoints .preset-btn { min-height: 110px; display: flex; flex-direction: column; justify-content: space-between; }
        #tab-apppoints .preset-btn strong { font-size: 0.95rem; margin-bottom: 0.3rem; display: block; }
        #tab-apppoints .preset-btn p { margin: 0; font-size: 0.8rem; font-weight: normal; opacity: 0.9; line-height: 1.3; flex-grow: 1; }
        #tab-apppoints .simulator-grid { grid-template-columns: 1fr 1fr; }
        #tab-apppoints .simulator-inputs { display: flex; flex-direction: column; gap: 0.5rem; }
        #tab-apppoints .calc-input-group {
            background: white;
            padding: 0.75rem 1rem;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            margin-bottom: 0;
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
        }
        #tab-apppoints .calc-input-group label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0;
            font-weight: 600;
            color: var(--secondary);
            font-size: 0.85rem;
        }
        #tab-apppoints .calc-input-group input {
            width: 100%;
            padding: 0.4rem;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            font-size: 0.9rem;
            text-align: center;
            color: var(--primary);
            font-weight: 600;
        }

        /* ============================================================
           RESPONSIVIDADE
           ============================================================ */
        @media (max-width: 768px) {
            .container { padding: 1rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
            .stat-value { font-size: 1.5rem; }
            .search-container { flex-direction: column; }
            .search-bar { min-width: 100%; }
            .filter-select { min-width: 100%; }
            .simulator-grid { grid-template-columns: 1fr; }
            .topbar { flex-direction: column; text-align: center; gap: 0.5rem; }
            .tabs { padding: 0 1rem; }
            .tab-button { padding: 0.75rem 1rem; font-size: 0.8rem; }
        }
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
        <div style="display:flex; align-items:center; gap:1rem;">
            <p style="text-align: right; color: #cbd5e1;">Gerado em:<br><strong>{datetime.now().strftime("%d/%m/%Y %H:%M")}</strong></p>
            {render_gear_icon()}
        </div>
    </div>
    <div class="tabs">
        <button class="tab-button active" onclick="openTab(event, 'tab-painel')">1. Painel Operacional</button>
        <button class="tab-button" onclick="openTab(event, 'tab-gov')">2. Governança & Saneamento</button>
        <button class="tab-button" onclick="openTab(event, 'tab-seguranca')">3. Segregação de Funções</button>
        <button class="tab-button" onclick="openTab(event, 'tab-saneamento')">4. Saneamento AD</button>
        <button class="tab-button" onclick="openTab(event, 'tab-migracao')">5. Recomendações de Migração</button>
        <button class="tab-button" onclick="openTab(event, 'tab-alloc-detail')">6. Detalhamento de Alocação</button>
        <button class="tab-button" onclick="openTab(event, 'tab-apppoints')">7. Cenários de AppPoints</button>
        <button class="tab-button" onclick="openTab(event, 'tab-peak')">8. Peak Contributors</button>
        <button class="tab-button" onclick="openTab(event, 'tab-tabela')">9. Plano de Ação</button>
    </div>
    """


def _render_scripts(analytics, identity_analytics):
    """Renders the JavaScript for charts and interactivity."""
    scenarios_by_scope_json = json.dumps(analytics.get('scenarios_by_scope', {}))
    points_json = json.dumps(analytics['scenario_points'])
    points_by_scope_json = json.dumps(analytics.get('scenario_points_by_scope', {}))
    ceiling_limit = analytics.get('ceiling_limit', 1200)

    domain_keys = json.dumps(list(identity_analytics['domain_counts'].keys()))
    domain_values = json.dumps(list(identity_analytics['domain_counts'].values()))

    return f"""
    <script>
        const scenariosByScope = {scenarios_by_scope_json};
                const scenarioPoints = {points_json};
        const scenarioPointsByScope = {points_by_scope_json};
        const ceilingLimit = {ceiling_limit};

        let currentScope = 'foresea';  // Estado global do filtro de escopo

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
            if (btnElement) btnElement.classList.add('active');

            const isFactoredScenario = scenarioKey === 'otimizado_p95' || scenarioKey === 'otimizado_p50';
            const physicalCountsKey = isFactoredScenario ? 'otimizado' : scenarioKey;

            // Usa o escopo corrente filtrado.
            // Fallback defensivo para evitar tela vazia quando faltar alguma chave.
            const scopeObj = scenariosByScope[currentScope] || scenariosByScope['foresea'] || scenariosByScope['todos'] || {{}};
            const data = scopeObj[physicalCountsKey] || {{ pA: 0, pC: 0, bA: 0, bC: 0 }};

            const safePA = parseInt(data.pA, 10) || 0;
            const safePC = parseInt(data.pC, 10) || 0;
            const safeBA = parseInt(data.bA, 10) || 0;
            const safeBC = parseInt(data.bC, 10) || 0;

            document.getElementById('inpPremAuth').value = safePA;
            document.getElementById('inpPremConc').value = safePC;
            document.getElementById('inpBaseAuth').value = safeBA;
            document.getElementById('inpBaseConc').value = safeBC;

                        // Regra de exibição:
            // - As-Is / Saneado: total calculado pela composição física do escopo selecionado.
            // - Otimizado P95 / P50: total NEM do escopo selecionado.
            const scopedPoints = scenarioPointsByScope[currentScope] || scenarioPointsByScope['todos'] || scenarioPoints;
            let totalPoints = 0;
            if (scenarioKey === 'otimizado_p95') {{
                totalPoints = Math.round(scopedPoints.p95 || 0);
            }} else if (scenarioKey === 'otimizado_p50') {{
                totalPoints = Math.round(scopedPoints.p50 || 0);
            }} else {{
                totalPoints = (safePA * 5) + (safePC * 15) + (safeBA * 3) + (safeBC * 10);
            }}


            document.getElementById('calcTotalDisplay').innerText = totalPoints.toLocaleString('pt-BR');
            updateCalculatorDisplay(totalPoints);
            updateChartFromInputs();
        }}



        let simChartInstance = null;
        function updateCalculator() {{
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

            if (totalPoints > ceilingLimit) {{
                document.getElementById('calcTotalDisplay').style.color = 'var(--danger)';
                alertEl.style.display = 'block';
                alertEl.innerText = 'TETO EXCEDIDO (>' + ceilingLimit.toLocaleString('pt-BR') + ')';
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
                const matchSearch = row.cells[0].textContent.toUpperCase().includes(input) || row.cells[1].textContent.toUpperCase().includes(input) || row.cells[9].textContent.toUpperCase().includes(input);
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

        // ---- Gráfico + cards + tabela da aba Peak: reativos ao escopo
        // (mesmo seletor de escopo da aba Cenários de AppPoints — pedido do
        // usuário 2026-07-11). Cada escopo recalcula sua PRÓPRIA curva,
        // pico e composição (não é um filtro visual sobre a série de TODOS).
        let peakChartInstance = null;
        function renderPeakChart(scope) {{
            const canvasEl = document.getElementById('peakLineChart');
            if (!canvasEl || typeof peakChartByScope === 'undefined') return;
            const series = peakChartByScope[scope] || peakChartByScope['todos'] || {{labels: [], users: [], points_concurrent: [], points_nem: []}};
            if (peakChartInstance) {{ peakChartInstance.destroy(); }}
            const ctxPeak = canvasEl.getContext('2d');
            peakChartInstance = new Chart(ctxPeak, {{
                type: 'line',
                data: {{
                    labels: series.labels,
                    datasets: [{{
                        label: 'Usuários Simultâneos',
                        data: series.users,
                        borderColor: '#7c3aed',
                        backgroundColor: 'rgba(124, 58, 237, 0.1)',
                        yAxisID: 'y-users',
                        borderWidth: 3,
                        tension: 0.3,
                        unit: 'usuarios'
                    }}, {{
                        label: 'Consumo de AppPoints',
                        data: series.points_concurrent,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        yAxisID: 'y-points',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.3,
                        unit: 'AppPoints'
                    }}, {{
                        label: 'AppPoints NEM',
                        data: series.points_nem,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        yAxisID: 'y-points',
                        borderWidth: 2,
                        tension: 0.3,
                        unit: 'AppPoints'
                    }}]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{ position: 'bottom' }},
                        tooltip: {{
                            position: 'nearest', padding: 10,
                            titleFont: {{ weight: 'bold' }}, bodySpacing: 5,
                            callbacks: {{
                                label: function(ctx) {{
                                    const label = ctx.dataset.label || '';
                                    const unit = ctx.dataset.unit || '';
                                    const value = Number(ctx.parsed.y || 0).toLocaleString('pt-BR');
                                    return label + ': ' + value + ' ' + unit;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{ title: {{ display: true, text: 'Hora do Dia' }} }},
                        'y-users': {{ type: 'linear', position: 'left', beginAtZero: true, title: {{ display: true, text: 'Nº de Usuários Simultâneos', color: '#7c3aed' }} }},
                        'y-points': {{ type: 'linear', position: 'right', beginAtZero: true, title: {{ display: true, text: 'AppPoints Consumidos (NEM)', color: '#ef4444' }}, grid: {{ drawOnChartArea: false }} }}
                    }}
                }}
            }});
        }}

        function renderPeakBreakdownTable(breakdown) {{
            const tbody = document.getElementById('peakBreakdownBody');
            if (!tbody) return;
            if (!breakdown || !breakdown.length) {{
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #64748b; padding: 2rem;">Nenhum contribuidor identificado nesse escopo.</td></tr>';
                return;
            }}
            tbody.innerHTML = breakdown.map(function(b) {{
                const color = peakLicenseBadgeColors[b.license_type] || '#64748b';
                const label = peakLicenseBadgeLabels[b.license_type] || b.license_type;
                const scopeLabel = peakScopeLabels[b.scope] || b.scope;
                return '<tr data-scope="' + b.scope + '">' +
                    '<td>' + scopeLabel + '</td>' +
                    '<td><span style="background:' + color + '; color:white; padding:2px 8px; border-radius:4px; font-size:0.75rem;">' + label + '</span></td>' +
                    '<td style="text-align:right;">' + b.qtd + '</td>' +
                    '<td style="text-align:right;"><strong>' + b.pts + '</strong> pts</td></tr>';
            }}).join('');
        }}

        function updateScopeFilterPeak() {{
            const els = document.getElementsByName('scopeFilterPeak');
            let scope = 'foresea';
            for (let i = 0; i < els.length; i++) {{
                if (els[i].checked) {{ scope = els[i].value; break; }}
            }}
            if (typeof peakStatsByScope === 'undefined') return;
            const s = peakStatsByScope[scope] || peakStatsByScope['todos'];

            renderPeakChart(scope);
            renderPeakBreakdownTable(s.breakdown);

            const setText = (id, val) => {{ const el = document.getElementById(id); if (el) el.innerText = val; }};
            setText('peakCardP50', Math.round(s.p50 || 0).toLocaleString('pt-BR'));
            setText('peakCardP100', Math.round(s.p100 || 0).toLocaleString('pt-BR'));
            setText('peakCardP95', Math.round(s.p95 || 0).toLocaleString('pt-BR'));
            setText('peakCardTime', s.peak_hour || 'N/A');
            setText('peakCardTime2', '(' + (s.peak_hour || 'N/A') + ')');
            setText('peakCardContributors', Number(s.contributors_count || 0).toLocaleString('pt-BR'));
            setText('peakCardScopeLabel1', 'Escopo: ' + (peakScopeLabels[scope] || scope));
            setText('peakContribText', Number(s.contributors_count || 0).toLocaleString('pt-BR') + ' pessoas simultâneas');
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            try {{
                if (typeof peakChartByScope !== 'undefined') {{
                    renderPeakChart('foresea');
                }}
            }} catch(e) {{ console.error('peakLineChart init failed', e); }}

            const initialPoints = Math.round(scenarioPoints.p95);
            document.getElementById('calcTotalDisplay').innerText = initialPoints.toLocaleString('pt-BR');

            loadScenario('otimizado_p95', document.getElementById('btnOtimizado'));
        }});

        // ---- Escopo Filter Toggle (Aba 3) ----
        function updateScopeFilter() {{
            var els = document.getElementsByName('scopeFilter');
            var newScope = 'foresea';
            for (var i = 0; i < els.length; i++) {{
                if (els[i].checked) {{ 
                    newScope = els[i].value; 
                    break; 
                }}
            }}
            
            // Atualiza variável global
            currentScope = newScope;
            
            // Atualiza label de escopo
            const scopeLabelEl = document.getElementById('currentScopeLabel');
            const scopeNames = {{
                foresea: 'FORESEA + PARCEIRO', terceiros: 'TERCEIROS',
                integracao: 'INTEGRAÇÃO (Oracle/Serviço)', todos: 'TODOS',
            }};
            if (scopeLabelEl) {{
                scopeLabelEl.innerText = 'Escopo: ' + (scopeNames[newScope] || 'TODOS');
            }}

            // Card "Cenário Conciliado" acompanha o mesmo escopo selecionado.
            const scopedPointsCard = scenarioPointsByScope[newScope] || scenarioPointsByScope['todos'];
            const setCardText = (id, val) => {{ const el = document.getElementById(id); if (el) el.innerText = val; }};
            setCardText('cardScopedP95', Math.round(scopedPointsCard.p95 || 0).toLocaleString('pt-BR'));
            setCardText('cardScopedP100', Math.round(scopedPointsCard.p100 || 0).toLocaleString('pt-BR'));
            setCardText('cardScopedP95Label', 'P95 — ' + (scopeNames[newScope] || 'TODOS'));
            setCardText('cardScopedConciliados', Number(scopedPointsCard.conciliados || 0).toLocaleString('pt-BR'));
            setCardText('cardScopedTerceiros', '+' + Number(scopedPointsCard.terceiros_ativos || 0).toLocaleString('pt-BR') + ' terceiros ativos');
            setCardText('cardScopedAuthConc', Number(scopedPointsCard.authorized || 0).toLocaleString('pt-BR') + ' / ' + Number(scopedPointsCard.concurrent || 0).toLocaleString('pt-BR'));
            setCardText('cardScopedReserva', Number(scopedPointsCard.reserva_authorized || 0).toLocaleString('pt-BR'));

            console.log("Filtro de escopo alterado para:", newScope);
            
            // Recarrega o cenário atualmente selecionado com novo escopo
            const activeBtn = document.querySelector('.preset-btn.active');
            if (activeBtn) {{
                const scenarioMap = {{
                    'btnAsIs': 'asis',
                    'btnSaneado': 'saneado',
                    'btnOtimizado': 'otimizado_p95',
                    'btnOtimizadoP50': 'otimizado_p50'
                }};
                const scenarioKey = scenarioMap[activeBtn.id] || 'otimizado_p95';
                loadScenario(scenarioKey, activeBtn);
            }} else {{
                loadScenario('otimizado_p95', document.getElementById('btnOtimizado'));
            }}
        }}

    </script>
    """


def render_html(data):
    """
    Orchestrates the rendering of the full HTML report by assembling components from each aba module.
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
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    {_render_styles()}
</head>
<body>
    {_render_header_and_tabs()}
    {render_bat_modal()}
    {render_tab_painel(analytics, identity_analytics)}
    {render_tab_gov(gov_tables, data.get('allocation_data'), data.get('security_audit_data'))}
    {render_tab_seguranca(data.get('security_audit_data'), data.get('group_baseline_data'), data.get('role_standardization_data'))}
    {render_tab_saneamento(data.get('sanity_data'))}
    {render_tab_migracao(data.get('migration_data'), data.get('allocation_data'))}
    {render_allocation_detail(data.get('allocation_data'))}
    {render_tab_apppoints(analytics, data.get('reconciliation_data'))}
    {render_tab_peak(analytics)}
    {render_tab_tabela(app_points_rows)}
    {_render_scripts(analytics, identity_analytics)}
    {render_tab_saneamento_scripts()}
    {render_tab_migracao_scripts()}
    {render_tab_seguranca_scripts()}
    {render_bat_modal_scripts()}
</body>
</html>"""

