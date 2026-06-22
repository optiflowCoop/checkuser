from pathlib import Path
import csv
from collections import Counter, defaultdict
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'reports'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_csv(path: Path):
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def fmt_br(num):
    return f"{num:,}".replace(",", ".")

def render_table(headers, rows, table_id="", extra_class=""):
    html = f'<div class="table-responsive"><table id="{table_id}" class="{extra_class}">\n'
    html += '  <thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead>\n'
    html += '  <tbody>\n'
    for row in rows:
        html += '    <tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>\n'
    html += '  </tbody>\n'
    html += '</table></div>\n'
    return html

def build_html():
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    cross_env = load_csv(IN_DIR / 'cross_env_userid_reuse.csv')
    login_conflicts = load_csv(IN_DIR / 'login_conflicts.csv')
    worklist = load_csv(IN_DIR / 'identity_collisions_enriched.csv')
    access_rows = load_csv(IN_DIR / 'consolidated_user_access_normalized.csv') or load_csv(IN_DIR / 'consolidated_user_access.csv')
    emails_data = load_csv(IN_DIR / 'consolidated_email.csv')
    
    # Phase 3: Usage and License Data
    usage_phase3 = load_csv(IN_DIR / 'usage_analysis_phase3.csv')
    license_recs = load_csv(IN_DIR / 'license_optimization_recommendations.csv')

    # Base Metrics
    total_records = len(identities)
    active_records = sum(1 for r in identities if r.get('STATUS', '').upper() == 'ACTIVE')
    by_env = Counter(r.get('ENV_DB', '') for r in identities)
    
    unique_logins = len(set([r.get('USERID', '').strip().upper() for r in identities if r.get('USERID', '').strip()]))
    active_logins_set = set([r.get('USERID', '').strip().upper() for r in identities if r.get('USERID', '').strip() and r.get('STATUS', '').upper() == 'ACTIVE'])
    unique_active_logins = len(active_logins_set)

    unique_active_by_env = {}
    for env in by_env.keys():
        unique_active_by_env[env] = len(set([
            r.get('USERID', '').strip().upper() 
            for r in identities 
            if r.get('ENV_DB', '') == env 
            and r.get('USERID', '').strip() 
            and r.get('STATUS', '').upper() == 'ACTIVE'
        ]))

    active_worklist = [w for w in worklist if w.get('STATUS', '').upper() == 'ACTIVE']
    
    reused_userids_active = set()
    for c in cross_env:
        statuses = c.get('STATUS_LIST', '').upper().split(';')
        if any('ACTIVE' in s.strip() for s in statuses):
            reused_userids_active.add(c.get('USERID', '').strip().upper())
            
    total_reused_active = len(reused_userids_active)
    critical_diff_active = sum(1 for w in worklist if w.get('STATUS', '').upper() == 'ACTIVE' and w.get('HYPOTHESIS') == 'CONFIRMED_DIFFERENT_PERSON') if worklist else 0
    critical_diff_all = sum(1 for w in worklist if w.get('HYPOTHESIS') == 'CONFIRMED_DIFFERENT_PERSON') if worklist else 0
    pending_ad_active = sum(1 for w in active_worklist if w.get('MERGE_DECISION') in ('AWAITING_AD_MATCH', 'MERGE_AFTER_AD_MATCH'))
    
    env_labels = list(by_env.keys())
    env_data = list(by_env.values())
    unique_active_env_data = [unique_active_by_env[env] for env in env_labels]

    login_statuses = defaultdict(set)
    for r in identities:
        lid = r.get('LOGINID', '').strip().upper()
        if lid:
            login_statuses[lid].add(r.get('STATUS', '').strip().upper())

    raw_profile_map = defaultdict(lambda: {
        'ENV_DB': '',
        'USERID': '',
        'DISPLAYNAME': '',
        'STATUS': '',
        'TYPE': '',
        'TITLE': set(),
        'PERSONGROUP': set()
    })
    for r in access_rows:
        raw_id = f"{r.get('ENV_DB', '').strip()}|{r.get('USERID', '').strip()}".strip('|')
        if not raw_id:
            continue
        profile = raw_profile_map[raw_id]
        if not profile['ENV_DB']:
            profile['ENV_DB'] = r.get('ENV_DB', '').strip()
            profile['USERID'] = r.get('USERID', '').strip()
            profile['DISPLAYNAME'] = r.get('DISPLAYNAME', '').strip()
            profile['STATUS'] = r.get('STATUS', '').strip().upper()
            profile['TYPE'] = r.get('TYPE', '').strip()
        title = r.get('TITLE', '').strip()
        pgroup = r.get('PERSONGROUP', '').strip()
        if title:
            profile['TITLE'].add(title)
        if pgroup:
            for grp in [g.strip() for g in pgroup.split(';') if g.strip()]:
                profile['PERSONGROUP'].add(grp)

    active_profiles_with_context = sum(
        1 for p in raw_profile_map.values()
        if p['STATUS'] == 'ACTIVE' and (p['TITLE'] or p['PERSONGROUP'])
    )
    
    # Domain Segregation Metrics (FORESEA vs TEMPORARY)
    email_map = {}
    for e in emails_data:
        userid = e.get('USERID', '').strip().upper()
        email = e.get('PRIMARYEMAIL', '') or e.get('EMAILADDRESS', '')
        if userid and email:
            email_map[userid] = email.lower()
    
    foresea_domains = ['@foresea.com', '@foresea-partner.com']
    foresea_active_count = 0
    temp_active_count = 0
    unknown_active_count = 0
    
    for r in identities:
        if r.get('STATUS', '').upper() == 'ACTIVE':
            userid = r.get('USERID', '').strip().upper()
            email = email_map.get(userid, '')
            if any(domain in email for domain in foresea_domains):
                foresea_active_count += 1
            elif email:
                temp_active_count += 1
            else:
                unknown_active_count += 1

    html = [
        '<!DOCTYPE html>',
        '<html lang="pt-BR">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<title>Maximo MAS 9 - Governan├ºa de Identidades</title>',
        '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
        '<style>',
        ':root { --primary: #0f172a; --secondary: #1e293b; --accent: #2563eb; --bg: #f8fafc; --card-bg: #ffffff; --text: #334155; --border: #e2e8f0; --danger: #ef4444; --warning: #f59e0b; --success: #10b981;}',
        '* { box-sizing: border-box; }',
        'body { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; margin: 0; background-color: var(--bg); color: var(--text); line-height: 1.5; }',
        '.topbar { background: var(--primary); color: white; padding: 1.5rem 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center;}',
        '.topbar h1 { margin: 0; font-size: 1.8rem; font-weight: 600; letter-spacing: -0.5px; }',
        '.topbar p { margin: 0; color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem; }',
        '.container { max-width: 1400px; margin: 0 auto; padding: 2rem; }',
        '.alert-box { background-color: #eff6ff; border-left: 4px solid var(--accent); padding: 1rem 1.5rem; border-radius: 6px; margin-bottom: 2rem; display: flex; flex-direction: column; gap: 0.5rem; }',
        '.alert-box strong { color: #1e3a8a; font-size: 1.1rem; }',
        '.alert-box p { margin: 0; color: #1e40af; }',
        '.alert-success { background-color: #ecfdf5; border-left: 4px solid var(--success); padding: 1rem 1.5rem; border-radius: 6px; margin-bottom: 2rem; display: flex; flex-direction: column; gap: 0.5rem; }',
        '.alert-success strong { color: #065f46; font-size: 1.1rem; }',
        '.alert-success p { margin: 0; color: #065f46; }',
        '.card { background: var(--card-bg); border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); border: 1px solid var(--border); padding: 1.8rem; margin-bottom: 2rem; }',
        '.card-header { margin-top: 0; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border); padding-bottom: 0.75rem; color: var(--secondary); font-size: 1.4rem; font-weight: 600; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }',
        '.card-header:hover { color: var(--accent); }',
        '.card-content { display: block; }',
        '.card-content.collapsed { display: none; }',
        '.toggle-icon { font-size: 1.2rem; transition: transform 0.3s ease; }',
        '.collapsed .toggle-icon { transform: rotate(-90deg); }',
        '.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; }',
        '.stat-card { background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; text-align: center; transition: transform 0.2s; position: relative; }',
        '.stat-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); }',
        '.stat-value { font-size: 2.2rem; font-weight: 700; color: var(--primary); margin-bottom: 0.2rem; }',
        '.stat-title { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #1e293b; font-weight: 700; margin-bottom: 0.5rem; }',
        '.stat-subtitle { font-size: 0.75rem; color: #64748b; line-height: 1.2; }',
        '.border-danger { border-bottom: 4px solid var(--danger); }',
        '.border-warning { border-bottom: 4px solid var(--warning); }',
        '.border-accent { border-bottom: 4px solid var(--accent); }',
        '.border-success { border-bottom: 4px solid var(--success); }',
        '.border-neutral { border-bottom: 4px solid #94a3b8; }',
        '.charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 2rem; margin-top: 2rem; }',
        '.chart-box { height: 320px; display: flex; justify-content: center; align-items: center; background: #ffffff; border-radius: 8px; border: 1px solid var(--border); padding: 1rem; }',
        '.table-responsive { overflow-x: auto; border-radius: 8px; border: 1px solid var(--border); max-height: 500px; overflow-y: auto; }',
        'table { width: 100%; border-collapse: collapse; text-align: left; }',
        'th, td { padding: 14px 16px; border-bottom: 1px solid var(--border); vertical-align: top; word-wrap: break-word; white-space: normal; }',
        'th { background-color: #f1f5f9; color: #334155; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; position: sticky; top: 0; z-index: 10; }',
        'tbody tr:hover { background-color: #f8fafc; }',
        'tbody tr:last-child td { border-bottom: none; }',
        '.badge { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; display: inline-block; text-align: center; }',
        '.badge-critical { background-color: #fef2f2; color: #991b1b; border: 1px solid #f87171; }',
        '.badge-high { background-color: #fff7ed; color: #9a3412; border: 1px solid #fb923c; }',
        '.badge-medium { background-color: #eff6ff; color: #1e40af; border: 1px solid #60a5fa; }',
        '.badge-low { background-color: #ecfdf5; color: #166534; border: 1px solid #34d399; }',
        '.legend-box { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #f8fafc; padding: 1rem; border-radius: 8px; border: 1px dashed #cbd5e1; }',
        '.legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #475569; }',
        '.search-container { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; background: #f1f5f9; padding: 1.5rem; border-radius: 8px; border: 1px solid #cbd5e1; }',
        '.search-bar { flex-grow: 1; padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; min-width: 250px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05); }',
        '.filter-select { padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; background: white; color: var(--text); min-width: 200px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }',
        '.search-bar:focus, .filter-select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(37,99,235,0.2); }',
        '.baseline-compare { display: flex; flex-direction: column; gap: 12px; }',
        '.grp-label { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 4px; display: block; }',
        '.common-groups { background: #f8fafc; border: 1px dashed #cbd5e1; padding: 10px; border-radius: 6px; }',
        '.diff-groups { background: #ffffff; border: 1px solid #e2e8f0; padding: 10px; border-radius: 6px; }',
        '.env-row { margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9; display: flex; align-items: flex-start; gap: 10px; }',
        '.env-row:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }',
        '.env-name { font-weight: bold; color: var(--primary); font-size: 0.85rem; background: #e2e8f0; padding: 3px 8px; border-radius: 4px; min-width: 60px; text-align: center; }',
        '.badge-grp { display: inline-block; padding: 4px 8px; margin: 2px; border-radius: 4px; font-size: 0.75rem; font-weight: 500; font-family: ui-monospace, monospace; }',
        '.badge-grp.common { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }',
        '.badge-grp.diff { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }',
        '.badge-grp.diff-none { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; font-style: italic; }',
        '.tooltip { position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #94a3b8; }',
        '.tooltip .tooltiptext { visibility: hidden; width: 300px; background-color: #1e293b; color: #fff; text-align: left; border-radius: 6px; padding: 10px; position: absolute; z-index: 100; bottom: 125%; left: 50%; margin-left: -150px; opacity: 0; transition: opacity 0.3s; font-size: 0.8rem; line-height: 1.4; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }',
        '.tooltip .tooltiptext::after { content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: #1e293b transparent transparent transparent; }',
        '.tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }',
        '.reason-cell { font-size: 0.8rem; color: #64748b; font-style: italic; max-width: 350px; word-wrap: break-word; }',
        '.type-analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }',
        '.type-card { background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; transition: box-shadow 0.2s; }',
        '.type-card:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.08); }',
        '.type-card h4 { margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; }',
        '.env-divergence { margin-bottom: 0.8rem; padding: 0.8rem; background: #f8fafc; border-left: 3px solid var(--warning); border-radius: 4px; }',
        '.env-divergence .env-header { font-weight: 700; color: var(--primary); margin-bottom: 0.4rem; font-size: 0.9rem; }',
        '.env-divergence .extra-groups { color: #1e40af; font-size: 0.85rem; }',
        '.env-divergence .baseline-groups { color: #64748b; font-size: 0.8rem; margin-top: 0.3rem; }',
        '@media (max-width: 768px) { .charts-container { grid-template-columns: 1fr; } .search-container { flex-direction: column; } .env-row { flex-direction: column; } .type-analysis-grid { grid-template-columns: 1fr; } }',
        '</style>',
        '</head>',
        '<body>',
        
        '<div class="topbar">',
        '<div>',
        '<h1>Dashboard Governan├ºa Maximo EAM</h1>',
        '<p>Fase 2: Padroniza├º├úo de Baseline e Governan├ºa de Acessos</p>',
        '</div>',
        f'<div><p style="text-align: right; color: #cbd5e1;">Atualizado em:<br><strong>{datetime.now().strftime("%d/%m/%Y %H:%M")}</strong></p></div>',
        '</div>',
        
        '<div class="container">',
    ]
    
    html.append('<div class="alert-box">')
    html.append('<strong>­ƒôï Apresenta├º├úo: Escopo de An├ílise e M├®trica de Neg├│cio</strong>')
    html.append('<p>Dashboard consolidado apresenta <strong>contas ativas</strong> de todas as unidades para mapeamento de risco e planejamento de licen├ºas MAS 9. <strong>M├®trica-chave:</strong> "Registros Ativos" contabiliza repeti├º├Áes entre bases (ex: esilva na base A + base B = 2 registros). "Pessoas ├Ünicas" elimina duplicatas (esilva = 1 pessoa real, independente de onde esteja alocado).</p>')
    html.append('</div>')
    html.append('<div class="alert-success">')
    html.append('<strong>­ƒÄ» Fase 2: Baseline Funcional e Rastreabilidade de Conflitos</strong>')
    html.append('<p>An├ílise expandida com dados de <strong>Title</strong> (cargo funcional ex: Supervisor de El├®trica) e <strong>PersonGroup</strong> (departamento/equipe) para identificar diverg├¬ncias de perfil de acesso entre unidades. Todos os conflitos exibem <strong>motivo t├®cnico detalhado</strong> para acelerar saneamento e padroniza├º├úo.</p>')
    html.append('</div>')

    # --- Bloco 1: Executive Summary ---
    html.append('<div class="card">')
    html.append('<h2 class="card-header" onclick="toggleSection(\'section1\')">1. Resumo Executivo Operacional <span class="toggle-icon">Ôû╝</span></h2>')
    html.append('<div id="section1" class="card-content">')
    
    # Calcular m├®tricas Fase 2
    total_titles = len(set([r.get('TITLE', '').strip() for r in identities if r.get('TITLE', '').strip()]))
    units_with_profiles = len(set([r.get('ENV_DB', '').strip() for r in identities if (r.get('TITLE', '').strip() or r.get('PERSONGROUP', '').strip())]))
    total_profiles_with_data = sum(1 for r in identities if (r.get('TITLE', '').strip() or r.get('PERSONGROUP', '').strip()))
    
    html.append('<h3 style="color: var(--primary); margin: 0 0 1rem 0; font-size: 1.1rem; border-left: 4px solid var(--accent); padding-left: 1rem;">­ƒôè M├®tricas de Governan├ºa de Identidades</h3>')
    html.append('<div class="stats-grid">')
    
    html.append(f'<div class="stat-card border-success"><div class="stat-value" id="stat-unique-active" style="color: var(--success);" data-active="{unique_active_logins}" data-all="{len(set([r.get('USERID', '').strip().upper() for r in identities if r.get('USERID', '').strip()]))}">{fmt_br(unique_active_logins)}</div><div class="stat-title">Pessoas ├Ünicas <span id="stat-unique-scope">(Ativas)</span></div><div class="stat-subtitle">"Pessoas f├¡sicas" projetadas para o MAS 9</div></div>')
    html.append(f'<div class="stat-card border-accent"><div class="stat-value" id="stat-records" data-active="{active_records}" data-all="{total_records}">{fmt_br(active_records)}</div><div class="stat-title">Registros <span id="stat-records-scope">(Ativos)</span></div><div class="stat-subtitle">Contas log├íveis no Maximo</div></div>')
    html.append(f'<div class="stat-card border-warning"><div class="stat-value" id="stat-reuse" style="color: var(--warning);" data-active="{total_reused_active}" data-all="{len(cross_env) if cross_env else 0}">{fmt_br(total_reused_active)}</div><div class="stat-title">Riscos de Reuso <span id="stat-reuse-scope">(Ativos)</span></div><div class="stat-subtitle">Logins repetidos entre sondas</div></div>')
    html.append(f'<div class="stat-card border-danger"><div class="stat-value" id="stat-critical" style="color: var(--danger);" data-active="{critical_diff_active}" data-all="{critical_diff_all}">{fmt_br(critical_diff_active)}</div><div class="stat-title">Colis├Áes Cr├¡ticas <span id="stat-critical-scope">(Ativas)</span></div><div class="stat-subtitle">Nomes diferentes no mesmo login</div></div>')
    
    html.append('</div>')  # fecha stats-grid governan├ºa
    
    html.append('<h3 style="color: var(--primary); margin: 2rem 0 1rem 0; font-size: 1.1rem; border-left: 4px solid #2563eb; padding-left: 1rem;">🎯 Segregação de Usuários para Migração MAS 9</h3>')
    html.append('<div class="stats-grid">')
    
    foresea_pct = (foresea_active_count / active_records * 100) if active_records > 0 else 0
    temp_pct = (temp_active_count / active_records * 100) if active_records > 0 else 0
    
    html.append(f'<div class="stat-card border-success"><div class="stat-value" style="color: var(--success);">{fmt_br(foresea_active_count)}</div><div class="stat-title">🏢 FORESEA (Migrar)</div><div class="stat-subtitle">{foresea_pct:.1f}% - @foresea.com / @foresea-partner.com</div></div>')
    html.append(f'<div class="stat-card border-warning"><div class="stat-value" style="color: var(--warning);">{fmt_br(temp_active_count)}</div><div class="stat-title">👷 TEMPORÁRIOS (Não Migrar)</div><div class="stat-subtitle">{temp_pct:.1f}% - Contratados terceirizados</div></div>')
    html.append(f'<div class="stat-card border-neutral"><div class="stat-value" style="color: #64748b;">{fmt_br(unknown_active_count)}</div><div class="stat-title">⚠️ Sem Email Cadastrado</div><div class="stat-subtitle">Requer investigação manual</div></div>')
    
    html.append('</div>')  # fecha stats-grid segregação
    
    html.append('<h3 style="color: var(--primary); margin: 2rem 0 1rem 0; font-size: 1.1rem; border-left: 4px solid #10b981; padding-left: 1rem;">📋 Fase 2: Baseline Funcional</h3>')
    html.append('<div class="stats-grid">')
    
    html.append(f'<div class="stat-card border-accent"><div class="stat-value" style="color: #10b981;">{fmt_br(total_titles)}</div><div class="stat-title">Fun├º├Áes Distintas (TITLE)</div><div class="stat-subtitle">Cargos ├║nicos mapeados na organiza├º├úo</div></div>')
    html.append(f'<div class="stat-card border-warning"><div class="stat-value" style="color: var(--warning);" id="stat-divergent">0</div><div class="stat-title">Fun├º├Áes com Diverg├¬ncia</div><div class="stat-subtitle">Cargos com TYPE ou grupos inconsistentes</div></div>')
    html.append(f'<div class="stat-card border-success"><div class="stat-value" id="stat-profile" style="color: var(--accent);" data-active="{active_profiles_with_context}" data-all="{total_profiles_with_data}">{fmt_br(active_profiles_with_context)}</div><div class="stat-title">Perfis Completos <span id="stat-profile-scope">(Ativos)</span></div><div class="stat-subtitle">Usu├írios com Title + PersonGroup</div></div>')
    html.append(f'<div class="stat-card border-neutral"><div class="stat-value" style="color: #64748b;">{fmt_br(units_with_profiles)}</div><div class="stat-title">Unidades com Dados</div><div class="stat-subtitle">Bases que possuem informa├º├Áes de perfil</div></div>')
    
    html.append('</div>')  # fecha stats-grid fase 2
    
    html.append('<div class="charts-container">')
    html.append('<div class="chart-box"><canvas id="uniqueEnvChart"></canvas></div>')
    html.append('<div class="chart-box"><canvas id="statusChart"></canvas></div>')
    html.append('</div>')
    html.append('</div></div>')

    # --- SEÇÃO 2: PHASE 3 - APPPOINTS OPTIMIZATION ---
    if usage_phase3:
        html.append('<div class="card">')
        html.append('<h2 class="card-header" onclick="toggleSection(\'section_phase3\')">2. 🎯 Otimização de AppPoints (Fase 3) <span class="toggle-icon">▼</span></h2>')
        html.append('<div id="section_phase3" class="card-content">')
        
        # Calcular métricas
        foresea_users = [u for u in usage_phase3 if u.get('USER_CATEGORY') == 'FORESEA']
        temp_users = [u for u in usage_phase3 if u.get('USER_CATEGORY') == 'TEMPORARY']
        offshore_users = [u for u in foresea_users if u.get('OPERATIONAL_PRESENCE') == 'OFFSHORE']
        onshore_users = [u for u in foresea_users if u.get('OPERATIONAL_PRESENCE') == 'ONSHORE']
        
        authorized_users = [u for u in foresea_users if 'AUTHORIZED' in u.get('REQUIRED_LICENSE', '')]
        concurrent_users = [u for u in foresea_users if 'CONCURRENT' in u.get('REQUIRED_LICENSE', '')]
        
        premium_users = [u for u in foresea_users if 'PREMIUM' in u.get('REQUIRED_LICENSE', '')]
        base_users = [u for u in foresea_users if 'BASE' in u.get('REQUIRED_LICENSE', '')]
        limited_users = [u for u in foresea_users if u.get('USER_TIER') == 'VERY_LIGHT']
        idle_users = [u for u in foresea_users if u.get('USER_TIER') == 'IDLE']
        
        foresea_cost = sum(float(u.get('APP_POINTS_COST', 0) or 0) for u in foresea_users)
        temp_cost_avoided = sum(float(u.get('APP_POINTS_COST', 0) or 0) for u in temp_users)
        
        html.append('<div class="alert-box">')
        html.append('<strong>🎯 Meta: Distribuir 1.200 AppPoints contratados de forma assertiva</strong>')
        html.append(f'<p><strong>Status:</strong> {foresea_cost:.0f} AppPoints estimados para {len(foresea_users)} usuários FORESEA (permanentes).</p>')
        html.append(f'<p><strong>Economia:</strong> {temp_cost_avoided:.0f} pts economizados excluindo {len(temp_users)} usuários TEMPORÁRIOS da migração.</p>')
        if foresea_cost > 1200:
            html.append(f'<p style="color: var(--danger);"><strong>⚠️ ATENÇÃO:</strong> Estimativa acima da capacidade contratada. Necessário otimização adicional!</p>')
        else:
            html.append(f'<p style="color: var(--success);"><strong>✅ OK:</strong> Dentro da capacidade. Margem de {1200-foresea_cost:.0f} AppPoints disponível.</p>')
        html.append('</div>')
        
        html.append('<h3 style="color: var(--primary); margin: 1.5rem 0 1rem 0;">📊 Distribuição de Licenças (Usuários FORESEA)</h3>')
        html.append('<div class="stats-grid">')
        html.append(f'<div class="stat-card border-accent"><div class="stat-value">{fmt_br(len(offshore_users))}</div><div class="stat-title">⛵ OFFSHORE</div><div class="stat-subtitle">Turnos 12h / Baixa simultaneidade</div></div>')
        html.append(f'<div class="stat-card border-accent"><div class="stat-value">{fmt_br(len(onshore_users))}</div><div class="stat-title">🏢 ONSHORE</div><div class="stat-subtitle">Administrativo / Alta simultaneidade</div></div>')
        html.append(f'<div class="stat-card border-success"><div class="stat-value">{fmt_br(len(authorized_users))}</div><div class="stat-title">🔑 AUTHORIZED</div><div class="stat-subtitle">{len(authorized_users)/len(foresea_users)*100:.1f}% - Uso intenso (>60 logins/90d)</div></div>')
        html.append(f'<div class="stat-card border-accent"><div class="stat-value">{fmt_br(len(concurrent_users))}</div><div class="stat-title">🔄 CONCURRENT</div><div class="stat-subtitle">{len(concurrent_users)/len(foresea_users)*100:.1f}% - Revezamento natural</div></div>')
        html.append(f'<div class="stat-card border-warning"><div class="stat-value">{fmt_br(len(premium_users))}</div><div class="stat-title">🛢️ PREMIUM O&G</div><div class="stat-subtitle">Usam módulos Oil & Gas</div></div>')
        html.append(f'<div class="stat-card border-success"><div class="stat-value">{fmt_br(len(base_users))}</div><div class="stat-title">📦 BASE</div><div class="stat-subtitle">Módulos standard</div></div>')
        html.append('</div>')
        
        html.append('<h3 style="color: var(--primary); margin: 2rem 0 1rem 0;">🔝 Top 15 Usuários FORESEA (Maior Custo AppPoints)</h3>')
        top15 = sorted(foresea_users, key=lambda u: float(u.get('APP_POINTS_COST', 0) or 0), reverse=True)[:15]
        top15_rows = []
        for u in top15:
            tier_badge = f'<span class="badge" style="background:{"#ef4444" if "PREMIUM" in u.get("REQUIRED_LICENSE","") else "#10b981"};">{u.get("USER_TIER", "")}</span>'
            top15_rows.append([
                u.get('USERID', ''),
                u.get('DISPLAYNAME', '')[:30],
                u.get('OPERATIONAL_PRESENCE', ''),
                u.get('LOGIN_COUNT_90D', '0'),
                tier_badge,
                u.get('REQUIRED_LICENSE', ''),
                f'<strong>{u.get("APP_POINTS_COST", "0")}</strong>'
            ])
        html.append(render_table(['USERID', 'Nome', 'Presença', 'Logins 90d', 'Perfil', 'Licença', 'AppPoints'], top15_rows))
        
        html.append('</div></div>')

    # --- Filtro Global ---
    html.append('<div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">')
    html.append('<h3 style="margin-top: 0; color: var(--primary);">­ƒöì Filtro Global de Saneamento (Aplica-se em todas as tabelas)</h3>')
    html.append('<p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1rem;">O Dashboard foca em contas Ativas por padr├úo. Use os filtros abaixo para refinar a an├ílise conforme necess├írio.</p>')
    html.append('<div class="search-container">')
    html.append('<input type="text" id="searchInput" class="search-bar" onkeyup="filterTable()" placeholder="­ƒöì Pesquisar por ID, Nome, Email...">')
    
    html.append('<select id="envFilter" class="filter-select" onchange="filterTable()">')
    html.append('<option value="">­ƒîÄ Todas as Unidades</option>')
    for env in env_labels:
        html.append(f'<option value="{env}">{env}</option>')
    html.append('</select>')

    html.append('<select id="statusFilter" class="filter-select" onchange="filterTable()">')
    html.append('<option value="ACTIVE" selected>­ƒƒó Somente Ativos (Foco AppPoints)</option>')
    html.append('<option value="">­ƒƒó/­ƒö┤ Todos os Status Hist├│ricos</option>')
    html.append('<option value="INACTIVE">­ƒö┤ Inativos / Bloqueados</option>')
    html.append('</select>')
    
    html.append('<select id="decFilter" class="filter-select" onchange="filterTable()">')
    html.append('<option value="">ÔÜû´©Å Todas as Decis├Áes</option>')
    html.append('<option value="PESSOAS DIFERENTES">­ƒö┤ PESSOAS DIFERENTES (Cr├¡tico)</option>')
    html.append('<option value="REQUER REVIS├âO">­ƒƒí REQUER REVIS├âO (Alerta)</option>')
    html.append('<option value="POSS├ìVEL MESMA PESSOA">­ƒƒó POSS├ìVEL MESMA PESSOA (Pendente AD)</option>')
    html.append('<option value="DO_NOT_MERGE">A├º├úo: DO_NOT_MERGE</option>')
    html.append('<option value="MANUAL_REVIEW_REQUIRED">A├º├úo: MANUAL_REVIEW_REQUIRED</option>')
    html.append('<option value="AWAITING_AD_MATCH">A├º├úo: AWAITING_AD_MATCH</option>')
    html.append('</select>')
    html.append('</div>')
    
    html.append('''
    <div class="legend-box">
        <div class="legend-item"><span class="badge badge-critical">PESSOAS DIFERENTES</span> O mesmo login (USERID) foi usado para nomes/pessoas diferentes. Bloqueado para unifica├º├úo.</div>
        <div class="legend-item"><span class="badge badge-medium">REQUER REVIS├âO</span> Inconsist├¬ncias de status, classe ou login corporativo cruzado.</div>
        <div class="legend-item"><span class="badge badge-low">POSS├ìVEL MESMA PESSOA</span> Nomes batem perfeitamente. Libera├º├úo final aguarda checagem com o AD.</div>
    </div>
    ''')
    html.append('</div>')

    # --- Bloco 2: Cat├ílogo Fase 2 (Title/PersonGroup) ---
    html.append('<div class="card">')
    html.append('<h2 class="card-header" onclick="toggleSection(\'section2phase2\')">2. ­ƒôï Cat├ílogo Fase 2: Title + PersonGroup por Usu├írio <span class="toggle-icon">Ôû╝</span></h2>')
    html.append('<div id="section2phase2" class="card-content">')
    html.append('<p style="color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem;"><strong>Legenda:</strong> <em>Title</em> = Cargo funcional (ex: Supervisor de El├®trica). <em>PersonGroup</em> = Departamento/time. <em>Tipo Funcional</em> = Classifica├º├úo TYPE do Maximo. Exibindo at├® 500 registros de contas ativas com perfil completo.</p>')
    profile_rows = []
    for raw_id, p in sorted(
        raw_profile_map.items(),
        key=lambda x: (x[1]['STATUS'] != 'ACTIVE', x[1]['ENV_DB'], x[1]['USERID'])
    ):
        title = '; '.join(sorted(p['TITLE']))
        person_group = '; '.join(sorted(p['PERSONGROUP']))
        if not title and not person_group:
            continue
        profile_rows.append([
            f"<span class='env-data'>{p['ENV_DB']}</span><span class='status-data' style='display:none;'>{p['STATUS']}</span>{raw_id}",
            p['DISPLAYNAME'],
            p['TYPE'],
            title,
            person_group,
            p['STATUS']
        ])
        if len(profile_rows) >= 500:
            break
    if profile_rows:
        html.append(render_table(['ID Bruto', 'Nome', 'Tipo Funcional', 'Title', 'PersonGroup', 'Status'], profile_rows, "profileTable", "filterable-table"))
    else:
        html.append('<p>Nenhum registro com Title/PersonGroup encontrado para exibi├º├úo.</p>')
    html.append('</div></div>')

    # --- Bloco 3: Fila Consolidada de Saneamento (Cross-Env + Worklist Unificados) ---
    html.append('<div class="card">')
    html.append('<h2 class="card-header" onclick="toggleSection(\'section3unified\')">3. ­ƒöä Fila Completa de Governan├ºa e Saneamento <span class="toggle-icon">Ôû╝</span></h2>')
    html.append('<div id="section3unified" class="card-content">')
    html.append('<p style="color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem;"><strong>Legenda:</strong> <span class="badge badge-critical">PESSOAS DIFERENTES</span> = login reusado para pessoas distintas (bloqueado). <span class="badge badge-medium">REQUER REVIS├âO</span> = inconsist├¬ncias detectadas. <span class="badge badge-low">POSS├ìVEL MESMA PESSOA</span> = candidato ├á unifica├º├úo (validar AD). <em>Escopo de An├ílise</em>: (Multi) = login presente em v├írias bases. (Single) = conflito em base ├║nica. <em>Motivo</em> detalha tecnicamente cada caso.</p>')
    
    if worklist:
        unified_rows = []
        
        # Processar worklist completa com flag de multi-ambiente
        for w in worklist:
            userid = w.get('USERID', '')
            raw_id = w.get('RAW_ID', '')
            
            # Verificar se ├® cross-environment
            is_multi_env = any(c.get('USERID') == userid for c in cross_env) if cross_env else False
            scope_flag = '­ƒîÉ Multi' if is_multi_env else '­ƒôì Single'
            
            prio = w.get('REVIEW_PRIORITY', 'LOW')
            badge = "badge-critical" if prio == 'CRITICAL' else "badge-high" if prio == 'HIGH' else "badge-medium" if prio == 'MEDIUM' else "badge-low"
            
            hypo = w.get('HYPOTHESIS', 'UNKNOWN')
            if hypo == 'CONFIRMED_DIFFERENT_PERSON': hypo_pt = 'PESSOAS DIFERENTES'
            elif hypo == 'POTENTIAL_SAME_PERSON': hypo_pt = 'POSS├ìVEL MESMA PESSOA'
            elif hypo == 'REQUIRES_REVIEW': hypo_pt = 'REQUER REVIS├âO'
            else: hypo_pt = hypo
            
            # Buscar dados complementares se multi-ambiente
            if is_multi_env:
                c_match = next((c for c in cross_env if c.get('USERID') == userid), None)
                if c_match:
                    env_list = c_match.get('ENV_LIST', w.get('ENV_DB', ''))
                    names_list = c_match.get('DISPLAYNAME_LIST', w.get('DISPLAYNAME', ''))
                    email_list = c_match.get('EMAIL_LIST', w.get('PRIMARYEMAIL', ''))
                    
                    # Title e PersonGroup do cross-env
                    raw_ids = [rid.strip() for rid in c_match.get('RAW_ID_LIST', '').split(';') if rid.strip()]
                    title_values = set()
                    pgroup_values = set()
                    for rid in raw_ids:
                        profile = raw_profile_map.get(rid)
                        if profile:
                            title_values.update(profile['TITLE'])
                            pgroup_values.update(profile['PERSONGROUP'])
                    if not title_values:
                        title_values.update([x.strip() for x in c_match.get('TITLE_LIST', '').split(';') if x.strip()])
                    if not pgroup_values:
                        for grouped in [x.strip() for x in c_match.get('PERSONGROUP_LIST', '').split(';') if x.strip()]:
                            pgroup_values.update([g.strip() for g in grouped.split(';') if g.strip()])
                    
                    title_display = '; '.join(sorted(title_values)) if title_values else w.get('TITLE', '')
                    pgroup_display = '; '.join(sorted(pgroup_values)) if pgroup_values else w.get('PERSONGROUP', '')
                else:
                    env_list = w.get('ENV_DB', '')
                    names_list = w.get('DISPLAYNAME', '')
                    email_list = w.get('PRIMARYEMAIL', '')
                    title_display = w.get('TITLE', '')
                    pgroup_display = w.get('PERSONGROUP', '')
            else:
                env_list = w.get('ENV_DB', '')
                names_list = w.get('DISPLAYNAME', '')
                email_list = w.get('PRIMARYEMAIL', '')
                title_display = w.get('TITLE', '')
                pgroup_display = w.get('PERSONGROUP', '')
            
            conflict_reason = w.get('CONFLICT_REASON', w.get('COLLISION_TYPE', ''))
            if not conflict_reason:
                if hypo == 'CONFIRMED_DIFFERENT_PERSON':
                    conflict_reason = 'Dados biom├®tricos divergentes entre ambientes'
                elif hypo == 'REQUIRES_REVIEW':
                    conflict_reason = 'Inconsist├¬ncias detectadas que requerem an├ílise humana'
                else:
                    conflict_reason = 'Compat├¡vel, aguardando valida├º├úo Active Directory'
            
            unified_rows.append([
                f"<span style='font-size:0.7rem;color:#64748b;'>{scope_flag}</span> <strong>{userid}</strong>",
                f"<span class='env-data'>{env_list}</span><span class='status-data' style='display:none;'>{w.get('STATUS', '')}</span>",
                names_list,
                email_list,
                title_display,
                pgroup_display,
                f'<span class="{badge} hyp-data">{hypo_pt}</span>',
                f"<span class='reason-cell'>{conflict_reason}</span>",
                f"<strong class='dec-data' style='color: {'#ef4444' if w.get('MERGE_DECISION')=='DO_NOT_MERGE' else '#1e293b'};'>{w.get('MERGE_DECISION', 'MANUAL_REVIEW_REQUIRED')}</strong>"
            ])
            
            if len(unified_rows) >= 500: break
        
        html.append(render_table(['USERID / Login', 'Bases', 'Nomes de Exibi├º├úo', 'E-mails', 'Title', 'PersonGroup', 'Conclus├úo', 'Motivo/Detalhes', 'A├º├úo MAS 9'], unified_rows, "unifiedTable", "filterable-table"))
    else:
        html.append('<p>Nenhum conflito detectado para saneamento.</p>')
    
    html.append('</div></div>')

    # --- Bloco 4: Login Conflicts (LOGINID AD) ---
    html.append('<div class="card">')
    html.append('<h2 class="card-header" onclick="toggleSection(\'section4loginid\')">4. ÔÜá´©Å Conflitos de LOGINID (Login Corporativo AD) <span class="toggle-icon">Ôû╝</span></h2>')
    html.append('<div id="section4loginid" class="card-content">')
    if login_conflicts:
        html.append('<p style="color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem;"><strong>Legenda:</strong> LoginID AD = login corporativo do Active Directory. Situa├º├úo: mesmo login corporativo vinculado a m├║ltiplos USERIDs/Pessoas no Maximo ÔÇö impacto em SSO e auditoria.</p>')
        l_rows = []
        for l in login_conflicts[:300]:
            lid_status = '; '.join(login_statuses.get(l.get('LOGINID'), set()))
            dec = l.get('MERGE_DECISION', 'MANUAL_REVIEW_REQUIRED')
            if not dec or dec == 'None': dec = 'MANUAL_REVIEW_REQUIRED'
            
            userid_count = len([u for u in l.get('USERID_LIST', '').split(';') if u.strip()])
            personid_count = len([p for p in l.get('PERSONID_LIST', '').split(';') if p.strip()])
            reason = f'LoginID mapeado para {userid_count} USERIDs e {personid_count} PERSONIDs diferentes'
            
            l_rows.append([
                f"<strong>{l.get('LOGINID')}</strong>", 
                f"<span class='env-data'>{l.get('ENV_LIST')}</span><span class='status-data' style='display:none;'>{lid_status}</span>", 
                l.get('USERID_LIST'), 
                l.get('DISPLAYNAME_LIST'),
                f"<span class='reason-cell'>{reason}</span>",
                f"<span class='dec-data' style='font-weight:600; color: #f59e0b;'>{dec}</span><span class='hyp-data' style='display:none;'>REQUER REVIS├âO</span>"
            ])
        html.append(render_table(['LOGINID AD', 'Bases', 'UserIDs do Maximo', 'Nomes Atribu├¡dos', 'Motivo', 'A├º├úo Recomendada'], l_rows, "loginTable", "filterable-table"))
    else:
        html.append('<p>Nenhum conflito de LOGINID detectado.</p>')
    html.append('</div></div>')

    # --- Bloco 5: Baseline de Perfis por TITLE ---
    html.append('<div class="card">')
    html.append('<h2 class="card-header" onclick="toggleSection(\'section5\')">5. ­ƒÄ» An├ílise de Baseline Funcional: Diverg├¬ncias por TITLE (Cargo Real) <span class="toggle-icon">Ôû╝</span></h2>')
    html.append('<div id="section5" class="card-content collapsed">')
    html.append('<p style="color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem;"><strong>Legenda:</strong> Agrupa usu├írios por cargo (TITLE). <span class="badge" style="background:#ef4444;">ÔÜá´©Å TYPE divergente</span> = na mesma base, pessoas com o mesmo cargo t├¬m TYPEs diferentes (ex: 2 Chefes de Mec├ónica, um TYPE 4 outro TYPE 5). <span class="badge" style="background:#f59e0b;">­ƒö© Grupos divergentes</span> = mesmo cargo, grupos de acesso distintos entre unidades. <strong>Padr├úo esperado:</strong> todos que ocupam o mesmo cargo devem ter TYPE e grupos id├¬nticos. Escopo: <strong>ATIVAS</strong>.</p>')
    
    # Agrupar por TITLE + ENV
    title_patterns = defaultdict(lambda: {
        'types': defaultdict(set),  # title -> env -> set of types
        'groups': defaultdict(set)  # title -> env -> set of groups
    })
    
    if access_rows:
        for item in access_rows:
            title = item.get('TITLE', '').strip()
            if not title:
                continue
            env = item.get('ENV_DB', '').strip()
            type_val = item.get('TYPE', '').strip()
            group = item.get('GROUPNAME', '').strip()
            status = item.get('STATUS', '').strip().upper()
            
            if status == 'ACTIVE' and env:
                if type_val and type_val != 'UNKNOWN':
                    title_patterns[title]['types'][env].add(type_val)
                if group:
                    title_patterns[title]['groups'][env].add(group)
    
    # Construir an├ílise detalhada por TITLE
    title_analysis = []
    for title, data in sorted(title_patterns.items()):
        types_by_env = data['types']
        groups_by_env = data['groups']
        
        all_envs = set(types_by_env.keys()) | set(groups_by_env.keys())
        if len(all_envs) <= 1:
            continue
        
        # Verificar diverg├¬ncia de TYPE
        all_types = set()
        for types_set in types_by_env.values():
            all_types.update(types_set)
        has_type_divergence = len(all_types) > 1
        
        # Verificar diverg├¬ncia de grupos
        if groups_by_env:
            common_groups = set.intersection(*groups_by_env.values()) if len(groups_by_env) > 1 else set()
            has_group_divergence = not all(s == list(groups_by_env.values())[0] for s in groups_by_env.values())
        else:
            common_groups = set()
            has_group_divergence = False
        
        if not has_type_divergence and not has_group_divergence:
            continue
        
        # Construir detalhes
        type_details = []
        group_details = []
        
        if has_type_divergence:
            for env in sorted(all_envs):
                types_in_env = types_by_env.get(env, set())
                if types_in_env and len(types_in_env) > 0:
                    type_details.append({
                        'env': env,
                        'types': sorted(types_in_env),
                        'count': len(types_in_env)
                    })
        
        if has_group_divergence:
            for env in sorted(all_envs):
                groups_in_env = groups_by_env.get(env, set())
                extra_groups = groups_in_env - common_groups if common_groups else groups_in_env
                if groups_in_env:
                    group_details.append({
                        'env': env,
                        'total': len(groups_in_env),
                        'extra': sorted(extra_groups),
                        'common_count': len(common_groups)
                    })
        
        if type_details or group_details:
            title_analysis.append({
                'title': title,
                'envs': sorted(all_envs),
                'has_type_divergence': has_type_divergence,
                'has_group_divergence': has_group_divergence,
                'type_details': type_details,
                'group_details': group_details,
                'common_groups': sorted(common_groups),
                'all_types': sorted(all_types)
            })
    
    if title_analysis:
        html.append('<div class="type-analysis-grid">')
        for ta in title_analysis[:30]:  # Top 30
            html.append('<div class="type-card">')
            
            # Header com badges de alerta
            alerts = []
            if ta['has_type_divergence']:
                alerts.append('<span style="background:#fef2f2;color:#991b1b;padding:2px 6px;border-radius:3px;font-size:0.7rem;font-weight:700;">TYPE DIVERGENTE</span>')
            if ta['has_group_divergence']:
                alerts.append('<span style="background:#fff7ed;color:#9a3412;padding:2px 6px;border-radius:3px;font-size:0.7rem;font-weight:700;">GRUPOS DIVERGENTES</span>')
            
            html.append(f'<h4><span class="tooltip">{ta["title"]} {" ".join(alerts)}<span class="tooltiptext">Este cargo aparece em {len(ta["envs"])} unidades: {", ".join(ta["envs"])}</span></span></h4>')
            
            # Diverg├¬ncias de TYPE
            if ta['has_type_divergence'] and ta['type_details']:
                html.append(f'<div style="margin-bottom: 1rem; padding: 0.6rem; background: #fef2f2; border-left: 3px solid #ef4444; border-radius: 4px;">')
                html.append(f'<div style="font-weight: 600; color: #991b1b; font-size: 0.85rem; margin-bottom: 0.3rem;">ÔÜá´©Å Inconsist├¬ncia de TYPE ÔÇö {len(ta["all_types"])} classifica├º├Áes para o mesmo cargo:</div>')
                for td in ta['type_details']:
                    types_list = ', '.join([f"{t}" for t in sorted(td['types'])])
                    html.append(f'<div style="font-size: 0.8rem; color: #7f1d1d; margin-left: 0.5rem;">­ƒôì <strong>{td["env"]}</strong>: {types_list} <span style="color:#991b1b;">({td["count"]} usu├írio{"s" if td["count"] > 1 else ""} neste cargo com TYPE{"s" if td["count"] > 1 else ""} diferente{"s" if td["count"] > 1 else ""})</span></div>')
                html.append('</div>')
            
            # Baseline e Diverg├¬ncias de Grupos
            if ta['has_group_divergence'] and ta['group_details']:
                if ta['common_groups']:
                    html.append(f'<div style="margin-bottom: 0.8rem; padding: 0.6rem; background: #f0fdf4; border-left: 3px solid #10b981; border-radius: 4px;">')
                    html.append(f'<div style="font-weight: 600; color: #166534; font-size: 0.85rem; margin-bottom: 0.3rem;">Ô£ô Baseline Comum ({len(ta["common_groups"])} grupos):</div>')
                    html.append(f'<div style="font-size: 0.75rem; color: #166534;">{", ".join(ta["common_groups"][:8])}{"..." if len(ta["common_groups"]) > 8 else ""}</div>')
                    html.append('</div>')
                
                for gd in ta['group_details']:
                    if gd['extra']:
                        html.append(f'<div class="env-divergence">')
                        html.append(f'<div class="env-header">­ƒö© {gd["env"]} ÔÇö {gd["total"]} grupos (+{len(gd["extra"])} extras)</div>')
                        html.append(f'<div class="extra-groups"><strong>Adi├º├Áes locais:</strong> {", ".join(gd["extra"][:10])}{"..." if len(gd["extra"]) > 10 else ""}</div>')
                        html.append('</div>')
            
            html.append('</div>')
        html.append('</div>')
    else:
        html.append('<div class="alert-success" style="margin-top:0;"><strong>Ô£à Baseline Perfeito!</strong> N├úo h├í diverg├¬ncias detectadas. Todos os cargos (TITLEs) possuem TYPE e grupos consistentes entre unidades.</div>')
    
    # Atualizar card de diverg├¬ncias
    html.append(f'<script>document.getElementById("stat-divergent").innerHTML = "{fmt_br(len(title_analysis))}";</script>')
    
    html.append('</div></div>')
    
    # --- Legacy Baseline View (Mantido para compatibilidade) ---
    html.append('<div class="card">')
    html.append('<h2 class="card-header" onclick="toggleSection(\'section5legacy\')">6. ­ƒôè Vis├úo Legada: Auditoria de Perfis (Modo Comparativo) <span class="toggle-icon">Ôû╝</span></h2>')
    html.append('<div id="section5legacy" class="card-content collapsed">')
    html.append('<p style="color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem;"><strong>Legenda:</strong> Comparativo de grupos por TYPE (classifica├º├úo gen├®rica). <span class="badge-grp common">Grupos comuns</span> = presentes em todas as unidades. <span class="badge-grp diff">Grupos locais</span> = adicionados apenas em algumas bases (destacados em azul por unidade). Escopo: <em>todas as contas</em>.</p>')
    
    type_group_patterns_legacy = defaultdict(lambda: defaultdict(set))
    if access_rows:
        for item in access_rows:
            t = item.get('TYPE', '').strip()
            env = item.get('ENV_DB', '').strip()
            group = item.get('GROUPNAME', '').strip()
            if t and t != 'UNKNOWN' and group:
                type_group_patterns_legacy[t][env].add(group)
                
    divergences_html = []
    divergences_excel = []
    
    for t, envs_data in sorted(type_group_patterns_legacy.items()):
        all_envs = list(envs_data.keys())
        if len(all_envs) <= 1: continue
        
        first_env = all_envs[0]
        base_set = envs_data[first_env]
        if all(s == base_set for s in envs_data.values()): continue

        common_groups = set.intersection(*envs_data.values())
        
        html_str = "<div class='baseline-compare'>"
        if common_groups:
            html_str += "<div class='common-groups'><span class='grp-label'>Padr├úo Comum a todas as bases envolvidas:</span>"
            html_str += "".join([f"<span class='badge-grp common'>{g}</span>" for g in sorted(common_groups)])
            html_str += "</div>"
        
        html_str += "<div class='diff-groups'><span class='grp-label'>Diverg├¬ncias (Grupos a mais adicionados localmente):</span>"
        for env in sorted(all_envs):
            diff = envs_data[env] - common_groups
            html_str += f"<div class='env-row'><span class='env-name'>{env}</span> "
            if diff:
                html_str += "".join([f"<span class='badge-grp diff'>{g}</span>" for g in sorted(diff)])
            else:
                html_str += "<span class='badge-grp diff-none'>Mesmo do padr├úo comum</span>"
            html_str += "</div>"
        html_str += "</div></div>"
        
        divergences_html.append([f"<strong>{t}</strong>", html_str])
        
        xl_str = ""
        if common_groups:
            xl_str += "COMUM A TODAS: " + ", ".join(sorted(common_groups)) + "\n"
        for env in sorted(all_envs):
            diff = envs_data[env] - common_groups
            if diff:
                xl_str += f"Diferen├ºa em {env} (+): " + ", ".join(sorted(diff)) + "\n"
        divergences_excel.append([t, xl_str.strip()])

    if divergences_html:
        # Manually build the table to avoid escaping HTML
        html.append('<div class="table-responsive"><table><thead><tr><th>Cargo / TYPE Funcional</th><th>An├ílise do Pacote de Grupos de Seguran├ºa</th></tr></thead><tbody>')
        for row in divergences_html[:30]:
            html.append(f'<tr><td>{row[0]}</td><td>{row[1]}</td></tr>')
        html.append('</tbody></table></div>')
    else:
        html.append('<div class="alert-success" style="margin-top:0;"><strong>Ô£à Padr├úo Perfeito!</strong> N├úo h├í diverg├¬ncias de grupos de seguran├ºa mapeados nas fun├º├Áes atuais.</div>')
        
    html.append('</div></div>')

    # Footer and Scripts
    html.append('''
        </div>
        <script>
            // Toggle Acordeon
            function toggleSection(id) {
                var element = document.getElementById(id);
                var header = element.previousElementSibling;
                var icon = header.querySelector('.toggle-icon');
                if (element.classList.contains("collapsed")) {
                    element.classList.remove("collapsed");
                    header.classList.remove("collapsed");
                } else {
                    element.classList.add("collapsed");
                    header.classList.add("collapsed");
                }
            }

            // Executa o filtro de Status 'Ativo' ao carregar a pagina 
            document.addEventListener("DOMContentLoaded", function() {
                filterTable();
            });
            
            function filterTable() {
                var input = document.getElementById("searchInput").value.toUpperCase();
                var envFilter = document.getElementById("envFilter").value.toUpperCase();
                var statusFilter = document.getElementById("statusFilter").value.toUpperCase();
                var decFilter = document.getElementById("decFilter").value.toUpperCase();
                
                // Atualizar cards baseado no filtro de status
                updateStatCards(statusFilter);
                
                var tables = document.querySelectorAll(".filterable-table");
                
                tables.forEach(function(table) {
                    var tr = table.getElementsByTagName("tr");
                    
                    for (var i = 1; i < tr.length; i++) {
                        var td = tr[i].getElementsByTagName("td");
                        
                        if(td.length > 0) {
                            var textContent = tr[i].textContent || tr[i].innerText;
                            var matchInput = input === "" || textContent.toUpperCase().indexOf(input) > -1;
                            
                            var envSpan = tr[i].querySelector('.env-data');
                            var envContent = envSpan ? envSpan.innerText.toUpperCase() : "";
                            var matchEnv = envFilter === "" || envContent.indexOf(envFilter) > -1;
                            
                            var statusSpan = tr[i].querySelector('.status-data');
                            var statusContent = statusSpan ? statusSpan.innerText.toUpperCase() : "";
                            var matchStatus = true;
                            
                            if (statusFilter !== "") {
                                var statuses = statusContent.split(';').map(function(s) { return s.trim(); });
                                if (statusFilter === "ACTIVE") {
                                    matchStatus = statuses.includes("ACTIVE");
                                } else if (statusFilter === "INACTIVE") {
                                    matchStatus = statuses.some(function(s) { return s !== "ACTIVE" && s !== ""; }) || statusContent === "";
                                }
                            }
                            
                            var decSpan = tr[i].querySelector('.dec-data');
                            var decContent = decSpan ? decSpan.innerText.toUpperCase() : "";
                            
                            var hypSpan = tr[i].querySelector('.hyp-data');
                            var hypContent = hypSpan ? hypSpan.innerText.toUpperCase() : "";
                            
                            var matchDec = decFilter === "" || decContent.indexOf(decFilter) > -1 || hypContent.indexOf(decFilter) > -1;
                            
                            if (matchInput && matchEnv && matchStatus && matchDec) {
                                tr[i].style.display = "";
                            } else {
                                tr[i].style.display = "none";
                            }
                        }
                    }
                });
            }
            
            function updateStatCards(statusFilter) {
                function formatBR(num) {
                    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
                }
                
                var statUnique = document.getElementById("stat-unique-active");
                var statRecords = document.getElementById("stat-records");
                var statReuse = document.getElementById("stat-reuse");
                var statCritical = document.getElementById("stat-critical");
                var statProfile = document.getElementById("stat-profile");
                
                var scopeLabel = statusFilter === "ACTIVE" ? "(Ativas)" : statusFilter === "INACTIVE" ? "(Inativas)" : "(Todas)";
                
                if (statusFilter === "" || statusFilter === "ACTIVE") {
                    statUnique.innerHTML = formatBR(statUnique.getAttribute('data-active'));
                    statRecords.innerHTML = formatBR(statRecords.getAttribute('data-active'));
                    statReuse.innerHTML = formatBR(statReuse.getAttribute('data-active'));
                    statCritical.innerHTML = formatBR(statCritical.getAttribute('data-active'));
                    statProfile.innerHTML = formatBR(statProfile.getAttribute('data-active'));
                } else {
                    statUnique.innerHTML = formatBR(statUnique.getAttribute('data-all'));
                    statRecords.innerHTML = formatBR(statRecords.getAttribute('data-all'));
                    statReuse.innerHTML = formatBR(statReuse.getAttribute('data-all'));
                    statCritical.innerHTML = formatBR(statCritical.getAttribute('data-all'));
                    statProfile.innerHTML = formatBR(statProfile.getAttribute('data-all'));
                }
                
                document.getElementById("stat-unique-scope").innerHTML = scopeLabel;
                document.getElementById("stat-records-scope").innerHTML = scopeLabel;
                document.getElementById("stat-reuse-scope").innerHTML = scopeLabel;
                document.getElementById("stat-critical-scope").innerHTML = scopeLabel;
                document.getElementById("stat-profile-scope").innerHTML = scopeLabel;
            }
            
            
            // Graficos Chart.js
            
            const uniqueEnvCtx = document.getElementById('uniqueEnvChart').getContext('2d');
            new Chart(uniqueEnvCtx, {
                type: 'bar',
                data: {
                    labels: ''' + str(env_labels) + ''',
                    datasets: [{
                        label: 'Contas Ativas (Logins ├Ünicos por Sonda)',
                        data: ''' + str(unique_active_env_data) + ''',
                        backgroundColor: '#10b981',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false }, title: { display: true, text: 'Mapeamento AppPoints: Pessoas ├Ünicas por Base', font: {size: 14} } },
                    scales: { y: { beginAtZero: true } }
                }
            });
            
            const statCtx = document.getElementById('statusChart').getContext('2d');
            new Chart(statCtx, {
                type: 'pie',
                data: {
                    labels: ['Ativos', 'Inativos/Outros'],
                    datasets: [{
                        data: [''' + str(active_records) + ''', ''' + str(total_records - active_records) + '''],
                        backgroundColor: ['#10b981', '#cbd5e1'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'right' }, title: { display: true, text: 'Status Global da Base Hist├│rica', font: {size: 14} } }
                }
            });
        </script>
        </body></html>
    ''')
    return '\n'.join(html), divergences_excel


