# services/analysis.py
from collections import Counter, defaultdict

def analyze_governance(active_profiles):
    """
    Performs basic governance analysis, like counting users by domain.
    """
    domain_counts = Counter(p['DOMAIN_CATEGORY'] for p in active_profiles)
    return domain_counts

def analyze_title_divergences(access_rows, user_profiles):
    """
    Analyzes title divergences across different environments for active users.
    Returns a list of divergent titles and a detailed structure for reporting.
    """
    title_patterns = defaultdict(lambda: {'types': defaultdict(set), 'groups': defaultdict(set)})
    
    for item in access_rows:
        # Process only active users
        if user_profiles.get(item.get('USERID','').strip().upper(), {}).get('STATUS') == 'ACTIVE':
            title = item.get('TITLE', '').strip()
            if not title:
                continue
            
            env = item.get('ENV_DB', '').strip()
            type_val = item.get('TYPE', '').strip()
            group = item.get('GROUPNAME', '').strip()
            
            if env and type_val:
                title_patterns[title]['types'][env].add(type_val)
            if env and group:
                title_patterns[title]['groups'][env].add(group)
    
    divergent_titles = []
    detailed_divergences = []

    for title, data in title_patterns.items():
        # Check for type inconsistencies
        all_types = {t for types in data['types'].values() for t in types}
        has_type_divergence = len(all_types) > 1
        
        # Check for group inconsistencies
        base_groups = next(iter(data['groups'].values()), set())
        has_group_divergence = any(s != base_groups for s in data['groups'].values())
        
        if has_type_divergence or has_group_divergence:
            divergent_titles.append(title)
            detailed_divergences.append({'title': title, 'data': data})
            
    return divergent_titles, detailed_divergences
