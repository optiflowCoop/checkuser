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
        for line in lines:
            if 'CSV_ROW' in line or line.startswith('-') or 'record(s) selected' in line or not line.strip():
                continue
                
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
    
    for fpath in txt_files:
        if fpath.name.startswith('validate_'): continue
        parts = fpath.stem.split('_', 1)
        if len(parts) != 2: continue
        env, query = parts
        
        header, rows = parse_db2cli_output(fpath, query)
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
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ENVIRONMENT'] + header)
            for row in all_rows:
                writer.writerow(row)
        print(f"WROTE {csv_path.name}: {len(all_rows)} rows")

if __name__ == '__main__':
    consolidate()