#!/usr/bin/env python3
"""
Extração Pontual: LOGINTRACKING

Script para atualizar apenas dados de uso (últimos 90 dias)
sem necessidade de extrair toda a base novamente.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"

# Query apenas do LOGINTRACKING
QUERY_NAME = "logintracking"

def main():
    print("=" * 70)
    print("🔄 EXTRAÇÃO PONTUAL: Histórico de Uso (LOGINTRACKING)")
    print("=" * 70)
    print("\nExtraindo dados dos últimos 90 dias de todas as bases...")
    print("⏳ Este processo pode levar alguns minutos...\n")
    
    # Executar apenas query de logintracking
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_db2cli_queries.py"),
        "--queries", QUERY_NAME
    ]
    
    try:
        result = subprocess.run(cmd, check=True, text=True)
        print("\n✅ LOGINTRACKING extraído com sucesso!")
        print("\n📋 Próximos passos:")
        print("   1. Execute: python run_pipeline.py --skip-extract")
        print("   2. Revise: output/consolidated/usage_analysis_phase3.csv")
        print("   3. Abra: output/reports/maximo_identity_sanity_report.html")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERRO na extração: código {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ ERRO: Script run_db2cli_queries.py não encontrado")
        sys.exit(1)

if __name__ == '__main__':
    main()
