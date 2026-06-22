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
    # --- Cálculo de Resumos e Cenários Previsionais (DATA-DRIVEN) ---
    custo_atual = 0
    custo_saneado = 0
    custo_otimizado = 0
    inativos_count = 0
    downgrade_count = 0
    concurrent_count = 0

    final_prem_auth = 0
    final_prem_conc_users = 0
    final_base_auth = 0
    final_base_conc_users = 0

    # Analítica de fatores para o simulador
    sum_concurrent_factors = 0
    count_concurrent_users = 0

    for u in app_points:
        pts = u['APP_POINTS']
        lic = u['LICENSE_MODEL']
        ent = u['ENTITLEMENT']
        rec = u['OPTIMIZATION_REC']
        real_factor = u.get('REAL_FACTOR', 0.3333)

        # 1. Custo Atual Base (Multiplica pela CONCORRÊNCIA REAL e não mais pela média)
        val_atual = pts if lic == 'AUTHORIZED' else pts * real_factor
        custo_atual += val_atual

        if rec == 'INATIVO (>90d)':
            inativos_count += 1
            continue

        if rec == 'DOWNGRADE_CANDIDATE': downgrade_count += 1
        if rec == 'MOVE_TO_CONCURRENT': concurrent_count += 1

        custo_saneado += val_atual

        # --- Determinação do Perfil Final Pós-Otimização (To-Be) ---
        final_ent = 'BASE' if (rec == 'DOWNGRADE_CANDIDATE' and ent == 'PREMIUM') else ent
        final_lic = 'CONCURRENT' if rec == 'MOVE_TO_CONCURRENT' else lic

        # Calcula Custo Otimizado com Tabela IBM MAS 9 Oficial e Fator Real
        if final_ent == 'PREMIUM':
            pts_novo = 5 if final_lic == 'AUTHORIZED' else 15
        else:
            pts_novo = 3 if final_lic == 'AUTHORIZED' else 10

        val_otimizado = pts_novo if final_lic == 'AUTHORIZED' else pts_novo * real_factor
        custo_otimizado += val_otimizado

        # Popula os baldes para o Simulador e calcula a média do fator real
        if final_ent == 'PREMIUM':
            if final_lic == 'AUTHORIZED':
                final_prem_auth += 1
            else:
                final_prem_conc_users += 1
                sum_concurrent_factors += real_factor
                count_concurrent_users += 1
        else:
            if final_lic == 'AUTHORIZED':
                final_base_auth += 1
            else:
                final_base_conc_users += 1
                sum_concurrent_factors += real_factor
                count_concurrent_users += 1

    # --- Cálculos de ROI e Simulador ---
    pontos_salvos_saneamento = custo_atual - custo_saneado
    pontos_salvos_inteligencia = custo_saneado - custo_otimizado

    # O Simulador agora usa a média da concorrência REAL do logintracking
    avg_real_factor = (sum_concurrent_factors / count_concurrent_users) if count_concurrent_users > 0 else 0.3333

    sim_prem_auth = final_prem_auth
    sim_prem_conc = int(final_prem_conc_users * avg_real_factor)
    sim_base_auth = final_base_auth
    sim_base_conc = int(final_base_conc_users * avg_real_factor)

    # --- Build Tables ---
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
                '<div class="env-divergence"><div class="env-header">⚠️ Inconsistência de TYPE nas Sondas</div>')
            for env, types in sorted(data['types'].items()):
                title_divergence_html.append(f'<div>📍 {env}: {", ".join(sorted(t for t in types if t))}</div>')
            title_divergence_html.append('</div>')
        title_divergence_html.append('</div>')

    # Na tabela de AppPoints, adicionamos o campo "Fator Escala" para provar a matemática
    app_points_rows = []
    for s in sorted(app_points, key=lambda x: x['APP_POINTS'], reverse=True)[:1000]:
        fator_display = f"{s.get('REAL_FACTOR', 0.3333) * 100:.1f}%" if s[
                                                                            'LICENSE_MODEL'] == 'CONCURRENT' else "100% (Fixo)"

        app_points_rows.append([
            f"<strong>{s['USERID']}</strong>",
            s['DISPLAYNAME'][:30],
            get_recommendation_badge(s['OPTIMIZATION_REC']),
            f"<span class='badge' style='background:#f1f5f9;'>{s['ENTITLEMENT']}</span>",
            f"<span style='font-weight:600;'>{s['LICENSE_MODEL']}</span>",
            f"<strong>{s['APP_POINTS']}</strong>",
            f"<span style='color:var(--accent); font-weight:600;'>{fator_display}</span>",
            # NOVO: Exibe a concorrência exata
            s['TITLES'][:40] + ("..." if len(s['TITLES']) > 40 else "")
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

        .card {{ background: var(--card-bg); border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); border: 1px solid var(--border); padding: 1.8rem; margin-bottom: 2rem; }}
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

        .table-responsive {{ overflow-x: auto; border-radius: 8px; border: 1px solid var(--border); max-height: 600px; overflow-y: auto; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 14px 16px; border-bottom: 1px solid var(--border); vertical-align: top; word-wrap: break-word; white-space: normal; font-size: 0.9rem;}}
        th {{ background-color: #f1f5f9; color: #334155; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; position: sticky; top: 0; z-index: 10; }}
        tbody tr:hover {{ background-color: #f8fafc; }}

        .badge {{ padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: inline-block; text-align: center; }}
        .badge-critical {{ background-color: var(--danger); color: white; }}
        .badge-high {{ background-color: var(--warning); color: white; }}
        .badge-medium {{ background-color: var(--accent); color: white; }}
        .badge-success {{ background-color: var(--success); color: white; }}
        .badge-neutral {{ background-color: var(--neutral); color: white; }}

        .search-container {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #f1f5f9; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); align-items: center; }}
        .search-bar {{ flex-grow: 1; padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; min-width: 250px; }}
        .filter-select {{ padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; background: white; min-width: 180px; }}

        .btn-export {{ background-color: #10b981; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-size: 0.95rem; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: background 0.2s; }}
        .btn-export:hover {{ background-color: #059669; }}

        .type-analysis-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }}
        .type-card {{ background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; transition: box-shadow 0.2s; }}
        .type-card h4 {{ margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; display: flex; align-items: center; flex-wrap: wrap; }}
        .env-divergence {{ margin-bottom: 0.8rem; padding: 0.8rem; background: #f8fafc; border-left: 3px solid var(--warning); border-radius: 4px; }}
        .env-header {{ font-weight: 700; color: var(--primary); margin-bottom: 0.4rem; font-size: 0.9rem; }}

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
    </style>
</head>
<body>
    <div class="topbar">
        <div>
            <h1>Dashboard Gerencial MAS 9.1 | Foresea</h1>
            <p>Saneamento e Capacity Planning Baseado em Dados (Logintracking Analytics)</p>
        </div>
        <div>
            <p style="text-align: right; color: #cbd5e1;">Gerado em:<br><strong>{datetime.now().strftime("%d/%m/%Y %H:%M")}</strong></p>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-button active" onclick="openTab(event, 'tab-painel')">1. Resumo Consolidador (7 Bases)</button>
        <button class="tab-button" onclick="openTab(event, 'tab-apppoints')">2. Otimização e ROI (Financeiro)</button>
        <button class="tab-button" onclick="openTab(event, 'tab-gov')">3. Matriz de Risco e Saneamento</button>
    </div>

    <div id="tab-painel" class="container tab-content active">
        <div class="alert-box">
            <strong>🎯 Visão de Diretoria — Oportunidade de Redução de Custos (Opex)</strong>
            <p>O algoritmo consolidou as identidades de Sondas e Base, extraiu o <i>logintracking</i> e mapeou fisicamente as equipes. Detectamos {fmt_br(inativos_count)} inativos e {fmt_br(downgrade_count + concurrent_count)} elegíveis a partilha de turnos/downgrade.</p>
        </div>

        <div class="card">
            <h2 class="card-header">Radar Operacional de Identidades</h2>
            <div class="stats-grid">
                <div class="stat-card border-success"><div class="stat-value" style="color: var(--success);">{fmt_br(summary['active_profiles_count'])}</div><div class="stat-title">Pessoas Únicas</div><div class="stat-subtitle">Efetivo consolidado real</div></div>
                <div class="stat-card border-neutral"><div class="stat-value" style="color: var(--neutral);">{fmt_br(inativos_count)}</div><div class="stat-title">Contas Zumbi</div><div class="stat-subtitle">Sem login há > 90 dias</div></div>
                <div class="stat-card border-warning"><div class="stat-value" style="color: var(--warning);">{fmt_br(downgrade_count)}</div><div class="stat-title">Elegíveis Downgrade</div><div class="stat-subtitle">Premium ocioso -> Base</div></div>
                <div class="stat-card border-accent"><div class="stat-value" style="color: var(--accent);">{fmt_br(concurrent_count)}</div><div class="stat-title">Migração Offshore</div><div class="stat-subtitle">Escalas alocadas em Concurrent</div></div>
            </div>

            <div class="charts-container" style="grid-template-columns: 1fr 2fr;">
                <div class="chart-box" style="flex-direction: column;">
                    <h3 style="margin-top:0; font-size: 1rem; color: var(--primary);">Distribuição Contratual (Domínio)</h3>
                    <canvas id="domainChart"></canvas>
                </div>
                <div class="chart-box" style="align-items: flex-start; padding: 2rem;">
                    <div style="width: 100%;">
                        <h3 style="margin-top:0; font-size: 1rem; color: var(--primary);">Entendimento Financeiro da Segregação</h3>
                        <p style="font-size: 0.9rem; color: var(--text); margin-bottom: 1rem;">
                            Terceiros e contas genéricas representam um passivo. A recomendação arquitetural é transferir terceiros esporádicos para integrações API, libertando AppPoints para a operação-fim da Foresea.
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

    <div id="tab-apppoints" class="container tab-content">

        <div class="card" style="border-left: 4px solid var(--success); background-image: linear-gradient(to right, #ffffff, #f8fafc);">
            <div class="card-header" style="border-bottom:none; margin-bottom:0;">
                <div>
                    <h2 style="margin:0; font-size:1.5rem; color:var(--success);">🧮 Simulador Pós-Migração (Fatores Reais da Base de Dados)</h2>
                    <p style="font-size: 0.9rem; color: #64748b; font-weight: normal; margin-top: 4px;">Ao invés da média (1 para 3), a inteligência calculou o pico máximo diário de acessos cruzando as tabelas LOGINTRACKING e TITLES da Foresea.</p>
                </div>
            </div>

            <div style="display: flex; gap: 2rem; flex-wrap: wrap; margin-top: 1rem;">
                <div style="flex: 1; min-width: 300px; background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                    <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 2px solid #e2e8f0;">
                        <label style="display:block; font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">💵 Custo Estimado por AppPoint/Ano (USD/BRL):</label>
                        <div style="display: flex; align-items: center;">
                            <span style="font-size: 1.2rem; font-weight: bold; padding: 8px; background: #f1f5f9; border: 1px solid var(--border); border-right: none; border-radius: 6px 0 0 6px;">$</span>
                            <input type="number" id="inpCustoUnitario" value="500" min="0" oninput="updateCalculator()" style="width: 100%; padding: 10px; font-size: 1.2rem; font-weight: bold; border: 1px solid var(--border); border-radius: 0 6px 6px 0;">
                        </div>
                    </div>

                    <div class="calc-input-group">
                        <label>Premium Auth (Onshore/Fixos) <span class="calc-badge-pts">5 pts</span></label>
                        <input type="number" id="inpPremAuth" value="{sim_prem_auth}" oninput="updateCalculator()">
                    </div>
                    <div class="calc-input-group">
                        <label>Premium Conc (Fator Calculado: {avg_real_factor * 100:.1f}%) <span class="calc-badge-pts">15 pts</span></label>
                        <input type="number" id="inpPremConc" value="{sim_prem_conc}" oninput="updateCalculator()">
                    </div>
                    <div class="calc-input-group">
                        <label>Base Auth (Onshore) <span class="calc-badge-pts">3 pts</span></label>
                        <input type="number" id="inpBaseAuth" value="{sim_base_auth}" oninput="updateCalculator()">
                    </div>
                    <div class="calc-input-group" style="border-bottom:none; margin-bottom:0; padding-bottom:0;">
                        <label>Base Conc (Fator Calculado: {avg_real_factor * 100:.1f}%) <span class="calc-badge-pts">10 pts</span></label>
                        <input type="number" id="inpBaseConc" value="{sim_base_conc}" oninput="updateCalculator()">
                    </div>
                </div>

                <div style="flex: 1; min-width: 250px; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                    <h3 style="margin: 0; font-size: 1rem; color: var(--secondary); text-transform: uppercase; letter-spacing: 1px;">Projeção Real Otimizada</h3>
                    <div id="calcTotalDisplay" style="font-size: 4rem; font-weight: 800; color: var(--success); line-height: 1.2;">0</div>
                    <div style="font-size: 0.95rem; color: #64748b; font-weight: 600;">Teto do Orçamento: 1.200 AppPoints</div>

                    <div class="financial-box">
                        <div style="font-size: 0.85rem; text-transform: uppercase; font-weight: bold; color: #065f46;">Custo Anual de Licenças Projetado</div>
                        <div id="calcFinancialTotal" class="financial-value">$ 0</div>
                    </div>

                    <div id="calcAlertBox" style="margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 6px; background-color: var(--danger); color: white; font-weight: bold; font-size: 1.1rem; display: none; box-shadow: 0 4px 6px -1px rgba(239,68,68,0.4);">
                        ⚠️ ORÇAMENTO EXCEDIDO (>1200)
                    </div>
                </div>

                <div style="flex: 1; min-width: 300px; height: 280px; display: flex; justify-content: center; align-items: center;">
                    <canvas id="simChart"></canvas>
                </div>
            </div>
        </div>

        <div class="card" style="border-top: 4px solid var(--primary); background-color: #ffffff;">
            <h2 class="card-header" style="border-bottom: none; margin-bottom: 0.5rem; color: var(--primary);">🧠 Motor de Decisão: Como o Algoritmo Classificou</h2>
            <p style="font-size: 0.95rem; color: #64748b; margin-top: 0; margin-bottom: 1.5rem;">Os valores injetados no simulador acima basearam-se na leitura do <i>logintracking</i> e segurança de todas as 7 instâncias.</p>

            <div class="legend-grid">
                <div class="legend-box" style="border-left: 3px solid #1e3a8a;">
                    <h3><span style="font-size:1.2rem;">🔰</span> Nível (Entitlement)</h3>
                    <ul class="legend-list">
                        <li><strong>PREMIUM:</strong> Obrigatório a todo o corpo O&G da Foresea que toca em Permissão de Trabalho (PTW) e HSE.</li>
                        <li><strong>BASE / LIMITED:</strong> Alocado à equipa estrita de backoffice ou visualizadores, após triagem de módulos.</li>
                    </ul>
                </div>

                <div class="legend-box" style="border-left: 3px solid #f59e0b;">
                    <h3><span style="font-size:1.2rem;">🔑</span> Modelo e Data-Driven</h3>
                    <ul class="legend-list">
                        <li><strong>AUTHORIZED:</strong> Lideranças e Pessoal da Base. 1 utilizador = 1 Licença nominal fixa.</li>
                        <li><strong>CONCURRENT (Por Cargo):</strong> Ao invés de usar uma média plana (33%), o Python agrupa o <b>LOGINTRACKING</b> pelo cargo (Ex: Eletricista) e extrai o pico real de concorrência na Sonda, refletindo fielmente a operação.</li>
                    </ul>
                </div>

                <div class="legend-box" style="border-left: 3px solid #64748b;">
                    <h3><span style="font-size:1.2rem;">🪙</span> Pesos (MAS 9)</h3>
                    <p style="font-size: 0.85rem; color: #64748b; margin-top:-0.5rem; margin-bottom: 0.8rem;">Matriz IBM utilizada nos cálculos.</p>
                    <table style="width: 100%; font-size: 0.85rem; text-align: left; border-collapse: collapse; background: white;">
                        <tr style="background: #f1f5f9;"><th style="padding: 6px;">Nível</th><th style="padding: 6px;">Authorized</th><th style="padding: 6px;">Concurrent</th></tr>
                        <tr style="border-bottom: 1px solid var(--border);"><td style="padding: 6px;"><b>Premium</b></td><td style="padding: 6px; font-weight:bold;">5 pts</td><td style="padding: 6px; font-weight:bold;">15 pts</td></tr>
                        <tr style="border-bottom: 1px solid var(--border);"><td style="padding: 6px;"><b>Base</b></td><td style="padding: 6px;">3 pts</td><td style="padding: 6px;">10 pts</td></tr>
                    </table>
                </div>
            </div>
        </div>

        <div class="card">
            <h2 class="card-header">Impacto de Saneamento e Algoritmo na Base Real</h2>
            <div class="stats-grid">
                <div class="stat-card border-danger">
                    <div class="stat-value" style="color: var(--danger);">{fmt_br(custo_atual)}</div>
                    <div class="stat-title">As-Is (Migração Cega)</div>
                    <div class="stat-subtitle">Custaria caro sem análise</div>
                </div>
                <div class="stat-card border-warning">
                    <div class="stat-value" style="color: var(--warning);">{fmt_br(custo_saneado)}</div>
                    <div class="stat-title">Pós-Saneamento</div>
                    <div class="stat-subtitle">Apenas remoção de zumbis</div>
                </div>
                <div class="stat-card border-success">
                    <div class="stat-value" style="color: var(--success);">{fmt_br(custo_otimizado)}</div>
                    <div class="stat-title">Otimizado pelas Escalas</div>
                    <div class="stat-subtitle">Concorrência Extraída do Tracking</div>
                </div>
            </div>
            <div style="text-align:center; margin-top: 1.5rem; font-size: 1.1rem; font-weight: bold; color: var(--primary);">
                Graças à análise de logintracking e partilha de sondas, estamos a recuperar tecnicamente <span style="color: var(--success); font-size: 1.3rem;">{fmt_br(pontos_salvos_saneamento + pontos_salvos_inteligencia)} AppPoints virtuais</span> face ao modelo fixo.
            </div>
        </div>

        <div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">
            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: var(--primary);">📋 Plano de Ação: Tabela de Escala por Cargo</h3>
                <button class="btn-export" onclick="exportTableToCSV('table-apppoints', 'Plano_Saneamento_Maximo.csv')">
                    Exportar Lista Atual para CSV
                </button>
            </div>

            <div class="search-container">
                <input type="text" id="searchAppPoints" class="search-bar" onkeyup="filterAppPoints()" placeholder="Pesquisar por ID, Nome, Cargo...">
                <select id="filterRec" class="filter-select" onchange="filterAppPoints()">
                    <option value="">💡 Todas Ações / Status</option>
                    <option value="OK">OK / Normal</option>
                    <option value="INATIVO">🔴 Inativos (>90d) - Para Corte</option>
                    <option value="DOWNGRADE">🟡 Requer Downgrade (Premium p/ Base)</option>
                    <option value="P/ CONCURRENT">🔵 Mover para Escala Offshore (Concurrent)</option>
                    <option value="CONFIRMADO">🟢 Confirmado Authorized</option>
                </select>
                <select id="filterEntitlement" class="filter-select" onchange="filterAppPoints()">
                    <option value="">🔰 Nível de Acesso (Entitlement)</option>
                    <option value="PREMIUM">PREMIUM</option>
                    <option value="BASE">BASE</option>
                </select>
            </div>

            {render_table(['USERID', 'Nome', 'Recomendação', 'Entitlement', 'Licença Atual', 'AppPoints Ref.', 'Fator Escala (Real)', 'Cargos Unificados'], app_points_rows, 'table-apppoints', 'filterable-table')}
        </div>
    </div>

    <div id="tab-gov" class="container tab-content">
        <div class="alert-box" style="border-left-color: var(--warning); background-color: #fffbeb;">
            <strong style="color: #b45309;">⚠️ Gestão de Passivo Multi-Sonda</strong>
            <p style="color: #92400e;">Detetámos utilizadores com logins ativos repetidos em diferentes bases, gerando colisão de identidades e duplicação de consumo.</p>
        </div>

        <div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">
            <h3 style="margin-top: 0; color: var(--primary);">🔍 Filtro Interativo de Risco</h3>
            <div class="search-container">
                <input type="text" id="searchInput" class="search-bar" onkeyup="filterTable()" placeholder="Buscar por ID ou Nome...">
                <select id="decFilter" class="filter-select" onchange="filterTable()">
                    <option value="">Nível de Gravidade</option>
                    <option value="PESSOAS DIFERENTES">🔴 ALTO - Colisão (Nomes Divergentes no mesmo Login)</option>
                    <option value="REQUER REVISÃO">🟡 MÉDIO - Requer Análise de RH</option>
                    <option value="POSSÍVEL MESMA PESSOA">🟢 BAIXO - Duplicidade Padrão de Revezamento</option>
                </select>
            </div>
        </div>

        <div class="card">
            <div style="display:flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); margin-bottom: 1.5rem; padding-bottom: 0.75rem;">
                <h2 style="margin:0; color: var(--secondary); font-size: 1.4rem; font-weight: 600;">Fila de Resolução (Cross-Environment)</h2>
                <button class="btn-export" style="background-color: var(--secondary);" onclick="exportTableToCSV('table-worklist', 'Conflitos_Identidade_Foresea.csv')">Exportar Backlog</button>
            </div>
            {render_table(['ID Bruto', 'Nome', 'Login AD', 'Tipo Colisão', 'Gravidade', 'Ação'], worklist_rows, 'table-worklist', 'filterable-table')}
        </div>

        <div class="card">
            <h2 class="card-header">Top 30: Permissões de Segurança Divergentes (Base vs Sondas)</h2>
            <div class="type-analysis-grid">
                {''.join(title_divergence_html)}
            </div>
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

        let simChartInstance = null;
        function formatMoney(amount) {{
            return "$" + amount.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}

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

            const totalAppPoints = costPAuth + costPConc + costBAuth + costBConc;
            const totalFinancial = totalAppPoints * unitCost;

            const displayEl = document.getElementById('calcTotalDisplay');
            const alertEl = document.getElementById('calcAlertBox');
            const financialEl = document.getElementById('calcFinancialTotal');

            displayEl.innerText = totalAppPoints.toLocaleString('pt-BR');
            financialEl.innerText = formatMoney(totalFinancial);

            if (totalAppPoints > 1200) {{
                displayEl.style.color = 'var(--danger)';
                alertEl.style.display = 'block';
            }} else {{
                displayEl.style.color = 'var(--success)';
                alertEl.style.display = 'none';
            }}

            const ctxSim = document.getElementById('simChart').getContext('2d');
            const simData = [costPAuth, costPConc, costBAuth, costBConc];

            if (simChartInstance) {{
                simChartInstance.data.datasets[0].data = simData;
                simChartInstance.update();
            }} else {{
                simChartInstance = new Chart(ctxSim, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Premium Auth', 'Premium Conc', 'Base Auth', 'Base Conc'],
                        datasets: [{{ data: simData, backgroundColor: ['#1e3a8a', '#3b82f6', '#047857', '#10b981'], borderWidth: 2, borderColor: '#ffffff' }}]
                    }},
                    options: {{ responsive: true, maintainAspectRatio: false, cutout: '55%', plugins: {{ legend: {{ position: 'bottom' }} }} }}
                }});
            }}
        }}
        document.addEventListener('DOMContentLoaded', updateCalculator);

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
            var entFilter = document.getElementById("filterEntitlement").value.toUpperCase();

            var table = document.getElementById("table-apppoints");
            if(!table) return;
            var tr = table.getElementsByTagName("tr");

            for (var i = 1; i < tr.length; i++) {{
                var tdNameTitle = tr[i].cells[0].textContent + " " + tr[i].cells[1].textContent + " " + tr[i].cells[7].textContent;
                var tdRec = tr[i].cells[2].textContent.toUpperCase();
                var tdEnt = tr[i].cells[3].textContent.toUpperCase();

                var matchSearch = input === "" || tdNameTitle.toUpperCase().indexOf(input) > -1;
                var matchRec = recFilter === "" || tdRec.indexOf(recFilter) > -1;
                var matchEnt = entFilter === "" || tdEnt.indexOf(entFilter) > -1;

                tr[i].style.display = (matchSearch && matchRec && matchEnt) ? "" : "none";
            }}
        }}

        function downloadCSV(csv, filename) {{
            var csvFile;
            var downloadLink;
            var BOM = "\\uFEFF";
            csvFile = new Blob([BOM + csv], {{type: "text/csv;charset=utf-8;"}});
            downloadLink = document.createElement("a");
            downloadLink.download = filename;
            downloadLink.href = window.URL.createObjectURL(csvFile);
            downloadLink.style.display = "none";
            document.body.appendChild(downloadLink);
            downloadLink.click();
        }}

        function exportTableToCSV(tableId, filename) {{
            var csv = [];
            var table = document.getElementById(tableId);
            var rows = table.querySelectorAll("tr");

            for (var i = 0; i < rows.length; i++) {{
                if(rows[i].style.display === "none") continue;
                var row = [], cols = rows[i].querySelectorAll("td, th");
                for (var j = 0; j < cols.length; j++) {{
                    var data = cols[j].innerText.replace(/(\\r\\n|\\n|\\r)/gm, " ").replace(/"/g, '""');
                    row.push('"' + data + '"');
                }}
                csv.push(row.join(";"));
            }}
            downloadCSV(csv.join("\\n"), filename);
        }}
    </script>
</body>
</html>"""