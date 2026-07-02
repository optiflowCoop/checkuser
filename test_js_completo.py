from pathlib import Path
import re

html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

print('VERIFICACAO COMPLETA DO JAVASCRIPT:')
print('=' * 60)

# Extrair o JavaScript da Aba 8
aba8_js_match = re.search(r'<div id="tab-migracao".*?(<script>.*?</script>)', html, re.DOTALL)
if aba8_js_match:
    js_code = aba8_js_match.group(1)
    print('JavaScript encontrado na Aba 8:')
    print(js_code[:1000])
    print('...')
else:
    print('✗ JavaScript NÃO encontrado na Aba 8')
    
# Verificar se há erros de sintaxe
print('\n' + '=' * 60)
print('VERIFICACAO DE SINTAXE:')
print('=' * 60)

# Contar chaves abertas e fechadas
open_braces = html.count('{')
close_braces = html.count('}')
print(f'Chaves abertas: {open_braces}')
print(f'Chaves fechadas: {close_braces}')
print(f'Balanceado: {open_braces == close_braces}')

# Verificar se há funções duplicadas
functions = re.findall(r'function\s+(\w+)', html)
unique_functions = set(functions)
print(f'\nFunções encontradas: {len(functions)}')
print(f'Funções únicas: {len(unique_functions)}')
if len(functions) != len(unique_functions):
    print('⚠️ ATENÇÃO: Há funções duplicadas!')
    from collections import Counter
    func_counts = Counter(functions)
    for func, count in func_counts.items():
        if count > 1:
            print(f'  - {func}: {count}x')
else:
    print('✓ Nenhuma função duplicada')

print('\n✅ Verificação concluída!')