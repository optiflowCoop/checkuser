# domain/app_points.py
from scripts.config import get_entitlement_keywords, get_critical_titles, get_app_points_config

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

def simulate_app_points(active_profiles):
    foresea_profiles = [p for p in active_profiles if p['DOMAIN_CATEGORY'] in ('FORESEA', 'PARCEIRO')]
    app_points_data = []
    for profile in foresea_profiles:
        usage = classify_usage_profile(len(profile['GROUPS']))
        entitlement = determine_user_entitlement(profile['GROUPS'])
        license_model = assign_license_model(usage, profile['TITLES'])
        points = calculate_app_points(entitlement, license_model)
        app_points_data.append({
            'USERID': profile['USERID'], 
            'DISPLAYNAME': '; '.join(sorted(profile['DISPLAYNAME'])),
            'ENTITLEMENT': entitlement, 
            'LICENSE_MODEL': license_model, 
            'APP_POINTS': points,
            'USAGE_PROFILE': usage, 
            'TITLES': '; '.join(sorted(profile['TITLES'])),
            'GROUP_COUNT': len(profile['GROUPS']),
        })
    return app_points_data
