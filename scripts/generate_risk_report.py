# generate_risk_report.py (Orchestrator)
import sys
import csv
import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# --- CRITICAL FIX: Add the project root to sys.path ---
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import modularized components
from scripts.config import get_app_points_config, get_entitlement_keywords, get_critical_titles, get_foresea_domains
from scripts.domain.user import build_user_profiles, get_user_domain_category
from scripts.services.analysis import analyze_governance, analyze_title_divergences
from scripts.services.app_points import simulate_app_points
from scripts.reporting.html_builder import build_html_structure
from scripts.reporting.html_helpers import fmt_br, render_table
# --- NOVA IMPORTAÇÃO CORRIGIDA ---
from scripts.domain.identity_analyzer import get_unique_users_data
# --- NOVA IMPORTAÇÃO: SANITY ANALYZER ---
from scripts.domain.sanity_analyzer import analyze_sanity
from scripts.domain.migration_advisor import analyze_migration


# --- Constants ---
IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'reports'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Data Loading ---
def load_all_data():
    """Loads all necessary CSV files from the consolidated directory."""
    return {
        "identities": load_csv(IN_DIR / 'consolidated_user_identity.csv'),
        "access_rows": load_csv(IN_DIR / 'consolidated_user_access_normalized.csv') or load_csv(IN_DIR / 'consolidated_user_access.csv'),
        "cross_env": load_csv(IN_DIR / 'cross_env_userid_reuse.csv'),
        "login_conflicts": load_csv(IN_DIR / 'login_conflicts.csv'),
        "worklist": load_csv(IN_DIR / 'identity_collisions_enriched.csv'),
        "emails": load_csv(IN_DIR / 'consolidated_email.csv'),
        "persons": load_csv(IN_DIR / 'consolidated_person.csv') + load_person_supplements(),
        "persongroupview": load_csv(IN_DIR / 'consolidated_persongroupview.csv'),
        # --- NOVAS FONTES: AD e Maximo ---
        "ad_users": load_csv(IN_DIR / 'consolidated_ad_users.csv'),
        "maximo_users": load_csv(IN_DIR / 'consolidated_maximo_users.csv'),
    }

def detect_delimiter(path: Path):
    """Detecta automaticamente o delimitador de um CSV."""
    with path.open('r', encoding='utf-8-sig') as f:
        first_line = f.readline()
    if ';' in first_line:
        return ';'
    return ','

def load_csv(path: Path):
    """Helper to load a single CSV, returning an empty list if not found."""
    if not path.exists(): return []
    delim = detect_delimiter(path)
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delim))

def load_person_supplements():
    """Loads supplemental PERSON snapshots kept in the knowledge base folder."""
    rows = []
    base_dir = ROOT / 'Base Conhecimento' / 'Base'
    for path in base_dir.glob('PERSON_*.csv'):
        rows.extend(load_csv(path))
    return rows

def write_license_decision_plan(rows):
    """Writes an auditable CSV with the final license recommendation per user.
    Ensures LOCATION_SITE is present by enriching rows from usage_analysis_phase3.csv when missing.
    """
    if not rows:
        return
    # Build a mapping user -> LOCATION_SITE from usage CSV (if available)
    # IMPORTANT: Take the FIRST non-empty value found (don't overwrite with empty values)
    usage_map = {}
    usage_path = IN_DIR / 'usage_analysis_phase3.csv'
    if usage_path.exists():
        try:
            with usage_path.open(encoding='utf-8-sig', newline='') as uf:
                ureader = csv.DictReader(uf)
                for ur in ureader:
                    uid = str(ur.get('USERID', '')).strip().upper()
                    if uid and uid not in usage_map:  # Only set if not already set
                        # O campo no CSV é LOCAL_SITE (não LOCATION_SITE)
                        location = ur.get('LOCAL_SITE') or ur.get('LOCATION_SITE') or ur.get('LOCATION') or ''
                        if location:  # Only set if non-empty
                            usage_map[uid] = location
        except Exception:
            pass

    # Enrich rows with LOCATION_SITE if missing or invalid (e.g., '0')
    for row in rows:
        uid = str(row.get('USERID', '')).strip().upper()
        location_site = row.get('LOCATION_SITE', '')
        if uid and (not location_site or location_site == '0'):
            row['LOCATION_SITE'] = usage_map.get(uid, '')

    fieldnames = [
        'USERID', 'DISPLAYNAME', 'ENTITLEMENT', 'LICENSE_MODEL', 'APP_POINTS',
        'EMAIL', 'DOMAIN_CATEGORY', 'MIGRATION_SCOPE', 'OPERATIONAL_PRESENCE',
        'LOCATION_SITE', 'USAGE_PROFILE', 'OPTIMIZATION_REC',
        'OPTIMIZATION_REASON', 'LOGIN_COUNT_90D', 'DAYS_SINCE_LAST',
        'FACTOR_P50', 'FACTOR_P95', 'FACTOR_P100', 'TITLES', 'ACTIVE_HOURS'
    ]
    out_path = IN_DIR / 'license_decision_plan.csv'
    with out_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            if 'ACTIVE_HOURS' in row and isinstance(row['ACTIVE_HOURS'], list):
                row['ACTIVE_HOURS'] = '|'.join(row['ACTIVE_HOURS'])
            writer.writerow(row)
    print(f'✓ WROTE {out_path.name}')

