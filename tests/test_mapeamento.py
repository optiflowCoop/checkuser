import re
from pathlib import Path

html = Path('output/reports/maximo_unified_dashboard.html').read_text(encoding='utf-8')

print('MAPEAMENTO CARD -> DATA-TIPO:')
mapeamento = {
    'card-all': 'all',
    'card-match': 'match',
    'card-ad_only': 'ad_only',
    'card-maximo_only': 'maximo_only',
    'card-name_divergence': 'name_divergence',
    'card-multi_userid': 'multi_userid',
    'card-prefix_match': 'prefix_match',
    'card-no_match': 'no_match',
}

for card_id, expected_tipo in mapeamento.items():
    card_exists = card_id in html
    pattern = 'data-tipo="' + expected_tipo + '"'
    linhas_tipo = re.findall(pattern, html)
    qtd = len(linhas_tipo)
    status_card = 'OK' if card_exists else 'FALTA'
    print(f'  {card_id:<25} -> {expected_tipo:<20} Card: {status_card} | Linhas: {qtd}')

total_linhas = len(re.findall(r'<tr data-tipo=', html))
print(f'\nTotal de linhas na tabela: {total_linhas}')
print(f'Numero BR nos cards: {"2.424" in html}')