def build_excel(divergences_excel):
    if not HAS_OPENPYXL:
        return
        
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    cross_env = load_csv(IN_DIR / 'cross_env_userid_reuse.csv')
    login_conflicts = load_csv(IN_DIR / 'login_conflicts.csv')
    worklist = load_csv(IN_DIR / 'identity_collisions_enriched.csv')
    access_rows = load_csv(IN_DIR / 'consolidated_user_access_normalized.csv') or load_csv(IN_DIR / 'consolidated_user_access.csv')
    
    header_fill = PatternFill(start_color='0f172a', end_color='0f172a', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    thin_border = Border(left=Side(style='thin', color='e2e8f0'), right=Side(style='thin', color='e2e8f0'), top=Side(style='thin', color='e2e8f0'), bottom=Side(style='thin', color='e2e8f0'))

    def add_sheet(title, headers, rows_of_dicts=None, raw_rows=None):
        ws = wb.create_sheet(title)
        ws.append(headers)
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
            
        if rows_of_dicts:
            for row_dict in rows_of_dicts:
                row_data = []
                for h in headers:
                    val = row_dict.get(h, '')
                    try:
                        if str(val).isdigit(): val = int(val)
                    except: pass
                    if isinstance(val, str):
                        val = val.replace('<br/>', '\n').replace('<strong>', '').replace('</strong>', '')
                    row_data.append(val)
                ws.append(row_data)
        elif raw_rows:
            for row in raw_rows:
                ws.append(row)
                
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.border = thin_border
                if cell.value and isinstance(cell.value, str) and '\n' in cell.value:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
                    
        for col in ws.columns:
            max_len = max((len(str(cell.value)) for cell in col if cell.value), default=0)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 45)

    # 1. ExecutiveSummary
    ws = wb.create_sheet('1_VisaoExecutiva')
    ws.append(['M├®trica', 'Valor'])
    
    unique_logins_all = len(set([r.get('USERID', '').strip().upper() for r in identities if r.get('USERID', '').strip()]))
    unique_active_logins = len(set([r.get('USERID', '').strip().upper() for r in identities if r.get('USERID', '').strip() and r.get('STATUS', '').upper() == 'ACTIVE']))
    
    ws.append(['Total de Usu├írios (Base Hist├│rica Bruta)', len(identities) if identities else 0])
    ws.append(['Pessoas ├Ünicas Identificadas (Apenas Ativos para AppPoints)', unique_active_logins])
    ws.append(['Registros Ativos no Maximo (N├úo Tratados)', sum(1 for r in identities if r.get('STATUS', '').upper() == 'ACTIVE') if identities else 0])
    
    # Baseado na view ATIVA:
    active_worklist = [w for w in worklist if w.get('STATUS', '').upper() == 'ACTIVE']
    ws.append(['USERIDs Repetidos (Risco de Reuso Ativo)', len(set([w.get('USERID') for w in active_worklist])) if active_worklist else 0])
    ws.append(['Colis├Áes Cr├¡ticas (Pessoas Diferentes Ativas)', sum(1 for c in active_worklist if c.get('HYPOTHESIS') == 'CONFIRMED_DIFFERENT_PERSON') if active_worklist else 0])
    ws.append(['Pendentes Valida├º├úo AD (Ativos)', sum(1 for c in active_worklist if c.get('MERGE_DECISION') in ('AWAITING_AD_MATCH', 'MERGE_AFTER_AD_MATCH')) if active_worklist else 0])
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
    ws.column_dimensions['A'].width = 45
    ws.column_dimensions['B'].width = 20

    if identities: add_sheet('2_ResumoIdentidades', list(identities[0].keys()), identities)
    if cross_env: add_sheet('3_ReusoUSERID_CrossEnv', list(cross_env[0].keys()), cross_env)
    if login_conflicts: add_sheet('4_ConflitosLoginID', list(login_conflicts[0].keys()), login_conflicts)
        
    if worklist:
        critical = [c for c in worklist if c.get('HYPOTHESIS') == 'CONFIRMED_DIFFERENT_PERSON']
        if critical: add_sheet('5_Criticos_PessoasDiferentes', list(critical[0].keys()), critical)
        awaiting = [c for c in worklist if c.get('MERGE_DECISION') in ('AWAITING_AD_MATCH', 'MERGE_AFTER_AD_MATCH')]
        if awaiting: add_sheet('6_AguardandoMatchAD', list(awaiting[0].keys()), awaiting)
        add_sheet('7_FilaSaneamento_Worklist', list(worklist[0].keys()), worklist)
        
    if access_rows:
        acc_map = defaultdict(lambda: {'ENV_DB':'', 'USERID':'', 'PERSONID':'', 'STATUS':'', 'TYPE':'', 'GROUPS':set()})
        for r in access_rows:
            raw = f"{r.get('ENV_DB','').strip()}|{r.get('USERID','').strip()}"
            if not acc_map[raw]['ENV_DB']:
                acc_map[raw].update({
                    'ENV_DB': r.get('ENV_DB',''), 'USERID': r.get('USERID',''),
                    'PERSONID': r.get('PERSONID',''), 'STATUS': r.get('STATUS',''), 'TYPE': r.get('TYPE','')
                })
            grp = r.get('GROUPNAME','')
            if grp: acc_map[raw]['GROUPS'].add(grp.strip())
            
        flat_acc = []
        for raw, data in sorted(acc_map.items()):
            data['GROUPS_LIST'] = '; '.join(sorted(data['GROUPS']))
            data['GROUPS_COUNT'] = len(data['GROUPS'])
            flat_acc.append(data)
            
        add_sheet('8_AcessosPorIDBruto', ['ENV_DB', 'USERID', 'PERSONID', 'STATUS', 'TYPE', 'GROUPS_COUNT', 'GROUPS_LIST'], flat_acc)
        
        # --- Baseline Divergences (Aba 9 Excel) ---
        if divergences_excel:
            add_sheet('9_BaselineDivergences', ['User Type', 'Divergences'], raw_rows=divergences_excel)
            
        add_sheet('10_AcessosExpandido', list(access_rows[0].keys()), access_rows)

    try:
        wb.save(OUT_DIR / 'maximo_identity_sanity_workbook.xlsx')
        print(f"WROTE maximo_identity_sanity_workbook.xlsx")
    except PermissionError:
        print(f"ERROR: Cannot save Excel file. Please close it.")

def main():
    html_content, div_xl = build_html()
    html_path = OUT_DIR / 'maximo_identity_sanity_report.html'
    html_path.write_text(html_content, encoding='utf-8')
    print(f'WROTE {html_path.name}')
    build_excel(div_xl)

if __name__ == '__main__':
    main()
