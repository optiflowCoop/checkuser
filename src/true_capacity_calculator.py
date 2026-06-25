#!/usr/bin/env python3
"""
Fase 4: Cálculo Real de AppPoints (Data Science)
1. Deduplicação Global: Transforma IDs em 'Pessoas Únicas' baseadas no EMAIL.
2. Separação de Pools: Authorized (Custo Fixo) vs Concurrent (Custo de Pico).
"""
import csv
import sys
import json
from pathlib import Path
from collections import defaultdict

# Configuração de caminhos
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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
    print("📊 Fase 4: CÁLCULO DE CAPACIDADE REAL (Golden Record & High-Water Mark)")

    optimizations = load_csv('license_optimization_recommendations.csv')
    if not optimizations:
        print("❌ ERRO: license_optimization_recommendations.csv não encontrado.")
        return

    # ---------------------------------------------------------
    # 1. DEDUPLICAÇÃO DE IDENTIDADES (O Golden Record)
    # Regra IBM: Uma pessoa (Email) paga apenas pela sua licença mais cara,
    # independentemente de quantos ambientes (N06, ODN1, etc.) ela acesse.
    # ---------------------------------------------------------
    golden_records = {}

    for row in optimizations:
        email = row.get('EMAIL', '').strip().lower()
        if not email or email == 'none':
            # Fallback para USERID se o email estiver vazio
            email = row.get('USERID', 'UNKNOWN')

        cost = int(row.get('APP_POINTS_COST', 0))
        rec_type = row.get('RECOMMENDATION', '')
        req_lic = row.get('REQUIRED_LICENSE', '')

        # Ignorar usuários recomendados para desativação
        if 'DESATIVAR' in rec_type or 'NÃO MIGRAR' in rec_type:
            continue

        # Se o usuário já existe no nosso registro global, mantemos a licença MAIS CARA dele.
        if email not in golden_records:
            golden_records[email] = {
                'email': email,
                'max_cost': cost,
                'license_type': req_lic
            }
        else:
            if cost > golden_records[email]['max_cost']:
                golden_records[email]['max_cost'] = cost
                golden_records[email]['license_type'] = req_lic

    print(f"✓ Deduplicação: De {len(optimizations)} acessos para {len(golden_records)} pessoas reais.")

    # ---------------------------------------------------------
    # 2. SEPARAÇÃO DE POOLS (Authorized vs Concurrent)
    # ---------------------------------------------------------
    authorized_cost = 0
    concurrent_pool = []

    for email, data in golden_records.items():
        lic_type = data['license_type']
        cost = data['max_cost']

        # Authorized é dedicado, sempre cobra 100% do valor.
        if 'AUTHORIZED' in lic_type:
            authorized_cost += cost
        # Concurrent vai para o pool de disputa.
        elif 'CONCURRENT' in lic_type:
            concurrent_pool.append(cost)

    # O Custo Base do Concurrent Pool (Soma Simples, apenas para efeito de comparação)
    raw_concurrent_cost = sum(concurrent_pool)

    # ---------------------------------------------------------
    # 3. CÁLCULO DO HIGH-WATER MARK (Simultaneidade Estimada)
    # Como não temos o histórico minuto a minuto extraído de todas as sondas agora,
    # aplicamos a heurística de Turno (Offshore) / Ociosidade padrão do mercado O&G:
    # Apenas ~35% dos usuários concorrentes ficam online simultaneamente no pico do dia.
    # ---------------------------------------------------------
    CONCURRENCY_FACTOR = 0.35
    peak_concurrent_cost = int(raw_concurrent_cost * CONCURRENCY_FACTOR)

    true_total_app_points = authorized_cost + peak_concurrent_cost
    contracted = rules_manager.capacity.get('contracted_app_points', 1200)

    # ---------------------------------------------------------
    # 4. GERAÇÃO DE SAÍDA E RELATÓRIO
    # ---------------------------------------------------------
    print("\n=======================================================")
    print("💰 RESUMO FINANCEIRO E DE LICENCIAMENTO (REALIDADE)")
    print("=======================================================")
    print(f"🔹 Custo Fixo (Authorized Dedicado):     {authorized_cost} AppPoints")
    print(
        f"🔹 Custo Variável (Pico de Concurrent):  {peak_concurrent_cost} AppPoints (calculado via fator {CONCURRENCY_FACTOR * 100}%)")
    print(f"-------------------------------------------------------")
    print(f"📈 TOTAL ESTIMADO DE APP POINTS:         {true_total_app_points} AppPoints")
    print(f"📦 CAPACIDADE CONTRATADA MAS:            {contracted} AppPoints")
    print("=======================================================\n")

    if true_total_app_points > contracted:
        print(f"🚨 ALERTA: Estamos em DEFICIT de {true_total_app_points - contracted} AppPoints.")
    else:
        print(f"✅ SAUDÁVEL: Temos uma folga de {contracted - true_total_app_points} AppPoints.")

    # Salva o JSON com a realidade para o Dashboard HTML consumir
    metrics = {
        "unique_human_users": len(golden_records),
        "authorized_reserved_points": authorized_cost,
        "concurrent_pool_raw_points": raw_concurrent_cost,
        "concurrent_peak_estimated_points": peak_concurrent_cost,
        "true_total_app_points": true_total_app_points,
        "contracted_app_points": contracted
    }

    with open(OUT_DIR / 'true_capacity_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)

    print(f"✅ Arquivo gerado: true_capacity_metrics.json (Pronto para o Dashboard HTML)")


if __name__ == '__main__':
    main()