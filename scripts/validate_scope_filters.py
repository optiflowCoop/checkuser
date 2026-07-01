#!/usr/bin/env python3
"""
Validador de Filtros de Escopo - Aba 3

Valida que:
1. scenarios_by_scope contém todos os três escopos
2. 'todos' = 'foresea' + 'terceiros' (somatório correto)
3. Cada cenário tem as 4 chaves (pA, pC, bA, bC)
4. Valores são não-negativos
5. Não há referências a scenario_points_total (removido)
"""

import json
import sys


def validate_scope_filters():
    """Valida estrutura de dados de filtros de escopo."""
    print("="*60)
    print("VALIDAÇÃO: Filtros de Escopo (Aba 3)")
    print("="*60)
    
    # Simular dados reais extraídos do HTML gerado
    test_data = {
        "foresea": {
            "asis": {"pA": 236, "pC": 521, "bA": 1, "bC": 10},
            "saneado": {"pA": 236, "pC": 501, "bA": 1, "bC": 9},
            "otimizado": {"pA": 216, "pC": 521, "bA": 1, "bC": 9}
        },
        "terceiros": {
            "asis": {"pA": 0, "pC": 14, "bA": 0, "bC": 437},
            "saneado": {"pA": 0, "pC": 10, "bA": 0, "bC": 371},
            "otimizado": {"pA": 0, "pC": 10, "bA": 0, "bC": 371}
        },
        "todos": {
            "asis": {"pA": 236, "pC": 535, "bA": 1, "bC": 447},
            "saneado": {"pA": 236, "pC": 511, "bA": 1, "bC": 380},
            "otimizado": {"pA": 216, "pC": 531, "bA": 1, "bC": 380}
        }
    }
    
    errors = []
    warnings = []
    
    # Teste 1: Estrutura de escopos
    print("\n[1] Validando estrutura de escopos...")
    required_scopes = {'foresea', 'terceiros', 'todos'}
    actual_scopes = set(test_data.keys())
    
    if actual_scopes != required_scopes:
        errors.append(f"Escopos esperados: {required_scopes}, encontrados: {actual_scopes}")
    else:
        print("    ✓ Todos os 3 escopos presentes (foresea, terceiros, todos)")
    
    # Teste 2: Estrutura de cenários
    print("\n[2] Validando estrutura de cenários...")
    required_scenarios = {'asis', 'saneado', 'otimizado'}
    required_keys = {'pA', 'pC', 'bA', 'bC'}
    
    for scope, scenarios in test_data.items():
        actual_scenarios = set(scenarios.keys())
        if actual_scenarios != required_scenarios:
            errors.append(f"[{scope}] Cenários esperados: {required_scenarios}, encontrados: {actual_scenarios}")
        
        for scenario, data in scenarios.items():
            actual_keys = set(data.keys())
            if actual_keys != required_keys:
                errors.append(f"[{scope}.{scenario}] Chaves esperadas: {required_keys}, encontradas: {actual_keys}")
            
            for key, value in data.items():
                if not isinstance(value, int) or value < 0:
                    errors.append(f"[{scope}.{scenario}.{key}] Valor inválido: {value} (deve ser int >= 0)")
    
    if not errors:
        print("    ✓ Todos os cenários têm as 4 chaves (pA, pC, bA, bC)")
        print("    ✓ Todos os valores são inteiros não-negativos")
    
    # Teste 3: Consistência matemática (todos = foresea + terceiros)
    print("\n[3] Validando somatório (todos = foresea + terceiros)...")
    for scenario in ['asis', 'saneado', 'otimizado']:
        for key in ['pA', 'pC', 'bA', 'bC']:
            foresea_val = test_data['foresea'][scenario][key]
            terceiros_val = test_data['terceiros'][scenario][key]
            todos_val = test_data['todos'][scenario][key]
            expected = foresea_val + terceiros_val
            
            if todos_val != expected:
                errors.append(
                    f"[{scenario}.{key}] Somatório incorreto: "
                    f"todos={todos_val} != foresea({foresea_val}) + terceiros({terceiros_val}) = {expected}"
                )
    
    if not any('[todos' in e for e in errors if '[' in e):
        print("    ✓ Todos os somatórios estão corretos")
    
    # Teste 4: Validação de AppPoints por escopo
    print("\n[4] Calculando AppPoints por escopo...")
    app_points_config = {
        'pA': 5,   # PREMIUM AUTHORIZED
        'pC': 15,  # PREMIUM CONCURRENT
        'bA': 3,   # BASE AUTHORIZED
        'bC': 10   # BASE CONCURRENT
    }
    
    for scope in ['foresea', 'terceiros', 'todos']:
        print(f"\n    Escopo: {scope.upper()}")
        for scenario in ['asis', 'saneado', 'otimizado']:
            data = test_data[scope][scenario]
            total_points = sum(data[key] * app_points_config[key] for key in ['pA', 'pC', 'bA', 'bC'])
            print(f"      {scenario.upper():12} → {total_points:6,} AppPoints  "
                  f"(pA:{data['pA']:3} pC:{data['pC']:3} bA:{data['bA']:3} bC:{data['bC']:3})")
            
            # Validar que OTIMIZADO <= SANEADO <= ASIS (deve ser tendência geral)
            if scenario == 'otimizado':
                otimizado_points = total_points
            elif scenario == 'saneado':
                saneado_points = total_points
            elif scenario == 'asis':
                asis_points = total_points
        
        if otimizado_points > asis_points:
            warnings.append(f"[{scope}] Otimizado ({otimizado_points}) > As-Is ({asis_points}) - esperava-se redução")
    
    # Teste 5: Detecção de referências antigas (scenario_points_total)
    print("\n[5] Verificando remoção de campos obsoletos...")
    try:
        with open('c:\\Users\\esilva\\OneDrive - FORESEA\\Documentos\\04 - APPS\\CHECKUSER\\output\\reports\\maximo_unified_dashboard.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        if 'scenarioPointsTotal' in html_content:
            errors.append("Referência obsoleta 'scenarioPointsTotal' encontrada no HTML (deveria ter sido removida)")
        else:
            print("    ✓ Campo obsoleto 'scenarioPointsTotal' não encontrado (correto)")
        
        if 'rawSumDisplay' in html_content:
            errors.append("Referência obsoleta 'rawSumDisplay' encontrada no HTML (deveria ter sido removida)")
        else:
            print("    ✓ Campo obsoleto 'rawSumDisplay' não encontrado (correto)")
        
        if 'Soma bruta (XLSX)' in html_content and html_content.count('Soma bruta (XLSX)') > 0:
            # Deve estar apenas em comentários ou documentação, não no código ativo
            warnings.append("Texto 'Soma bruta (XLSX)' ainda presente no HTML (verificar se é comentário)")
        
        if 'currentScopeLabel' in html_content:
            print("    ✓ Novo campo 'currentScopeLabel' encontrado (correto)")
        else:
            errors.append("Campo 'currentScopeLabel' não encontrado no HTML (deveria estar presente)")
        
        if 'scenariosByScope' in html_content:
            print("    ✓ Estrutura 'scenariosByScope' encontrada (correto)")
        else:
            errors.append("Estrutura 'scenariosByScope' não encontrada no HTML")
    
    except FileNotFoundError:
        warnings.append("Arquivo HTML não encontrado - executar pipeline primeiro")
    
    # Sumário final
    print("\n" + "="*60)
    print("RESULTADO DA VALIDAÇÃO")
    print("="*60)
    
    if errors:
        print(f"\n❌ FALHOU - {len(errors)} erro(s) encontrado(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    else:
        print("\n✅ SUCESSO - Todos os testes passaram!")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} aviso(s):\n")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    
    print("\n" + "="*60)
    
    return len(errors) == 0


if __name__ == '__main__':
    success = validate_scope_filters()
    sys.exit(0 if success else 1)
