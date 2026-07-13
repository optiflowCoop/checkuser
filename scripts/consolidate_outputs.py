from pathlib import Path
import csv
from collections import defaultdict
import re

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / 'output' / 'raw'
OUT_DIR = ROOT / 'output' / 'consolidated'

HEADERS_MAP = {
    'person': ['PERSONID', 'FIRSTNAME', 'LASTNAME', 'DISPLAYNAME'],
    'email': ['PERSONID', 'EMAILADDRESS'],
    'maxuser': ['USERID', 'PERSONID', 'STATUS', 'TYPE', 'DEFSITE', 'LOGINID', 'MAXUSERID'],
    'groupuser': ['GROUPUSERID', 'USERID', 'GROUPNAME'],
    'pr_sod_evidence': ['SITEID', 'PRNUM', 'DESCRIPTION', 'TOTALCOST', 'STATUS', 'REQUESTEDBY', 'PERSONID', 'DATA_SUBMISSAO', 'DATA_APROVACAO', 'ROTEADO_2A_INSTANCIA'],
    'pr_self_approval': ['SITEID', 'PRNUM', 'DESCRIPTION', 'TOTALCOST', 'STATUS', 'SOLICITANTE_REAL', 'PERSONID_APROVOU', 'DATA_APROVACAO', 'ROTEADO_2A_INSTANCIA'],
    'pr_po_same_approver': ['SITEID', 'PRNUM', 'DESCRIPTION', 'TOTALCOST', 'STATUS', 'PERSONID', 'DATA_APROVACAO_PR', 'DATA_CRIACAO_PO', 'PONUM_GERADA'],
    'persongroupview': [
        "personid", "status", "displayname", "firstname", "lastname", "department", "title", "employeetype", "jobcode", "supervisor", "birthdate", "lastevaldate", "nextevaldate", "hiredate", "terminationdate", "location", "locationsite", "locationorg", "shiptoaddress", "billtoaddress", "droppoint", "wfmailelection", "transemailelection", "delegate", "delegatefromdate", "delegatetodate", "pcardnum", "pcardtype", "pcardexpdate", "pcardverification", "addressline1", "addressline2", "addressline3", "city", "regiondistrict", "county", "stateprovince", "country", "postalcode", "vip", "statusdate", "acceptingwfmail", "wopriority", "loctoservreq", "personuid", "langcode", "sendersysid", "sourcesysid", "ownersysid", "externalrefid", "language", "locale", "timezone", "hasld", "rowstamp", "resppartygroup", "respparty", "resppartygroupseq", "resppartyseq", "usefororg", "useforsite", "groupdefault", "orgdefault", "sitedefault", "persongroupteamid", "persongroup"
    ]
}

def parse_db2cli_output(path: Path, query: str):
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    
    header = None
    rows = []
    
    if query in HEADERS_MAP:
        header = HEADERS_MAP[query]
        # Pular linhas de cabeçalho (copyright, query, metadados)
        data_started = False
        for line in lines:
            # Pular linhas até encontrar o header CSV_ROW
            if not data_started:
                if 'CSV_ROW' in line or 'Columns:' in line:
                    data_started = True
                continue
            
            # Pular linhas de separação ou vazias
            if line.startswith('-') or 'record(s) selected' in line or not line.strip():
                continue
                
            # Processar dados
            if ',' in line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) > len(header):
                    parts = parts[:len(header)]
                elif len(parts) < len(header):
                    parts += [''] * (len(header) - len(parts))
                rows.append(parts)
        return header, rows
    
    for idx, line in enumerate(lines):
        if 'Columns:' in line or 'Column:' in line or line.startswith('USERID') or line.startswith('PERSONID') or line.startswith('GROUPNAME'):
            if 'Columns:' in line or 'Column:' in line:
                j = idx + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    header = lines[j].strip().split()
            else:
                header = line.strip().split()
                j = idx
                
            if not header:
                break
                
            k = j + 1
            while k < len(lines) and (not lines[k].strip() or lines[k].strip().startswith('-')):
                k += 1
            
            while k < len(lines):
                s = lines[k].strip()
                if "record(s) selected" in s or "Statement executed successfully" in s:
                    break
                    
                if s:
                    if ',' in s:
                        parts = [p.strip() for p in s.split(',')]
                    else:
                        parts = s.split(None, len(header) - 1)

                    if len(parts) > len(header):
                        parts = parts[:len(header)]
                    elif len(parts) < len(header):
                        parts += [''] * (len(header) - len(parts))
                    rows.append(parts)
                k += 1
            break
            
    if not header and len(lines) > 5:
        for i, line in enumerate(lines[:15]):
            if line.strip() and not line.strip().startswith('-----'):
                header = line.strip().split()
                for k in range(i+1, min(i+10, len(lines))):
                    if lines[k].strip().startswith('-----'):
                        for m in range(k+1, len(lines)):
                            s = lines[m].strip()
                            if "record(s) selected" in s or "Statement executed" in s:
                                break
                            if s:
                                if ',' in s:
                                    parts = [p.strip() for p in s.split(',')]
                                else:
                                    parts = s.split(None, len(header) - 1)
                                if len(parts) > len(header):
                                    parts = parts[:len(header)]
                                elif len(parts) < len(header):
                                    parts += [''] * (len(header) - len(parts))
                                rows.append(parts)
                        return header, rows
                        
    return header, rows

