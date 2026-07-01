# scripts/reporting/html_template.py - Orquestrador de Abas
from datetime import datetime
import json

from .html_helpers import fmt_br, render_table
from .ab1_painel import render_tab_painel
from .ab2_governanca import render_tab_gov
from .ab3_cenarios import render_tab_apppoints
from .ab4_eventos import render_tab_eventos
from .ab5_plano_acao import render_tab_tabela
from .ab6_peak import render_tab_peak


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
        .stat-value { font-size: 2.2rem; font-weight: 700; color: var(--primary); margin-bottom: 0.2rem; word-break: break-word; }
        .stat-title { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #1e293b; font-weight: 700; margin-bottom: 0.5rem; }
        .stat-subtitle { font-size: 0.75rem; color: #64748b; line-height: 1.2; }
        .border-danger { border-bottom: 4px solid var(--danger); }
        .border-warning { border-bottom: 4px solid var(--warning); }
        .border-accent { border-bottom: 4px solid var(--accent); }
        .border-success { border-bottom: 4px solid var(--success); }
        .border-neutral { border-bottom: 4px solid var(--neutral); }
        .charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 2rem; margin-top: 2rem; }
        .chart-box { height: 320px; display: flex; justify-content: center; align-items: center; background: #ffffff; border-radius: 8px; border: 1px solid var(--border); padding: 1rem; }
        .simulator-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; align-items: stretch; }
        .simulator-inputs { background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); }
        .simulator-total { background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); text-align: center; display: flex; flex-direction: column; justify-content: center; }
        .simulator-chart { background: white; padding: 1rem; border-radius: 8px; border: 1px solid var(--border); height: 300px; }
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
        .calc-input-group input { width: 120px; padding: 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 1.1rem; text-align: center; color: var(--primary); font-weight: bold; }
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


def _render_scripts(analytics, identity_analytics):
    """Renders the JavaScript for charts and interactivity."""
    scenarios_by_scope_json = json.dumps(analytics.get('scenarios_by_scope', {}))
    points_json = json.dumps(analytics['scenario_points'])
    ceiling_limit = analytics.get('ceiling_limit', 1200)
    domain_keys = json.dumps(list(identity_analytics['domain_counts'].keys()))
    domain_values = json.dumps(list(identity_analytics['domain_counts'].values()))

    return f"""
    <script>
        const scenariosByScope = {scenarios_by_scope_json};
        const scenarioPoints = {points_json};
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
            if(btnElement) btnElement.classList.add('active');
            
            const isFactoredScenario = scenarioKey === 'otimizado_p95' || scenarioKey === 'otimizado_p50';
            const physicalCountsKey = isFactoredScenario ? 'otimizado' : scenarioKey;
            
            // Usa o escopo corrente filtrado
            const data = scenariosByScope[currentScope][physicalCountsKey];

            document.getElementById('inpPremAuth').value = data.pA;
            document.getElementById('inpPremConc').value = data.pC;
            document.getElementById('inpBaseAuth').value = data.bA;
            document.getElementById('inpBaseConc').value = data.bC;

            // CÁLCULO CORRETO:
            // - AS-IS/SANEADO: Soma de licenças físicas (inventário)
            // - OTIMIZADO P95/P50: NEM real baseado em sessões concorrentes
            let totalPoints = 0;
            if (scenarioKey === 'otimizado_p95') {{
                totalPoints = Math.round(scenarioPoints.p95);  // NEM real (~705)
            }} else if (scenarioKey === 'otimizado_p50') {{
                totalPoints = Math.round(scenarioPoints.p50);  // NEM mediana (~480)
            }} else {{
                // AS-IS ou SANEADO: soma do inventário de licenças
                totalPoints = (data.pA * 5) + (data.pC * 15) + (data.bA * 3) + (data.bC * 10);
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
                alertEl.innerText = '⚠️ TETO EXCEDIDO (>' + ceilingLimit.toLocaleString('pt-BR') + ')';
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

            if (type === 'p50') {{ titleText = "🟢 Cenário Cotidiano (P50)"; description = "Consumo normal em dia comum."; }} 
            else if (type === 'p95') {{ titleText = "🟡 Pico Seguro (P95)"; description = "Consumo elevado dentro do esperado."; }}
            else if (type === 'p100') {{ titleText = "🔴 Emergência Operacional (P100)"; description = "Pico máximo histórico registrado."; }}
            else if (type === 'blackout') {{ titleText = "⚡ Blackout Total (100%)"; description = "Cenário extremo com todos os usuários ativos simultâneos."; }}

            const outBox = document.getElementById('eventOutputBox');
            outBox.innerText = titleText + ': ' + totalPoints.toLocaleString('pt-BR') + ' AppPoints. ' + description;
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
                                'y-points': {{ type: 'linear', position: 'right', beginAtZero: true, title: {{ display: true, text: 'AppPoints Consumidos', color: '#f59e0b' }}, grid: {{ drawOnChartArea: false }} }}
                            }}
                        }}
                    }});
                }}
            }} catch(e) {{ console.error('peakLineChart init failed', e); }}

            const initialPoints = Math.round(scenarioPoints.p95);
            document.getElementById('calcTotalDisplay').innerText = initialPoints.toLocaleString('pt-BR');
            try {{
                const ceilLabel = document.getElementById('eventCeilingLabel');
                if (ceilLabel) ceilLabel.innerText = 'Termômetro de Impacto (Limite: ' + ceilingLimit.toLocaleString('pt-BR') + ')';
            }} catch(e) {{ }}

            loadScenario('otimizado_p95', document.getElementById('btnOtimizado'));
            triggerEventScenario('p95');
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
            if (scopeLabelEl) {{
                if (newScope === 'foresea') {{
                    scopeLabelEl.innerText = 'Escopo: FORESEA + PARCEIRO';
                }} else if (newScope === 'terceiros') {{
                    scopeLabelEl.innerText = 'Escopo: TERCEIROS';
                }} else if (newScope === 'integracao') {{
                    scopeLabelEl.innerText = 'Escopo: INTEGRAÇÃO (Oracle/Serviço)';
                }} else {{
                    scopeLabelEl.innerText = 'Escopo: TODOS';
                }}
            }}
            
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

        // ---- Escopo Filter Toggle (Aba 6) ----
        function updateScopeFilterPeak() {{
            var els2 = document.getElementsByName('scopeFilterPeak');
            var sc2 = 'foresea';
            for (var j = 0; j < els2.length; j++) {{
                if (els2[j].checked) {{ sc2 = els2[j].value; break; }}
            }}
            console.log("Filtro de escopo Peak alterado para:", sc2);
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
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {_render_styles()}
</head>
<body>
    {_render_header_and_tabs()}
    {render_tab_painel(analytics, identity_analytics)}
    {render_tab_gov(gov_tables)}
    {render_tab_apppoints(analytics)}
    {render_tab_eventos(analytics)}
    {render_tab_peak(analytics)}
    {render_tab_tabela(app_points_rows)}
    {_render_scripts(analytics, identity_analytics)}
</body>
</html>"""