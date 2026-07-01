# analysis/classification.py
# CANONICAL MODULE: User classification logic
# Single source of truth for usage profile determination
from scripts.config import get_entitlement_keywords

def classify_usage_profile(group_count):
    """
    CANONICAL: Classifies user usage profile based on the number of groups they belong to.
    
    This heuristic correlates group membership with system usage intensity:
    - POWER: Users with access to many modules (>8 groups)
    - MEDIUM: Regular users with moderate access (>4 groups)
    - LIGHT: Occasional users with minimal access (≤4 groups)
    
    Args:
        group_count: Number of security groups the user belongs to
        
    Returns:
        'POWER', 'MEDIUM', or 'LIGHT'
        
    Reference: docs/SISTEMA_DOCUMENTACAO.md, Section 4.2
    """
    if group_count > 8: return "POWER"
    if group_count > 4: return "MEDIUM"
    return "LIGHT"

def determine_user_entitlement(user_groups):
    """
    CANONICAL: Determines user entitlement based on group keywords.
    
    DEPRECATED WARNING: This function is duplicated in scripts.analysis.entitlement.
    Use scripts.analysis.entitlement.determine_user_entitlement instead.
    This duplicate exists for backward compatibility only.
    
    Args:
        user_groups: List of security group names
        
    Returns:
        'PREMIUM', 'BASE', 'LIMITED', or 'SELF FREE'
    """
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