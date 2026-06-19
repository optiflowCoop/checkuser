#!/usr/bin/env python3
"""Identity collision detection using consolidated_user_identity.csv

Outputs:
- `output/consolidated/identity_clusters.csv` (Cross-Env USERID Reuse)
- `output/consolidated/login_conflicts.csv` (Cross-Env LOGINID Conflicts)
- `output/consolidated/identity_collisions_enriched.csv` (The Sanitation Worklist)
"""
from __future__ import annotations
import csv
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
OUTDIR = os.path.join(ROOT, 'output', 'consolidated')
IN_FILE = os.path.join(OUTDIR, 'consolidated_user_identity.csv')
WORKLIST_FILE = os.path.join(OUTDIR, 'identity_collisions_enriched.csv')
CLUSTER_FILE = os.path.join(OUTDIR, 'identity_clusters.csv')
LOGIN_CONFLICTS_FILE = os.path.join(OUTDIR, 'login_conflicts.csv')

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def main():
    rows = read_csv(IN_FILE)
    if not rows:
        print(f"No input rows found in {IN_FILE}. Run normalize.py first.")
        return

    # Group records by USERID to find cross-environment repetitions
    clusters = defaultdict(list)
    login_clusters = defaultdict(list)

    for r in rows:
        userid = r.get('USERID', '').strip().upper()
        loginid = r.get('LOGINID', '').strip().upper()
        if userid:
            clusters[userid].append(r)
        if loginid and loginid != 'NULL' and loginid != 'NONE':
            login_clusters[loginid].append(r)

    worklist_rows = []
    cluster_summaries = []
    login_conflicts = []

    # 1. Process USERID Clusters (Cross-Env Reuse)
    for uid, members in clusters.items():
        if len(members) > 1:
            envs = set(m.get('ENV_DB', '').strip() for m in members)
            
            if len(envs) > 1:
                personids = set(m.get('PERSONID', '').strip().upper() for m in members if m.get('PERSONID', '').strip())
                loginids = set(m.get('LOGINID', '').strip().upper() for m in members if m.get('LOGINID', '').strip())
                
                # Apply conservative rules
                if len(personids) > 1:
                    hypothesis = 'CONFIRMED_DIFFERENT_PERSON'
                    priority = 'CRITICAL'
                    col_type = 'PERSONID_CONFLICT'
                    merge_decision = 'DO_NOT_MERGE'
                    confidence = 'HIGH'
                    needs_human = 'YES'
                    needs_ad = 'YES'
                    rules = 'SAME_USERID + DIFFERENT_PERSONID'
                elif len(loginids) > 1:
                    hypothesis = 'REQUIRES_REVIEW'
                    priority = 'HIGH'
                    col_type = 'LOGINID_CONFLICT'
                    merge_decision = 'MANUAL_REVIEW_REQUIRED'
                    confidence = 'MEDIUM'
                    needs_human = 'YES'
                    needs_ad = 'YES'
                    rules = 'SAME_USERID + DIFFERENT_LOGINID'
                else:
                    hypothesis = 'POTENTIAL_SAME_PERSON'
                    priority = 'MEDIUM'
                    col_type = 'EXACT_TECHNICAL_MATCH'
                    merge_decision = 'AWAITING_AD_MATCH'
                    confidence = 'LOW (Lacks AD)'
                    needs_human = 'NO'
                    needs_ad = 'YES'
                    rules = 'SAME_USERID + SAME_PERSONID + SAME_LOGINID'
                    
                cluster_summaries.append({
                    'USERID': uid,
                    'ENV_COUNT': len(envs),
                    'PERSONID_COUNT': len(personids),
                    'LOGINID_COUNT': len(loginids),
                    'HYPOTHESIS': hypothesis,
                    'REVIEW_PRIORITY': priority,
                    'MERGE_DECISION': merge_decision,
                    'NEEDS_AD_CONFIRMATION': needs_ad,
                    'ENV_LIST': '; '.join(sorted(envs)),
                    'PERSONID_LIST': '; '.join(sorted(personids))
                })
                
                # Generate worklist items
                for m in members:
                    env = m.get('ENV_DB', '').strip()
                    worklist_rows.append({
                        'RAW_ID': f"{env}|{m.get('USERID', '')}",
                        'ENV_DB': env,
                        'USERID': m.get('USERID', ''),
                        'PERSONID': m.get('PERSONID', ''),
                        'LOGINID': m.get('LOGINID', ''),
                        'STATUS': m.get('STATUS', ''),
                        'COLLISION_TYPE': col_type,
                        'SAME_PERSON_HYPOTHESIS': hypothesis,
                        'REVIEW_PRIORITY': priority,
                        'MATCH_RULES_TRIGGERED': rules,
                        'MATCH_CONFIDENCE': confidence,
                        'NEEDS_AD_CONFIRMATION': needs_ad,
                        'NEEDS_HUMAN_REVIEW': needs_human,
                        'MERGE_DECISION': merge_decision,
                        'AD_MATCH': 'PENDING',
                        'RESOLUTION_STATUS': 'OPEN',
                        'COMMENTS': ''
                    })

    # 2. Process LOGINID Clusters (Finding Login Conflicts)
    for lid, members in login_clusters.items():
        if len(members) > 1:
            envs = set(m.get('ENV_DB', '').strip() for m in members)
            userids = set(m.get('USERID', '').strip().upper() for m in members)
            personids = set(m.get('PERSONID', '').strip().upper() for m in members if m.get('PERSONID', '').strip())

            # If the same login is mapped to different USERIDs or PERSONIDs across/within envs
            if len(userids) > 1 or len(personids) > 1:
                login_conflicts.append({
                    'LOGINID': lid,
                    'CONFLICT_TYPE': 'MULTIPLE_USERS_SAME_LOGIN',
                    'ENV_COUNT': len(envs),
                    'ENV_LIST': '; '.join(sorted(envs)),
                    'USERID_LIST': '; '.join(sorted(userids)),
                    'PERSONID_LIST': '; '.join(sorted(personids)),
                    'REQUIRES_REVIEW': 'YES'
                })

    # Write CLUSTERS
    if cluster_summaries:
        c_fields = list(cluster_summaries[0].keys())
        with open(CLUSTER_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=c_fields)
            writer.writeheader()
            for r in sorted(cluster_summaries, key=lambda x: (x['REVIEW_PRIORITY']!='CRITICAL', x['REVIEW_PRIORITY']!='HIGH', x['USERID'])):
                writer.writerow(r)
        print(f"WROTE {CLUSTER_FILE} ({len(cluster_summaries)} clusters)")

    # Write LOGIN CONFLICTS
    if login_conflicts:
        l_fields = list(login_conflicts[0].keys())
        with open(LOGIN_CONFLICTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=l_fields)
            writer.writeheader()
            for r in sorted(login_conflicts, key=lambda x: x['LOGINID']):
                writer.writerow(r)
        print(f"WROTE {LOGIN_CONFLICTS_FILE} ({len(login_conflicts)} conflicts)")

    # Write WORKLIST
    if worklist_rows:
        w_fields = list(worklist_rows[0].keys())
        with open(WORKLIST_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=w_fields)
            writer.writeheader()
            for r in sorted(worklist_rows, key=lambda x: (x['REVIEW_PRIORITY']!='CRITICAL', x['REVIEW_PRIORITY']!='HIGH', x['USERID'])):
                writer.writerow(r)
        print(f"WROTE {WORKLIST_FILE} ({len(worklist_rows)} worklist items)")
    else:
        print("No cross-environment collisions detected.")

if __name__ == '__main__':
    main()