def write_excel_workbook(summary, governance, license_rows, domain_counts, missing_email_rows, sanity_data=None, migration_data=None, identities=None):
    """Creates the final consolidated governance workbook used by the pipeline."""
    wb = Workbook()
    wb.remove(wb.active)

    header_fill = PatternFill(start_color='0f172a', end_color='0f172a', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    thin_border = Border(
        left=Side(style='thin', color='e2e8f0'),
        right=Side(style='thin', color='e2e8f0'),
        top=Side(style='thin', color='e2e8f0'),
        bottom=Side(style='thin', color='e2e8f0'),
    )

    def add_sheet(title, headers, rows):
        ws = wb.create_sheet(title[:31])
        ws.append(headers)
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center')

        for row in rows:
            if isinstance(row, dict):
                values = []
                for h in headers:
                    v = row.get(h, '')
                    # Convert sets to strings for Excel compatibility
                    if isinstance(v, set):
                        v = '; '.join(sorted(str(x) for x in v if x)) if v else ''
                    values.append(v)
            else:
                values = row
            ws.append(values)

        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical='top', wrap_text=True)

        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            max_len = max((len(str(cell.value)) for cell in col if cell.value is not None), default=0)
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 2, 12), 45)

    license_headers = [
        'USERID', 'DISPLAYNAME', 'EMAIL', 'DOMAIN_CATEGORY', 'MIGRATION_SCOPE',
        'ENTITLEMENT', 'LICENSE_MODEL', 'APP_POINTS', 'LOCATION_SITE',
        'USAGE_PROFILE', 'OPTIMIZATION_REC', 'OPTIMIZATION_REASON',
        'LOGIN_COUNT_90D', 'DAYS_SINCE_LAST', 'FACTOR_P50', 'FACTOR_P95',
        'FACTOR_P100', 'TITLES'
    ]

    scenario = summary.get('app_points_summary', {})
    executive_rows = [
        ['Gerado em', datetime.now().strftime('%d/%m/%Y %H:%M')],
        ['Usuarios ativos analisados', summary.get('active_profiles_count', 0)],
        ['Usuarios no plano de licenca', len(license_rows)],
        ['Usuarios sem dominio para revisao', len(missing_email_rows)],
        ['Authorized', len(scenario.get('auth_users', []))],
        ['Concurrent', len(scenario.get('conc_users', []))],
        ['Premium', len(scenario.get('premium_users', []))],
    ]
    for domain, count in sorted(domain_counts.items()):
        executive_rows.append([f'Dominio: {domain}', count])

    add_sheet('1_VisaoExecutiva', ['Metrica', 'Valor'], executive_rows)
    add_sheet('2_LicenseDecisionPlan', license_headers, license_rows)

    # Add concurrency peak and contributors if available in summary
    concurrency = summary.get('concurrency', {})
    if concurrency:
        hourly_users = concurrency.get('hourly_counts', {})
        hourly_points = concurrency.get('hourly_app_points', {})
        hourly_nem = concurrency.get('hourly_app_points_nem', {})
        if hourly_users or hourly_points or hourly_nem:
            hours = sorted(set(hourly_users) | set(hourly_points) | set(hourly_nem))
            hourly_rows = [
                [h, hourly_users.get(h, 0), hourly_points.get(h, 0), hourly_nem.get(h, 0)]
                for h in hours
            ]
            add_sheet(
                '7_ConcurrentPeak',
                ['Hour', 'Usuarios simultaneos', 'AppPoints observados', 'AppPoints NEM'],
                hourly_rows,
            )

        # Peak contributors sheet (8_PeakContributors)
        contributors = concurrency.get('peak_contributors', [])
        if contributors:
            # contributors is a list of USERID or dicts
            if isinstance(contributors[0], dict):
                contrib_headers = list(contributors[0].keys())
                add_sheet('8_PeakContributors', contrib_headers, contributors)
            else:
                add_sheet('8_PeakContributors', ['USERID'], [[c] for c in contributors])

    if missing_email_rows:
        review_headers = [
            'USERID', 'DISPLAYNAME', 'STATUS', 'ENVS', 'TYPE', 'GROUPS_COUNT',
            'GROUPS', 'TITLES', 'PERSONGROUPS', 'REVIEW_REASON'
        ]
        add_sheet('3_RevisarSemDominio', review_headers, missing_email_rows)

    for sheet_name, key in [
        ('4_ReusoUSERID_CrossEnv', 'cross_env'),
        ('5_ConflitosLoginID', 'login_conflicts'),
        ('6_FilaSaneamento', 'worklist'),
    ]:
        rows = governance.get(key, [])
        if rows:
            add_sheet(sheet_name, list(rows[0].keys()), rows)

    # Adicionar Aba 7: Saneamento de Identidades (AD vs Maximo)
    if sanity_data:
        add_sanity_sheets(wb, sanity_data, add_sheet)
    
    # Adicionar Aba 8: Recomendações de Migração
    if migration_data:
        add_migration_sheets(wb, migration_data, add_sheet)
    
    # Adicionar Aba 18: Usuários Ativos Únicos do Maximo
    if identities:
        add_maximo_active_users_sheet(wb, identities, add_sheet)
    
    # Adicionar Aba 19: Acessos por Tipo de Perfil
    if identities:
        add_profile_access_sheet(wb, identities, add_sheet)
    
    # Adicionar Aba 20: Auditoria - Data de Concessão de Acesso
    persongroupview = governance.get('persongroupview', [])
    if persongroupview:
        add_audit_sheet(wb, persongroupview, add_sheet)

    out_path = OUT_DIR / 'maximo_risk_and_optimization_workbook.xlsx'
    try:
        # Tentar remover arquivo existente se houver
        if out_path.exists():
            out_path.unlink()
        wb.save(out_path)
        print(f'✓ WROTE {out_path.name}')
    except PermissionError:
        # Se não conseguir sobrescrever, usar nome com timestamp
        alt_path = OUT_DIR / f'maximo_risk_and_optimization_workbook_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        wb.save(alt_path)
        print(f'✓ WROTE {alt_path.name} (arquivo original estava aberto)')

