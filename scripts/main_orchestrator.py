# scripts/main_orchestrator.py
import sys
from pathlib import Path
import csv

# Ensure the project root is in the system path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import modularized components
from scripts.domain.user import build_user_profiles
from scripts.analysis.governance import analyze_domain_distribution, analyze_title_divergences
from scripts.analysis.licensing import simulate_app_points
from scripts.reporting.html_builder import build_html_structure
from scripts.services.usage_analyzer import analyze_usage # Assuming this service exists and is needed

# --- Constants ---
IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'reports'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Data Loading ---
def load_csv(path: Path):
    """Loads a CSV file, returning an empty list if it doesn't exist."""
    if not path.exists():
        print(f"Warning: File not found - {path}")
        return []
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f))
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return []

def main():
    """Orchestrates the data loading, analysis, and report generation process."""

    # 1. Load All Necessary Data
    print("Step 1: Loading all consolidated data...")
    all_data = {
        "identities": load_csv(IN_DIR / 'consolidated_user_identity.csv'),
        "access_rows": load_csv(IN_DIR / 'consolidated_user_access_normalized.csv') or load_csv(IN_DIR / 'consolidated_user_access.csv'),
        "cross_env": load_csv(IN_DIR / 'cross_env_userid_reuse.csv'),
        "login_conflicts": load_csv(IN_DIR / 'login_conflicts.csv'),
        "worklist": load_csv(IN_DIR / 'identity_collisions_enriched.csv'),
    }

    # 2. Build User Profiles from Raw Data
    print("Step 2: Building user profiles...")
    user_profiles = build_user_profiles(all_data["identities"], all_data["access_rows"])
    active_profiles = [p for p in user_profiles.values() if p.get('STATUS') == 'ACTIVE']
    print(f"Found {len(active_profiles)} active user profiles.")

    # 3. Perform Governance and Divergence Analysis
    print("Step 3: Analyzing governance and title divergences...")
    domain_counts = analyze_domain_distribution(active_profiles)
    title_divergences_list, detailed_divergences = analyze_title_divergences(all_data["access_rows"], user_profiles)
    print(f"Identified {len(title_divergences_list)} titles with divergences.")

    # 4. Simulate AppPoints based on rules
    print("Step 4: Simulating AppPoints licensing...")
    app_points_data = simulate_app_points(active_profiles)

    # 5. Apply Usage Intelligence for Optimization Recommendations
    print("Step 5: Applying usage intelligence for optimization...")
    app_points_data_optimized = analyze_usage(app_points_data)

    # 6. Prepare Data Structures for the HTML Report
    print("Step 6: Preparing data for the report...")
    summary_data = {
        'active_profiles_count': len(active_profiles),
        'title_divergence_count': len(title_divergences_list),
    }
    governance_data = {
        'cross_env': all_data['cross_env'],
        'login_conflicts': all_data['login_conflicts'],
        'worklist': all_data['worklist'],
        'detailed_divergences': detailed_divergences,
    }

    # 7. Build and Write the Final HTML Dashboard
    print("Step 7: Building and writing the HTML dashboard...")
    html_content = build_html_structure(
        summary=summary_data,
        governance=governance_data,
        app_points=app_points_data_optimized,
        domains=domain_counts
    )
    
    report_path = OUT_DIR / 'maximo_unified_dashboard.html'
    try:
        report_path.write_text(html_content, encoding='utf-8')
        print(f"Successfully wrote report to {report_path}")
    except Exception as e:
        print(f"Error writing HTML file: {e}")

if __name__ == '__main__':
    main()