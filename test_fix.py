#!/usr/bin/env python
import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from scripts.reporting.html_data_processor import DataProcessor

# Load data
IN_DIR = Path('output/consolidated')
OUT_DIR = Path('output/reports')

# Minimal test data
summary_data = {'concurrency': {}}
governance_data = {}

# Load app_points
app_points = []
with open(IN_DIR / 'license_decision_plan.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    app_points = list(reader)

# Load identity_analytics (minimal)
identity_analytics = {
    'total_unique_users': 1246,
    'total_active_unique': 1100,
    'status_counts': {'ACTIVE': 1100, 'INACTIVE': 146},
    'domain_counts': {'foresea': 1050, 'foresea_partner': 100, 'other': 50, 'no_domain': 46}
}

# Process
processor = DataProcessor(summary_data, governance_data, app_points, {}, identity_analytics)
analytics = processor.process_app_points_analytics()

print("Scenario Points:")
print(f"  p50: {analytics['scenario_points']['p50']}")
print(f"  p95: {analytics['scenario_points']['p95']}")
print(f"  p100: {analytics['scenario_points']['p100']}")
print(f"  blackout: {analytics['scenario_points']['blackout']}")
print()
print("Expected: All should be 9025")
