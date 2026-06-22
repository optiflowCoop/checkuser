# analysis/classification.py
from scripts.config import get_critical_titles

def classify_usage_profile(group_count):
    """
    Classifica o perfil de uso (POWER, MEDIUM, LIGHT) com base na contagem de grupos.
    """
    if group_count > 8:
        return "POWER"
    elif group_count > 4:
        return "MEDIUM"
    else:
        return "LIGHT"

def assign_license_model(usage_profile, user_titles):
    """
    Atribui o modelo de licença (Authorized ou Concurrent) com base no perfil de uso
    e na criticidade do cargo do usuário.
    """
    critical_titles = get_critical_titles()
    user_titles_str = " ".join(user_titles).upper()
    is_critical = any(crit_title in user_titles_str for crit_title in critical_titles)
    
    if usage_profile == "POWER" or is_critical:
        return "AUTHORIZED"
    
    return "CONCURRENT"