# --- Sanity Excel Sheets ---
def add_sanity_sheets(wb, sanity_data, add_sheet):
    """Adiciona abas do Excel com dados de saneamento de identidades."""
    
    # Aba 9: Resumo de Saneamento
    stats = sanity_data['stats']
    summary_rows = [
        ['Métrica', 'Valor'],
        ['Total AD', stats['total_ad']],
        ['Total Maximo (identities)', stats['total_maximo_identities']],
        ['Total Maximo (USERIDs únicos)', stats['total_maximo_userids']],
        ['', ''],
        ['MATCH POR EMAIL', ''],
        ['Match perfeito', stats['match_email']],
        ['Apenas no AD', stats['only_ad']],
        ['Apenas no Maximo', stats['only_maximo']],
        ['', ''],
        ['DIVERGÊNCIAS', ''],
        ['Nomes diferentes (mesmo email)', stats['name_divergences']],
        ['Múltiplos USERIDs (mesmo email)', stats['multi_userid']],
        ['Domínios divergentes', stats['domain_divergences']],
        ['', ''],
        ['MATCH POR PREFIXO (USERID)', ''],
        ['Match encontrado', stats['prefix_match']],
        ['Sem match no Maximo', stats['no_match']],
        ['', ''],
        ['MAXIMO SEM EMAIL', ''],
        ['Com match no AD', stats['maximo_sem_email_match']],
        ['Sem match no AD', stats['maximo_sem_email_nomatch']],
    ]
    add_sheet('9_Saneamento_Resumo', ['Métrica', 'Valor'], summary_rows)
    
    # Aba 10: Divergências de Nome
    if sanity_data['analises']['name_divergences']:
        headers = ['Email', 'Nome AD', 'GivenName AD', 'Surname AD', 'Nomes Maximo', 
                   'USERIDs Maximo', 'Ambientes Maximo', 'Status Maximo', 'Domínio', 
                   'AD Habilitado', 'Qtd Grupos AD', 'Tipo']
        rows = []
        for d in sanity_data['analises']['name_divergences']:
            rows.append({
                'Email': d['email'],
                'Nome AD': d['ad_displayname'],
                'GivenName AD': d['ad_givenname'],
                'Surname AD': d['ad_surname'],
                'Nomes Maximo': d['maximo_names'],
                'USERIDs Maximo': d['maximo_userids'],
                'Ambientes Maximo': d['maximo_envs'],
                'Status Maximo': d['maximo_statuses'],
                'Domínio': d['domain'],
                'AD Habilitado': 'Sim' if d['ad_enabled'] else 'Não',
                'Qtd Grupos AD': d['ad_groups_count'],
                'Tipo': d['tipo'],
            })
        add_sheet('10_Divergencias_Nome', headers, rows)
    
    # Aba 11: Múltiplos USERIDs
    if sanity_data['analises']['multi_userid']:
        headers = ['Email', 'Nome AD', 'Qtd USERIDs', 'USERIDs', 'Ambientes', 'Status', 'Domínio', 'Tipo']
        rows = []
        for d in sanity_data['analises']['multi_userid']:
            rows.append({
                'Email': d['email'],
                'Nome AD': d['ad_displayname'],
                'Qtd USERIDs': d['qtd_userids'],
                'USERIDs': d['userids'],
                'Ambientes': d['envs'],
                'Status': d['statuses'],
                'Domínio': d['domain'],
                'Tipo': d['tipo'],
            })
        add_sheet('11_Multiplos_USERIDs', headers, rows)
    
    # Aba 12: Match por Prefixo (USERID)
    if sanity_data['analises']['prefix_match']:
        headers = ['Email', 'Nome AD', 'USERID Maximo', 'Nomes Maximo', 'Ambientes Maximo',
                   'Status Maximo', 'Emails Maximo', 'Domínio', 'AD Habilitado', 'Qtd Grupos AD', 'Tipo']
        rows = []
        for d in sanity_data['analises']['prefix_match']:
            rows.append({
                'Email': d['email'],
                'Nome AD': d['ad_displayname'],
                'USERID Maximo': d['maximo_userid'],
                'Nomes Maximo': d['maximo_displaynames'],
                'Ambientes Maximo': d['maximo_envs'],
                'Status Maximo': d['maximo_statuses'],
                'Emails Maximo': d['maximo_emails'],
                'Domínio': d['domain'],
                'AD Habilitado': 'Sim' if d['ad_enabled'] else 'Não',
                'Qtd Grupos AD': d['ad_groups_count'],
                'Tipo': d['tipo'],
            })
        add_sheet('12_Match_Prefixo', headers, rows)
    
    # Aba 13: Sem Match no Maximo
    if sanity_data['analises']['no_match']:
        headers = ['Email', 'Nome AD', 'GivenName AD', 'Surname AD', 'Prefixo', 
                   'Domínio', 'AD Habilitado', 'Qtd Grupos AD', 'Tipo']
        rows = []
        for d in sanity_data['analises']['no_match']:
            rows.append({
                'Email': d['email'],
                'Nome AD': d['ad_displayname'],
                'GivenName AD': d['ad_givenname'],
                'Surname AD': d['ad_surname'],
                'Prefixo': d['prefix'],
                'Domínio': d['domain'],
                'AD Habilitado': 'Sim' if d['ad_enabled'] else 'Não',
                'Qtd Grupos AD': d['ad_groups_count'],
                'Tipo': d['tipo'],
            })
        add_sheet('13_Sem_Match_Maximo', headers, rows)
    
    # Aba 14: Maximo sem Email (com match AD)
    if sanity_data['analises']['maximo_sem_email_match']:
        headers = ['USERID', 'Nomes Maximo', 'Ambientes Maximo', 'Status Maximo', 'Títulos Maximo',
                   'Email AD', 'Nome AD', 'AD Habilitado', 'Qtd Grupos AD', 'Tipo']
        rows = []
        for d in sanity_data['analises']['maximo_sem_email_match']:
            rows.append({
                'USERID': d['userid'],
                'Nomes Maximo': d['maximo_displaynames'],
                'Ambientes Maximo': d['maximo_envs'],
                'Status Maximo': d['maximo_statuses'],
                'Títulos Maximo': d['maximo_titles'],
                'Email AD': d['ad_email'],
                'Nome AD': d['ad_displayname'],
                'AD Habilitado': 'Sim' if d['ad_enabled'] else 'Não',
                'Qtd Grupos AD': d['ad_groups_count'],
                'Tipo': d['tipo'],
            })
        add_sheet('14_Maximo_Sem_Email_Match', headers, rows)
    
    # Aba 15: Divergências de Domínio
    if sanity_data['analises']['domain_divergences']:
        headers = ['Email', 'Nome AD', 'Domínio AD', 'Domínio Maximo', 'USERID Maximo',
                   'Ambiente Maximo', 'Status Maximo', 'Tipo']
        rows = []
        for d in sanity_data['analises']['domain_divergences']:
            rows.append({
                'Email': d['email'],
                'Nome AD': d['ad_displayname'],
                'Domínio AD': d['ad_domain'],
                'Domínio Maximo': d['maximo_domain'],
                'USERID Maximo': d['maximo_userid'],
                'Ambiente Maximo': d['maximo_env'],
                'Status Maximo': d['maximo_status'],
                'Tipo': d['tipo'],
            })
        add_sheet('15_Divergencias_Dominio', headers, rows)


