# reporting/html_builder.py
from datetime import datetime


def fmt_br(num):
    return f"{num:,.0f}".replace(",", ".")


def render_table(headers, rows, table_id="", extra_class=""):
    html = f'<div class="table-responsive"><table id="{table_id}" class="{extra_class}">\n'
    html += '  <thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead>\n'
    html += '  <tbody>\n'
    for row in rows:
        html += '    <tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>\n'
    html += '  </tbody>\n</table></div>\n'
    return html


def get_recommendation_badge(rec):
    if rec == "INATIVO (>90d)":
        return '<span class="badge badge-neutral">INATIVO (>90d)</span>'
    if rec == "DOWNGRADE_CANDIDATE":
        return '<span class="badge badge-warning">DOWNGRADE</span>'
    if rec == "MOVE_TO_CONCURRENT":
        return '<span class="badge badge-accent">P/ CONCURRENT</span>'
    if rec == "CONFIRMED_AUTHORIZED":
        return '<span class="badge badge-success">CONFIRMADO</span>'
    return '<span>OK</span>'


def build_html_structure(summary, governance, app_points, domains):
    # --- Cálculo de Resumos e Cenários Previsionais de AppPoints ---
    auth_users = summary['app_points_summary']['auth_users']
    conc_users = summary['app_points_summary']['conc_users']
    premium_users = summary['app_points_summary']['premium_users']

    custo_atual = 0
    custo_saneado = 0
    custo_otimizado = 0

    for u in app_points:
        pts = u['APP_POINTS']
        lic = u['LICENSE_MODEL']
        rec = u['OPTIMIZATION_REC']

        # 1. Custo Atual Base (com rácio concurrent assumido)
        val_atual = pts if lic == 'AUTHORIZED' else pts * 0.3
        custo_atual += val_atual

        # 2. Custo Pós-Saneamento (remove inativos > 90d)
        if rec != 'INATIVO (>90d)':
            custo_saneado += val_atual

            # 3. Custo Pós-Otimização
            val_otimizado = val_atual
            if rec == 'DOWNGRADE_CANDIDATE':
                # Simula poupança de Downgrade (ex: de Premium [15] para Base [10])
                if u['ENTITLEMENT'] == 'PREMIUM':
                    pts_novo = 10
                    val_otimizado = pts_novo if lic == 'AUTHORIZED' else pts_novo * 0.3
            elif rec == 'MOVE_TO_CONCURRENT':
                # Move utilizador Authorized para Concurrent (passa a consumir 30%)
                val_otimizado = pts * 0.3

            custo_otimizado += val_otimizado

    # --- Build Governance Table Rows ---
    cross_env_rows = [[f"<strong>{c.get('USERID')}</strong>", c.get('ENV_LIST'), c.get('DISPLAYNAME_LIST'),
                       get_recommendation_badge(c.get('HYPOTHESIS', ''))] for c in governance['cross_env'][:200]]
    login_conflicts_rows = [[f"<strong>{l.get('LOGINID')}</strong>", l.get('USERID_LIST'), l.get('DISPLAYNAME_LIST'),
                             get_recommendation_badge(l.get('MERGE_DECISION', ''))] for l in
                            governance['login_conflicts'][:200]]
    worklist_rows = [[w.get('RAW_ID'), w.get('DISPLAYNAME'), w.get('HYPOTHESIS'), w.get('MERGE_DECISION')] for w in
                     governance['worklist'][:200]]

    title_divergence_html = []
    for div in governance['detailed_divergences'][:30]:
        title = div['title']
        data = div['data']
        alerts = []
        all_types = {t for types in data['types'].values() for t in types if t}
        if len(all_types) > 1: alerts.append('<span class="badge badge-critical">TYPE DIVERGENTE</span>')

        base_groups = next(iter(data['groups'].values()), set())
        if any(s != base_groups for s in data['groups'].values()): alerts.append(
            '<span class="badge badge-high">GRUPOS DIVERGENTES</span>')

        title_divergence_html.append(f'<div class="type-card"><h4>{title} {" ".join(alerts)}</h4>')
        if len(all_types) > 1:
            title_divergence_html.append(
                '<div class="env-divergence"><div class="env-header">⚠️ Inconsistência de TYPE</div>')
            for env, types in sorted(data['types'].items()):
                title_divergence_html.append(f'<div>📍 {env}: {", ".join(sorted(t for t in types if t))}</div>')
            title_divergence_html.append('</div>')
        title_divergence_html.append('</div>')

    # --- Build AppPoints Table ---
    app_points_rows = []
    for s in sorted(app_points, key=lambda x: x['APP_POINTS'], reverse=True)[:500]:
        app_points_rows.append([
            f"<strong>{s['USERID']}</strong>",
            s['DISPLAYNAME'][:30],
            get_recommendation_badge(s['OPTIMIZATION_REC']),
            f"<span class='badge' style='background:#f1f5f9;'>{s['ENTITLEMENT']}</span>",
            f"<span style='font-weight:600;'>{s['LICENSE_MODEL']}</span>",
            f"<strong>{s['APP_POINTS']}</strong>",
            s['LOGIN_COUNT_90D'],
            s['TITLES'][:40] + ("..." if len(s['TITLES']) > 40 else "")
        ])

    # --- Final HTML Assembly ---
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Maximo Unificado</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{ --primary: #0f172a; --secondary: #1e293b; --accent: #2563eb; --bg: #f8fafc; --card-bg: #ffffff; --text: #334155; --border: #e2e8f0; --danger: #ef4444; --warning: #f59e0b; --success: #10b981; --neutral:#64748b}}
        * {{ box-sizing: border-box; }}
        body {{ font-family: "Segoe UI", system-ui, -apple-system, sans-serif; margin: 0; background-color: var(--bg); color: var(--text); line-height: 1.5; }}
        .topbar {{ background: var(--primary); color: white; padding: 1.5rem 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center;}}
        .topbar h1 {{ margin: 0; font-size: 1.8rem; font-weight: 600; letter-spacing: -0.5px; }}
        .topbar p {{ margin: 0; color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem; }}
        .tabs {{ background: var(--secondary); padding: 0 2rem; display: flex; gap: 1rem; }}
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

        .card {{ background: var(--card-bg); border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); border: 1px solid var(--border); padding: 1.8rem; margin-bottom: 2rem; }}
        .card-header {{ margin-top: 0; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border); padding-bottom: 0.75rem; color: var(--secondary); font-size: 1.4rem; font-weight: 600; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
        .card-header:hover {{ color: var(--accent); }}

        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; }}
        .stat-card {{ background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; text-align: center; transition: transform 0.2s; position: relative; }}
        .stat-card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); }}
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

        .table-responsive {{ overflow-x: auto; border-radius: 8px; border: 1px solid var(--border); max-height: 600px; overflow-y: auto; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 14px 16px; border-bottom: 1px solid var(--border); vertical-align: top; word-wrap: break-word; white-space: normal; }}
        th {{ background-color: #f1f5f9; color: #334155; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; position: sticky; top: 0; z-index: 10; }}
        tbody tr:hover {{ background-color: #f8fafc; }}
        tbody tr:last-child td {{ border-bottom: none; }}

        .badge {{ padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: inline-block; text-align: center; }}
        .badge-critical {{ background-color: var(--danger); color: white; }}
        .badge-high {{ background-color: var(--warning); color: white; }}
        .badge-medium {{ background-color: var(--accent); color: white; }}
        .badge-success {{ background-color: var(--success); color: white; }}
        .badge-neutral {{ background-color: var(--neutral); color: white; }}

        .search-container {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #f1f5f9; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); }}
        .search-bar {{ flex-grow: 1; padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; min-width: 250px; }}
        .filter-select {{ padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; background: white; min-width: 200px; }}

        /* Analysis Grid CSS */
        .type-analysis-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }}
        .type-card {{ background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; transition: box-shadow 0.2s; }}
        .type-card:hover {{ box-shadow: 0 4px 8px rgba(0,0,0,0.08); }}
        .type-card h4 {{ margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; display: flex; align-items: center; flex-wrap: wrap; }}
        .env-divergence {{ margin-bottom: 0.8rem; padding: 0.8rem; background: #f8fafc; border-left: 3px solid var(--warning); border-radius: 4px; }}
        .env-header {{ font-weight: 700; color: var(--primary); margin-bottom: 0.4rem; font-size: 0.9rem; }}
        .extra-groups {{ color: #1e40af; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="topbar">
        <div>
            <h1>Dashboard Governança Maximo EAM</h1>
            <p>Saneamento e Planejamento de Licenças MAS 9</p>
        </div>
        <div>
            <p style="text-align: right; color: #cbd5e1;">Atualizado em:<br><strong>{datetime.now().strftime("%d/%m/%Y %H:%M")}</strong></p>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-button active" onclick="openTab(event, 'tab-painel')">1. Painel Operacional</button>
        <button class="tab-button" onclick="openTab(event, 'tab-gov')">2. Governança & Saneamento</button>
        <button class="tab-button" onclick="openTab(event, 'tab-apppoints')">3. Otimização AppPoints</button>
    </div>

    <div id="tab-painel" class="container tab-content active">
        <div class="alert-box">
            <strong>Visão de Negócio — Foco em MAS 9 AppPoints e Identidades Ativas</strong>
            <p>Este Dashboard foca nativamente na visão de contas ativas para mapear o risco real e auxiliar no capacity planning do MAS 9.</p>
        </div>

        <div class="card">
            <h2 class="card-header">Resumo Executivo Operacional</h2>
            <div class="stats-grid">
                <div class="stat-card border-success"><div class="stat-value" style="color: var(--success);">{fmt_br(summary['active_profiles_count'])}</div><div class="stat-title">Pessoas Únicas Ativas</div><div class="stat-subtitle">"Pessoas físicas" projetadas</div></div>
                <div class="stat-card border-warning"><div class="stat-value" style="color: var(--warning);">{fmt_br(summary['title_divergence_count'])}</div><div class="stat-title">Cargos com Divergência</div><div class="stat-subtitle">Requer padronização de perfil</div></div>
                <div class="stat-card border-accent"><div class="stat-value">{fmt_br(len(governance['cross_env']))}</div><div class="stat-title">Riscos de Reuso</div><div class="stat-subtitle">Logins ativos repetidos</div></div>
                <div class="stat-card border-danger"><div class="stat-value" style="color: var(--danger);">{fmt_br(len([w for w in governance['worklist'] if w.get('HYPOTHESIS') == 'CONFIRMED_DIFFERENT_PERSON']))}</div><div class="stat-title">Colisões Críticas</div><div class="stat-subtitle">Nomes diferentes no mesmo login</div></div>
            </div>

            <div class="charts-container" style="grid-template-columns: 1fr 2fr;">
                <div class="chart-box" style="flex-direction: column;">
                    <h3 style="margin-top:0; font-size: 1rem; color: var(--primary);">Distribuição por Domínio</h3>
                    <canvas id="domainChart"></canvas>
                </div>
                <div class="chart-box" style="align-items: flex-start; padding: 2rem;">
                    <div style="width: 100%;">
                        <h3 style="margin-top:0; font-size: 1rem; color: var(--primary);">Entendimento da Segregação</h3>
                        <p style="font-size: 0.9rem; color: var(--text); margin-bottom: 1rem;">
                            A análise foca em segregar os utilizadores que são colaboradores diretos (Foresea) e parceiros integrados, dos terceiros ou temporários, para otimizar o consumo de licenças.
                        </p>
                        <div style="display: flex; justify-content: space-between; padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border);">
                            <div><strong style="color: #10b981; font-size: 1.2rem;">{fmt_br(domains.get('FORESEA', 0))}</strong> <br><span style="font-size: 0.8rem; color: #64748b;">FORESEA</span></div>
                            <div><strong style="color: #2563eb; font-size: 1.2rem;">{fmt_br(domains.get('PARCEIRO', 0))}</strong> <br><span style="font-size: 0.8rem; color: #64748b;">PARCEIROS</span></div>
                            <div><strong style="color: #f59e0b; font-size: 1.2rem;">{fmt_br(domains.get('TERCEIRO', 0))}</strong> <br><span style="font-size: 0.8rem; color: #64748b;">TERCEIROS</span></div>
                            <div><strong style="color: #94a3b8; font-size: 1.2rem;">{fmt_br(domains.get('SEM DOMINIO', 0))}</strong> <br><span style="font-size: 0.8rem; color: #64748b;">S/ DOMÍNIO</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="tab-gov" class="container tab-content">
        <div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">
            <h3 style="margin-top: 0; color: var(--primary);">🔍 Filtro Interativo (Aplica-se às tabelas abaixo)</h3>
            <div class="search-container">
                <input type="text" id="searchInput" class="search-bar" onkeyup="filterTable()" placeholder="Pesquisar por ID, Nome, Email...">
                <select id="statusFilter" class="filter-select" onchange="filterTable()">
                    <option value="ACTIVE" selected>🟢 Somente Ativos</option>
                    <option value="">🟢/🔴 Todos os Status</option>
                    <option value="INACTIVE">🔴 Inativos</option>
                </select>
                <select id="decFilter" class="filter-select" onchange="filterTable()">
                    <option value="">⚖️ Todas as Decisões / Hipóteses</option>
                    <option value="PESSOAS DIFERENTES">🔴 PESSOAS DIFERENTES</option>
                    <option value="REQUER REVISÃO">🟡 REQUER REVISÃO</option>
                    <option value="POSSÍVEL MESMA PESSOA">🟢 POSSÍVEL MESMA PESSOA</option>
                </select>
            </div>
        </div>

        <div class="card">
            <h2 class="card-header">Amostra 1: Cargos com Divergência de Perfil (Fase 2)</h2>
            <div class="type-analysis-grid">
                {''.join(title_divergence_html)}
            </div>
        </div>

        <div class="card">
            <h2 class="card-header">Amostra 2: Reuso de USERID (Multi-Ambiente)</h2>
            {render_table(['USERID', 'Bases Encontradas', 'Nomes de Exibição', 'Conclusão', 'Ação'], cross_env_rows, 'table-cross-env', 'filterable-table')}
        </div>

        <div class="card">
            <h2 class="card-header">Amostra 3: Conflitos de LOGINID (AD)</h2>
            {render_table(['LOGINID AD', 'Bases', 'USERIDs', 'Nomes', 'Ação Recomendada'], login_conflicts_rows, 'table-login-conflicts', 'filterable-table')}
        </div>

        <div class="card">
            <h2 class="card-header">Amostra 4: Fila de Saneamento Completa</h2>
            {render_table(['ID Bruto', 'Nome', 'Email/Login', 'Tipo Colisão', 'Hipótese', 'Ação'], worklist_rows, 'table-worklist', 'filterable-table')}
        </div>
    </div>

    <div id="tab-apppoints" class="container tab-content">
        <div class="alert-box" style="border-left-color: var(--success); background-color: #ecfdf5;">
            <strong>🎯 Meta: Otimização de Licenciamento MAS 9 (Foresea e Parceiros)</strong>
            <p>Os cenários previsionais abaixo quantificam o potencial de poupança (AppPoints diários) entre o "As-Is", a limpeza de inativos e a aplicação das recomendações da inteligência (Downgrades e migração para o modelo Concurrent com rácio de 30%).</p>
        </div>

        <div class="card">
            <h2 class="card-header">Cenários Previsionais de Uso (AppPoints)</h2>
            <div class="stats-grid">
                <div class="stat-card border-danger">
                    <div class="stat-value" style="color: var(--danger);">{fmt_br(custo_atual)}</div>
                    <div class="stat-title">Cenário Atual Bruto</div>
                    <div class="stat-subtitle">Soma base do parque atual</div>
                </div>
                <div class="stat-card border-warning">
                    <div class="stat-value" style="color: var(--warning);">{fmt_br(custo_saneado)}</div>
                    <div class="stat-title">Pós-Saneamento</div>
                    <div class="stat-subtitle">Limpeza de utilizadores Inativos</div>
                </div>
                <div class="stat-card border-success">
                    <div class="stat-value" style="color: var(--success);">{fmt_br(custo_otimizado)}</div>
                    <div class="stat-title">Pós-Otimização</div>
                    <div class="stat-subtitle">Regras de Downgrade + Concurrent</div>
                </div>
            </div>
        </div>

        <div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">
            <h3 style="margin-top: 0; color: var(--primary);">🔍 Filtros de Licenciamento</h3>
            <div class="search-container">
                <input type="text" id="searchAppPoints" class="search-bar" onkeyup="filterAppPoints()" placeholder="Pesquisar por ID, Nome, Cargo...">
                <select id="filterEntitlement" class="filter-select" onchange="filterAppPoints()">
                    <option value="">🔰 Todos os Entitlements</option>
                    <option value="PREMIUM">PREMIUM</option>
                    <option value="BASE">BASE</option>
                    <option value="LIMITED">LIMITED</option>
                    <option value="SELF FREE">SELF FREE</option>
                </select>
                <select id="filterLicense" class="filter-select" onchange="filterAppPoints()">
                    <option value="">🔑 Todos os Tipos de Licença</option>
                    <option value="AUTHORIZED">AUTHORIZED</option>
                    <option value="CONCURRENT">CONCURRENT</option>
                </select>
                <select id="filterRec" class="filter-select" onchange="filterAppPoints()">
                    <option value="">💡 Todas as Recomendações</option>
                    <option value="OK">OK</option>
                    <option value="INATIVO">Inativo (>90d)</option>
                    <option value="DOWNGRADE">Downgrade Candidate</option>
                    <option value="P/ CONCURRENT">Move to Concurrent</option>
                    <option value="CONFIRMADO">Confirmado Authorized</option>
                </select>
            </div>
        </div>

        <div class="card">
            <h2 class="card-header">Detalhes da Simulação (Top 500 Maior Custo)</h2>
            {render_table(['USERID', 'Nome', 'Recomendação', 'Entitlement', 'Licença', 'Custo', 'Logins 90d', 'Cargos'], app_points_rows, 'table-apppoints', 'filterable-table')}
        </div>
    </div>

    <script>
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

        // Filtro Geral da Tab de Governança
        function filterTable() {{
            var input = document.getElementById("searchInput").value.toUpperCase();
            var statusFilter = document.getElementById("statusFilter").value.toUpperCase();
            var decFilter = document.getElementById("decFilter").value.toUpperCase();

            var tables = document.querySelectorAll("#tab-gov .filterable-table");
            tables.forEach(function(table) {{
                var tr = table.getElementsByTagName("tr");
                for (var i = 1; i < tr.length; i++) {{
                    var rowText = tr[i].textContent || tr[i].innerText;
                    var matchInput = input === "" || rowText.toUpperCase().indexOf(input) > -1;

                    var statusSpan = tr[i].querySelector('.status-data');
                    var statusContent = statusSpan ? statusSpan.innerText.toUpperCase() : "";
                    var matchStatus = true;
                    if (statusFilter !== "") {{
                        if (statusFilter === "ACTIVE") matchStatus = statusContent.indexOf("ACTIVE") > -1;
                        else if (statusFilter === "INACTIVE") matchStatus = statusContent.indexOf("ACTIVE") === -1;
                    }}
                    var matchDec = decFilter === "" || rowText.toUpperCase().indexOf(decFilter) > -1;
                    tr[i].style.display = (matchInput && matchStatus && matchDec) ? "" : "none";
                }}
            }});
        }}

        // Novo Filtro Específico para a Tab AppPoints
        function filterAppPoints() {{
            var input = document.getElementById("searchAppPoints").value.toUpperCase();
            var entFilter = document.getElementById("filterEntitlement").value.toUpperCase();
            var licFilter = document.getElementById("filterLicense").value.toUpperCase();
            var recFilter = document.getElementById("filterRec").value.toUpperCase();

            var table = document.getElementById("table-apppoints");
            if(!table) return;
            var tr = table.getElementsByTagName("tr");

            for (var i = 1; i < tr.length; i++) {{
                // Colunas específicas: 0(ID), 1(Nome), 2(Recomendação), 3(Entitlement), 4(Licença), 7(Cargos)
                var tdNameTitle = tr[i].cells[0].textContent + " " + tr[i].cells[1].textContent + " " + tr[i].cells[7].textContent;
                var tdRec = tr[i].cells[2].textContent.toUpperCase();
                var tdEnt = tr[i].cells[3].textContent.toUpperCase();
                var tdLic = tr[i].cells[4].textContent.toUpperCase();

                var matchSearch = input === "" || tdNameTitle.toUpperCase().indexOf(input) > -1;
                var matchEnt = entFilter === "" || tdEnt.indexOf(entFilter) > -1;
                var matchLic = licFilter === "" || tdLic.indexOf(licFilter) > -1;
                var matchRec = recFilter === "" || tdRec.indexOf(recFilter) > -1;

                tr[i].style.display = (matchSearch && matchEnt && matchLic && matchRec) ? "" : "none";
            }}
        }}

        const domainLabels = {list(domains.keys())};
        const domainValues = {list(domains.values())};
        new Chart(document.getElementById('domainChart'), {{
            type: 'doughnut',
            data: {{
                labels: domainLabels,
                datasets: [{{
                    data: domainValues,
                    backgroundColor: ['#10b981', '#2563eb', '#f59e0b', '#94a3b8'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: {{ legend: {{ position: 'right' }} }} }}
        }});
    </script>
</body>
</html>"""