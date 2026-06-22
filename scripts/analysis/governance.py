# analysis/governance.py
from collections import Counter, defaultdict

def analyze_domain_distribution(active_profiles):
    """Counts active users per domain category."""
    return Counter(p['DOMAIN_CATEGORY'] for p in active_profiles)

def analyze_title_divergences(access_rows, user_profiles):
    """
    Finds titles that have inconsistent TYPEs or security groups across different environments.
    """
    title_patterns = defaultdict(lambda: {'types': defaultdict(set), 'groups': defaultdict(set)})
    
    # Only consider access rows for active users
    active_access_rows = [
        r for r in access_rows
        if user_profiles.get(r.get('USERID','').strip().upper(), {}).get('STATUS') == 'ACTIVE'
    ]

    for item in active_access_rows:
        title = item.get('TITLE', '').strip()
        if not title: continue
        
        env = item.get('ENV_DB', '').strip()
        type_val = item.get('TYPE', '').strip()
        group = item.get('GROUPNAME', '').strip()

        if env:
            if type_val:
                title_patterns[title]['types'][env].add(type_val)
            if group:
                title_patterns[title]['groups'][env].add(group)

    divergences = []
    for title, data in title_patterns.items():
        # Check if the title exists in more than one environment
        all_envs = set(data['types'].keys()) | set(data['groups'].keys())
        if len(all_envs) <= 1:
            continue

        # Check for type divergence: more than one unique type across all environments
        all_types = {t for types_set in data['types'].values() for t in types_set}
        has_type_divergence = len(all_types) > 1

        # Check for group divergence: not all environments have the exact same set of groups
        if data['groups']:
            base_groups = next(iter(data['groups'].values()))
            has_group_divergence = any(s != base_groups for s in data['groups'].values())
        else:
            has_group_divergence = False

        if has_type_divergence or has_group_divergence:
            divergences.append(title)

    return divergences, title_patterns
