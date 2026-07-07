import re
from pathlib import Path

html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

# 1. Verificar números no formato BR
print("FORMATO DE NUMEROS (BR):")
card_valores = re.findall(r'<div class="stat-value">([^<]+)</div>', html)
for v in card_valores:
    print(f'  Valor no card: "{v}"')

# 2. Verificar se os cards tem onclick
tem_onclick = 'onclick="filterByType' in html
print(f'\nCards com onclick: {tem_onclick}')

# 3. Verificar filterByType function
tem_filter = 'function filterByType' in html
print(f'Function filterByType: {tem_filter}')

# 4. data-tipo
tem_datatipo = 'data-tipo="' in html
print(f'data-tipo nas linhas: {tem_datatipo}')

# 5. Conteudo
print(f'\nNome Divergente: {"Nome Divergente" in html}')
print(f'Match USERID: {"Match USERID" in html}')
print(f'Apenas AD: {"Apenas AD" in html}')

# 6. Exemplo
print(f'\nExemplo de linha divergente:')
for line in html.split('\n'):
    if 'Nome Divergente' in line:
        print(f'  {line.strip()[:150]}')
        break