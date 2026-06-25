import os
import subprocess
import sys
from pathlib import Path
import time
import logging
from datetime import datetime

ROOT = Path(__file__).resolve().parent

# =========================================================================
# 🛠️ CONFIGURAÇÃO DE LOGGING
# =========================================================================
LOG_DIR = ROOT / "output" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"pipeline_exec_{current_time_str}.log"

# Configura o log para sair no console e salvar no arquivo simultaneamente
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# =========================================================================
# 🚀 DEFINIÇÃO DAS ETAPAS DO PIPELINE
# =========================================================================
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
        "name": "12. [FASE 4] Cálculo Real de AppPoints (true_capacity_calculator.py)",
        "cmd": [sys.executable, str(ROOT / "src" / "true_capacity_calculator.py")]
    },
    {
        "name": "13. Gerando Relatório Final (Dashboard HTML e Workbook Excel)",
        "cmd": [sys.executable, str(ROOT / "scripts" / "generate_risk_report.py")]
    }
]


def main():
    logger.info("=" * 70)
    logger.info("🚀 Iniciando Pipeline: Maximo Identity Sanity & MAS 9")
    logger.info("=" * 70)
    logger.info(f"📁 Arquivo de log gerado em: {LOG_FILE}")

    skip_extract = '--skip-extract' in sys.argv
    start_time = time.time()

    # Rastreamento de métricas para resumo final
    execution_metrics = []

    # Copia o ambiente atual e define PYTHONIOENCODING para UTF-8
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    for step in PIPELINE_STEPS:
        original_step_number = int(step['name'].split('.')[0])

        if original_step_number == 1 and skip_extract:
            logger.info(f"⏩ Pulando: {step['name']} (--skip-extract passado)")
            execution_metrics.append((step['name'], 0.0, "SKIPPED"))
            continue

        logger.info(f"\n{'-' * 70}")
        logger.info(f"⏳ Executando: {step['name']}")
        logger.info(f"{'-' * 70}")

        step_start_time = time.time()
        try:
            result = subprocess.run(
                step['cmd'],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )

            # Injeta a saída padrão no log de forma limpa
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    logger.info(f"   [STDOUT] {line}")

            if result.stderr.strip():
                for line in result.stderr.strip().split('\n'):
                    logger.warning(f"   [STDERR] {line}")

            step_duration = time.time() - step_start_time
            logger.info(f"✅ Concluído: {step['name']} (Tempo: {step_duration:.2f}s)")
            execution_metrics.append((step['name'], step_duration, "SUCCESS"))

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ ERRO CRÍTICO no passo: {step['name']}")

            if e.stdout:
                logger.error("--- ÚLTIMA SAÍDA ANTES DO ERRO ---")
                for line in e.stdout.strip().split('\n'):
                    logger.error(f"   [STDOUT] {line}")

            if e.stderr:
                logger.error("--- DETALHES DO ERRO ---")
                for line in e.stderr.strip().split('\n'):
                    logger.error(f"   [STDERR] {line}")

            logger.error(f"Processo abortado com código de saída: {e.returncode}")
            execution_metrics.append((step['name'], time.time() - step_start_time, "FAILED"))
            sys.exit(1)

        except FileNotFoundError as e:
            logger.error(f"❌ ARQUIVO NÃO ENCONTRADO no passo: {step['name']}")
            logger.error(str(e))
            execution_metrics.append((step['name'], time.time() - step_start_time, "FAILED"))
            sys.exit(1)

    total_time = time.time() - start_time

    # =========================================================================
    # 📊 QUADRO DE RESUMO FINAL
    # =========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMO DE EXECUÇÃO DO PIPELINE (MÉTRICAS)")
    logger.info("=" * 70)
    for step_name, duration, status in execution_metrics:
        status_icon = "✅" if status == "SUCCESS" else "⏩" if status == "SKIPPED" else "❌"
        logger.info(f"{status_icon} [{duration:06.2f}s] - {step_name}")

    logger.info("=" * 70)
    logger.info(f"🏆 PIPELINE CONCLUÍDO COM SUCESSO! (Tempo total: {total_time:.2f}s)")
    logger.info("=" * 70)
    logger.info("📄 Relatórios gerados em: output/reports/")
    logger.info("   - maximo_unified_dashboard.html")
    logger.info("   - maximo_risk_and_optimization_workbook.xlsx")
    logger.info("   - true_capacity_metrics.json")
    logger.info(f"📝 Log salvo em: {LOG_FILE}")


if __name__ == "__main__":
    main()