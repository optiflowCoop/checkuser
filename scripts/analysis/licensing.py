# analysis/licensing.py
from scripts.config import get_app_points_config, get_critical_titles, get_foresea_domains
from .classification import classify_usage_profile, determine_user_entitlement

def assign_license_model(usage_profile, user_titles):
    """Determines the license model based on usage profile and titles."""
    critical_titles = get_critical_titles()
    user_titles_str = " ".join(user_titles).upper()
    is_critical = any(crit_title in user_titles_str for crit_title in critical_titles)
    
    if usage_profile == "POWER" or is_critical:
        return "AUTHORIZED"
    return "CONCURRENT"

def calculate_app_points(entitlement, license_model):
    """Calculates AppPoints based on entitlement and license model."""
    config = get_app_points_config()
    return config.get(entitlement, {}).get(license_model, 0)

def simulate_app_points(active_profiles):
    """
    Runs the AppPoints simulation for eligible users (Foresea and Partners).
    """
    foresea_domains = get_foresea_domains()
    eligible_profiles = [p for p in active_profiles if p['DOMAIN_CATEGORY'] in foresea_domains]
    
    app_points_results = []
    for profile in eligible_profiles:
        usage = classify_usage_profile(len(profile['GROUPS']))
        entitlement = determine_user_entitlement(profile['GROUPS'])
        license_model = assign_license_model(usage, profile['TITLES'])
        points = calculate_app_points(entitlement, license_model)
        
        app_points_results.append({
            'USERID': profile['USERID'], 
            'DISPLAYNAME': '; '.join(profile['DISPLAYNAME']),
            'ENTITLEMENT': entitlement, 
            'LICENSE_MODEL': license_model, 
            'APP_POINTS': points,
            'USAGE_PROFILE': usage, 
            'TITLES': '; '.join(profile['TITLES']),
            'LOGIN_COUNT_90D': profile.get('LOGIN_COUNT_90D', 0), # Pass through for usage analysis
            'OPTIMIZATION_REC': 'N/A', # Placeholder for the next step
        })
        
    return app_points_results
