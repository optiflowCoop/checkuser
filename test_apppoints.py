#!/usr/bin/env python
# Quick test to verify AppPoints sum
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent
IN_DIR = ROOT / 'output' / 'consolidated'

# Load license_decision_plan
usage_data = []
with open(IN_DIR / 'license_decision_plan.csv') as f:
    for i, row in enumerate(csv.DictReader(f)):
        if i < 5:
            print(f"User {i}: {row['USERID']} - APP_POINTS={row['APP_POINTS']} - LICENSE={row['LICENSE_MODEL']}")
        usage_data.append(row)

total_points = sum(int(r['APP_POINTS']) for r in usage_data)
print(f'\n✓ Total AppPoints in CSV: {total_points:,}')
print(f'✓ Number of rows: {len(usage_data)}')
print(f'✓ Average AppPoints per user: {total_points / len(usage_data):.2f}')

# Count by license model
from collections import Counter
licenses = Counter(r['LICENSE_MODEL'] for r in usage_data)
print(f'\n✓ License distribution:')
for lic, count in licenses.items():
    total = sum(int(r['APP_POINTS']) for r in usage_data if r['LICENSE_MODEL'] == lic)
    print(f'  - {lic}: {count} users = {total} AppPoints')
