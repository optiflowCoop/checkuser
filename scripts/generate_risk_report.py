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
    }

def load_csv(path: Path):
    """Helper to load a single CSV, returning an empty list if not found."""
    if not path.exists(): return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

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
    usage_map = {}
    usage_path = IN_DIR / 'usage_analysis_phase3.csv'
    if usage_path.exists():
        try:
            with usage_path.open(encoding='utf-8-sig', newline='') as uf:
                ureader = csv.DictReader(uf)
                for ur in ureader:
                    uid = str(ur.get('USERID', '')).strip().upper()
                    if uid:
                        usage_map[uid] = ur.get('LOCATION_SITE') or ur.get('LOCATION') or ''
        except Exception:
            pass

    # Enrich rows with LOCATION_SITE if missing
    for row in rows:
        uid = str(row.get('USERID', '')).strip().upper()
        if uid and (not row.get('LOCATION_SITE')):
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

def write_excel_workbook(summary, governance, license_rows, domain_counts, missing_email_rows):
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
                values = [row.get(h, '') for h in headers]
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

    out_path = OUT_DIR / 'maximo_risk_and_optimization_workbook.xlsx'
    wb.save(out_path)
    print(f'✓ WROTE {out_path.name}')

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

    foresea_app_points = simulate_app_points(foresea_profiles)
    other_app_points = simulate_app_points(other_profiles)

    app_points_by_scope = {
        'foresea': foresea_app_points,
        'other': other_app_points,
    }

    # Gera o license decision plan usando o conjunto completo que alimenta o pipeline:
    # (foresea + other). 'SEM DOMINIO' fica fora por inconsistência.
    all_app_points_for_plan = foresea_app_points + other_app_points
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
                'peak_count': metrics.get('true_total_app_points'),
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
        'user_profiles': user_profiles # Pass consolidated profiles for detailed tables
    }

    # 7. Build and Write HTML
    html_content = build_html_structure(summary_data, governance_data, app_points_data_optimized, domain_counts, identity_analytics)
    html_path = OUT_DIR / 'maximo_unified_dashboard.html'
    html_path.write_text(html_content, encoding='utf-8')
    print(f'WROTE {html_path.name}')
    write_excel_workbook(summary_data, governance_data, app_points_data_optimized, domain_counts, missing_email_rows)

if __name__ == '__main__':
    main()
