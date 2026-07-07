import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.generate_risk_report import load_all_data

all_data = load_all_data()
print('Dados carregados:')
print(f'  AD users: {len(all_data.get("ad_users", []))}')
print(f'  Maximo users: {len(all_data.get("maximo_users", []))}')
print(f'  Identities: {len(all_data.get("identities", []))}')

# Verificar se os arquivos existem
ad_path = Path('output/consolidated/consolidated_ad_users.csv')
maximo_path = Path('output/consolidated/consolidated_maximo_users.csv')
print(f'\nArquivos existem:')
print(f'  AD: {ad_path.exists()} - {ad_path}')
print(f'  Maximo: {maximo_path.exists()} - {maximo_path}')

# Verificar estrutura dos dados
if all_data.get('ad_users'):
    print(f'\nExemplo AD: {all_data["ad_users"][0]}')
if all_data.get('maximo_users'):
    print(f'\nExemplo Maximo: {all_data["maximo_users"][0]}')