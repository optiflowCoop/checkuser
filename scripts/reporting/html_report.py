# reporting/html_report.py
from datetime import datetime

def fmt_br(num):
    return f"{num:,}".replace(",", ".")

def build_html_structure(summary_data, governance_data, app_points_data, domain_counts):
    # --- CSS ---
    css = """
<style>
    :root { --primary: #0f172a; --secondary: #1e293b; --accent: #2563eb; --bg: #f8fafc; --card-bg: #ffffff; --text: #334155; --border: #e2e8f0; --danger: #ef4444; --warning: #f59e0b; --success: #10b981;}
    body { font-family: "Segoe UI", sans-serif; margin: 0; background-color: var(--bg); color: var(--text); }
    .topbar { background: var(--primary); color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
    .tabs { background: var(--secondary); padding: 0 2rem; }
    .tab-button { background: none; border: none; color: #cbd5e1; padding: 1rem 1.5rem; cursor: pointer; font-size: 1rem; border-bottom: 3px solid transparent; }
    .tab-button.active { color: white; border-bottom-color: var(--accent); }
    .container { max-width: 1600px; margin: 0 auto; padding: 2rem; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; }
    .card { background: var(--card-bg); border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid var(--border); padding: 1.5rem; margin-bottom: 2rem; }
    .card-header { margin: -1.5rem -1.5rem 1.5rem; padding: 1rem 1.5rem; border-bottom: 1px solid var(--border); font-size: 1.2rem; font-weight: 600; }
    .stat-value { font-size: 2.5rem; font-weight: 700; color: var(--primary); }
    .stat-title { font-size: 0.9rem; text-transform: uppercase; font-weight: 600; margin-top: 0.5rem; }
    .chart-container { height: 300px; }
    .table-responsive { overflow-x: auto; max-height: 500px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px 15px; border-bottom: 1px solid var(--border); text-align: left; white-space: nowrap; }
    th { background-color: #f1f5f9; position: sticky; top: 0; }
    .type-analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 1.5rem; }
    .type-card { background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; }
    .type-card h4 { margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; }
</style>
"""
    # --- AppPoints Summaries ---
    auth_users = summary_data['app_points_summary']['auth_users']
    conc_users = summary_data['app_points_summary']['conc_users']
    premium_users = summary_data['app_points_summary']['premium_users']
    total_auth_points = sum(u['APP_POINTS'] for u in auth_users)
    total_conc_points = sum(u['APP_POINTS'] for u in conc_users)
    total_estimated_cost = total_auth_points + int(total_conc_points * 0.3)

    # --- Build HTML for each tab ---
    painel_html = build_painel_tab(summary_data, domain_counts)
    governanca_html = build_governanca_tab(governance_data)
    app_points_html = build_app_points_tab(app_points_data, total_estimated_cost, premium_users, auth_users, conc_users)

    # --- Final Assembly ---
    return f"""
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Dashboard Unificado</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>{css}</head>
    <body>
        <div class="topbar"><h1>Dashboard de Governança e AppPoints</h1><p>Atualizado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p></div>
        <div class="tabs">
            <button class="tab-button active" onclick="openTab(event,'painel')">Painel de Controle</button>
            <button class="tab-button" onclick="openTab(event,'governanca')">Governança e Saneamento</button>
            <button class="tab-button" onclick="openTab(event,'app-points')">Simulação de AppPoints</button>
        </div>
        {painel_html}
        {governanca_html}
        {app_points_html}
        <script>
            function openTab(e,t){{var n,a,o;for(a=(n=document.getElementsByClassName("tab-content")).length,o=0;o<a;o++)n[o].style.display="none";for(a=(o=document.getElementsByClassName("tab-button")).length,n=0;n<a;n++)o[n].className=o[n].className.replace(" active","");document.getElementById(t).style.display="block",e.currentTarget.className+=" active"}}
            const domainLabels={list(domain_counts.keys())},domainValues={list(domain_counts.values())};
            new Chart(document.getElementById("domainChart"),{{type:"pie",data:{{labels:domainLabels,datasets:[{{data:domainValues,backgroundColor:["#10b981","#2563eb","#f59e0b","#94a3b8"]}}]}},options:{{responsive:!0,maintainAspectRatio:!1,plugins:{{legend:{{position:"bottom"}}}}}}}});
        </script>
    </body></html>
    """

