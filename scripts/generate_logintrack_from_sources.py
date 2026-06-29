#!/usr/bin/env python3
"""
Gera consolidated_logintracking_from_sources.csv a partir do 
consolidated_logintracking.csv (que tem dados dos 7 ambientes).

O arquivo de saída mantém a coluna ENVIRONMENT para identificar 
qual ambiente cada registro pertence, permitindo análises 
detalhadas por ambiente no dashboard.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'consolidated'

def main():
    print("🔄 Gerando consolidated_logintracking_from_sources.csv...")
    
    in_path = IN_DIR / 'consolidated_logintracking.csv'
    out_path = OUT_DIR / 'consolidated_logintracking_from_sources.csv'
    
    if not in_path.exists():
        print(f"❌ Arquivo de origem não encontrado: {in_path}")
        print("   Execute primeiro: python scripts/consolidate_outputs.py")
        return
    
    with in_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("❌ Nenhum dado encontrado no consolidated_logintracking.csv")
        return
    
    # Define os campos de saída (mantendo ENVIRONMENT e adicionando source_file)
    fieldnames = ['ENVIRONMENT', 'USERID', 'APP', 'ATTEMPTDATE', 'ATTEMPTRESULT', 
                  'CLIENTHOST', 'CLIENTADDR', 'source_file']
    
    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for row in rows:
            env = row.get('ENVIRONMENT', '').strip()
            out_row = {
                'ENVIRONMENT': env,
                'USERID': row.get('USERID', '').strip(),
                'APP': row.get('APP', '').strip(),
                'ATTEMPTDATE': row.get('ATTEMPTDATE', '').strip(),
                'ATTEMPTRESULT': row.get('ATTEMPTRESULT', '').strip(),
                'CLIENTHOST': row.get('CLIENTHOST', '').strip(),
                'CLIENTADDR': row.get('CLIENTADDR', '').strip(),
                'source_file': f'consolidated_logintracking_{env}.csv'
            }
            writer.writerow(out_row)
    
    # Estatísticas
    with out_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        out_rows = list(reader)
    
    env_counts = {}
    for r in out_rows:
        env = r.get('ENVIRONMENT', 'UNKNOWN')
        env_counts[env] = env_counts.get(env, 0) + 1
    
    users = set(r.get('USERID', '').strip().upper() for r in out_rows if r.get('USERID'))
    logins = [r for r in out_rows if r.get('ATTEMPTRESULT', '').strip().upper() == 'LOGIN']
    login_users = set(r.get('USERID', '').strip().upper() for r in logins if r.get('USERID'))
    
    print(f"\n✅ {out_path.name} gerado com sucesso!")
    print(f"   Total de registros: {len(out_rows)}")
    print(f"   Total de LOGINs: {len(logins)}")
    print(f"   Usuários únicos: {len(users)}")
    print(f"   Usuários com LOGIN: {len(login_users)}")
    print(f"\n📊 Distribuição por ambiente:")
    for env in sorted(env_counts.keys()):
        print(f"   • {env}: {env_counts[env]:,} registros")

if __name__ == '__main__':
    main()