#!/usr/bin/env python3
"""
Validador: Aba 6 - Peak Contributors
Valida integridade e consistência dos dados de pico horário.
"""

import json
import re
import sys


def validate_peak_tab():
    """Valida a Aba 6 (Peak Contributors)."""
    print("="*60)
    print("VALIDAÇÃO: Aba 6 - Peak Contributors")
    print("="*60)
    
    errors = []
    
    # 1. Verificar se true_capacity_metrics.json existe e está correto
    print("\n[1] Verificando true_capacity_metrics.json...")
    
    try:
        with open('c:\\Users\\esilva\\OneDrive - FORESEA\\Documentos\\04 - APPS\\CHECKUSER\\output\\consolidated\\true_capacity_metrics.json', 'r') as f:
            capacity_data = json.load(f)
        
        print(f"    ✓ Arquivo carregado com sucesso")
        
        # Valida estrutura
        required_keys = ['unique_human_users', 'authorized_reserved_points', 'true_total_app_points', 'hourly_counts']
        missing = [k for k in required_keys if k not in capacity_data]
        
        if missing:
            errors.append(f"Chaves obrigatórias ausentes em true_capacity_metrics.json: {missing}")
        else:
            print(f"    ✓ Estrutura de dados completa")
            
        hourly_counts = capacity_data.get('hourly_counts', {})
        if not hourly_counts:
            errors.append("Nenhum dado horário encontrado em 'hourly_counts'")
        else:
            print(f"    ✓ {len(hourly_counts)} registros horários encontrados")
            
            # Valida valores máximos
            max_hour = max(hourly_counts, key=hourly_counts.get)
            max_value = hourly_counts[max_hour]
            print(f"      • Pico máximo: {max_value} AppPoints em {max_hour}")
            
            if max_value != capacity_data.get('true_total_app_points', 0):
                print(f"      ⚠️  Divergência: true_total_app_points ({capacity_data.get('true_total_app_points')}) != max_hour ({max_value})")
            
    except FileNotFoundError:
        errors.append("Arquivo true_capacity_metrics.json não encontrado")
        return False
    except json.JSONDecodeError as e:
        errors.append(f"Erro ao parsear JSON: {e}")
        return False
    
    # 2. Verificar se HTML contém dados corretos do gráfico
    print("\n[2] Validando dados no HTML gerado...")
    
    try:
        with open('c:\\Users\\esilva\\OneDrive - FORESEA\\Documentos\\04 - APPS\\CHECKUSER\\output\\reports\\maximo_unified_dashboard.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extrai atributos data-* do canvas
        match_labels = re.search(r"data-labels='(\[.*?\])'", html_content)
        match_users = re.search(r"data-users-data='(\[.*?\])'", html_content)
        match_points = re.search(r"data-points-data='(\[.*?\])'", html_content)
        match_nem = re.search(r"data-nem-data='(\[.*?\])'", html_content)
        
        if not all([match_labels, match_users, match_points, match_nem]):
            errors.append("Atributos data-* do gráfico não encontrados no HTML")
        else:
            labels = json.loads(match_labels.group(1))
            users_data = json.loads(match_users.group(1))
            points_data = json.loads(match_points.group(1))
            nem_data = json.loads(match_nem.group(1))
            
            print(f"    ✓ {len(labels)} pontos de dados no gráfico")
            print(f"      • Labels: {len(labels)}")
            print(f"      • Usuários: {len(users_data)}")
            print(f"      • AppPoints: {len(points_data)}")
            print(f"      • NEM: {len(nem_data)}")
            
            # Valida consistência de tamanhos
            if not (len(labels) == len(users_data) == len(points_data) == len(nem_data)):
                errors.append(f"Tamanhos de séries inconsistentes: labels={len(labels)}, users={len(users_data)}, points={len(points_data)}, nem={len(nem_data)}")
            else:
                print(f"    ✓ Todas as séries têm o mesmo comprimento")
            
            # Valida valores plausíveis
            max_users = max(users_data)
            max_points = max(points_data)
            max_nem = max(nem_data)
            
            print(f"\n    Máximos registrados:")
            print(f"      • Usuários simultâneos: {max_users:.0f}")
            print(f"      • AppPoints (padrão): {max_points:.0f}")
            print(f"      • AppPoints NEM: {max_nem:.0f}")
            
            # Valida que NEM >= Points (NEM é o cálculo correto, Points pode ser legado)
            if max_nem < max_points * 0.9:  # Margem de 10%
                print(f"      ⚠️  NEM ({max_nem}) significativamente menor que Points ({max_points})")
            
            # Valida relação usuários/AppPoints
            if max_users > 0:
                ratio = max_nem / max_users
                print(f"      • Razão AppPoints/Usuário: {ratio:.2f}")
                
                if ratio < 2 or ratio > 20:
                    errors.append(f"Razão AppPoints/Usuário ({ratio:.2f}) fora do esperado (2-20)")
            
    except FileNotFoundError:
        errors.append("Arquivo HTML não encontrado")
        return False
    except Exception as e:
        errors.append(f"Erro ao processar HTML: {e}")
        return False
    
    # 3. Verificar stats cards na Aba 6
    print("\n[3] Validando cards de estatísticas...")
    
    match_p100 = re.search(r'<div class="stat-title">Pico Real \(P100\)</div>', html_content)
    match_p95 = re.search(r'<div class="stat-title">Pico Seguro \(P95\)</div>', html_content)
    match_peak = re.search(r'<div class="stat-title">Maior Pico Registrado</div>', html_content)
    
    if all([match_p100, match_p95, match_peak]):
        print("    ✓ Cards P100, P95 e Maior Pico encontrados")
    else:
        errors.append("Cards de estatísticas ausentes ou incompletos")
    
    # 4. Verificar inicialização do gráfico
    print("\n[4] Validando JavaScript do gráfico...")
    
    if 'peakLineChart' in html_content:
        print("    ✓ Canvas peakLineChart encontrado")
    else:
        errors.append("Canvas peakLineChart não encontrado")
    
    if "new Chart(ctxPeak, {" in html_content:
        print("    ✓ Inicialização Chart.js encontrada")
    else:
        errors.append("Código de inicialização do gráfico ausente")
    
    # Valida eixos Y
    if "'y-users'" in html_content and "'y-points'" in html_content:
        print("    ✓ Eixos Y dual configurados (usuários + AppPoints)")
    else:
        errors.append("Configuração de eixos Y ausente ou incorreta")
    
    # Sumário
    print("\n" + "="*60)
    print("RESULTADO DA VALIDAÇÃO")
    print("="*60)
    
    if errors:
        print(f"\n❌ FALHOU - {len(errors)} erro(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return False
    else:
        print("\n✅ SUCESSO - Aba 6 está estruturada corretamente!")
        print("\nRESUMO:")
        print(f"  • Dados horários completos ({len(hourly_counts)} registros)")
        print(f"  • Gráfico com {len(labels)} pontos de pico")
        print(f"  • Pico máximo: {max_nem:.0f} AppPoints ({max_users:.0f} usuários)")
        print(f"  • Razão AppPoints/Usuário: {ratio:.2f}")
        print("\n  ✓ Dados de capacidade corretos")
        print("  ✓ Gráfico renderizando 3 séries (Usuários, AppPoints, NEM)")
        print("  ✓ Eixos Y dual configurados corretamente")
        return True


if __name__ == '__main__':
    success = validate_peak_tab()
    sys.exit(0 if success else 1)
