#!/usr/bin/env python3
"""Applies the scoring logic to classify identity conflicts and merges decisions."""
import csv
import os
from config_loader import load_identity_rules

ROOT = os.path.dirname(os.path.dirname(__file__))
OUTDIR = os.path.join(ROOT, 'output', 'consolidated')

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def main():
    identities = read_csv(os.path.join(OUTDIR, 'consolidated_user_identity.csv'))
    reused = read_csv(os.path.join(OUTDIR, 'cross_env_userid_reuse.csv'))
    rules = load_identity_rules()
    
    if not identities or not reused:
        return

    # Map raw records for easy lookup
    raw_map = {}
    for r in identities:
        raw_map[r['RAW_ID']] = r

    worklist_out = []
    
    for c in reused:
        raw_ids = [x.strip() for x in c.get('RAW_ID_LIST', '').split(';') if x.strip()]
        pids = [x.strip() for x in c.get('PERSONID_LIST', '').split(';') if x.strip()]
        lids = [x.strip() for x in c.get('LOGINID_LIST', '').split(';') if x.strip()]
        dnames = [x.strip() for x in c.get('DISPLAYNAME_LIST', '').split(';') if x.strip()]
        emails = [x.strip() for x in c.get('EMAIL_LIST', '').split(';') if x.strip()]
        stats = [x.strip() for x in c.get('STATUS_LIST', '').split(';') if x.strip()]
        acls = [x.strip() for x in c.get('ACCOUNT_CLASS_LIST', '').split(';') if x.strip()]
        envs_count = int(c.get('ENV_COUNT', 1))
        
        # 1. Hard Rules (Explicit Conflicts)
        hypothesis = ''
        merge_decision = ''
        review_prio = ''
        col_type = 'NO_CONFLICT'
        score = 0
        rules_triggered = []
        
        # O Ponto Cego Resolvido: DisplayName ou Email divergentes são PROVAS HUMANAS de colisão
        conflict_reason = ''
        if envs_count > 1 and len(dnames) > 1:
            col_type = 'DISPLAYNAME_CONFLICT'
            hypothesis = 'CONFIRMED_DIFFERENT_PERSON'
            merge_decision = 'DO_NOT_MERGE'
            review_prio = 'CRITICAL'
            rules_triggered.append('displayname_conflict')
            conflict_reason = f'Nomes diferentes detectados: {"; ".join(sorted(dnames))}'
        elif envs_count > 1 and len(emails) > 1:
            col_type = 'EMAIL_CONFLICT'
            hypothesis = 'CONFIRMED_DIFFERENT_PERSON'
            merge_decision = 'DO_NOT_MERGE'
            review_prio = 'CRITICAL'
            rules_triggered.append('email_conflict')
            conflict_reason = f'E-mails diferentes: {"; ".join(sorted(emails))}'
        elif envs_count > 1 and len(pids) > 1:
            col_type = 'PERSONID_CONFLICT'
            hypothesis = 'CONFIRMED_DIFFERENT_PERSON'
            merge_decision = 'DO_NOT_MERGE'
            review_prio = 'HIGH'
            rules_triggered.append('personid_conflict')
            conflict_reason = f'PersonIDs diferentes: {"; ".join(sorted(pids))}'
        elif envs_count > 1 and len(lids) > 1:
            col_type = 'LOGINID_CONFLICT'
            hypothesis = 'REQUIRES_REVIEW'
            merge_decision = 'MANUAL_REVIEW_REQUIRED'
            review_prio = 'MEDIUM'
            rules_triggered.append('loginid_conflict')
            conflict_reason = f'LoginIDs corporativos distintos: {"; ".join(sorted(lids))}'
        elif envs_count > 1 and len(stats) > 1:
            col_type = 'STATUS_CONFLICT'
            hypothesis = 'REQUIRES_REVIEW'
            merge_decision = 'MANUAL_REVIEW_REQUIRED'
            review_prio = 'MEDIUM'
            rules_triggered.append('status_conflict')
            conflict_reason = f'Status inconsistentes: {"; ".join(sorted(stats))}'
        elif envs_count > 1 and len(acls) > 1 and 'HUMAN' in acls:
            col_type = 'ACCOUNT_CLASS_CONFLICT'
            hypothesis = 'REQUIRES_REVIEW'
            merge_decision = 'MANUAL_REVIEW_REQUIRED'
            review_prio = 'MEDIUM'
            rules_triggered.append('account_class_conflict')
            conflict_reason = f'Classes de conta mistas: {"; ".join(sorted(acls))}'
            
        # 2. Score Match (Soft Rules) se não for hard conflict
        if col_type == 'NO_CONFLICT':
            if len(pids) == 1 and pids[0]: score += 40
            if len(lids) == 1 and lids[0]: score += 30
            if len(acls) == 1 and acls[0]: score += 10
            
            # Penalties
            if len(pids) > 1: score -= 50
            if len(lids) > 1: score -= 40
            if len(stats) > 1: score -= 20
            if len(acls) > 1: score -= 15
            
            if score <= 0:
                hypothesis = 'CONFIRMED_DIFFERENT_PERSON'
                merge_decision = 'DO_NOT_MERGE'
                review_prio = 'HIGH'
            elif 1 <= score <= 49:
                hypothesis = 'REQUIRES_REVIEW'
                merge_decision = 'MANUAL_REVIEW_REQUIRED'
                review_prio = 'MEDIUM'
            elif 50 <= score <= 79:
                hypothesis = 'POTENTIAL_SAME_PERSON'
                merge_decision = 'AWAITING_AD_MATCH'
                review_prio = 'LOW'
            else:
                hypothesis = 'POTENTIAL_SAME_PERSON'
                merge_decision = 'MERGE_AFTER_AD_MATCH'
                review_prio = 'LOW'

            col_type = 'CROSS_ENV_USERID_REUSE'
            rules_triggered.append('score_bands')
            if score <= 0:
                conflict_reason = f'Score negativo ({score}): inconsistências múltiplas detectadas'
            elif 1 <= score <= 49:
                conflict_reason = f'Score baixo ({score}): dados parcialmente compatíveis, requer revisão humana'
            else:
                conflict_reason = f'Score adequado ({score}): aguardando validação Active Directory'

        # Create Worklist rows for each raw id in the cluster
        for raw_id in raw_ids:
            ident = raw_map.get(raw_id, {})
            worklist_out.append({
                'RAW_ID': raw_id,
                'ENV_DB': ident.get('ENV_DB',''),
                'USERID': ident.get('USERID',''),
                'PERSONID': ident.get('PERSONID',''),
                'LOGINID': ident.get('LOGINID',''),
                'DISPLAYNAME': ident.get('DISPLAYNAME',''),
                'PRIMARYEMAIL': ident.get('PRIMARYEMAIL',''),
                'STATUS': ident.get('STATUS',''),
                'DEFSITE': ident.get('DEFSITE',''),
                'TYPE': ident.get('TYPE',''),
                'TITLE': ident.get('TITLE',''),
                'PERSONGROUP': ident.get('PERSONGROUP',''),
                'ACCOUNT_CLASS': ident.get('ACCOUNT_CLASS',''),
                'COLLISION_TYPE': col_type,
                'MATCH_SCORE': score,
                'HYPOTHESIS': hypothesis,
                'AD_MATCH_STATUS': 'PENDING',
                'MERGE_DECISION': merge_decision,
                'REVIEW_PRIORITY': review_prio,
                'MATCH_RULES_TRIGGERED': '; '.join(rules_triggered),
                'CONFLICT_REASON': conflict_reason,
                'COMMENTS': ''
            })
            
    if worklist_out:
        out_file = os.path.join(OUTDIR, 'identity_collisions_enriched.csv')
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(worklist_out[0].keys()))
            writer.writeheader()
            writer.writerows(sorted(worklist_out, key=lambda x: (x['REVIEW_PRIORITY']!='CRITICAL', x['REVIEW_PRIORITY']!='HIGH', x['REVIEW_PRIORITY']!='MEDIUM', x['USERID'])))
        print(f"WROTE {out_file} ({len(worklist_out)} records)")

if __name__ == '__main__':
    main()