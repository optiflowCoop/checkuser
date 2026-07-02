from pathlib import Path
html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

print('Verificacao da Aba 7:')
print(f'  Tab button: {"tab-saneamento" in html}')
print(f'  Card principal: {"Saneamento de Identidades" in html}')
print(f'  Estatisticas AD: {"Usuarios no AD" in html}')
print(f'  Divergencias de Nome: {"Divergencias de Nome" in html}')
print(f'  Tabela: {"table-saneamento" in html}')

# Contar cards
import re
cards = re.findall(r'<div class="stat-value">([0-9.]+)</div>', html)
print(f'\nCards encontrados: {len(cards)}')
if cards:
    print(f'Valores: {cards[:8]}')

print(f'\nTamanho do HTML: {len(html):,} bytes')