from pathlib import Path
import re

html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

print('VERIFICACAO JAVASCRIPT ABA 8:')
print('=' * 60)

# Procurar a função filterByType
if 'function filterByType' in html:
    print('✓ function filterByType encontrada')
    # Extrair o código da função
    match = re.search(r'function filterByType\(\) \{.*?\n\s+}', html, re.DOTALL)
    if match:
        print('\nCódigo da função:')
        print(match.group(0)[:500])
else:
    print('✗ function filterByType NÃO encontrada')

# Procurar a função filterMigracaoTable
if 'function filterMigracaoTable' in html:
    print('\n✓ function filterMigracaoTable encontrada')
else:
    print('\n✗ function filterMigracaoTable NÃO encontrada')

# Verificar se o script está dentro da aba 8
aba8_pos = html.find('tab-migracao')
if aba8_pos > 0:
    script_after_aba8 = html.find('function filterByType', aba8_pos)
    if script_after_aba8 > 0:
        print('✓ JavaScript está após a aba 8')
    else:
        print('✗ JavaScript NÃO está após a aba 8')
else:
    print('✗ Aba 8 não encontrada')

print('\n✅ Verificação concluída!')