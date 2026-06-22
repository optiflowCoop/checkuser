#!/usr/bin/env python3
"""Create consolidated_user_access.csv by joining maxuser, person, email, groupuser and maxgroup."""

from __future__ import annotations
import csv
import os
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(__file__))
OUTDIR = os.path.join(ROOT, "output", "consolidated")
os.makedirs(OUTDIR, exist_ok=True)

def read_csv(path):
    if not os.path.exists(path):
        print(f"WARN: missing {path}")
        return []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)

def main():
    maxuser_f = os.path.join(OUTDIR, "consolidated_maxuser.csv")
    person_f = os.path.join(OUTDIR, "consolidated_person.csv")
    email_f = os.path.join(OUTDIR, "consolidated_email.csv")
    groupuser_f = os.path.join(OUTDIR, "consolidated_groupuser.csv")
    maxgroup_f = os.path.join(OUTDIR, "consolidated_maxgroup.csv")
    persongroupview_f = os.path.join(OUTDIR, "consolidated_persongroupview.csv")

    maxusers = read_csv(maxuser_f)
    persons = read_csv(person_f)
    emails = read_csv(email_f)
    groupusers = read_csv(groupuser_f)
    maxgroups = read_csv(maxgroup_f)
    persongroupviews = read_csv(persongroupview_f)

    env_alias = {'N06': 'NORBE06', 'N08': 'NORBE08', 'N09': 'NORBE09'}
    def canon_env(v):
        v = (v or '').strip()
        return env_alias.get(v, v)

    email_index = {}
    for e in emails:
        env = canon_env(e.get('ENVIRONMENT', ''))
        pid = e.get('PERSONID', '').strip()
        if env and pid:
            email_index[f"{env}|{pid}"] = e.get('EMAILADDRESS', '')

    person_index = {}
    for p in persons:
        env = canon_env(p.get('ENVIRONMENT', ''))
        pid = p.get('PERSONID', '').strip()
        if env and pid:
            p['PRIMARYEMAIL'] = email_index.get(f"{env}|{pid}", "")
            person_index[f"{env}|{pid}"] = p

    persongroupview_index = defaultdict(list)
    for pgv in persongroupviews:
        env = canon_env(pgv.get('ENVIRONMENT', ''))
        pid = pgv.get('personid', '').strip() # Note: DDL shows lowercase
        if env and pid:
            persongroupview_index[f"{env}|{pid}"].append(pgv)

    user_index = {}
    for r in maxusers:
        env = canon_env(r.get('ENVIRONMENT', ''))
        userid = r.get('USERID', '').strip()
        if not env or not userid: continue
        
        pid = r.get('PERSONID', '').strip()
        pdata = person_index.get(f"{env}|{pid}", {})
        
        r['FIRSTNAME'] = pdata.get('FIRSTNAME', '').strip()
        r['LASTNAME'] = pdata.get('LASTNAME', '').strip()
        r['PRIMARYEMAIL'] = pdata.get('PRIMARYEMAIL', '').strip()
        
        disp = pdata.get('DISPLAYNAME', '').strip()
        if not disp and (r['FIRSTNAME'] or r['LASTNAME']):
            disp = f"{r['FIRSTNAME']} {r['LASTNAME']}".strip()
        r['DISPLAYNAME'] = disp

        pgv_data_list = persongroupview_index.get(f"{env}|{pid}", [])
        if pgv_data_list:
            pgv_data = pgv_data_list[0]
            r['TITLE'] = pgv_data.get('title', '')
            r['PERSONGROUP'] = '; '.join(sorted(list(set(pgv.get('persongroup', '') for pgv in pgv_data_list if pgv.get('persongroup')))))
        else:
            r['TITLE'] = ''
            r['PERSONGROUP'] = ''
        
        user_index[f"{env}|{userid}"] = r

    group_index = {g.get('GROUPNAME', '').strip(): g for g in maxgroups if g.get('GROUPNAME')}

    group_flag_cols = [
        'AUTHALLSITES','AUTHALLGLS','AUTHALLSTOREROOMS',
        'AUTHLABORALL','AUTHLABORCREW','AUTHLABORSELF','AUTHLABORSUPER',
        'AUTHPERSONGROUP','DFLTAPP','WORKCENTER'
    ]

    header = [
        'ENV_DB','USERID','PERSONID','LOGINID','STATUS','DEFSITE','TYPE',
        'FIRSTNAME','LASTNAME','DISPLAYNAME','PRIMARYEMAIL',
        'TITLE', 'PERSONGROUP',
        'GROUPNAME','GROUP_DESCRIPTION','GROUP_FLAGS','SOURCE_FILE','LOAD_TIMESTAMP'
    ] + group_flag_cols

    out_rows = []

    if groupusers:
        for g in groupusers:
            env = canon_env(g.get('ENVIRONMENT', ''))
            userid = g.get('USERID', '').strip()
            groupname = g.get('GROUPNAME', '').strip()
            source = g.get('_source', 'consolidated_groupuser')
            
            row = dict.fromkeys(header, '')
            row['ENV_DB'] = env
            row['USERID'] = userid
            
            user = user_index.get(f"{env}|{userid}")
            if user:
                # Copia apenas as chaves que existem no header
                for key in header:
                    if key in user:
                        row[key] = user[key]
                row['SOURCE_FILE'] = maxuser_f
            else:
                row['SOURCE_FILE'] = source
                
            row['GROUPNAME'] = groupname
            grp = group_index.get(groupname)
            if grp:
                flags = []
                for k in ('AUTHALLSITES','AUTHALLSTOREROOMS','AUTHLABORALL','AUTHPERSONGROUP'):
                    v = grp.get(k)
                    if v and v.strip().upper() not in ('0','FALSE','N'):
                        flags.append(k)
                row['GROUP_FLAGS'] = ';'.join(flags)
                row['GROUP_DESCRIPTION'] = grp.get('DESCRIPTION', '')
                for k in group_flag_cols:
                    row[k] = grp.get(k,'')
                    
            row['LOAD_TIMESTAMP'] = datetime.now(timezone.utc).isoformat()
            out_rows.append(row)
    else:
        for key, user in user_index.items():
            row = {k: '' for k in header}
            for k in header:
                if k in user:
                    row[k] = user[k]
            row['SOURCE_FILE'] = maxuser_f
            out_rows.append(row)

    out_path = os.path.join(OUTDIR, 'consolidated_user_access.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"WROTE {out_path} ({len(out_rows)} rows)")

if __name__ == '__main__':
    main()