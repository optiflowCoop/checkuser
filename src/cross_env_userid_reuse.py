#!/usr/bin/env python3
"""Identifies USERIDs that are reused across multiple environments."""
import csv
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
IN_FILE = os.path.join(ROOT, 'output', 'consolidated', 'consolidated_user_identity.csv')
OUT_FILE = os.path.join(ROOT, 'output', 'consolidated', 'cross_env_userid_reuse.csv')

def main():
    if not os.path.exists(IN_FILE):
        return
        
    with open(IN_FILE, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
        
    clusters = defaultdict(list)
    for r in rows:
        uid = r.get('USERID','').strip().upper()
        if uid:
            clusters[uid].append(r)
            
    out = []
    for uid, members in clusters.items():
        envs = set(m.get('ENV_DB','') for m in members if m.get('ENV_DB'))
        if len(envs) > 1:
            out.append({
                'USERID': uid,
                'ENV_COUNT': len(envs),
                'ENV_LIST': '; '.join(sorted(envs)),
                'RAW_ID_LIST': '; '.join(sorted(set(m.get('RAW_ID','') for m in members if m.get('RAW_ID')))),
                'PERSONID_LIST': '; '.join(sorted(set(m.get('PERSONID','') for m in members if m.get('PERSONID')))),
                'LOGINID_LIST': '; '.join(sorted(set(m.get('LOGINID','') for m in members if m.get('LOGINID')))),
                'DISPLAYNAME_LIST': '; '.join(sorted(set(m.get('DISPLAYNAME','') for m in members if m.get('DISPLAYNAME')))),
                'EMAIL_LIST': '; '.join(sorted(set(m.get('PRIMARYEMAIL','') for m in members if m.get('PRIMARYEMAIL')))),
                'STATUS_LIST': '; '.join(sorted(set(m.get('STATUS','') for m in members if m.get('STATUS')))),
                'ACCOUNT_CLASS_LIST': '; '.join(sorted(set(m.get('ACCOUNT_CLASS','') for m in members if m.get('ACCOUNT_CLASS')))),
                'GROUPS_COUNT_LIST': '; '.join(sorted(set(m.get('TOTAL_GROUPS','') for m in members if m.get('TOTAL_GROUPS')))),
                'REUSE_FLAG': 'TRUE'
            })
            
    if out:
        with open(OUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            writer.writeheader()
            writer.writerows(sorted(out, key=lambda x: (-x['ENV_COUNT'], x['USERID'])))
        print(f"WROTE {OUT_FILE} ({len(out)} records)")

if __name__ == '__main__':
    main()