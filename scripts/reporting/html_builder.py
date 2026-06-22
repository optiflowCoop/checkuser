# scripts/reporting/html_builder.py
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
    # --- Cálculo de Resumos e Cenários Previsionais ---
    custo_atual = 0
    custo_saneado = 0
    custo_otimizado_p95 = 0
    inativos_count = 0
    downgrade_count = 0
    concurrent_count = 0

    # Contadores físicos para o simulador
    final_prem_auth = 0
    final_prem_conc_users = 0
    final_base_auth = 0
    final_base_conc_users = 0

    # Fatores estatísticos reais extraídos do logintracking
    sum_p50 = 0
    sum_p95 = 0
    sum_p100 = 0
    count_conc = 0

    for u in app_points:
        pts = u['APP_POINTS']
        lic = u['LICENSE_MODEL']
        ent = u['ENTITLEMENT']
        rec = u['OPTIMIZATION_REC']

        f_p50 = u.get('FACTOR_P50', 0.33)
        f_p95 = u.get('FACTOR_P95', 0.50)
        f_p100 = u.get('FACTOR_P100', 0.85)

        # 1. Custo Atual Bruto (Antes do Saneamento)
        val_atual = pts if lic == 'AUTHORIZED' else pts * f_p95
        custo_atual += val_atual

        if rec == 'INATIVO (>90d)':
            inativos_count += 1
            continue

        if rec == 'DOWNGRADE_CANDIDATE': downgrade_count += 1
        if rec == 'MOVE_TO_CONCURRENT': concurrent_count += 1

        # Custo Pós-Saneamento básico
        custo_saneado += val_atual

        # Perfil Destino Otimizado (To-Be)
        final_ent = 'BASE' if (rec == 'DOWNGRADE_CANDIDATE' and ent == 'PREMIUM') else ent
        final_lic = 'CONCURRENT' if rec == 'MOVE_TO_CONCURRENT' else lic

        if final_ent == 'PREMIUM':
            pts_novo = 5 if final_lic == 'AUTHORIZED' else 15
        else:
            pts_novo = 3 if final_lic == 'AUTHORIZED' else 10

        # Acumula baldes físicos e fatores
        if final_lic == 'AUTHORIZED':
            if final_ent == 'PREMIUM':
                final_prem_auth += 1
            else:
                final_base_auth += 1
        else:
            if final_ent == 'PREMIUM':
                final_prem_conc_users += 1
            else:
                final_base_conc_users += 1
            sum_p50 += f_p50
            sum_p95 += f_p95
            sum_p100 += f_p100
            count_conc += 1

    # Médias estatísticas da base real da Foresea para alimentar o JS
    avg_f_p50 = (sum_p50 / count_conc) if count_conc > 0 else 0.25
    avg_f_p95 = (sum_p95 / count_conc) if count_conc > 0 else 0.45
    avg_f_p100 = (sum_p100 / count_conc) if count_conc > 0 else 0.75

    # --- Construção das Linhas das Tabelas de Governança ---
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

    # --- Construção da Tabela Completa de Licenciamento ---
    app_points_rows = []
    for s in sorted(app_points, key=lambda x: x['APP_POINTS'], reverse=True)[:1000]:
        fator_display = f"Med: {s.get('FACTOR_P50', 0) * 100:.0f}% | Pico: {s.get('FACTOR_P95', 0) * 100:.0f}%" if s[
                                                                                                                       'LICENSE_MODEL'] == 'CONCURRENT' else "100% Fixo (Prioritário)"
        app_points_rows.append([
            f"<strong>{s['USERID']}</strong>",
            s['DISPLAYNAME'][:30],
            get_recommendation_badge(s['OPTIMIZATION_REC']),
            f"<span class='badge' style='background:#f1f5f9; color:var(--primary);'>{s['ENTITLEMENT']}</span>",
            f"<strong>{s['LICENSE_MODEL']}</strong>",
            f"<strong>{s['APP_POINTS']}</strong>",
            f"<span style='color:var(--accent); font-weight:600;'>{fator_display}</span>",
            s['LOGIN_COUNT_90D'],
            s['TITLES'][:40]
        ])

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

        .card {{ background: var(--card-bg); border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid var(--border); padding: 1.8rem; margin-bottom: 2rem; }}
        .card-header {{ margin-top: 0; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border); padding-bottom: 0.75rem; color: var(--secondary); font-size: 1.4rem; font-weight: 600; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}

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

        .search-container {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #f1f5f9; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); align-items: center; }}
        .search-bar {{ flex-grow: 1; padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; min-width: 250px; }}
        .filter-select {{ padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; background: white; min-width: 180px; }}

        .btn-export {{ background-color: #10b981; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-size: 0.95rem; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: background 0.2s; }}
        .btn-export:hover {{ background-color: #059669; }}

        .calc-input-group {{ margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed var(--border); padding-bottom: 0.5rem; }}
        .calc-input-group label {{ font-weight: 600; color: var(--text); font-size: 0.95rem; }}
        .calc-input-group input {{ width: 100px; padding: 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 1.1rem; text-align: center; color: var(--primary); font-weight: bold; }}
        .calc-badge-pts {{ font-size: 0.75rem; background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; margin-left: 8px; }}
        .financial-box {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 1rem; text-align: center; margin-top: 1rem; }}
        .financial-value {{ font-size: 1.8rem; font-weight: 800; color: #047857; margin: 0.5rem 0; }}

        .legend-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
        .legend-box {{ background: #f8fafc; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
        .legend-box h3 {{ margin-top: 0; color: var(--primary); font-size: 1.05rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 6px;}}
        .legend-list {{ padding-left: 1.2rem; margin-bottom: 0; font-size: 0.88rem; color: var(--text); }}
        .legend-list li {{ margin-bottom: 0.6rem; }}

        .type-analysis-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }}
        .type-card {{ background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; }}
        .env-divergence {{ margin-bottom: 0.8rem; padding: 0.8rem; background: #f8fafc; border-left: 3px solid var(--warning); border-radius: 4px; }}
        .env-header {{ font-weight: 700; color: var(--primary); margin-bottom: 0.4rem; font-size: 0.9rem; }}

        /* Event Simulator Specific CSS */
        .event-card {{ background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid var(--warning); padding: 1.2rem; border-radius: 8px; margin-bottom: 1rem; cursor: pointer; transition: background 0.2s; }}
        .event-card:hover {{ background: #fef08a; }}
        .event-card h4 {{ margin: 0 0 0.4rem 0; color: #92400e; font-size: 1.1rem; }}
        .event-card p {{ margin: 0; font-size: 0.85rem; color: #b45309; }}
    </style>
</head>
<body>
    <div class="topbar">
        <div>
            <h1>Dashboard Governança Maximo EAM | Foresea</h1>
            <p>Saneamento de Identidades, Fatores Estatísticos de Escala e Capacity Planning MAS 9.1</p>
        </div>
        <div>
            <p style="text-align: right; color: #cbd5e1;">Mapeamento Técnico de Produção:<br><strong>{datetime.now().strftime("%d/%m/%Y %H:%M")}</strong></p>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-button active" onclick="openTab(event, 'tab-painel')">1. Painel Operacional</button>
        <button class="tab-button" onclick="openTab(event, 'tab-gov')">2. Governança & Saneamento</button>
        <button class="tab-button" onclick="openTab(event, 'tab-apppoints')">3. Otimização AppPoints & ROI</button>
        <button class="tab-button" onclick="openTab(event, 'tab-eventos')" style="color:var(--warning); font-weight:700;">4. Simulador de Eventos Críticos</button>
    </div>

    <div id="tab-painel" class="container tab-content active">
        <div class="alert-box">
            <strong>Visão de Negócio — Foco em MAS 9 AppPoints e Identidades Ativas</strong>
            <p>Este Dashboard consolida os dados das 7 bases operacionais (Sondas + Onshore) para mapear o risco real e auxiliar no planejamento de capacidade.</p>
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
                            A análise segrega os utilizadores que são colaboradores diretos (Foresea) e parceiros integrados, dos terceiros ou temporários, para otimizar o consumo de licenças.
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
            <h3 style="margin-top: 0; color: var(--primary);">🔍 Filtro Interativo de Governança</h3>
            <div class="search-container">
                <input type="text" id="searchInput" class="search-bar" onkeyup="filterTable()" placeholder="Pesquisar por ID, Nome, Email...">
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
            {render_table(['USERID', 'Bases Encontradas', 'Nomes de Exibição', 'Conclusão'], cross_env_rows, 'table-cross-env', 'filterable-table')}
        </div>

        <div class="card">
            <h2 class="card-header">Amostra 3: Conflitos de LOGINID (AD)</h2>
            {render_table(['LOGINID AD', 'Bases', 'USERIDs', 'Nomes'], login_conflicts_rows, 'table-login-conflicts', 'filterable-table')}
        </div>

        <div class="card">
            <h2 class="card-header">Amostra 4: Fila de Saneamento Completa</h2>
            {render_table(['ID Bruto', 'Nome', 'Hipótese', 'Ação Recomendada'], worklist_rows, 'table-worklist', 'filterable-table')}
        </div>
    </div>

    <div id="tab-apppoints" class="container tab-content">

        <div class="card" style="border-left: 4px solid var(--success); background-image: linear-gradient(to right, #ffffff, #f8fafc);">
            <h2 class="card-header" style="border:none; margin-bottom:0.5rem; color:var(--success);">🧮 Simulador Gerencial de Custos (Estimativa Opex)</h2>
            <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 300px; background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border);">
                    <div style="margin-bottom: 1rem;">
                        <label style="font-weight: bold; color: var(--primary);">💵 Valor Estimado por AppPoint/Ano:</label>
                        <input type="number" id="inpCustoUnitario" value="500" min="0" oninput="updateCalculator()" style="width: 100%; padding: 8px; margin-top: 4px; font-weight: bold; border: 1px solid var(--border); border-radius: 6px;">
                    </div>
                    <div class="calc-input-group"><label>Premium Authorized</label><input type="number" id="inpPremAuth" value="{final_prem_auth}" oninput="updateCalculator()"></div>
                    <div class="calc-input-group"><label>Premium Concurrent</label><input type="number" id="inpPremConc" value="{int(final_prem_conc_users * avg_f_p95)}" oninput="updateCalculator()"></div>
                    <div class="calc-input-group"><label>Base Authorized</label><input type="number" id="inpBaseAuth" value="{final_base_auth}" oninput="updateCalculator()"></div>
                    <div class="calc-input-group" style="border:none;"><label>Base Concurrent</label><input type="number" id="inpBaseConc" value="{int(final_base_conc_users * avg_f_p95)}" oninput="updateCalculator()"></div>
                </div>
                <div style="flex: 1; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                    <h3 style="margin: 0; font-size: 1rem; color: var(--secondary);">AppPoints Simulados</h3>
                    <div id="calcTotalDisplay" style="font-size: 4rem; font-weight: 800; color: var(--success);">0</div>
                    <div class="financial-box">
                        <div style="font-size: 0.85rem; font-weight: bold; color: #065f46;">Custo Anual de Contrato Projetado</div>
                        <div id="calcFinancialTotal" class="financial-value">$ 0</div>
                    </div>
                    <div id="calcAlertBox" style="margin-top: 1rem; padding: 0.5rem; background: var(--danger); color:white; font-weight:bold; border-radius:6px; display:none;">⚠️ TETO EXCEDIDO (>1200)</div>
                </div>
                <div style="flex: 1; min-width: 300px; height: 260px;"><canvas id="simChart"></canvas></div>
            </div>
        </div>

        <div class="card" style="border-top: 4px solid var(--primary);">
            <h2 class="card-header" style="border:none; margin-bottom:0.5rem;">🧠 Motor de Decisão: Critérios de Classificação</h2>
            <div class="legend-grid">
                <div class="legend-box" style="border-left: 3px solid #1e3a8a;">
                    <h3>🔰 Nível de Acesso (Entitlement)</h3>
                    <ul class="legend-list">
                        <li><strong>PREMIUM (5 ou 15 pts):</strong> Exigido para qualquer utilizador que aceda a módulos de <b>Óleo & Gás (Foresea)</b> como PTW, HSE, Drilling e Asset contextuais.</li>
                        <li><strong>BASE (3 ou 10 pts):</strong> Perfis de manutenção e supply padrão (Almoxarifado, PCM, O.S.).</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid #f59e0b;">
                    <h3>🔑 Modelo (Auth vs Conc)</h3>
                    <ul class="legend-list">
                        <li><strong>AUTHORIZED (Fixo):</strong> Alocado a <b>Funções Críticas e Liderança</b> (Supervisores, Almoxarifes, Planners, Engenheiros) com garantia de acesso 24/7.</li>
                        <li><strong>CONCURRENT (Escala):</strong> Aplicado ao grosso do time operacional <b>Offshore</b>. A concorrência é calculada com base nos picos do <i>logintracking</i>.</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid #64748b;">
                    <h3>📊 Pesos Oficiais MAS 9</h3>
                    <table style="width:100%; font-size:0.8rem; border-collapse:collapse; background:white; margin-top:0.5rem;">
                        <tr style="background:#f1f5f9;"><th style="padding:4px;">Camada</th><th style="padding:4px;">Authorized</th><th style="padding:4px;">Concurrent</th></tr>
                        <tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:4px;"><b>Premium</b></td><td style="padding:4px; font-weight:bold;">5 pts</td><td style="padding:4px; font-weight:bold;">15 pts</td></tr>
                        <tr><td style="padding:4px;"><b>Base</b></td><td style="padding:4px;">3 pts</td><td style="padding:4px;">10 pts</td></tr>
                    </table>
                </div>
            </div>
        </div>

        <div class="card">
            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: var(--primary);">📋 Plano de Ação Contractual</h3>
                <button class="btn-export" onclick="exportTableToCSV('table-apppoints', 'Plano_Acao_Licenciamento_Foresea.csv')">Exportar CSV</button>
            </div>
            <div class="search-container">
                <input type="text" id="searchAppPoints" class="search-bar" onkeyup="filterAppPoints()" placeholder="Pesquisar por ID, Nome, Cargo...">
                <select id="filterRec" class="filter-select" onchange="filterAppPoints()">
                    <option value="">💡 Filtrar Ação</option>
                    <option value="INATIVO">🔴 Inativos (>90d)</option>
                    <option value="DOWNGRADE">🟡 Requer Downgrade</option>
                    <option value="P/ CONCURRENT">🔵 Escala Offshore (Concurrent)</option>
                    <option value="CONFIRMADO">🟢 Autorizado Fixo (Authorized)</option>
                </select>
            </div>
            {render_table(['USERID', 'Nome', 'Recomendação', 'Entitlement', 'Modelo Licença', 'Pontos', 'Métrica Concorrência', 'Logins 90d', 'Cargo'], app_points_rows, 'table-apppoints', 'filterable-table')}
        </div>
    </div>

    <div id="tab-eventos" class="container tab-content">
        <div class="alert-box" style="background: #fffbeb; border-left-color: var(--warning);">
            <strong style="color:#92400e;">⚠️ Módulo de Estresse e Simulação de Eventos Simultâneos</strong>
            <p style="color:#b45309;">Simule cenários atípicos na operação da Foresea. O que acontece com o consumo de AppPoints se houver um evento crítico e múltiplos profissionais precisarem de se logar ao mesmo tempo nas sondas?</p>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem;">
            <div>
                <div class="card">
                    <h3 style="margin-top:0; font-size:1.1rem; color:var(--primary);">🚀 Disparadores de Eventos (Gatilhos)</h3>

                    <div class="event-card" onclick="triggerEventScenario('normal')">
                        <h4>🟢 Cenário Cotidiano (Mediana Reais)</h4>
                        <p>Aplica a concorrência normal registrada no cotidiano das sondas (~{avg_f_p50 * 100:.0f}% dos times logados).</p>
                    </div>

                    <div class="event-card" onclick="triggerEventScenario('p95')" style="border-left-color: var(--warning);">
                        <h4>🟡 Pico Estatístico Seguro (Percentil 95)</h4>
                        <p>Simula o teto padrão seguro. Comporta h客观andovers de turno normais (~{avg_f_p95 * 100:.0f}% simultâneos).</p>
                    </div>

                    <div class="event-card" onclick="triggerEventScenario('crisis')" style="border-left-color: var(--danger);">
                        <h4>🔴 Emergência Operacional (Worst-Case)</h4>
                        <p>Simula um incidente grave onde quase toda a tripulação a bordo e de sobreaviso se conecta (~{avg_f_p100 * 100:.0f}% simultâneos).</p>
                    </div>

                    <div class="event-card" onclick="triggerEventScenario('blackout')" style="border-left-color: #7c3aed; background: #faf5ff; border-color:#e9d5ff">
                        <h4>⚡ Blackout Total / Parada de Sonda (Estresse Máximo)</h4>
                        <p>Cenário extremo: 100% dos usuários ativos (Onshore + equipes Offshore completas) tentam logar simultaneamente no sistema.</p>
                    </div>
                </div>
            </div>

            <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <h3 style="margin-top:0; font-size:1.2rem; color:var(--secondary);">Termômetro de Impacto Orçamental (Limite: 1.200)</h3>
                <div style="height: 280px; position: relative;">
                    <canvas id="eventChart"></canvas>
                </div>
                <div id="eventOutputBox" style="padding: 1rem; text-align: center; font-weight: bold; border-radius: 6px; font-size: 1.1rem; margin-top: 1rem; background: #ecfdf5; color:#047857;">
                    Carregando análise...
                </div>
            </div>
        </div>
    </div>

    <script>
        function openTab(evt, tabName) {{
            var i, tc, tb;
            tc = document.getElementsByClassName("tab-content");
            for (i = 0; i < tc.length; i++) {{ tc[i].style.display = "none"; tc[i].classList.remove("active"); }}
            tb = document.getElementsByClassName("tab-button");
            for (i = 0; i < tb.length; i++) tb[i].classList.remove("active");
            var target = document.getElementById(tabName);
            target.style.display = "block";
            setTimeout(() => target.classList.add("active"), 10);
            evt.currentTarget.classList.add("active");
        }}

        // --- Módulo 1: Gráfico de Domínios ---
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

        // --- Módulo 2: Simulador Financeiro & Projeção ---
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
            document.getElementById('calcFinancialTotal').innerText = "$" + (totalPoints * unitCost).toLocaleString('pt-BR', {{minimumFractionDigits: 2}});

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

        // --- Módulo 3: Novo Simulador Estatístico de Eventos/Estresse ---
        let eventChartInstance = null;
        const baseAuthCount = {final_prem_auth + final_base_auth};
        const totalConcPhysical = {final_prem_conc_users + final_base_conc_users};

        function triggerEventScenario(type) {{
            let factor = 0.33;
            let titleText = "";
            let description = "";

            if (type === 'normal') {{
                factor = {avg_f_p50};
                titleText = "🟢 Cenário Cotidiano";
                description = "Dentro da meta contratada. Operação saudável.";
            }} else if (type === 'p95') {{
                factor = {avg_f_p95};
                titleText = "🟡 Pico Estatístico Seguro (P95)";
                description = "Teto recomendado para dimensionamento. Absorve handovers de turno.";
            }} else if (type === 'crisis') {{
                factor = {avg_f_p100};
                titleText = "🔴 Emergência Operacional";
                description = "Alerta: O desvio padrão indica alto risco de enfileiramento de chamados.";
            }} else if (type === 'blackout') {{
                factor = 1.0;
                titleText = "⚡ ESTRESSE MÁXIMO (100% Simultâneo)";
                description = "Cenário Crítico Catastrófico: Todos logados ao mesmo tempo.";
            }}

            // Cálculo dos pesos baseado na distribuição real de Premium e Base da Foresea
            const ptsAuth = ({final_prem_auth} * 5) + ({final_base_auth} * 3);
            const ptsConc = (({final_prem_conc_users} * 15) + ({final_base_conc_users} * 10)) * factor;
            const totalPoints = Math.round(ptsAuth + ptsConc);

            const outBox = document.getElementById('eventOutputBox');
            outBox.innerText = titleText + ": " + totalPoints + " AppPoints Requeridos. " + description;

            if (totalPoints > 1200) {{
                outBox.style.background = '#fef2f2'; outBox.style.color = 'var(--danger)';
            }} else {{
                outBox.style.background = '#ecfdf5'; outBox.style.color = '#047857';
            }}

            const ctxEvent = document.getElementById('eventChart').getContext('2d');
            if (eventChartInstance) {{
                eventChartInstance.data.datasets[0].data = [totalPoints];
                eventChartInstance.update();
            }} else {{
                eventChartInstance = new Chart(ctxEvent, {{
                    type: 'bar',
                    data: {{
                        labels: ['Consumo do Evento'],
                        datasets: [{{ label: 'AppPoints Requeridos', data: [totalPoints], backgroundColor: '#2563eb', barThickness: 50 }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{ x: {{ max: 2500, beginAtZero: true }} }},
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}
        }}

        // --- Módulo 4: Filtros e Exportadores das Tabelas ---
        function filterTable() {{
            var input = document.getElementById("searchInput").value.toUpperCase();
            var decFilter = document.getElementById("decFilter").value.toUpperCase();
            var tables = document.querySelectorAll("#tab-gov .filterable-table");
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

        function filterAppPoints() {{
            var input = document.getElementById("searchAppPoints").value.toUpperCase();
            var recFilter = document.getElementById("filterRec").value.toUpperCase();
            var table = document.getElementById("table-apppoints");
            if(!table) return;
            var tr = table.getElementsByTagName("tr");
            for (var i = 1; i < tr.length; i++) {{
                var tdNameTitle = tr[i].cells[0].textContent + " " + tr[i].cells[1].textContent + " " + tr[i].cells[8].textContent;
                var tdRec = tr[i].cells[2].textContent.toUpperCase();
                var matchSearch = input === "" || tdNameTitle.toUpperCase().indexOf(input) > -1;
                var matchRec = recFilter === "" || tdRec.indexOf(recFilter) > -1;
                tr[i].style.display = (matchSearch && matchRec) ? "" : "none";
            }}
        }}

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
            updateCalculator();
            triggerEventScenario('p95');
        }});
    </script>
</body>
</html>"""