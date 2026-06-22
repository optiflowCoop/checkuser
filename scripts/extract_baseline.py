#!/usr/bin/env python3
"""
Extração Pontual: Baseline Funcional

Script para atualizar apenas dados de perfil (PERSONGROUPVIEW)
para análise de baseline sem necessidade de extração completa.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"

# Queries relacionadas ao baseline funcional
BASELINE_QUERIES = [
    "persongroupview",
    "persongroup",
    "persongroupteam"
]

def main():
    print("=" * 70)
    print("🎯 EXTRAÇÃO PONTUAL: Baseline Funcional (Perfis de Acesso)")
    print("=" * 70)
    print("\nExtraindo dados de perfil de todas as bases...")
    print("⏳ Este processo pode levar alguns minutos...\n")
    
    # Executar queries de baseline
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_db2cli_queries.py"),
        "--queries", ",".join(BASELINE_QUERIES)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, text=True)
        print("\n✅ Baseline Funcional extraído com sucesso!")
        print("\n📋 Próximos passos:")
        print("   1. Execute: python run_pipeline.py --skip-extract")
        print("   2. Abra dashboard HTML para ver divergências atualizadas")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERRO na extração: código {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ ERRO: Script run_db2cli_queries.py não encontrado")
        sys.exit(1)

if __name__ == '__main__':
    main()
