# scripts/extract_indicadores.py
# Script para extrair indicadores mensais dos dados reais do MAXIMO via DB2CLI

import csv
from pathlib import Path
from collections import defaultdict
import sys

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / 'output' / 'raw'
CONSOLIDATED_DIR = ROOT / 'output' / 'consolidated'

# Mapeamento de SITEID para unidade
SITEID_TO_UNIDADE = {
    "ODN1": "ODN1",
    "ODN2": "ODN2", 
    "N06": "N06",
    "N08": "N08",
    "N09": "N09",
    "HTQ": "HTQ",
    "POL": "POL",
    "PGA": "PGA",
    "PGB": "PGB",
    "PGC": "PGC",
    "BASE": "BASE"
}

def _parse_line(line):
    """Parse uma linha do DB2CLI - formato: SITEID, TOTAL, ANO, MES"""
    line = line.strip()
    # Pula cabeçalhos e linhas vazias
    if not line or 'SITEID' in line or 'FetchAll' in line or 'IBM Db2' in line or 'SELECT' in line or '>' in line or 'Columns:' in line or 'All Rights' in line or '(C) COPYRIGHT' in line:
        return None
    
    try:
        parts = line.split(',')
        if len(parts) >= 4:
            siteid = parts[0].strip()
            total = int(parts[1].strip())
            ano = parts[2].strip()
            mes = int(parts[3].strip())
            return siteid, total, ano, mes
    except (ValueError, IndexError):
        pass
    return None

def extract_indicadores():
    """Extrai indicadores dos arquivos raw gerados pelo DB2CLI"""
    
    # Estrutura: {ano: {tipo: {unidade: {mes: total}}}}
    indicadores = {
        'work_orders': defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
        'moc': defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
        'ptw': defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
        'loto': defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    }
    
    # Processa cada ambiente
    for env in ['BASE', 'ODN1', 'ODN2', 'N06', 'N08', 'N09', 'HTQ']:
        # Work Orders
        wo_file = RAW_DIR / f'{env}_workorder_indicadores.txt'
        if wo_file.exists():
            print(f"📂 Processando: {wo_file.name}")
            with open(wo_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parsed = _parse_line(line)
                    if parsed:
                        siteid, total, ano, mes = parsed
                        unidade = SITEID_TO_UNIDADE.get(siteid, siteid)
                        indicadores['work_orders'][ano][unidade][mes] += total
        
        # MOC
        moc_file = RAW_DIR / f'{env}_moc_indicadores.txt'
        if moc_file.exists():
            print(f"📂 Processando: {moc_file.name}")
            with open(moc_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parsed = _parse_line(line)
                    if parsed:
                        siteid, total, ano, mes = parsed
                        unidade = SITEID_TO_UNIDADE.get(siteid, siteid)
                        indicadores['moc'][ano][unidade][mes] += total
        
        # PTWs
        ptw_file = RAW_DIR / f'{env}_ptw_indicadores.txt'
        if ptw_file.exists():
            print(f"📂 Processando: {ptw_file.name}")
            with open(ptw_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parsed = _parse_line(line)
                    if parsed:
                        siteid, total, ano, mes = parsed
                        unidade = SITEID_TO_UNIDADE.get(siteid, siteid)
                        indicadores['ptw'][ano][unidade][mes] += total
        
        # LOTO
        loto_file = RAW_DIR / f'{env}_loto_indicadores.txt'
        if loto_file.exists():
            print(f"📂 Processando: {loto_file.name}")
            with open(loto_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parsed = _parse_line(line)
                    if parsed:
                        siteid, total, ano, mes = parsed
                        unidade = SITEID_TO_UNIDADE.get(siteid, siteid)
                        indicadores['loto'][ano][unidade][mes] += total
    
    # Gera arquivos consolidados
    for tipo in ['workorder', 'moc', 'ptw', 'loto']:
        output_file = CONSOLIDATED_DIR / f'consolidated_{tipo}_indicadores.csv'
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['SITEID', 'ANO', 'MES', 'TOTAL'])
            
            tipo_key = 'work_orders' if tipo == 'workorder' else tipo
            
            for ano in sorted(indicadores[tipo_key].keys()):
                for unidade in sorted(indicadores[tipo_key][ano].keys()):
                    for mes in sorted(indicadores[tipo_key][ano][unidade].keys()):
                        total = indicadores[tipo_key][ano][unidade][mes]
                        writer.writerow([unidade, ano, mes, total])
        
        print(f"✅ Gerado: {output_file.name}")
    
    return indicadores

if __name__ == '__main__':
    print("=" * 60)
    print("EXTRAINDO INDICADORES MAXIMO - DADOS REAIS DO DB2")
    print("=" * 60)
    
    indicadores = extract_indicadores()
    
    print("\n" + "=" * 60)
    print("RESUMO DOS INDICADORES")
    print("=" * 60)
    
    for tipo in ['work_orders', 'moc', 'ptw', 'loto']:
        print(f"\n{tipo}:")
        for ano in sorted(indicadores[tipo].keys()):
            total_ano = sum(indicadores[tipo][ano][u][m] 
                         for u in indicadores[tipo][ano] 
                         for m in indicadores[tipo][ano][u])
            print(f"  Ano {ano}: {total_ano} registros")
    
    print("\n✅ Concluído!")