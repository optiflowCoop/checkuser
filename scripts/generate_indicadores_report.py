#!/usr/bin/env python3
# scripts/generate_indicadores_report.py
# Script dedicado para geração do relatório de indicadores mensais

import sys
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=" * 60)
    print("📊 GERADOR DE RELATÓRIO DE INDICADORES MAXIMO")
    print("=" * 60)
    
    # Parse argumentos
    ano = "2026"
    mes_inicio = 1
    mes_fim = 6
    
    if '--ano' in sys.argv:
        try:
            idx = sys.argv.index('--ano') + 1
            if idx < len(sys.argv):
                ano = sys.argv[idx]
        except:
            pass
    
    if '--mes-inicio' in sys.argv:
        try:
            idx = sys.argv.index('--mes-inicio') + 1
            if idx < len(sys.argv):
                mes_inicio = int(sys.argv[idx])
        except:
            pass
    
    if '--mes-fim' in sys.argv:
        try:
            idx = sys.argv.index('--mes-fim') + 1
            if idx < len(sys.argv):
                mes_fim = int(sys.argv[idx])
        except:
            pass
    
    # Calcula datas
    data_inicio = f"{ano}-01-01 00:00:00"
    data_fim = f"{ano}-12-31 23:59:59"
    
    if mes_fim < 12:
        # Calcula último dia do mês
        if mes_fim in [1,3,5,7,8,10,12]:
            data_fim = f"{ano}-{mes_fim:02d}-31 23:59:59"
        elif mes_fim in [4,6,9,11]:
            data_fim = f"{ano}-{mes_fim:02d}-30 23:59:59"
        else:
            data_fim = f"{ano}-{mes_fim:02d}-28 23:59:59"
    
    if mes_inicio > 1:
        data_inicio = f"{ano}-{mes_inicio:02d}-01 00:00:00"
    
    print(f"\n📅 Período: {data_inicio} a {data_fim}")
    
    # Passo 1: Executar queries no DB2
    print("\n[1/2] Extraindo dados do DB2...")
    cmd = [
        sys.executable, str(ROOT / 'scripts' / 'run_db2cli_queries.py'),
        '--queries', 'workorder_indicadores,moc_indicadores,ptw_indicadores,loto_indicadores',
        '--data-inicio', data_inicio,
        '--data-fim', data_fim
    ]
    subprocess.run(cmd, check=True)
    
    # Passo 2: Processar dados
    print("\n[2/2] Processando dados...")
    cmd = [sys.executable, str(ROOT / 'scripts' / 'extract_indicadores.py')]
    subprocess.run(cmd, check=True)
    
    # Passo 3: Gerar relatório
    print("\n[3/3] Gerando relatório HTML...")
    cmd = [sys.executable, str(ROOT / 'scripts' / 'generate_risk_report.py')]
    subprocess.run(cmd, check=True)
    
    print("\n" + "=" * 60)
    print("✅ Relatório gerado com sucesso!")
    print(f"📄 Arquivo: {ROOT / 'output' / 'reports' / 'maximo_unified_dashboard.html'}")
    print("=" * 60)

if __name__ == '__main__':
    main()