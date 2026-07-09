#!/usr/bin/env python3
"""
Extract and consolidate Maximo users from the consolidated person data.
Generates a standardized CSV with email, name, and status for comparison with AD.
"""
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'consolidated'
OUT_FILE = OUT_DIR / 'consolidated_maximo_users.csv'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path):
    """Helper to load a single CSV, returning an empty list if not found."""
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=','))


def main():
    # Carrega dados consolidados do Maximo
    persons = load_csv(IN_DIR / 'consolidated_person.csv')
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    access_rows = load_csv(IN_DIR / 'consolidated_user_access_normalized.csv') or load_csv(IN_DIR / 'consolidated_user_access.csv')
    
    print(f"📥 Carregando dados do Maximo:")
    print(f"   Persons: {len(persons)}")
    print(f"   Identities: {len(identities)}")
    print(f"   Access Rows: {len(access_rows)}")
    
    # Construir mapa de email por USERID a partir de identities
    # CONSIDERAR APENAS EMAILS COM @ (válidos)
    email_by_userid = {}
    for row in identities:
        uid = str(row.get('USERID', '')).strip().upper()
        # Tentar PRIMARYEMAIL, depois EMAIL
        email = row.get('PRIMARYEMAIL', row.get('EMAIL', '')).strip()
        # Apenas emails válidos (com @)
        if uid and email and '@' in email:
            if uid not in email_by_userid:
                email_by_userid[uid] = email
    
    # Construir mapa de displayname por USERID
    name_by_userid = {}
    for row in persons:
        uid = str(row.get('PERSONID', '')).strip().upper()
        displayname = row.get('DISPLAYNAME', row.get('NAME', '')).strip()
        if uid and displayname:
            if uid not in name_by_userid:
                name_by_userid[uid] = displayname
    
    # Coletar todos os USERIDs únicos do access_rows
    user_ids = set()
    for row in access_rows:
        uid = str(row.get('USERID', '')).strip().upper()
        if uid:
            user_ids.add(uid)
    
    # Para identities que não estão em access_rows, também incluir
    for row in identities:
        uid = str(row.get('USERID', '')).strip().upper()
        if uid:
            user_ids.add(uid)
    
    print(f"\n   Total de USERIDs únicos: {len(user_ids)}")
    
    # Gerar linhas para o CSV de Maximo
    # USUÁRIOS COM EMAIL VÁLIDO
    maximo_rows_with_email = []
    # USUÁRIOS SEM EMAIL (não comparáveis no saneamento)
    maximo_rows_without_email = []
    
    for uid in sorted(user_ids):
        email = email_by_userid.get(uid, '')
        nome = name_by_userid.get(uid, uid)
        
        # Determinar domínio
        if not email or '@' not in email:
            domain = 'SEM DOMINIO'
            maximo_rows_without_email.append({
                'USERID': uid,
                'NOME': nome,
                'EMAIL': email,
                'DOMAIN': domain,
                'COMPARABLE': 'NÃO',  # Não pode ser comparado no saneamento
            })
        else:
            domain = email.split('@')[1].lower().strip()
            maximo_rows_with_email.append({
                'USERID': uid,
                'NOME': nome,
                'EMAIL': email,
                'DOMAIN': domain,
                'COMPARABLE': 'SIM',  # Pode ser comparado no saneamento
            })
    
    # Combinar todos
    maximo_rows = maximo_rows_with_email + maximo_rows_without_email
    
    # Estatísticas
    total = len(maximo_rows)
    with_email = len(maximo_rows_with_email)
    without_email = len(maximo_rows_without_email)
    
    foresea_count = sum(1 for r in maximo_rows_with_email if 'foresea.com' in r['EMAIL'].lower())
    partner_count = sum(1 for r in maximo_rows_with_email if 'foresea-partner.com' in r['EMAIL'].lower())
    
    print(f"\n📊 Estatísticas do Maximo:")
    print(f"   Total de usuários: {total}")
    print(f"   Com email (comparáveis): {with_email}")
    print(f"   Sem email (não comparáveis): {without_email}")
    print(f"   Domínio @foresea.com: {foresea_count}")
    print(f"   Domínio @foresea-partner.com: {partner_count}")
    
    # Escrever arquivo consolidado
    fieldnames = ['USERID', 'NOME', 'EMAIL', 'DOMAIN', 'COMPARABLE']
    
    with OUT_FILE.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=',', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(maximo_rows)
    
    print(f"\n✅ Arquivo consolidado escrito: {OUT_FILE.name}")
    print(f"   {total} usuários exportados com {len(fieldnames)} colunas")
    print(f"   {with_email} comparáveis no saneamento")
    print(f"   {without_email} não comparáveis (sem email)")


if __name__ == '__main__':
    main()