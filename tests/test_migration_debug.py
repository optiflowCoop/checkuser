import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts.domain.migration_advisor import load_csv, analyze_migration

# Carregar dados
ad_rows = load_csv(ROOT / 'output' / 'consolidated' / 'consolidated_ad_users.csv')
identities = load_csv(ROOT / 'output' / 'consolidated' / 'consolidated_user_identity.csv')

print(f"AD: {len(ad_rows)} usuários")
print(f"Identities: {len(identities)} registros")

# Construir mapas
ad_by_email = {}
for r in ad_rows:
    email = r.get('mail', '').strip().lower()
    if email and '@' in email:
        ad_by_email[email] = r

print(f"\nAD emails únicos: {len(ad_by_email)}")

# Maximo emails únicos
from collections import defaultdict
maximo_by_userid = defaultdict(lambda: {'emails': set(), 'statuses': set()})
for r in identities:
    userid = r.get('USERID', '').strip().upper()
    email = r.get('PRIMARYEMAIL', '').strip().lower()
    status = r.get('STATUS', '').strip().upper()
    if userid and email:
        maximo_by_userid[userid]['emails'].add(email)
    if userid and status:
        maximo_by_userid[userid]['statuses'].add(status)

print(f"Maximo USERIDs com email: {sum(1 for mx in maximo_by_userid.values() if mx['emails'])}")

# Contar matches
matches = 0
for email in ad_by_email:
    has_match = any(email in mx['emails'] for mx in maximo_by_userid.values())
    if has_match:
        matches += 1

print(f"Matches por email: {matches}")
print(f"Apenas no AD: {len(ad_by_email) - matches}")