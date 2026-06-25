#!/usr/bin/env python
"""Quick HTML regeneration script using existing data."""
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts.reporting.html_builder import build_html_structure
from scripts.domain.identity_analyzer import get_unique_users_data

IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'reports'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load app_points
app_points = []
with open(IN_DIR / 'license_decision_plan.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    app_points = list(reader)

print(f"✓ Loaded {len(app_points)} user records")

# Load identity analytics
identity_analytics = get_unique_users_data()
print(f"✓ Loaded identity analytics: {identity_analytics['total_unique_users']} unique users")

# Minimal summary and governance for HTML builder
summary_data = {'concurrency': {}}
governance_data = {
    'cross_env': [],
    'login_conflicts': [],
    'worklist': [],
    'detailed_divergences': [],
    'identities': [],
    'access_rows': [],
    'user_profiles': []
}
domain_counts = {}

# Build HTML
html_content = build_html_structure(summary_data, governance_data, app_points, domain_counts, identity_analytics)

# Write HTML
html_path = OUT_DIR / 'maximo_unified_dashboard.html'
html_path.write_text(html_content, encoding='utf-8')
print(f'✓ WROTE {html_path.name}')
print()
print("HTML regenerated successfully. Check tab 3 for AppPoints value.")