def build_painel_tab(summary, domains):
    return f"""
    <div id="painel" class="container tab-content active">
        <div class="grid">
            <div class="card"><div class="card-header">Distribuição por Domínio</div><div class="chart-container"><canvas id="domainChart"></canvas></div></div>
            <div class="card"><div class="card-header">Saúde da Governança</div>
                <div class="grid" style="grid-template-columns:1fr 1fr;text-align:center;">
                    <div><div class="stat-value" style="color:var(--success)">{fmt_br(summary['active_profiles_count'])}</div><div class="stat-title">Pessoas Ativas</div></div>
                    <div><div class="stat-value" style="color:var(--warning)">{fmt_br(summary['title_divergence_count'])}</div><div class="stat-title">Cargos com Divergência</div></div>
                </div>
            </div>
        </div>
    </div>
    """

def build_governanca_tab(data):
    cross_env_rows = ''.join(f"<tr><td>{c.get('USERID')}</td><td>{c.get('ENV_LIST')}</td><td>{c.get('DISPLAYNAME_LIST')}</td></tr>" for c in data['cross_env'][:200])
    login_conflicts_rows = ''.join(f"<tr><td>{c.get('LOGINID')}</td><td>{c.get('USERID_LIST')}</td><td>{c.get('DISPLAYNAME_LIST')}</td></tr>" for c in data['login_conflicts'][:200])
    worklist_rows = ''.join(f"<tr><td>{w.get('RAW_ID')}</td><td>{w.get('DISPLAYNAME')}</td><td>{w.get('HYPOTHESIS')}</td><td>{w.get('MERGE_DECISION')}</td></tr>" for w in data['worklist'][:200])
    title_divergence_rows = ''.join(f"<tr><td>{d['title']}</td></tr>" for d in data['title_divergences'])
    
    return f"""
    <div id="governanca" class="container tab-content">
        <div class="card"><div class="card-header">Cargos com Divergência de Perfil</div><div class="table-responsive"><table><thead><tr><th>Cargo (TITLE)</th></tr></thead><tbody>{title_divergence_rows}</tbody></table></div></div>
        <div class="card"><div class="card-header">Reuso de USERID entre Ambientes</div><div class="table-responsive"><table><thead><tr><th>USERID</th><th>Ambientes</th><th>Nomes</th></tr></thead><tbody>{cross_env_rows}</tbody></table></div></div>
        <div class="card"><div class="card-header">Conflitos de Login Corporativo (LOGINID)</div><div class="table-responsive"><table><thead><tr><th>LOGINID</th><th>USERIDs</th><th>Nomes</th></tr></thead><tbody>{login_conflicts_rows}</tbody></table></div></div>
        <div class="card"><div class="card-header">Fila de Saneamento (Worklist)</div><div class="table-responsive"><table><thead><tr><th>ID Bruto</th><th>Nome</th><th>Hipótese</th><th>Decisão</th></tr></thead><tbody>{worklist_rows}</tbody></table></div></div>
    </div>
    """

def build_app_points_tab(data, total_cost, premium, auth, conc):
    app_points_rows = ''.join(f"<tr><td>{s['USERID']}</td><td>{s['DISPLAYNAME']}</td><td>{s['ENTITLEMENT']}</td><td>{s['LICENSE_MODEL']}</td><td>{s['APP_POINTS']}</td><td>{s['USAGE_PROFILE']}</td><td>{s['TITLES']}</td></tr>" for s in sorted(data, key=lambda x: x['APP_POINTS'], reverse=True)[:500])
    return f"""
    <div id="app-points" class="container tab-content">
        <div class="card"><div class="card-header">Resumo da Simulação (Universo Foresea)</div>
            <div class="grid">
                <div style="text-align:center"><div class="stat-value" style="color:var(--danger)">{fmt_br(total_cost)}</div><div class="stat-title">Custo Total Estimado</div></div>
                <div style="text-align:center"><div class="stat-value" style="color:var(--warning)">{fmt_br(len(premium))}</div><div class="stat-title">Usuários Premium (O&G)</div></div>
                <div style="text-align:center"><div class="stat-value">{fmt_br(len(auth))}</div><div class="stat-title">Usuários Authorized</div></div>
                <div style="text-align:center"><div class="stat-value">{fmt_br(len(conc))}</div><div class="stat-title">Usuários Concurrent</div></div>
            </div>
        </div>
        <div class="card"><div class="card-header">Detalhes da Simulação (Top 500 por Custo)</div><div class="table-responsive"><table><thead><tr><th>USERID</th><th>Nome</th><th>Entitlement</th><th>Licença</th><th>Custo</th><th>Perfil</th><th>Cargos</th></tr></thead><tbody>{app_points_rows}</tbody></table></div></div>
    </div>
    """
