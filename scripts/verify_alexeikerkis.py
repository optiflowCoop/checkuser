#!/usr/bin/env python3
"""Verifica o LOCAL_SITE do ALEXEIKERKIS em todas as fontes."""
import csv
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent.parent / "output" / "consolidated"

def main():
    user_id = "ALEXEIKERKIS"
    
    print("=" * 70)
    print("VERIFICAÇÃO DO LOCAL_SITE DO ALEXEIKERKIS")
    print("=" * 70)
    
    # 1. Verificar license_decision_plan.csv
    print("\n1. LICENSE_DECISION_PLAN.CSV")
    print("-" * 70)
    try:
        with open(OUTDIR / "license_decision_plan.csv", newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('USERID', '').upper() == user_id:
                    print(f"USERID: {row.get('USERID')}")
                    print(f"LOCATION_SITE: {row.get('LOCATION_SITE', 'VAZIO')}")
                    print(f"DISPLAYNAME: {row.get('DISPLAYNAME')}")
                    print(f"ENTITLEMENT: {row.get('ENTITLEMENT')}")
                    print(f"LICENSE_MODEL: {row.get('LICENSE_MODEL')}")
                    print(f"APP_POINTS: {row.get('APP_POINTS')}")
                    break
    except Exception as e:
        print(f"ERRO: {e}")
    
    # 2. Verificar license_optimization_recommendations.csv
    print("\n2. LICENSE_OPTIMIZATION_RECOMMENDATIONS.CSV")
    print("-" * 70)
    try:
        with open(OUTDIR / "license_optimization_recommendations.csv", newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('USERID', '').upper() == user_id:
                    print(f"USERID: {row.get('USERID')}")
                    print(f"LOCATION_SITE: {row.get('LOCATION_SITE', 'VAZIO')}")
                    print(f"DISPLAYNAME: {row.get('DISPLAYNAME')}")
                    print(f"ENTITLEMENT: {row.get('ENTITLEMENT')}")
                    print(f"LICENSE_MODEL: {row.get('LICENSE_MODEL')}")
                    print(f"APP_POINTS: {row.get('APP_POINTS')}")
                    break
    except Exception as e:
        print(f"ERRO: {e}")
    
    # 3. Verificar usage_analysis_phase3.csv
    print("\n3. USAGE_ANALYSIS_PHASE3.CSV")
    print("-" * 70)
    try:
        with open(OUTDIR / "usage_analysis_phase3.csv", newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('USERID', '').upper() == user_id:
                    print(f"USERID: {row.get('USERID')}")
                    print(f"LOCAL_SITE: {row.get('LOCAL_SITE', 'VAZIO')}")
                    print(f"DISPLAYNAME: {row.get('DISPLAYNAME')}")
                    print(f"AUTH_SCORE: {row.get('AUTH_SCORE')}")
                    print(f"REQUIRED_LICENSE: {row.get('REQUIRED_LICENSE')}")
                    print(f"APP_POINTS_COST: {row.get('APP_POINTS_COST')}")
                    break
    except Exception as e:
        print(f"ERRO: {e}")
    
    # 4. Verificar consolidated_user_identity.csv
    print("\n4. CONSOLIDATED_USER_IDENTITY.CSV")
    print("-" * 70)
    try:
        with open(OUTDIR / "consolidated_user_identity.csv", newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('USERID', '').upper() == user_id:
                    print(f"USERID: {row.get('USERID')}")
                    print(f"ENV_DB: {row.get('ENV_DB', 'VAZIO')}")
                    print(f"DEFSITE: {row.get('DEFSITE', 'VAZIO')}")
                    print(f"DISPLAYNAME: {row.get('DISPLAYNAME')}")
                    break
    except Exception as e:
        print(f"ERRO: {e}")
    
    print("\n" + "=" * 70)
    print("CONCLUSÃO:")
    print("=" * 70)
    print("Se LICENSE_DECISION_PLAN.CSV e LICENSE_OPTIMIZATION_RECOMMENDATIONS.CSV")
    print("mostram ODN2, mas o HTML mostra 0, o problema está na geração do HTML.")
    print("Execute: python scripts/generate_risk_report.py")

if __name__ == '__main__':
    main()