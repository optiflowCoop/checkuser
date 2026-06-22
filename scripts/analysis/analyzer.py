# analysis/analyzer.py
from collections import Counter, defaultdict
from scripts.config import get_app_points_config, get_entitlement_keywords, get_critical_titles, get_foresea_domains

def classify_usage_profile(group_count):
    if group_count > 8: return "POWER"
    if group_count > 4: return "MEDIUM"
    return "LIGHT"

def determine_user_entitlement(user_groups):
    keywords = get_entitlement_keywords()
    for group in user_groups:
        group_upper = group.upper()
        if any(keyword in group_upper for keyword in keywords['PREMIUM']): return 'PREMIUM'
    for group in user_groups:
        group_upper = group.upper()
        if any(keyword in group_upper for keyword in keywords['BASE']): return 'BASE'
    for group in user_groups:
        group_upper = group.upper()
        if any(keyword in group_upper for keyword in keywords['LIMITED']): return 'LIMITED'
    return 'SELF FREE'

def assign_license_model(usage_profile, user_titles):
    critical_titles = get_critical_titles()
    user_titles_str = " ".join(user_titles).upper()
    is_critical = any(crit_title in user_titles_str for crit_title in critical_titles)
    if usage_profile == "POWER" or is_critical:
        return "AUTHORIZED"
    return "CONCURRENT"

def calculate_app_points(entitlement, license_model):
    config = get_app_points_config()
    return config.get(entitlement, {}).get(license_model, 0)

def run_governance_analysis(active_profiles, access_rows):
    """
    Performs governance analysis, such as domain distribution and title divergence.
    """
    domain_counts = Counter(p['DOMAIN_CATEGORY'] for p in active_profiles)
    
    title_patterns = defaultdict(lambda: {'types': defaultdict(set), 'groups': defaultdict(set)})
    for item in access_rows:
        # This check is simplified because we assume access_rows is for active users
        title = item.get('TITLE', '').strip()
        if not title: continue
        title_patterns[title]['types'][item.get('ENV_DB')].add(item.get('TYPE'))
        title_patterns[title]['groups'][item.get('ENV_DB')].add(item.get('GROUPNAME'))
    
    title_divergences = []
    for title, data in title_patterns.items():
        # Check for divergence only if the title appears in more than one context (env)
        if len(data['types']) > 1 or len(data['groups']) > 1:
            all_types = {t for types in data['types'].values() for t in types}
            base_groups = next(iter(data['groups'].values()), set())
            # A divergence exists if there's more than one type OR if not all group sets are identical
            if len(all_types) > 1 or any(s != base_groups for s in data['groups'].values()):
                title_divergences.append(title)
                
    return {
        'domain_counts': domain_counts,
        'title_divergences': title_divergences,
    }

def run_app_points_simulation(active_profiles):
    """
    Runs the AppPoints simulation for eligible users.
    """
    foresea_domains = get_foresea_domains()
    foresea_profiles = [p for p in active_profiles if p['DOMAIN_CATEGORY'] in ('FORESEA', 'PARCEIRO')]
    
    app_points_data = []
    for profile in foresea_profiles:
        usage = classify_usage_profile(len(profile['GROUPS']))
        entitlement = determine_user_entitlement(profile['GROUPS'])
        license_model = assign_license_model(usage, profile['TITLES'])
        points = calculate_app_points(entitlement, license_model)
        
        app_points_data.append({
            'USERID': profile['USERID'], 
            'DISPLAYNAME': '; '.join(profile['DISPLAYNAME']),
            'ENTITLEMENT': entitlement, 
            'LICENSE_MODEL': license_model, 
            'APP_POINTS': points,
            'USAGE_PROFILE': usage, 
            'TITLES': '; '.join(profile['TITLES']),
        })
        
    return app_points_data
