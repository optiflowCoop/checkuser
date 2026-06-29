#!/usr/bin/env python3
"""
Maximo Identity Sanity - Pipeline Executor (VERSAO COM SOLID REFACTORING)

Runs all scripts in the correct order to extract, consolidate, 
classify identities, and generate the final risk reports.

MUDANCAS:
✓ Usa analyze_usage.py (com UserClassificationEngine + SOLID)
✓ Usa license_optimizer.py (com LicenseOptimizer + SOLID)
✓ Logs MUITO detalhados em cada fase
✓ 100% dados REAIS (não mocks/random)
✓ Suporta --skip-extract para re-run rápido
"""
import subprocess
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent

PIPELINE_STEPS = [
    {
        "name": "1. Extraindo Dados do DB2 (run_db2cli_queries.py)",
        "cmd": [sys.executable, str(ROOT / "scripts" / "run_db2cli_queries.py")],
        "skippable": True
    },
    {
        "name": "2. Consolidando Textos Brutos (consolidate_outputs.py)",
        "cmd": [sys.executable, str(ROOT / "scripts" / "consolidate_outputs.py")],
        "skippable": True
    },
    {
        "name": "3. Montando Base de Acessos (consolidate_user_access.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "consolidate_user_access.py")],
        "skippable": False
    },
    {
        "name": "4. Normalizando e Tipificando Contas (normalize.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "normalize.py")],
        "skippable": False
    },
    {
        "name": "5. Detectando Reuso de USERID (cross_env_userid_reuse.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "cross_env_userid_reuse.py")],
        "skippable": False
    },
    {
        "name": "6. Detectando Conflitos de Login (login_conflicts.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "login_conflicts.py")],
        "skippable": False
    },
    {
        "name": "7. Classificando Identidades e Worklist (identity_classification.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "identity_classification.py")],
        "skippable": False
    },
    {
        "name": "8. Consolidando Licenças (consolidate_license_footprint.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "consolidate_license_footprint.py")],
        "skippable": False
    },
    {
        "name": "9. [FASE 3] Analisando Histórico de Uso - SOLID (analyze_usage.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "analyze_usage.py")],
        "skippable": False,
        "features": "✓ Dados REAIS (não mocks) ✓ UserClassificationEngine (SOLID) ✓ 6 rules independentes"
    },
    {
        "name": "10. [FASE 3-B] Detector de Otimização - SOLID (license_optimizer.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "license_optimizer.py")],
        "skippable": False,
        "features": "✓ LicenseOptimizer (SOLID) ✓ 6 estratégias ✓ Batch processing ✓ Summary stats"
    },
    {
        "name": "11. Gerando Uso Real (true_capacity_calculator.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "true_capacity_calculator.py")],
        "skippable": False
    },
    {
        "name": "12. Gerando Dashboards e Excel de Risco (generate_risk_report.py)",
        "cmd": [sys.executable, str(ROOT / "scripts" / "generate_risk_report.py")],
        "skippable": False
    }
]


def main():
    print("\n" + "=" * 100)
    print("🚀 MAXIMO IDENTITY SANITY PIPELINE - COM REFACTORING SOLID")
    print("=" * 100)
    print("\nVersão: 1.0 SOLID (com UserClassificationEngine + LicenseOptimizer)")
    print("Dados: 100% REAIS de consolidated_logintracking.csv (nenhum mock, nenhum random)")
    print("Padrões: Strategy Pattern + SOLID Principles")
    
    # Parse arguments
    skip_extract = '--skip-extract' in sys.argv
    skip_steps = []
    if skip_extract:
        print("\nModo: --skip-extract (pulando extração do DB2)")
        skip_steps = [0, 1]  # Skip steps 1 and 2 (extraction)
    
    start_time = time.time()
    step_times = []
    
    for idx, step in enumerate(PIPELINE_STEPS):
        if idx in skip_steps:
            print(f"\n  ⏩ Pulando: {step['name']}")
            continue

        step_name = step['name']
        features = step.get('features', '')
        
        print(f"\n{'=' * 100}")
        print(f"[PASSO {idx + 1}] {step_name}")
        if features:
            print(f"        {features}")
        print(f"{'=' * 100}")
        
        step_start = time.time()
        
        try:
            result = subprocess.run(step['cmd'], check=True, text=True, capture_output=False)
        except subprocess.CalledProcessError as e:
            print(f"\n{'✗' * 50}")
            print(f"❌ ERRO CRÍTICO no passo: {step_name}")
            print(f"   Processo abortado com código de saída: {e.returncode}")
            print(f"{'✗' * 50}\n")
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"\n{'✗' * 50}")
            print(f"❌ ARQUIVO NÃO ENCONTRADO no passo: {step_name}")
            print(str(e))
            print(f"{'✗' * 50}\n")
            sys.exit(1)
        
        step_duration = time.time() - step_start
        step_times.append((step_name, step_duration))
        print(f"\n  ✓ Passo concluído em {step_duration:.2f}s")
    
    # Relatório final
    total_time = time.time() - start_time
    
    print("\n" + "=" * 100)
    print("✅ PIPELINE CONCLUÍDO COM SUCESSO!")
    print("=" * 100)
    
    print(f"\n[TEMPO TOTAL]")
    print(f"  {total_time:.2f}s ({total_time/60:.2f} minutos)")
    
    print(f"\n[TEMPO POR PASSO]")
    for step_name, duration in step_times:
        print(f"  • {duration:>6.2f}s - {step_name}")
    
    print(f"\n[ARQUIVOS GERADOS]")
    print(f"  📄 output/consolidated/")
    print(f"     • consolidated_user_identity.csv")
    print(f"     • consolidated_user_access_normalized.csv")
    print(f"     • consolidated_logintracking.csv (dados REAIS)")
    print(f"     • usage_analysis_phase3.csv (com UserClassificationEngine)")
    print(f"     • license_optimization_recommendations.csv (com LicenseOptimizer)")
    print(f"  📊 output/reports/")
    print(f"     • maximo_identity_sanity_report.html (dashboard)")
    print(f"     • maximo_identity_sanity_workbook.xlsx (excel)")
    
    print(f"\n[FEATURES SOLID APLICADAS]")
    print(f"  ✓ Strategy Pattern (ClassificationRule, OptimizationStrategy)")
    print(f"  ✓ Facade Pattern (UserClassificationEngine, LicenseOptimizer)")
    print(f"  ✓ Single Responsibility Principle")
    print(f"  ✓ Open/Closed Principle (extensível sem modificar core)")
    print(f"  ✓ Liskov Substitution Principle")
    print(f"  ✓ Interface Segregation Principle")
    print(f"  ✓ Dependency Inversion Principle")
    
    print(f"\n[PROXIMOS PASSOS]")
    print(f"  1. Revisar arquivo: output/consolidated/usage_analysis_phase3.csv")
    print(f"  2. Revisar arquivo: output/consolidated/license_optimization_recommendations.csv")
    print(f"  3. Abrir dashboard em: output/reports/maximo_identity_sanity_report.html")
    print(f"  4. Abrir workbook em: output/reports/maximo_identity_sanity_workbook.xlsx")
    
    print(f"\n[PROXIMA EXECUCAO RAPIDA]")
    print(f"  $ python run_pipeline_new.py --skip-extract")
    print(f"  (Pula extração DB2 e roda apenas análise + otimização)")
    
    print(f"\n{'=' * 100}\n")


if __name__ == "__main__":
    main()