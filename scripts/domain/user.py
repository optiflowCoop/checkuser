# domain/user.py
from collections import defaultdict
from scripts.config import get_foresea_domains

def get_user_domain_category(email):
    if not email or '@' not in email:
        return 'SEM DOMINIO'
    domain = email.split('@')[1].lower()
    foresea_domains = get_foresea_domains()
    if domain == foresea_domains[0]:
        return 'FORESEA'
    if domain == foresea_domains[1]:
        return 'PARCEIRO'
    return 'TERCEIRO'

def build_user_profiles(identities, access_rows, email_rows=None, person_rows=None, persongroupview_rows=None):
    user_profiles = defaultdict(lambda: {
        'USERID': '', 'DISPLAYNAME': set(), 'STATUS': 'INACTIVE', 'EMAIL': '',
        'DOMAIN_CATEGORY': 'SEM DOMINIO', 'PERSONGROUPS': set(), 'TITLES': set(),
        'GROUPS': set(), 'ENVS': set(), 'TYPE': set(),
    })
    
    for r in identities:
        userid = r.get('USERID', '').strip().upper()
        if not userid: continue
        profile = user_profiles[userid]
        profile['USERID'] = userid
        profile['DISPLAYNAME'].add(r.get('DISPLAYNAME', '').strip())
        profile['ENVS'].add(r.get('ENV_DB', '').strip())
        if r.get('STATUS', '').upper() == 'ACTIVE': profile['STATUS'] = 'ACTIVE'
        email = r.get('PRIMARYEMAIL', '').strip()
        if email and not profile['EMAIL']:
            profile['EMAIL'] = email
            profile['DOMAIN_CATEGORY'] = get_user_domain_category(email)

    for r in email_rows or []:
        userid = (r.get('PERSONID') or r.get('USERID') or '').strip().upper()
        email = (r.get('EMAILADDRESS') or r.get('PRIMARYEMAIL') or '').strip()
        if not userid or not email or userid not in user_profiles:
            continue
        profile = user_profiles[userid]
        if not profile['EMAIL']:
            profile['EMAIL'] = email
            profile['DOMAIN_CATEGORY'] = get_user_domain_category(email)

    for r in person_rows or []:
        userid = (r.get('PERSONID') or r.get('personid') or '').strip().upper()
        if not userid or userid not in user_profiles:
            continue
        profile = user_profiles[userid]
        display = (r.get('DISPLAYNAME') or r.get('displayname') or '').strip()
        title = (r.get('TITLE') or r.get('title') or '').strip()
        if display:
            profile['DISPLAYNAME'].add(display)
        if title:
            profile['TITLES'].add(title)

    for r in persongroupview_rows or []:
        userid = (r.get('personid') or r.get('PERSONID') or '').strip().upper()
        if not userid or userid not in user_profiles:
            continue
        profile = user_profiles[userid]
        display = (r.get('displayname') or r.get('DISPLAYNAME') or '').strip()
        title = (r.get('title') or r.get('TITLE') or '').strip()
        persongroup = (r.get('persongroup') or r.get('PERSONGROUP') or '').strip()
        if display:
            profile['DISPLAYNAME'].add(display)
        if title:
            profile['TITLES'].add(title)
        if persongroup:
            profile['PERSONGROUPS'].add(persongroup)

    for r in access_rows:
        userid = r.get('USERID', '').strip().upper()
        if userid in user_profiles and user_profiles[userid]['STATUS'] == 'ACTIVE':
            profile = user_profiles[userid]
            persongroup = r.get('PERSONGROUP', '').strip()
            title = r.get('TITLE', '').strip()
            group = r.get('GROUPNAME', '').strip()
            account_type = r.get('TYPE', '').strip()
            if persongroup:
                profile['PERSONGROUPS'].add(persongroup)
            if title:
                profile['TITLES'].add(title)
            if group:
                profile['GROUPS'].add(group)
            if account_type:
                profile['TYPE'].add(account_type)
            
    return user_profiles
