# analysis/governance.py
from collections import Counter, defaultdict

def analyze_domain_distribution(active_profiles):
    """Analyzes the distribution of users across different domain categories."""
    return Counter(p['DOMAIN_CATEGORY'] for p in active_profiles)

def analyze_title_divergences(access_rows, user_profiles):
    """
    Analyzes divergences in user titles and group assignments across different environments.
    Returns a list of divergent titles and a detailed dictionary of the divergences.
    """
    title_patterns = defaultdict(lambda: {
        'types': defaultdict(set),
        'groups': defaultdict(set),
        'users': defaultdict(list)
    })

    # 1. Aggregate data from access_rows
    for item in access_rows:
        userid = item.get('USERID')
        profile = user_profiles.get(userid)
        
        # We only care about active users
        if not profile or profile.get('STATUS') != 'ACTIVE':
            continue

        title = item.get('TITLE', '').strip()
        if not title:
            continue
            
        env = item.get('ENV_DB')
        title_patterns[title]['types'][env].add(item.get('TYPE'))
        title_patterns[title]['groups'][env].add(item.get('GROUPNAME'))
        title_patterns[title]['users'][env].append(userid)

    # 2. Identify and structure the divergences
    divergent_titles = []
    detailed_divergences = []
    for title, data in title_patterns.items():
        # Flatten all observed types and groups
        all_types = {t for types_in_env in data['types'].values() for t in types_in_env if t}
        all_groups = {g for groups_in_env in data['groups'].values() for g in groups_in_env if g}

        # Check for divergence conditions
        has_type_divergence = len(all_types) > 1
        
        # Check if group assignments are inconsistent across environments
        # Use the first group set as a baseline
        base_groups = next(iter(data['groups'].values()), set())
        has_group_divergence = any(s != base_groups for s in data['groups'].values())

        if has_type_divergence or has_group_divergence:
            divergent_titles.append(title)
            detailed_divergences.append({
                'title': title,
                'has_type_divergence': has_type_divergence,
                'has_group_divergence': has_group_divergence,
                'data': {
                    'types': {k: sorted(list(v)) for k, v in data['types'].items()},
                    'groups': {k: sorted(list(v)) for k, v in data['groups'].items()},
                }
            })
            
    return divergent_titles, detailed_divergences
