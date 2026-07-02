from pathlib import Path
import re

html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

print('SIMULACAO DO FILTRO JAVASCRIPT:')
print('=' * 60)

# Extrair todas as linhas da tabela
table_match = re.search(r'<table id="table-migracao">.*?</table>', html, re.DOTALL)
if table_match:
    table_html = table_match.group(0)
    
    # Extrair data-tipo de cada linha
    tipos_na_tabela = re.findall(r'<tr data-tipo="([^"]+)"', table_html)
    print(f'Total de linhas na tabela: {len(tipos_na_tabela)}')
    
    # Simular filtro por tipo
    tipos_esperados = ['remover', 'migrar', 'manter', 'criar_no_maximo', 'verificar_ad']
    
    print('\nSimulando filtro por cada tipo:')
    for filtro in tipos_esperados:
        count = 0
        for tipo in tipos_na_tabela:
            # Lógica do JavaScript: tipo.toUpperCase() === effectiveFilter.toUpperCase()
            if tipo.upper() == filtro.upper():
                count += 1
        print(f'  filterByType("{filtro}"): {count} linhas visíveis')
    
    # Simular busca vazia
    print('\nCom busca vazia e sem filtro:')
    count_all = len(tipos_na_tabela)
    print(f'  filterByType("all"): {count_all} linhas visíveis')
else:
    print('✗ Tabela não encontrada')

print('\n✅ Simulação concluída!')