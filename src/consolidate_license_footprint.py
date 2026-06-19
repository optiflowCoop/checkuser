#!/usr/bin/env python3
"""Create consolidated_license_footprint.csv by joining maxuser and maxlicusage."""
import csv
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / 'output' / 'consolidated'

def load_csv(filename):
    path = OUTDIR / filename
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def main():
    if not OUTDIR.exists():
        OUTDIR.mkdir(parents=True, exist_ok=True)
        
    users = load_csv('consolidated_maxuser.csv')
    licusage = load_csv('consolidated_maxlicusage.csv')

    # Create mapping of ENV_DB + USERID to user details
    user_map = {}
    for row in users:
        env = (row.get('ENVIRONMENT') or row.get('ENV_DB') or '').strip()
        userid = (row.get('USERID') or '').strip()
        if env and userid:
            user_map[f"{env}|{userid}"] = {
                'PERSONID': row.get('PERSONID', ''),
                'LOGINID': row.get('LOGINID', ''),
                'STATUS': row.get('STATUS', ''),
                'TYPE': row.get('TYPE', '')
            }

    out_rows = []
    
    # Process maxlicusage records
    for row in licusage:
        env = (row.get('ENVIRONMENT') or row.get('ENV_DB') or '').strip()
        userid = (row.get('USERID') or '').strip()
        
        user_info = user_map.get(f"{env}|{userid}", {})
        
        out_rows.append({
            'ENV_DB': env,
            'USERID': userid,
            'PERSONID': user_info.get('PERSONID', ''),
            'LOGINID': user_info.get('LOGINID', ''),
            'STATUS': user_info.get('STATUS', ''),
            'TYPE': user_info.get('TYPE', ''),
            'LICENSENUM': row.get('LICENSENUM', ''),
            'ISLATEST': row.get('ISLATEST', ''),
            'ISUNLICUSER': row.get('ISUNLICUSER', ''),
            'ISSELFSERVICEUSER': row.get('ISSELFSERVICEUSER', '')
        })

    out_path = OUTDIR / 'consolidated_license_footprint.csv'
    if out_rows:
        with out_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            writer.writeheader()
            for row in out_rows:
                writer.writerow(row)
        print(f"WROTE {out_path.name} ({len(out_rows)} rows)")
    else:
        print("No license footprint data to write.")

if __name__ == '__main__':
    main()