# --- Maximo Active Users Excel Sheet ---
def add_maximo_active_users_sheet(wb, identities, add_sheet):
    """Adiciona aba com todos os usuários únicos ativos no Maximo."""
    
    def clean_value(v):
        """Remove caracteres ilegais do Excel (caracteres de controle)."""
        if v is None:
            return ''
        s = str(v)
        return ''.join(c if ord(c) >= 32 or c in '\n\r\t' else '' for c in s)
    
    # Filtrar apenas usuários ativos
    active_users = [r for r in identities if r.get('STATUS', '').strip().upper() == 'ACTIVE']
    
    # Deduplicar por USERID (pegar primeiro registro de cada USERID)
    seen_userids = set()
    unique_active = []
    for user in active_users:
        userid = user.get('USERID', '').strip().upper()
        if userid and userid not in seen_userids:
            seen_userids.add(userid)
            unique_active.append(user)
    
    # Preparar headers e rows
    headers = ['USERID', 'DISPLAYNAME', 'PRIMARYEMAIL', 'ENV_DB', 'STATUS', 
               'TYPE', 'DEFSITE', 'FIRSTNAME', 'LASTNAME', 'TITLE', 'PERSONGROUP']
    
    rows = []
    for user in unique_active:
        rows.append({
            'USERID': clean_value(user.get('USERID', '')),
            'DISPLAYNAME': clean_value(user.get('DISPLAYNAME', '')),
            'PRIMARYEMAIL': clean_value(user.get('PRIMARYEMAIL', '')),
            'ENV_DB': clean_value(user.get('ENV_DB', '')),
            'STATUS': clean_value(user.get('STATUS', '')),
            'TYPE': clean_value(user.get('TYPE', '')),
            'DEFSITE': clean_value(user.get('DEFSITE', '')),
            'FIRSTNAME': clean_value(user.get('FIRSTNAME', '')),
            'LASTNAME': clean_value(user.get('LASTNAME', '')),
            'TITLE': clean_value(user.get('TITLE', '')),
            'PERSONGROUP': clean_value(user.get('PERSONGROUP', '')),
        })
    
    add_sheet('18_Maximo_Usuarios_Ativos', headers, rows)
    print(f'✓ Aba 18 adicionada: {len(rows)} usuários ativos únicos do Maximo')