def consolidate():
    if not IN_DIR.exists():
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    query_data = defaultdict(list)
    txt_files = sorted(IN_DIR.glob('*_*.txt'))
    failed_extractions = []

    for fpath in txt_files:
        if fpath.name.startswith('validate_'): continue
        parts = fpath.stem.split('_', 1)
        if len(parts) != 2: continue
        env, query = parts

        header, rows = parse_db2cli_output(fpath, query)

        # Extração que falhou (erro de conexão/SQL) deixa um .txt contendo o
        # erro do driver em vez de dados — antes isso virava silenciosamente
        # "0 linhas daquele ambiente" e ambientes inteiros sumiam das
        # análises sem aviso (aconteceu com ODN2, subcontando a auditoria de
        # SoD por semanas). Só marca como podre se NÃO houver dado nenhum:
        # um arquivo com dados + aviso SQL não pode ser descartado.
        if not rows:
            raw_text = fpath.read_text(encoding='utf-8', errors='replace')
            if 'SQL30081N' in raw_text or 'SQLError' in raw_text:
                failed_extractions.append((env, query, fpath.name))
                print(f"!! EXTRACAO PODRE {fpath.name}: erro DB2 sem dados — 0 linhas para {env}/{query}")
                continue

        if not header:
            print(f"SKIP {fpath.name}: no header found")
            continue

        query_data[query].append((env, header, rows))
        print(f"PARSED {fpath.name}: {len(rows)} rows")
    
    for query, env_data in sorted(query_data.items()):
        if not env_data: continue
        header = env_data[0][1]
        all_rows = []
        for env, h, rows in env_data:
            for row in rows:
                all_rows.append([env] + row)
        
        csv_path = OUT_DIR / f'consolidated_{query}.csv'
        try:
            if csv_path.exists():
                csv_path.unlink()
            with csv_path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(['ENVIRONMENT'] + header)
                for row in all_rows:
                    writer.writerow(row)
            print(f"WROTE {csv_path.name}: {len(all_rows)} rows")
        except (PermissionError, OSError):
            from datetime import datetime
            alt_path = OUT_DIR / f'consolidated_{query}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            with alt_path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(['ENVIRONMENT'] + header)
                for row in all_rows:
                    writer.writerow(row)
            print(f"WROTE {alt_path.name}: {len(all_rows)} rows (arquivo original estava aberto)")

    if failed_extractions:
        print("\n" + "!" * 80)
        print(f"ATENCAO: {len(failed_extractions)} extracao(oes) com ERRO DE CONEXAO — dados desses")
        print("ambientes/queries estao FALTANDO nos consolidados. Reprocesse com:")
        for env, query, fname in failed_extractions:
            print(f"  python scripts/run_db2cli_queries.py --only-env {env} --only-query {query}   # {fname}")
        print("!" * 80)

if __name__ == '__main__':
    consolidate()