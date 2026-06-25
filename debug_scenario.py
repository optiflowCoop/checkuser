#!/usr/bin/env python
import csv
import numpy as np
from pathlib import Path

IN_DIR = Path('output/consolidated')

# Load CSV
app_points = []
with open(IN_DIR / 'license_decision_plan.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    app_points = list(reader)

print(f"Total users: {len(app_points)}")
print()

# Simulate the scenario_points calculation
opt_auth_points = 0
opt_conc_users = []
hourly_concurrent_points = {}

for u in app_points:
    lic = u.get('LICENSE_MODEL')
    ent = u.get('ENTITLEMENT')
    rec = u.get('OPTIMIZATION_REC')
    
    if rec == 'INATIVO (>90d)':
        continue
    
    final_ent = 'BASE' if (rec == 'DOWNGRADE_CANDIDATE' and ent == 'PREMIUM') else ent
    final_lic = 'CONCURRENT' if rec == 'MOVE_TO_CONCURRENT' else lic
    f_is_prem = (final_ent == 'PREMIUM')
    f_is_auth = (final_lic == 'AUTHORIZED')
    
    if f_is_auth:
        points = 5 if f_is_prem else 2
        opt_auth_points += points
    else:
        points = 15 if f_is_prem else 10
        opt_conc_users.append({
            'userid': u.get('USERID'),
            'points': points,
        })
        
        # Deserialize ACTIVE_HOURS
        active_hours = u.get('ACTIVE_HOURS', '')
        if isinstance(active_hours, str) and active_hours.strip():
            hours_list = [h.strip() for h in active_hours.split('|') if h.strip()]
        else:
            hours_list = []
        
        for hour in hours_list:
            hourly_concurrent_points[hour] = hourly_concurrent_points.get(hour, 0) + points

print(f"Authorized points (static): {opt_auth_points}")
print(f"Concurrent users count: {len(opt_conc_users)}")
print(f"Hourly slots with data: {len(hourly_concurrent_points)}")
print()

# Calculate percentiles
hourly_values = list(hourly_concurrent_points.values())
if hourly_values:
    p50 = float(np.percentile(hourly_values, 50))
    p95 = float(np.percentile(hourly_values, 95))
    p100 = max(hourly_values)
    
    print(f"Hourly values (min/max): {min(hourly_values)}/{max(hourly_values)}")
    print(f"P50: {p50}")
    print(f"P95: {p95}")
    print(f"P100: {p100}")
    print()
    
    scenario_points = {
        'p50': opt_auth_points + p50,
        'p95': opt_auth_points + p95,
        'p100': opt_auth_points + p100,
    }
else:
    scenario_points = {
        'p50': opt_auth_points,
        'p95': opt_auth_points,
        'p100': opt_auth_points,
    }

print("Final scenario_points:")
print(f"  p50: {scenario_points['p50']}")
print(f"  p95: {scenario_points['p95']}")
print(f"  p100: {scenario_points['p100']}")
print()
print(f"Expected p95: ~9000+")
