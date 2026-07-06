#!/usr/bin/env python3
"""Debug do ALEXEIKERKIS para entender por que está saindo 0."""
import csv
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent.parent / "output" / "consolidated"

def main():
    user_id = "ALEXEIKERKIS"
    
    # Verificar usage_analysis_phase3.csv
    print("=" * 70)
    print("USAGE_ANALYSIS_PHASE3.CSV")
    print("=" * 70)
    with open(OUTDIR / "usage_analysis_phase3.csv", newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('USERID', '').upper() == user_id:
                print(f"USERID: {row.get('USERID')}")
                print(f"LOCAL_SITE: {row.get('LOCAL_SITE')}")
                print(f"DEFSITE: {row.get('DEFSITE', 'N/A')}")
                print(f"LOGIN_COUNT_90D: {row.get('LOGIN_COUNT_90D')}")
                print("---")
    
    # Verificar license_optimization_recommendations.csv
    print("\n" + "=" * 70)
    print("LICENSE_OPTIMIZATION_RECOMMENDATIONS.CSV")
    print("=" * 70)
    with open(OUTDIR / "license_optimization_recommendations.csv", newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('USERID', '').upper() == user_id:
                print(f"USERID: {row.get('USERID')}")
                print(f"LOCATION_SITE: {row.get('LOCATION_SITE')}")
                print(f"REQUIRED_LICENSE: {row.get('REQUIRED_LICENSE')}")
                print(f"APP_POINTS_COST: {row.get('APP_POINTS_COST')}")
                print("---")
    
    # Verificar consolidated_user_identity.csv
    print("\n" + "=" * 70)
    print("CONSOLIDATED_USER_IDENTITY.CSV")
    print("=" * 70)
    with open(OUTDIR / "consolidated_user_identity.csv", newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('USERID', '').upper() == user_id:
                print(f"USERID: {row.get('USERID')}")
                print(f"ENV_DB: {row.get('ENV_DB')}")
                print(f"DEFSITE: {row.get('DEFSITE')}")
                print("---")

if __name__ == '__main__':
    main()
</parameter>
<task_progress>
- [x] Analisar estrutura dos arquivos de logintracking
- [x] Entender como cruzar persongroupview x logintrack
- [x] Criar script de cruzamento persongroupview x logintrack
- [x] Executar e validar resultados
- [x] Modificar analyze_usage.py para incluir LOCAL_SITE
- [x] Verificar impacto no cálculo de appoints
- [x] Incluir lógica de inferência baseada em CLIENTHOST
- [x] Criar lógica inteligente baseada em frequência de login
- [x] Ajustar lógica para servidor compartilhado
- [x] Adicionar queries de indicadores ajustadas
- [x] Consolidar scripts em único fluxo
- [x] Ajustar lógica para IPs (não inferir ambiente)
- [x] Modificar analyze_usage.py para usar inferência de ambiente
- [x] Modificar license_optimizer.py para usar LOCAL_SITE
- [x] Modificar generate_risk_report.py para usar ambiente real
- [x] Ajustar fallback para DEFSITE
- [x] Corrigir prioridade defsite vs environment
- [x] Adicionar mapeamento de IPs dos servidores Maximo
- [x] Debug ALEXEIKERKIS - unidade 0
</parameter>
</write_to_file>