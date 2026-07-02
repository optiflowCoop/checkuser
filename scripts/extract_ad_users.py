#!/usr/bin/env python3
"""
Extract and consolidate AD users from the CSV file provided by the Microsoft team.
Copies the file to the consolidated output directory with standardized column names.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_FILE = ROOT / 'adUsers' / 'adUsers.csv'
OUT_DIR = ROOT / 'output' / 'consolidated'
OUT_FILE = OUT_DIR / 'consolidated_ad_users.csv'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Mapeamento de colunas do CSV do AD para o formato padrão
COLUMN_MAP = {
    'Enabled': 'Enabled',
    'GivenName': 'GivenName',
    'Surname': 'Surname',
    'DisplayName': 'DisplayName',
    'mail': 'mail',
    'UserPrincipalName': 'UserPrincipalName',
    'MemberOf': 'MemberOf',
}

# Multiplicador de AppPoints por tipo de licença (não aplicável ao AD, mas mantido para compatibilidade)
APP_POINTS_MAP = {
    'PREMIUM': {'AUTHORIZED': 5, 'CONCURRENT': 15},
    'BASE': {'AUTHORIZED': 3, 'CONCURRENT': 10},
}


def extract_domain(email):
    """Extrai o domínio do email."""
    if not email or '@' not in str(email):
        return 'SEM DOMINIO'
    return str(email).split('@')[1].lower().strip()


def extract_email_prefix(email):
    """Extrai o prefixo (parte antes do @) do email como possível USERID."""
    if not email or '@' not in str(email):
        return ''
    return str(email).split('@')[0].lower().strip()


def parse_ad_csv(file_path):
    """
    Parseia CSV do AD manualmente para lidar com campos que contém vírgulas.
    O CSV do AD usa ; como delimitador, mas o campo MemberOf pode ter vírgulas dentro.
    """
    rows = []
    with file_path.open('r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    if not lines:
        return rows
    
    # Ler header
    header_line = lines[0].strip()
    headers = [h.strip() for h in header_line.split(';')]
    num_headers = len(headers)
    
    # Processar cada linha
    for line_num, line in enumerate(lines[1:], 2):
        line = line.strip()
        if not line:
            continue
        
        # Split por ; mas limitar ao número de colunas
        parts = line.split(';')
        
        # Se tem mais partes que headers, assumir que o excesso está no último campo (MemberOf)
        if len(parts) > num_headers:
            # Juntar partes extras no último campo
            excess = parts[num_headers-1:]
            parts = parts[:num_headers-1] + ['; '.join(excess)]
        
        # Se tem menos partes, preencher com vazio
        while len(parts) < num_headers:
            parts.append('')
        
        # Criar dicionário
        row = {}
        for i, header in enumerate(headers):
            row[header] = parts[i].strip() if i < len(parts) else ''
        
        rows.append(row)
    
    return rows


def main():
    if not IN_FILE.exists():
        print(f"❌ Arquivo de AD não encontrado: {IN_FILE}")
        print("   Coloque o arquivo CSV do AD na pasta 'adUsers/'")
        sys.exit(1)
    
    print(f"📥 Lendo dados do AD: {IN_FILE.name}")
    
    # Usar parser customizado
    ad_rows = parse_ad_csv(IN_FILE)
    
    print(f"   Total de registros lidos: {len(ad_rows)}")
    if ad_rows:
        print(f"   Colunas: {list(ad_rows[0].keys())}")
    
    # Estatísticas
    total = len(ad_rows)
    enabled = sum(1 for r in ad_rows if r.get('Enabled', '').strip().lower() == 'true')
    disabled = total - enabled
    
    # Contagem por domínio
    domain_counts = {}
    for r in ad_rows:
        email = r.get('mail', '')
        domain = extract_domain(email)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # Domínios FORESEA
    foresea_count = sum(1 for r in ad_rows if 'foresea.com' in str(r.get('mail', '')).lower())
    partner_count = sum(1 for r in ad_rows if 'foresea-partner.com' in str(r.get('mail', '')).lower())
    
    print(f"\n📊 Estatísticas do AD:")
    print(f"   Total de usuários: {total}")
    print(f"   Contas habilitadas: {enabled}")
    print(f"   Contas desabilitadas: {disabled}")
    print(f"   Domínio @foresea.com: {foresea_count}")
    print(f"   Domínio @foresea-partner.com: {partner_count}")
    print(f"   Outros domínios: {total - foresea_count - partner_count}")
    
    print(f"\n   Top 10 domínios:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"      {domain}: {count}")
    
    # Padronizar e escrever arquivo consolidado
    fieldnames = list(COLUMN_MAP.keys())
    
    with OUT_FILE.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        
        for row in ad_rows:
            # Padronizar campos
            out_row = {}
            for ad_col, std_col in COLUMN_MAP.items():
                value = row.get(ad_col, '').strip()
                out_row[std_col] = value
            
            writer.writerow(out_row)
    
    print(f"\n✅ Arquivo consolidado escrito: {OUT_FILE.name}")
    print(f"   {total} usuários exportados com {len(fieldnames)} colunas")


if __name__ == '__main__':
    main()