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

def build_user_profiles(identities, access_rows):
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

    for r in access_rows:
        userid = r.get('USERID', '').strip().upper()
        if userid in user_profiles and user_profiles[userid]['STATUS'] == 'ACTIVE':
            profile = user_profiles[userid]
            profile['PERSONGROUPS'].add(r.get('PERSONGROUP', '').strip())
            profile['TITLES'].add(r.get('TITLE', '').strip())
            profile['GROUPS'].add(r.get('GROUPNAME', '').strip())
            profile['TYPE'].add(r.get('TYPE', '').strip())
            
    return user_profiles
