import os
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
        "name": "6. Detectando Reuso de USERID (cross_env_userid_reuse.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "cross_env_userid_reuse.py")]
    },
    {
        "name": "7. Detectando Conflitos de Login (login_conflicts.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "login_conflicts.py")]
    },
    {
        "name": "8. Classificando Identidades e Worklist (identity_classification.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "identity_classification.py")]
    },
    {
        "name": "9. Consolidando Licenças (consolidate_license_footprint.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "consolidate_license_footprint.py")]
    },
    {
        "name": "10. [FASE 3] Analisando Histórico de Uso (analyze_usage.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "analyze_usage.py")]
    },
    {
        "name": "11. [FASE 3] Detector de Otimização (license_optimizer.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "license_optimizer.py")]
    },
    {
        "name": "12. Gerando Relatório Final (Dashboard HTML e Workbook Excel)",
        "cmd": [sys.executable, str(ROOT / "scripts" / "generate_risk_report.py")]
    }
]


def main():
    print("=" * 60)
    print("🚀 Iniciando Pipeline: Maximo Identity Sanity & MAS 9")
    print("=" * 60)

    skip_extract = '--skip-extract' in sys.argv
    start_time = time.time()

    # Copia o ambiente atual e define PYTHONIOENCODING para UTF-8
    # Isso força os subprocessos Python a usarem UTF-8 para sua saída
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    for idx, step in enumerate(PIPELINE_STEPS):
        original_step_number = int(step['name'].split('.')[0])
        if original_step_number == 1 and skip_extract:
            print(f"\n⏩ Pulando: {step['name']} (--skip-extract passado)")
            continue

        print(f"\n{'=' * 60}")
        print(f"⏳ Executando: {step['name']}")
        print(f"{'-' * 60}")

        step_start_time = time.time()
        try:
            result = subprocess.run(
                step['cmd'],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='replace',
                env=env  # Passa o ambiente modificado para o subprocesso
            )

            if result.stdout:
                print(f"\n--- SAÍDA PADRÃO ({step['name']}) ---")
                print(result.stdout.strip())

            if result.stderr:
                print(f"\n--- ERROS/AVISOS ({step['name']}) ---")
                print(result.stderr.strip())

            step_end_time = time.time()
            print(f"\n✅ Concluído: {step['name']} (Tempo: {step_end_time - step_start_time:.2f}s)")

        except subprocess.CalledProcessError as e:
            print(f"\n--- SAÍDA PADRÃO (ERRO em {step['name']}) ---")
            print(e.stdout.strip() if e.stdout else "Nenhuma saída padrão.")
            print(f"\n--- ERROS/AVISOS (ERRO em {step['name']}) ---")
            print(e.stderr.strip() if e.stderr else "Nenhum erro/aviso capturado.")
            print(f"\n❌ ERRO CRÍTICO no passo: {step['name']}")
            print(f"Processo abortado com código de saída: {e.returncode}")
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"\n❌ ARQUIVO NÃO ENCONTRADO no passo: {step['name']}")
            print(str(e))
            sys.exit(1)

    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"✅ PIPELINE CONCLUÍDO COM SUCESSO! (Tempo total: {total_time:.2f}s)")
    print("=" * 60)
    print("📄 Relatórios gerados em: output/reports/")
    print("   - maximo_unified_dashboard.html")
    print("   - maximo_risk_and_optimization_workbook.xlsx")


if __name__ == "__main__":
    main()