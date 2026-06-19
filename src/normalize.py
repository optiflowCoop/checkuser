#!/usr/bin/env python3
"""Normalize `consolidated_user_access.csv` values and produce `consolidated_user_identity.csv`."""
from __future__ import annotations
import csv
import os
import re
from config_loader import load_identity_rules

ROOT = os.path.dirname(os.path.dirname(__file__))
OUTDIR = os.path.join(ROOT, 'output', 'consolidated')
IN_FILE = os.path.join(OUTDIR, 'consolidated_user_access.csv')
NORMALIZED = os.path.join(OUTDIR, 'consolidated_user_access_normalized.csv')
IDENTITY = os.path.join(OUTDIR, 'consolidated_user_identity.csv')

def read_csv(path):
    if not os.path.exists(path):
        print(f"ERR: missing {path}")
        return []
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def get_account_class(userid, loginid, groups, rules):
    uid = (userid or '').upper()
    grp = (groups or '').upper()
    
    if not uid: return 'UNKNOWN'
    
    acc_rules = rules.get('account_classification', {})
    default_class = acc_rules.get('default_class', 'HUMAN')
    
    for rule in acc_rules.get('rules', []):
        cls = rule['class']
        if uid in [x.upper() for x in rule.get('match_userid_exact', [])]:
            return cls
        for rx in rule.get('match_userid_regex', []):
            if re.search(rx, uid): return cls
        for rx in rule.get('match_any_field_regex', []):
            if re.search(rx, uid) or re.search(rx, (loginid or '').upper()): return cls
        for rx in rule.get('match_groups_regex', []):
            if re.search(rx, grp): return cls
            
    return default_class

def norm_str(s):
    if s is None: return ''
    s = s.strip()
    if not s: return ''
    if s.upper() in ('NAN', 'NONE', 'NULL'): return ''
    return s

def main():
    rows = read_csv(IN_FILE)
    if not rows: return
        
    rules = load_identity_rules()

    fieldnames = list(rows[0].keys()) + ['ACCOUNT_CLASS']
    with open(NORMALIZED, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            r2 = {k: norm_str(v) for k,v in r.items()}
            if r2.get('USERID'): r2['USERID'] = r2['USERID'].upper()
            if r2.get('PERSONID'): r2['PERSONID'] = r2['PERSONID'].upper()
            if r2.get('LOGINID'): r2['LOGINID'] = r2['LOGINID'].lower()
            if r2.get('STATUS'): r2['STATUS'] = r2['STATUS'].upper()
            if r2.get('TYPE'): r2['TYPE'] = r2['TYPE'].upper()
            
            r2['ACCOUNT_CLASS'] = get_account_class(r2.get('USERID',''), r2.get('LOGINID',''), r2.get('GROUPNAME',''), rules)
            writer.writerow(r2)

    agg = {}
    for r in read_csv(NORMALIZED):
        env = r.get('ENV_DB','')
        userid = r.get('USERID','')
        key = f"{env}|{userid}"
        if key not in agg:
            agg[key] = {
                'RAW_ID': key,
                'ENV_DB': env,
                'USERID': userid,
                'PERSONID': r.get('PERSONID',''),
                'LOGINID': r.get('LOGINID',''),
                'FIRSTNAME': r.get('FIRSTNAME',''),
                'LASTNAME': r.get('LASTNAME',''),
                'DISPLAYNAME': r.get('DISPLAYNAME',''),
                'PRIMARYEMAIL': r.get('PRIMARYEMAIL',''),
                'STATUS': r.get('STATUS',''),
                'DEFSITE': r.get('DEFSITE',''),
                'TYPE': r.get('TYPE',''),
                'TOTAL_GROUPS': 0,
                'ACCOUNT_CLASS': r.get('ACCOUNT_CLASS','')
            }
        agg[key]['TOTAL_GROUPS'] += 1

    id_fields = ['RAW_ID', 'ENV_DB','USERID','PERSONID','LOGINID','FIRSTNAME','LASTNAME','DISPLAYNAME','PRIMARYEMAIL','STATUS','DEFSITE','TYPE','TOTAL_GROUPS','ACCOUNT_CLASS']
    with open(IDENTITY, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=id_fields)
        writer.writeheader()
        for v in agg.values():
            writer.writerow(v)

    print(f'WROTE {NORMALIZED} ({len(rows)} rows)')
    print(f'WROTE {IDENTITY} ({len(agg)} rows)')

if __name__ == '__main__':
    main()