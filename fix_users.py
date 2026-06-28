import sys
p = 'scripts/reporting/html_template.py'
with open(p, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar linha com '# Build chart series'
target = -1
for i, l in enumerate(lines):
    if l.strip().startswith('# Build chart series'):
        target = i
        break

if target < 0 or target+4 >= len(lines):
    print('block not found')
    sys.exit(1)

# Verificar as 4 linhas seguintes
print('Found at line', target+1)
print('Lines:', [lines[target].strip(), lines[target+1].strip(), lines[target+2].strip(), lines[target+3].strip(), lines[target+4].strip()])

# Substituir linhas 335-339 pelo novo bloco
users_block = [
    '    # Users series (capacidade)\n',
    '    peak_hours_users = analytics.get(\'concurrency_peak_users_hours\', []) or []\n',
    '    users_rows = []\n',
    '    if isinstance(peak_hours_users, dict):\n',
    '        users_rows = [[k, v] for k, v in sorted(peak_hours_users.items())]\n',
    '    elif isinstance(peak_hours_users, list):\n',
    '        for entry in peak_hours_users:\n',
    '            if isinstance(entry, (list, tuple)) and len(entry) >= 2:\n',
    '                users_rows.append([entry[0], entry[1]])\n',
    '            elif isinstance(entry, dict):\n',
    '                hour = entry.get(\'hour\') or entry.get(\'ts\') or entry.get(\'time\')\n',
    '                val = entry.get(\'value\') or entry.get(\'users\') or entry.get(\'count\')\n',
    '                users_rows.append([hour, val])\n',
    '\n',
    '    users_labels = [r[0] for r in users_rows if r and len(r) >= 2]\n',
    '    users_data = [r[1] for r in users_rows if r and len(r) >= 2]\n',
    '    points_labels = [r[0] for r in peak_rows if r and len(r) >= 2]\n',
    '    points_data = [r[1] for r in peak_rows if r and len(r) >= 2]\n',
    '\n',
    '    # Fallback: se n\u00e3o vierem dados de usu\u00e1rios (capacidade), desenha com AppPoints (consumo)\n',
    '    used_fallback_app_points = False\n',
    '    if (not users_data) and peak_rows:\n',
    '        users_labels = [r[0] for r in peak_rows if r and len(r) >= 2]\n',
    '        users_data = [r[1] for r in peak_rows if r and len(r) >= 2]\n',
    '        points_labels = []\n',
    '        points_data = []\n',
    '        used_fallback_app_points = True\n',
]

# Substituir
new_lines = lines[:target] + users_block + lines[target+5:]

with open(p, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('fixed ok')