# --- Profile Access Excel Sheet ---
def add_profile_access_sheet(wb, identities, add_sheet):
    """Adiciona aba com detalhamento de acessos por tipo de perfil."""
    
    def clean_value(v):
        """Remove caracteres ilegais do Excel (caracteres de controle)."""
        if v is None:
            return ''
        s = str(v)
        return ''.join(c if ord(c) >= 32 or c in '\n\r\t' else '' for c in s)
    
    # Filtrar apenas usuários ativos
    active_users = [r for r in identities if r.get('STATUS', '').strip().upper() == 'ACTIVE']
    
    # Agrupar por tipo
    by_type = {}
    for user in active_users:
        t = user.get('TYPE', '').strip() or 'N/A'
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(user)
    
    # Preparar headers
    headers = ['Tipo', 'Qtd Usuários', 'USERIDs Únicos', 'Ambientes', 'Títulos', 'PersonGroups']
    
    rows = []
    for tipo, users in sorted(by_type.items()):
        userids = set()
        envs = set()
        titulos = set()
        persongroups = set()
        
        for user in users:
            userids.add(clean_value(user.get('USERID', '')))
            envs.add(clean_value(user.get('ENV_DB', '')))
            titulos.add(clean_value(user.get('TITLE', '')))
            persongroups.add(clean_value(user.get('PERSONGROUP', '')))
        
        rows.append({
            'Tipo': clean_value(tipo),
            'Qtd Usuários': len(users),
            'USERIDs Únicos': len(userids),
            'Ambientes': '; '.join(sorted(e for e in envs if e)),
            'Títulos': '; '.join(sorted(t for t in titulos if t))[:100],
            'PersonGroups': '; '.join(sorted(pg for pg in persongroups if pg))[:100],
        })
    
    add_sheet('19_Acessos_por_Perfil', headers, rows)
    print(f'✓ Aba 19 adicionada: {len(rows)} tipos de perfil analisados')


