#!/usr/bin/env python3
"""
Maximo Identity Sanity - Pipeline Executor

Runs all scripts in the correct order to extract, consolidate, 
classify identities, and generate the final risk reports.
"""
import subprocess
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent

PIPELINE_STEPS = [
    {
        "name": "1. Extraindo Dados do DB2 (run_db2cli_queries.py)",
        "cmd": [sys.executable, str(ROOT / "scripts" / "run_db2cli_queries.py")]
    },
    {
        "name": "2. Consolidando Textos Brutos (consolidate_outputs.py)",
        "cmd": [sys.executable, str(ROOT / "scripts" / "consolidate_outputs.py")]
    },
    {
        "name": "3. Montando Base de Acessos (consolidate_user_access.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "consolidate_user_access.py")]
    },
    {
        "name": "4. Normalizando e Tipificando Contas (normalize.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "normalize.py")]
    },
    {
        "name": "5. Detectando Reuso de USERID (cross_env_userid_reuse.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "cross_env_userid_reuse.py")]
    },
    {
        "name": "6. Detectando Conflitos de Login (login_conflicts.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "login_conflicts.py")]
    },
    {
        "name": "7. Classificando Identidades e Worklist (identity_classification.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "identity_classification.py")]
    },
    {
        "name": "8. Consolidando Licenças (consolidate_license_footprint.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "consolidate_license_footprint.py")]
    },
    {
        "name": "9. [FASE 3] Analisando Histórico de Uso (analyze_usage.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "analyze_usage.py")]
    },
    {
        "name": "10. [FASE 3] Detector de Otimização (license_optimizer.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "license_optimizer.py")]
    },
    {
        "name": "11. Gerando Dashboards e Excel de Risco (generate_risk_report.py)",
        "cmd": [sys.executable, str(ROOT / "scripts" / "generate_risk_report.py")]
    }
]

def main():
    print("=" * 60)
    print("🚀 Iniciando Pipeline: Maximo Identity Sanity & MAS 9")
    print("=" * 60)
    
    # Allows skipping extraction if you pass --skip-extract
    skip_extract = '--skip-extract' in sys.argv
    start_time = time.time()
    
    for idx, step in enumerate(PIPELINE_STEPS):
        if idx == 0 and skip_extract:
            print(f"\n⏩ Pulando: {step['name']} (--skip-extract passado)")
            continue

        print(f"\n⏳ Executando: {step['name']}")
        try:
            result = subprocess.run(step['cmd'], check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ ERRO CRÍTICO no passo: {step['name']}")
            print(f"Processo abortado com código de saída: {e.returncode}")
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"❌ ARQUIVO NÃO ENCONTRADO no passo: {step['name']}")
            print(str(e))
            sys.exit(1)
            
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"✅ PIPELINE CONCLUÍDO COM SUCESSO! (Tempo total: {total_time:.2f}s)")
    print("=" * 60)
    print("📄 Relatórios gerados em: output/reports/")
    print("   - maximo_identity_sanity_report.html")
    print("   - maximo_identity_sanity_workbook.xlsx")

if __name__ == "__main__":
    main()