# scripts/main_orchestrator.py
from pathlib import Path
from scripts.config import get_app_points_config, get_entitlement_keywords, get_critical_titles
from scripts.domain.user import build_user_profiles
from scripts.analysis.governance import analyze_domain_distribution, analyze_title_divergences
from scripts.analysis.licensing import simulate_app_points
from scripts.reporting.html_builder import build_unified_dashboard
import csv

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'reports'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_csv(path: Path):
    if not path.exists(): return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def main():
    # 1. Load Data
    print("Loading data...")
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    access_rows = load_csv(IN_DIR / 'consolidated_user_access_normalized.csv') or load_csv(IN_DIR / 'consolidated_user_access.csv')
    cross_env = load_csv(IN_DIR / 'cross_env_userid_reuse.csv')
    login_conflicts = load_csv(IN_DIR / 'login_conflicts.csv')
    worklist = load_csv(IN_DIR / 'identity_collisions_enriched.csv')

    # 2. Consolidate Profiles
    print("Building user profiles...")
    user_profiles = build_user_profiles(identities, access_rows)
    active_profiles = [p for p in user_profiles.values() if p['STATUS'] == 'ACTIVE']

    # 3. Analyze Governance
    print("Analyzing governance...")
    domain_counts = analyze_domain_distribution(active_profiles)
    title_divergences, _ = analyze_title_divergences(access_rows, user_profiles)

    # 4. Simulate AppPoints
    print("Simulating AppPoints...")
    app_points_data = simulate_app_points(active_profiles)

    # 5. Prepare Data for HTML
    print("Preparing HTML data...")
    summary_data = {
        'active_profiles_count': len(active_profiles),
        'title_divergence_count': len(title_divergences),
        'app_points_summary': {
            'auth_users': [s for s in app_points_data if s['LICENSE_MODEL'] == 'AUTHORIZED'],
            'conc_users': [s for s in app_points_data if s['LICENSE_MODEL'] == 'CONCURRENT'],
            'premium_users': [s for s in app_points_data if s['ENTITLEMENT'] == 'PREMIUM'],
        }
    }
    governance_data = {
        'cross_env': cross_env,
        'login_conflicts': login_conflicts,
        'worklist': worklist,
        'title_divergences': title_divergences,
    }

    # 6. Build and Save HTML
    print("Building HTML dashboard...")
    html_content = build_unified_dashboard(summary_data, governance_data, app_points_data, domain_counts)
    
    html_path = OUT_DIR / 'maximo_unified_dashboard_solid.html'
    html_path.write_text(html_content, encoding='utf-8')
    print(f'WROTE {html_path.name}')

if __name__ == '__main__':
    main()