# --- Audit Excel Sheet ---
def add_audit_sheet(wb, persongroupview, add_sheet):
    """Adiciona aba com dados de auditoria - data de concessão de acesso."""
    
    def clean_value(v):
        """Remove caracteres ilegais do Excel (caracteres de controle)."""
        if v is None:
            return ''
        s = str(v)
        return ''.join(c if ord(c) >= 32 or c in '\n\r\t' else '' for c in s)
    
    # Filtrar apenas usuários ativos com statusdate
    active_with_date = [r for r in persongroupview if r.get('status', '').strip().upper() == 'ACTIVE' and r.get('statusdate', '').strip()]
    
    # Preparar headers
    headers = ['USERID', 'DISPLAYNAME', 'STATUS', 'STATUSDATE', 'TYPE', 'DEFSITE', 'TITLE', 'PERSONGROUP', 'ENVIRONMENT']
    
    rows = []
    for r in active_with_date[:5000]:  # Limitar a 5000 linhas
        rows.append({
            'USERID': clean_value(r.get('personid', '')),
            'DISPLAYNAME': clean_value(r.get('displayname', '')),
            'STATUS': clean_value(r.get('status', '')),
            'STATUSDATE': clean_value(r.get('statusdate', '')),
            'TYPE': clean_value(r.get('employeetype', '')),
            'DEFSITE': clean_value(r.get('location', '')),
            'TITLE': clean_value(r.get('title', '')),
            'PERSONGROUP': clean_value(r.get('persongroup', '')),
            'ENVIRONMENT': clean_value(r.get('ENVIRONMENT', '')),
        })
    
    add_sheet('20_Auditoria_Acesso', headers, rows)
    print(f'✓ Aba 20 adicionada: {len(rows)} registros com data de concessão')


# --- Migration Excel Sheets ---
def add_migration_sheets(wb, migration_data, add_sheet):
    """Adiciona abas do Excel com recomendações de migração."""
    
    # Aba 16: Resumo de Recomendações
    summary_rows = [['Tipo', 'Prioridade', 'Quantidade']]
    tipo_counts = {}
    for r in migration_data:
        tipo = r['tipo']
        tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
    
    for tipo, count in sorted(tipo_counts.items()):
        prioridade = next((r['prioridade'] for r in migration_data if r['tipo'] == tipo), 'N/A')
        summary_rows.append([tipo, prioridade, count])
    
    add_sheet('16_Migracao_Resumo', ['Tipo', 'Prioridade', 'Quantidade'], summary_rows)
    
    # Aba 17: Lista Completa de Recomendações
    headers = ['Tipo', 'Prioridade', 'USERID', 'E-mail', 'Nome AD', 'Nome Maximo',
               'Status AD', 'Status Maximo', 'Ambientes', 'Grupos AD', 'Motivo', 'Ação']
    rows = []
    for r in migration_data:
        rows.append({
            'Tipo': r['tipo'],
            'Prioridade': r['prioridade'],
            'USERID': r['userid'],
            'E-mail': r['email'],
            'Nome AD': r['nome_ad'],
            'Nome Maximo': r['nome_maximo'],
            'Status AD': r['status_ad'],
            'Status Maximo': r['status_maximo'],
            'Ambientes': r['envs'],
            'Grupos AD': r['grupos_ad'],
            'Motivo': r['motivo'],
            'Ação': r['acao'],
        })
    add_sheet('17_Migracao_Detalhada', headers, rows)


