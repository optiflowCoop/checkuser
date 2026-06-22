#!/usr/bin/env python3
"""
Fase 3: Detector de Otimização de Licenças (OURO)

Identifica:
- Usuários com licença Premium mas uso Standard apenas
- Usuários ociosos (desperdício)
- Gaps entre contratado (1200) vs necessário
- Recomendações de downgrade/upgrade
"""
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / 'output' / 'consolidated'
OUT_DIR = ROOT / 'output' / 'consolidated'

CONTRACTED_APPPOINTS = 1200

def load_csv(filename):
    path = IN_DIR / filename
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def main():
    print("🏆 Fase 3: DETECTOR DE OTIMIZAÇÃO DE LICENÇAS (OURO)")
    print(f"Capacidade contratada: {CONTRACTED_APPPOINTS:,} AppPoints\n")
    
    # Carregar análise de uso
    usage_path = IN_DIR / 'usage_analysis_phase3.csv'
    if not usage_path.exists():
        print(f"❌ ERRO: {usage_path.name} não encontrado.")
        print("Execute primeiro: python src/analyze_usage.py")
        return
    
    usage_data = load_csv('usage_analysis_phase3.csv')
    print(f"✓ Carregados {len(usage_data)} usuários com análise de uso")
    
    # Carregar licenças atualmente alocadas
    licenses = load_csv('consolidated_license_footprint.csv')
    
    # Criar mapeamento de licença atual
    current_licenses = {}
    for lic in licenses:
        key = f"{lic.get('ENV_DB')}|{lic.get('USERID')}"
        current_licenses[key] = {
            'license_num': lic.get('LICENSENUM', ''),
            'is_unlicensed': lic.get('ISUNLICUSER', '0') == '1',
            'is_selfservice': lic.get('ISSELFSERVICEUSER', '0') == '1'
        }
    
    # Análise de otimização
    optimizations = []
    waste_points = 0
    needed_points = 0
    
    for user in usage_data:
        userid = user.get('USERID', '')
        tier = user.get('USER_TIER', '')
        required_lic = user.get('REQUIRED_LICENSE', '')
        cost = int(user.get('APP_POINTS_COST', 0))
        logins = int(user.get('LOGIN_COUNT_90D', 0))
        premium_apps = user.get('PREMIUM_APPS', '')
        user_category = user.get('USER_CATEGORY', 'UNKNOWN')
        
        # Focar apenas em usuários FORESEA para contagem real
        if user_category == 'FORESEA':
            needed_points += cost
        
        # Regras de otimização
        recommendation = ''
        savings = 0
        optimization_type = ''
        
        # TEMPORÁRIOS: Marcar para não migração
        if user_category == 'TEMPORARY':
            recommendation = '🔵 NÃO MIGRAR - Usuário temporário/contratado'
            savings = cost
            optimization_type = 'Exclusão Temporário'
            waste_points += cost
        
        elif tier == 'IDLE':
            recommendation = '🔴 DESATIVAR - Sem uso há 90 dias'
            savings = cost
            optimization_type = 'Usuário Ocioso'
            waste_points += cost
        
        elif tier == 'VERY_LIGHT' and logins < 5:
            recommendation = '🟠 AVALIAR DESATIVAÇÃO - Uso extremamente baixo'
            savings = cost * 0.7  # Economia potencial parcial
            optimization_type = 'Uso Muito Baixo'
            waste_points += savings
        
        elif 'PREMIUM' in required_lic and not premium_apps:
            recommendation = '🟡 DOWNGRADE para BASE - Não usa módulos O&G'
            savings = 10  # Diferença Premium → Base
            optimization_type = 'Premium sem uso O&G'
            waste_points += savings
        
        elif 'AUTHORIZED' in required_lic and logins < 30:
            recommendation = '🟡 MUDAR para CONCURRENT - Uso não justifica Authorized'
            savings = 3  # Diferença Authorized → Concurrent
            optimization_type = 'Authorized → Concurrent'
            waste_points += savings
        
        elif tier == 'MEDIUM_OG' and logins > 45:
            recommendation = '🟢 OK - Uso adequado para Premium'
            optimization_type = 'OK'
        
        elif tier == 'POWER_OG':
            recommendation = '🟢 POWER USER - Mantém Premium Authorized'
            optimization_type = 'OK'
        
        else:
            recommendation = '🟢 OK - Licença alinhada com uso'
            optimization_type = 'OK'
        
        optimizations.append({
            'USERID': userid,
            'DISPLAYNAME': user.get('DISPLAYNAME', ''),
            'EMAIL': user.get('EMAIL', ''),
            'USER_CATEGORY': user_category,
            'TITLE': user.get('TITLE', ''),
            'PERSONGROUP': user.get('PERSONGROUP', ''),
            'CURRENT_TIER': tier,
            'LOGIN_COUNT_90D': logins,
            'REQUIRED_LICENSE': required_lic,
            'APP_POINTS_COST': cost,
            'PREMIUM_APPS_USED': premium_apps,
            'OPTIMIZATION_TYPE': optimization_type,
            'RECOMMENDATION': recommendation,
            'POTENTIAL_SAVINGS': int(savings)
        })
    
    # Ordenar por potencial de economia
    optimizations.sort(key=lambda x: x['POTENTIAL_SAVINGS'], reverse=True)
    
    # Salvar relatório
    out_path = OUT_DIR / 'license_optimization_recommendations.csv'
    if optimizations:
        with out_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(optimizations[0].keys()))
            writer.writeheader()
            writer.writerows(optimizations)
        
        print(f"✅ ESCRITO: {out_path.name} ({len(optimizations)} recomendações)\n")
        
        # Estatísticas finais
        foresea_users = [o for o in optimizations if o['USER_CATEGORY'] == 'FORESEA']
        temp_users = [o for o in optimizations if o['USER_CATEGORY'] == 'TEMPORARY']
        
        idle_count = sum(1 for o in optimizations if o['CURRENT_TIER'] == 'IDLE')
        downgrade_count = sum(1 for o in optimizations if 'DOWNGRADE' in o['RECOMMENDATION'])
        concurrent_switch = sum(1 for o in optimizations if 'CONCURRENT' in o['RECOMMENDATION'])
        temp_exclusion = len(temp_users)
        
        print("=" * 70)
        print("📊 RELATÓRIO EXECUTIVO DE OTIMIZAÇÃO")
        print("=" * 70)
        print(f"👥 SEGREGAÇÃO DE USUÁRIOS:")
        print(f"   • Usuários FORESEA (permanentes): {len(foresea_users)}")
        print(f"   • Usuários TEMPORÁRIOS (não migrar): {temp_exclusion}")
        print(f"\n💰 APPPOINTS:")
        print(f"AppPoints Contratados:        {CONTRACTED_APPPOINTS:>10,}")
        print(f"AppPoints Necessários (atual):{needed_points:>10,} (apenas FORESEA)")
        print(f"AppPoints Desperdiçados:      {int(waste_points):>10,} ⚠️")
        print(f"AppPoints após Otimização:    {int(needed_points - waste_points):>10,}")
        print(f"Economia Potencial:           {int(waste_points):>10,} ({waste_points/needed_points*100 if needed_points > 0 else 0:.1f}%)")
        print("-" * 70)
        print(f"Status vs Contrato:           ", end='')
        
        optimized_cost = needed_points - waste_points
        if optimized_cost <= CONTRACTED_APPPOINTS:
            folga = CONTRACTED_APPPOINTS - optimized_cost
            print(f"✅ DENTRO DO LIMITE (+{int(folga)} pontos de folga)")
        else:
            deficit = optimized_cost - CONTRACTED_APPPOINTS
            print(f"⚠️  ACIMA DO CONTRATADO (-{int(deficit)} pontos)")
        
        print("=" * 70)
        print(f"\n🎯 AÇÕES RECOMENDADAS:")
        print(f"   • ❌ Excluir temporários da migração: {temp_exclusion} usuários")
        print(f"   • 🔴 Desativar usuários ociosos: {idle_count}")
        print(f"   • 🟡 Downgrade Premium → Base: {downgrade_count}")
        print(f"   • 🟡 Mudar Authorized → Concurrent: {concurrent_switch}")
        print(f"   • Economia estimada: {int(waste_points)} AppPoints")
        
        print(f"\n💡 PRÓXIMOS PASSOS:")
        print(f"   1. Revisar lista de ociosos com RH")
        print(f"   2. Validar downgrades com gestores funcionais")
        print(f"   3. Executar otimizações em janela de manutenção")
        print(f"   4. Monitorar uso pós-otimização (30 dias)")
    
    else:
        print("⚠️  Nenhuma otimização identificada")

if __name__ == '__main__':
    main()
