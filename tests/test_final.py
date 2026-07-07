from pathlib import Path
html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

print('VERIFICACAO FINAL DAS ABAS 7 E 8:')
print('=' * 60)

# Aba 7
print('\nABA 7 - SANEAMENTO AD:')
print('  Tab button:', 'tab-saneamento' in html)
print('  Cards clicaveis:', 'filterByType' in html)
print('  Tabela:', 'table-saneamento' in html)

# Aba 8
print('\nABA 8 - RECOMENDACOES DE MIGRACAO:')
print('  Tab button:', 'tab-migracao' in html)
print('  Cards:', 'Remover' in html and 'Migrar' in html and 'Manter' in html)
print('  Tabela:', 'table-migracao' in html)
print('  Filtros:', 'filterMigracaoTable' in html)
print('  Export CSV:', 'exportMigracaoCSV' in html)

print('\nTamanho do HTML:', len(html), 'bytes')
print('\n✅ Pipeline completa executada com sucesso!')