# --- Main Orchestration ---
def main():
    """
    Orchestrates the entire process of data loading, analysis, and report generation.
    """
    # 1. Load Data
    all_data = load_all_data()

    # --- INJEÇÃO DA NOVA ANÁLISE DE IDENTIDADE ---
    # Obtém os dados de identidade já processados e deduplicados
    identity_analytics = get_unique_users_data()

    # 2. Build User Profiles
    user_profiles = build_user_profiles(
        all_data["identities"],
        all_data["access_rows"],
        all_data["emails"],
        all_data["persons"],
        all_data["persongroupview"],
    )
    
    # 2b. Enrich with LOCATION_SITE from persongroupview (ENVIRONMENT column) - BEFORE simulation
    # Usa lógica inteligente: pega o ambiente do último login ou DEFSITE
    persongroupview_map = {}
    for pgv in all_data.get("persongroupview", []):
        uid = str(pgv.get('personid', '')).strip().upper()
        env = pgv.get('ENVIRONMENT', '').strip()
        defsite = pgv.get('sitedefault', '').strip() or pgv.get('locationsite', '').strip()
        if uid and env:
            if uid not in persongroupview_map:
                persongroupview_map[uid] = {'environment': env, 'defsite': defsite}
    
    # Carregar logintracking para inferir ambiente real
    logintrack = load_csv(IN_DIR / 'consolidated_logintracking_from_sources.csv')
    
    # Inferir ambiente real do usuário baseado em CLIENTHOST
    def infer_env_from_clienthost(clienthost):
        if not clienthost:
            return None, False
        host = clienthost.strip().upper()
        if host.replace('.', '').isdigit():
            return None, True
        if 'ODRL-SP-SV' in host:
            return None, True
        if 'ODRL-ODN2-SV' in host:
            return 'ODN2', False
        if 'ODRL-ODN1-SV' in host:
            return 'ODN1', False
        if 'ODRL-N06-SV' in host:
            return 'N06', False
        if 'ODRL-N08-SV' in host:
            return 'N08', False
        if 'ODRL-N09-SV' in host:
            return 'N09', False
        if host.startswith('OD2-') or '-OD2-' in host:
            return 'ODN2', False
        if host.startswith('OD1-') or '-OD1-' in host:
            return 'ODN1', False
        if host.startswith('ON06-') or '-N06-' in host:
            return 'N06', False
        if host.startswith('ON08-') or '-N08-' in host:
            return 'N08', False
        if host.startswith('ON09-') or '-N09-' in host:
            return 'N09', False
        return None, False
    
    # Calcular ambiente real por usuário
    user_real_env = {}
    for rec in logintrack:
        if rec.get('ATTEMPTRESULT', '').strip().upper() != 'LOGIN':
            continue
        userid = rec.get('USERID', '').strip().upper()
        clienthost = rec.get('CLIENTHOST', '').strip()
        if userid:
            env, is_shared = infer_env_from_clienthost(clienthost)
            if env:
                user_real_env[userid] = env
    
    for profile in user_profiles.values():
        uid = str(profile.get('USERID', '')).strip().upper()
        # Prioridade 1: ambiente real do logintracking
        if uid in user_real_env:
            profile['LOCATION_SITE'] = user_real_env[uid]
        # Prioridade 2: DEFSITE do persongroupview (já é o ambiente correto)
        elif uid in persongroupview_map:
            profile['LOCATION_SITE'] = persongroupview_map[uid]['defsite'] or persongroupview_map[uid]['environment']
        # Prioridade 3: DEFSITE do próprio perfil
        elif not profile.get('LOCATION_SITE'):
            profile['LOCATION_SITE'] = profile.get('DEFSITE', '')
    
    active_profiles = [p for p in user_profiles.values() if p['STATUS'] == 'ACTIVE']

    # 3. Perform Governance Analysis
    domain_counts = analyze_governance(active_profiles)
    title_divergences_list, detailed_divergences = analyze_title_divergences(all_data["access_rows"], user_profiles)

    # 4. Perform AppPoints Simulation (por escopo)
    foresea_profiles = [
        p for p in active_profiles
        if p['DOMAIN_CATEGORY'] in ('FORESEA', 'PARCEIRO')
    ]
    other_profiles = [
        p for p in active_profiles
        if p['DOMAIN_CATEGORY'] not in ('FORESEA', 'PARCEIRO', 'SEM DOMINIO')
    ]
    missing_email_profiles = [
        p for p in active_profiles
        if p['DOMAIN_CATEGORY'] == 'SEM DOMINIO'
    ]

    missing_email_rows = [
        {
            'USERID': p['USERID'],
            'DISPLAYNAME': '; '.join(sorted(x for x in p['DISPLAYNAME'] if x)) or p['USERID'],
            'STATUS': p['STATUS'],
            'ENVS': '; '.join(sorted(p['ENVS'])),
            'TYPE': '; '.join(sorted(p['TYPE'])),
            'GROUPS_COUNT': len(p['GROUPS']),
            'GROUPS': '; '.join(sorted(p['GROUPS'])),
            'TITLES': '; '.join(sorted(p['TITLES'])),
            'PERSONGROUPS': '; '.join(sorted(p['PERSONGROUPS'])),
            'REVIEW_REASON': 'Sem email nominal/dominio valido no cadastro. Revisar antes de contar AppPoints.',
        }
        for p in missing_email_profiles
    ]

    foresea_app_points = simulate_app_points(foresea_profiles, user_real_env)
    other_app_points = simulate_app_points(other_profiles, user_real_env)

    # Re-enrich with LOCATION_SITE after simulation (simulate_app_points creates new dicts)
    for row in foresea_app_points + other_app_points:
        uid = str(row.get('USERID', '')).strip().upper()
        if uid in persongroupview_map and not row.get('LOCATION_SITE'):
            # Priorizar defsite (ambiente alocado) sobre environment (ambiente do registro)
            row['LOCATION_SITE'] = persongroupview_map[uid]['defsite'] or persongroupview_map[uid]['environment']

    app_points_by_scope = {
        'foresea': foresea_app_points,
        'other': other_app_points,
    }

    # Gera o license decision plan com TODOS os usuários (incluindo SEM DOMINIO)
    # Usuários SEM DOMINIO são incluídos mas marcados para revisão
    sem_dominio_rows = [
        {
            **p, 
            'DOMAIN_CATEGORY': 'SEM DOMINIO', 
            'MIGRATION_SCOPE': 'REVIEW_MISSING_EMAIL',
            'LICENSE_MODEL': 'CONCURRENT',
            'ENTITLEMENT': 'BASE',
            'APP_POINTS': 10,
            'OPTIMIZATION_REC': 'REQUER_REVISAO',
            'OPTIMIZATION_REASON': 'Sem email cadastrado. Revisar antes de definir licença.'
        }
        for p in missing_email_profiles
    ]
    all_app_points_for_plan = foresea_app_points + other_app_points + sem_dominio_rows
    write_license_decision_plan(all_app_points_for_plan)

    # Compatibilidade com o pipeline/HTML atual (por enquanto ainda consumimos um único universo)
    # Depois este valor será substituído por dados por escopo no frontend.
    app_points_data_optimized = all_app_points_for_plan

    # 5b. Compute High-Water Mark and peak contributors for CONCURRENT pool
    concurrency_summary = {}
    try:
        # O true_capacity_calculator.py atual gera apenas true_capacity_metrics.json com agregados,
        # sem detalhes de "hora" e sem lista de contribuintes.
        # A UI (scripts/reporting/html_template.py) e o DataProcessor esperam um schema:
        #   - hourly_counts: dict (hour -> points/count)
        #   - peak_hours: list/dict (rows para a tabela)
        #   - peak_contributors: list (USERID/dicts)
        # Então, quando só houver métricas agregadas, preenchemos o mínimo sem quebrar a UI.
        # Trecho ajustado do bloco de concorrência

        metrics_path = ROOT / 'output' / 'consolidated' / 'true_capacity_metrics.json'

        concurrency_summary = {}

        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding='utf-8'))

        concurrency_summary = {
            'hourly_counts': metrics.get('hourly_counts', {}),
            'hourly_app_points': metrics.get('hourly_app_points', {}),
            'hourly_concurrent_app_points': metrics.get('hourly_concurrent_app_points', {}),
            'hourly_app_points_nem': metrics.get('hourly_app_points_nem', {}),
            'true_total_app_points': metrics.get('true_total_app_points', 0),
            'authorized_reserved_points': metrics.get('authorized_reserved_points', 0),
            'peak_hours': metrics.get('peak_hours', []),
            'peak_hours_users': metrics.get('peak_hours_users', []),
            'peak_contributors_count': metrics.get('peak_contributors_count', 0),
            'peak_contributors': metrics.get('peak_contributors', [])
        }
    except Exception as e:
        print(f"[Aviso] Falha ao calcular concorrência avançada: {e}")


    # 6. Prepare Data for HTML Builder
    summary_data = {
        'active_profiles_count': len(active_profiles),
        'title_divergence_count': len(title_divergences_list),
        'app_points_summary': {
            'auth_users': [s for s in app_points_data_optimized if s['LICENSE_MODEL'] == 'AUTHORIZED'],
            'conc_users': [s for s in app_points_data_optimized if s['LICENSE_MODEL'] == 'CONCURRENT'],
            'premium_users': [s for s in app_points_data_optimized if s['ENTITLEMENT'] == 'PREMIUM'],
        },
        'concurrency': concurrency_summary
    }
    governance_data = {
        'cross_env': all_data['cross_env'],
        'login_conflicts': all_data['login_conflicts'],
        'worklist': all_data['worklist'],
        'title_divergences_list': title_divergences_list, # List of just titles
        'detailed_divergences': detailed_divergences, # Detailed structure for section 5
        'identities': all_data['identities'], # Needed for some original metrics
        'access_rows': all_data['access_rows'], # Needed for some original metrics
        'user_profiles': user_profiles, # Pass consolidated profiles for detailed tables
        'persongroupview': all_data['persongroupview'], # For audit sheet
    }

    # 7. Análise de Saneamento de Identidades (AD vs Maximo)
    print("\n" + "=" * 100)
    print("ANÁLISE DE SANEAMENTO DE IDENTIDADES (AD vs Maximo)")
    print("=" * 100)
    sanity_result = analyze_sanity()
    
    # 7b. Análise de Recomendações de Migração
    print("\n" + "=" * 100)
    print("ANÁLISE DE RECOMENDAÇÕES DE MIGRAÇÃO")
    print("=" * 100)
    migration_recommendations = analyze_migration()
    
    # 8. Build and Write HTML (com dados de AD, Maximo, Sanity e Migration)
    html_content = build_html_structure(
        summary_data, 
        governance_data, 
        app_points_data_optimized, 
        domain_counts, 
        identity_analytics,
        ad_users=all_data.get('ad_users', []),
        maximo_users=all_data.get('maximo_users', []),
        sanity_data=sanity_result,
        migration_data=migration_recommendations
    )
    html_path = OUT_DIR / 'maximo_unified_dashboard.html'
    html_path.write_text(html_content, encoding='utf-8')
    print(f'WROTE {html_path.name}')
    write_excel_workbook(summary_data, governance_data, app_points_data_optimized, domain_counts, missing_email_rows, sanity_result, migration_recommendations, identities=all_data.get('identities', []))

if __name__ == '__main__':
    main()