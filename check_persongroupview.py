import csv
from pathlib import Path

p = Path('output/consolidated/consolidated_persongroupview.csv')
rows = list(csv.DictReader(p.open(encoding='utf-8-sig')))

print('Total rows:', len(rows))
print()

# Filtrar linhas válidas
valid_rows = [r for r in rows if r.get('personid') and r.get('personid') != '(C) COPYRIGHT International Business Machines Corp. 1993']
print('Linhas válidas:', len(valid_rows))
print()

print('Primeiras 10 linhas válidas:')
for r in valid_rows[:10]:
    print(f"{r['ENVIRONMENT']} | {r.get('personid', '')[:20]} | {r.get('locationsite', '')}")