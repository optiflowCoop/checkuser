# services/app_points.py
from scripts.analysis.classification import classify_usage_profile, assign_license_model
from scripts.analysis.entitlement import determine_user_entitlement, calculate_app_points


def simulate_app_points(profiles_to_simulate):
    """
    Performs the AppPoints simulation for a given list of user profiles.
    """
    app_points_data = []
    for profile in profiles_to_simulate:
        usage = classify_usage_profile(len(profile['GROUPS']))
        entitlement = determine_user_entitlement(profile['GROUPS'])
        license_model = assign_license_model(usage, profile['TITLES'])
        points = calculate_app_points(entitlement, license_model)

        # Filtro para remover valores vazios ou nulos que causam o ";" no início
        display_names = [n for n in profile.get('DISPLAYNAME', []) if n and str(n).strip()]
        titles = [t for t in profile.get('TITLES', []) if t and str(t).strip()]

        app_points_data.append({
            'USERID': profile['USERID'],
            'DISPLAYNAME': '; '.join(display_names),
            'ENTITLEMENT': entitlement,
            'LICENSE_MODEL': license_model,
            'APP_POINTS': points,
            'USAGE_PROFILE': usage,
            'TITLES': '; '.join(titles),
        })
    return app_points_data