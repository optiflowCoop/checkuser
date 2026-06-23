# analysis/classification.py
from scripts.config import get_entitlement_keywords

def classify_usage_profile(group_count):
    """Classifies user usage profile based on the number of groups they belong to."""
    if group_count > 8: return "POWER"
    if group_count > 4: return "MEDIUM"
    return "LIGHT"

def determine_user_entitlement(user_groups):
    """Determines user entitlement based on group keywords."""
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