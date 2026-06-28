import sys
p = 'scripts/reporting/html_template.py'
with open(p, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar linhas 357-360 e corrigir
for i, l in enumerate(lines):
    if l.strip() == 'used_fallback_app_points = False':
        # Linha 355 (0-indexed: 354)
        # Proximas linhas: if (not users_data), users_labels, users_data, points_labels, points_data, used_fallback
        start = i
        # Verificar
        print(f'Found at line {i+1}')
        print(f'  {lines[i].strip()}')
        print(f'  {lines[i+1].strip()}')
        print(f'  {lines[i+2].strip()}')
        print(f'  {lines[i+3].strip()}')
        print(f'  {lines[i+4].strip()}')
        print(f'  {lines[i+5].strip()}')
        
        # Substituir lines[i+2:i+4] (points_labels e points_data)
        # De [] para [r[0] for r in peak_rows] / [r[1] for r in peak_rows]
        old_pts_labels = lines[i+3]
        old_pts_data = lines[i+4]
        lines[i+3] = '        points_labels = [r[0] for r in peak_rows if r and len(r) >= 2]\n'
        lines[i+4] = '        points_data = [r[1] for r in peak_rows if r and len(r) >= 2]\n'
        
        with open(p, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print('fixed')
        break
else:
    print('not found')