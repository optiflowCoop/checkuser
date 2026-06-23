# generate_risk_report.py (Orchestrator)
import sys
import csv
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# --- CRITICAL FIX: Add the project root to sys.path ---
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import modularized components
from scripts.config import get_app_points_config, get_entitlement_keywords, get_critical_titles, get_foresea_domains
from scripts.domain.user import build_user_profiles, get_user_domain_category
from scripts.services.analysis import analyze_governance, analyze_title_divergences
from scripts.services.app_points import simulate_app_points
from scripts.services.usage_analyzer import analyze_usage
from scripts.reporting.html_builder import build_html_structure
from scripts.reporting.html_helpers import fmt_br, render_table

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
    }

def load_csv(path: Path):
    """Helper to load a single CSV, returning an empty list if not found."""
    if not path.exists(): return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

# --- Main Orchestration ---
def main():
    """
    Orchestrates the entire process of data loading, analysis, and report generation.
    """
    # 1. Load Data
    all_data = load_all_data()

    # 2. Build User Profiles
    user_profiles = build_user_profiles(all_data["identities"], all_data["access_rows"])
    active_profiles = [p for p in user_profiles.values() if p['STATUS'] == 'ACTIVE']

    # 3. Perform Governance Analysis
    domain_counts = analyze_governance(active_profiles)
    title_divergences_list, detailed_divergences = analyze_title_divergences(all_data["access_rows"], user_profiles)

    # 4. Perform AppPoints Simulation
    foresea_domains = get_foresea_domains()
    foresea_profiles = [p for p in active_profiles if p['DOMAIN_CATEGORY'] in ('FORESEA', 'PARCEIRO')]
    app_points_data = simulate_app_points(foresea_profiles)
    
    # 5. Apply Usage Intelligence (Optimization Recommendations)
    app_points_data_optimized = analyze_usage(app_points_data)

    # 6. Prepare Data for HTML Builder
    summary_data = {
        'active_profiles_count': len(active_profiles),
        'title_divergence_count': len(title_divergences_list),
        'app_points_summary': {
            'auth_users': [s for s in app_points_data_optimized if s['LICENSE_MODEL'] == 'AUTHORIZED'],
            'conc_users': [s for s in app_points_data_optimized if s['LICENSE_MODEL'] == 'CONCURRENT'],
            'premium_users': [s for s in app_points_data_optimized if s['ENTITLEMENT'] == 'PREMIUM'],
        }
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
    html_content = build_html_structure(summary_data, governance_data, app_points_data_optimized, domain_counts)
    html_path = OUT_DIR / 'maximo_unified_dashboard.html'
    html_path.write_text(html_content, encoding='utf-8')
    print(f'WROTE {html_path.name}')

if __name__ == '__main__':
    main()