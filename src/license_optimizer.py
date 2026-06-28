import csv
import sys
from pathlib import Path

# --- INÍCIO DO AJUSTE DE IMPORTAÇÃO ---
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# --- FIM DO AJUSTE ---

from src.engine.optimizer import LicenseOptimizerEngine
from src.rules_manager import rules_manager

IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'consolidated'


def load_csv(filename):
    path = IN_DIR / filename
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    print("  Fase 3: DETECTOR DE OTIMIZAÇÃO DE LICENÇAS (SOLID ENGINE)")

    # Busca a capacidade do RulesManager (desacoplado)
    contracted_points = rules_manager.capacity.get('contracted_app_points', 1200)
    print(f"Capacidade contratada: {contracted_points:,} AppPoints\n")

    usage_data = load_csv('usage_analysis_phase3.csv')
    if not usage_data:
        print("X ERRO: usage_analysis_phase3.csv não encontrado. Execute analyze_usage.py primeiro.")
        return

    print(f"V Carregados {len(usage_data)} usuários para análise.")

    # Instancia o motor de inteligência
    engine = LicenseOptimizerEngine()

    optimizations = []
    waste_points = 0
    needed_points = 0

    for user in usage_data:
        user_category = user.get('USER_CATEGORY', 'UNKNOWN')
        cost = int(user.get('APP_POINTS_COST', 0))

        if user_category == 'FORESEA':
            needed_points += cost

        # O processamento pesado de ifs/elifs sumiu! O Engine resolve tudo.
        decision = engine.process_user(user)

        waste_points += decision['savings']

        optimizations.append({
            'USERID': user.get('USERID', ''),
            'DISPLAYNAME': user.get('DISPLAYNAME', ''),
            'EMAIL': user.get('EMAIL', ''),
            'USER_CATEGORY': user_category,
            'TITLE': user.get('TITLE', ''),
            'LOCATION_SITE': user.get('LOCATION', 'UNKNOWN'),  # CORREÇÃO: Usar 'LOCATION' em vez de 'OPERATIONAL_PRESENCE'
            'CURRENT_TIER': user.get('USER_TIER', ''),
            'LOGIN_COUNT_90D': user.get('LOGIN_COUNT_90D', 0),
            'REQUIRED_LICENSE': user.get('REQUIRED_LICENSE', ''),
            'APP_POINTS_COST': cost,
            'PREMIUM_APPS_USED': user.get('PREMIUM_APPS', ''),
            'OPTIMIZATION_TYPE': decision['type'],
            'RECOMMENDATION': decision['recommendation'],
            'POTENTIAL_SAVINGS': decision['savings']
        })

    # Ordenar por potencial de economia (maior economia primeiro)
    optimizations.sort(key=lambda x: x['POTENTIAL_SAVINGS'], reverse=True)

    # Salvar relatório "Mastigado" para o Front/Dashboards
    out_path = OUT_DIR / 'license_optimization_recommendations.csv'
    if optimizations:
        # Garante que todas as chaves sejam incluídas no cabeçalho
        fieldnames = list(optimizations[0].keys())
        with out_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(optimizations)

        print(f"✅ RELATÓRIO GERADO: {out_path.name} ({len(optimizations)} recomendações)")
        print(f"📊 Economia Potencial Identificada: {int(waste_points)} AppPoints!")
    else:
        print("⚠️ Nenhuma recomendação gerada.")


if __name__ == '__main__':
    main()