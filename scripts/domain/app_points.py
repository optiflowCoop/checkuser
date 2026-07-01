# domain/app_points.py
# REFACTORED: Remove duplications, import from canonical modules
# This module now focuses only on simulation orchestration
#
# CANONICAL SOURCES (Single Source of Truth):
# - classify_usage_profile, determine_user_entitlement → scripts.analysis.classification
# - assign_license_model → scripts.analysis.licensing
# - calculate_app_points → scripts.analysis.entitlement
from scripts.analysis.classification import classify_usage_profile, determine_user_entitlement
from scripts.analysis.licensing import assign_license_model
from scripts.analysis.entitlement import calculate_app_points

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
