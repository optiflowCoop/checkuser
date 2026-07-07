from pathlib import Path
html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

print('VERIFICACAO FILTROS ABA 8:')
print('=' * 60)

# Verificar se o JavaScript da Aba 8 está presente
print('\n1. JAVASCRIPT:')
print('  function filterByType:', 'function filterByType' in html)
print('  function filterMigracaoTable:', 'function filterMigracaoTable' in html)

# Verificar se os data-tipo estão corretos
import re
tipos_esperados = ['remover', 'migrar', 'manter', 'criar_no_maximo', 'verificar_ad']
print('\n2. DATA-TIPO ESPERADOS:')
for tipo in tipos_esperados:
    count = html.count(f'data-tipo="{tipo}"')
    print(f'  {tipo}: {count}')

# Verificar onclick nos cards
print('\n3. ONCLICK NOS CARDS:')
for tipo in tipos_esperados:
    card_id = f'card-{tipo}'
    onclick = f'onclick="filterByType(\'{tipo}\')"'
    has_card = card_id in html
    has_onclick = onclick in html
    print(f'  {card_id}: card={has_card}, onclick={has_onclick}')

print('\n✅ Verificação concluída!')