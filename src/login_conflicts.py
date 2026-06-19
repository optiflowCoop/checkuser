#!/usr/bin/env python3
"""Identifies LOGINIDs that are reused across different USERIDs or PERSONIDs."""
import csv
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
IN_FILE = os.path.join(ROOT, 'output', 'consolidated', 'consolidated_user_identity.csv')
OUT_FILE = os.path.join(ROOT, 'output', 'consolidated', 'login_conflicts.csv')

def main():
    if not os.path.exists(IN_FILE):
        return
        
    with open(IN_FILE, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
        
    login_clusters = defaultdict(list)
    for r in rows:
        lid = r.get('LOGINID','').strip().lower()
        if lid and lid not in ('null', 'none'):
            login_clusters[lid].append(r)
            
    out = []
    for lid, members in login_clusters.items():
        if len(members) > 1:
            userids = set(m.get('USERID','').upper() for m in members if m.get('USERID'))
            personids = set(m.get('PERSONID','').upper() for m in members if m.get('PERSONID'))
            displaynames = set(m.get('DISPLAYNAME','').upper() for m in members if m.get('DISPLAYNAME'))
            
            if len(userids) > 1 or len(personids) > 1 or len(displaynames) > 1:
                envs = set(m.get('ENV_DB','') for m in members if m.get('ENV_DB'))
                out.append({
                    'LOGINID': lid,
                    'ENV_LIST': '; '.join(sorted(envs)),
                    'USERID_LIST': '; '.join(sorted(userids)),
                    'PERSONID_LIST': '; '.join(sorted(personids)),
                    'DISPLAYNAME_LIST': '; '.join(sorted(displaynames)),
                    'ACCOUNT_CLASS_LIST': '; '.join(sorted(set(m.get('ACCOUNT_CLASS','') for m in members if m.get('ACCOUNT_CLASS')))),
                    'LOGIN_REUSE_FLAG': 'TRUE',
                    'CONFLICT_HINT': 'MULTIPLE_USERS_SAME_LOGIN' if len(userids)>1 else 'MULTIPLE_PERSONS_SAME_LOGIN'
                })
                
    if out:
        with open(OUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            writer.writeheader()
            writer.writerows(sorted(out, key=lambda x: x['LOGINID']))
        print(f"WROTE {OUT_FILE} ({len(out)} records)")

if __name__ == '__main__':
    main()