from pathlib import Path
html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

print('VERIFICACAO SIMPLES ABA 8:')
print('=' * 60)

# Verificar cards
print('\n1. CARDS:')
print('  card-all:', 'id="card-all"' in html)
print('  card-remover:', 'id="card-remover"' in html)
print('  card-migrar:', 'id="card-migrar"' in html)
print('  card-manter:', 'id="card-manter"' in html)
print('  card-criar_no_maximo:', 'id="card-criar_no_maximo"' in html)
print('  card-verificar_ad:', 'id="card-verificar_ad"' in html)

# Verificar onclick
print('\n2. ONCLICK:')
print('  filterByType presente:', 'filterByType(' in html)

# Verificar tabela
print('\n3. TABELA:')
print('  table-migracao:', 'id="table-migracao"' in html)

# Verificar data-tipo
import re
tipos = re.findall(r'data-tipo="([^"]+)"', html)
print(f'\n4. DATA-TIPO ({len(tipos)} total):')
unique_tipos = {}
for t in tipos:
    unique_tipos[t] = unique_tipos.get(t, 0) + 1
for tipo, count in sorted(unique_tipos.items()):
    print(f'  {tipo}: {count}')

print('\n✅ Verificação concluída!')