#!/usr/bin/env python3
"""
Validador: Cálculos de AppPoints por Escopo
Valida que os valores de AppPoints variam corretamente entre escopos.
"""

import json
import sys


def validate_scope_calculations():
    """Valida que AppPoints diferem entre escopos conforme esperado."""
    print("="*60)
    print("VALIDAÇÃO: Cálculos de AppPoints por Escopo")
    print("="*60)
    
    # Lê os dados reais do HTML gerado
    import re
    html_path = 'c:\\Users\\esilva\\OneDrive - FORESEA\\Documentos\\04 - APPS\\CHECKUSER\\output\\reports\\maximo_unified_dashboard.html'
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Encontra scenariosByScope no HTML
        match = re.search(r'const scenariosByScope = ({.*?});', html_content, re.DOTALL)
        if not match:
            print("❌ ERRO: Não foi possível encontrar scenariosByScope no HTML")
            return False
        
        # Parse do JSON
        json_str = match.group(1)
        test_data = json.loads(json_str)
        print("\n✓ Dados lidos do HTML gerado com sucesso")
        
    except FileNotFoundError:
        print(f"❌ ERRO: Arquivo HTML não encontrado: {html_path}")
        return False
    except Exception as e:
        print(f"❌ ERRO ao ler HTML: {e}")
        return False
    
    # Fórmula de AppPoints
    app_points_config = {
        'pA': 5,   # PREMIUM AUTHORIZED
        'pC': 15,  # PREMIUM CONCURRENT
        'bA': 3,   # BASE AUTHORIZED
        'bC': 10   # BASE CONCURRENT
    }
    
    errors = []
    
    print("\n[1] Calculando AppPoints por Escopo e Cenário...")
    print("-" * 60)
    
    results = {}
    for scope in ['foresea', 'terceiros', 'integracao', 'todos']:
        results[scope] = {}
        print(f"\n  📍 {scope.upper()}")
        
        for scenario in ['asis', 'saneado', 'otimizado']:
            data = test_data[scope][scenario]
            total = (data['pA'] * 5) + (data['pC'] * 15) + (data['bA'] * 3) + (data['bC'] * 10)
            results[scope][scenario] = total
            
            print(f"    {scenario.upper():12} → {total:6,} AppPoints")
    
    print("\n" + "-" * 60)
    
    # Teste 1: Valores devem ser diferentes entre escopos
    print("\n[2] Validando que valores diferem entre escopos...")
    
    foresea_otim = results['foresea']['otimizado']
    terceiros_otim = results['terceiros']['otimizado']
    integracao_otim = results['integracao']['otimizado']
    todos_otim = results['todos']['otimizado']
    
    if foresea_otim == terceiros_otim == todos_otim:
        errors.append(
            f"ERRO CRÍTICO: Todos os escopos retornam o mesmo valor ({foresea_otim} AppPoints). "
            "Filtros de escopo NÃO estão funcionando!"
        )
    else:
        print(f"    ✓ FORESEA ({foresea_otim:,}) ≠ TERCEIROS ({terceiros_otim:,}) ≠ TODOS ({todos_otim:,})")
        print("    ✓ Filtros de escopo estão aplicando cálculos distintos")
    
    # Teste 2: Validar que TODOS = FORESEA + TERCEIROS + INTEGRACAO
    print("\n[3] Validando somatório (todos = foresea + terceiros + integracao)...")
    
    for scenario in ['asis', 'saneado', 'otimizado']:
        expected = results['foresea'][scenario] + results['terceiros'][scenario] + results['integracao'][scenario]
        actual = results['todos'][scenario]
        
        if actual != expected:
            errors.append(
                f"[{scenario}] Somatório incorreto: "
                f"todos={actual} != foresea({results['foresea'][scenario]}) + "
                f"terceiros({results['terceiros'][scenario]}) + integracao({results['integracao'][scenario]}) = {expected}"
            )
        else:
            print(f"    ✓ {scenario.upper()}: {actual:,} = {results['foresea'][scenario]:,} + {results['terceiros'][scenario]:,} + {results['integracao'][scenario]:,}")
    
    # Teste 3: Validar que valores são plausíveis
    print("\n[4] Validando plausibilidade dos valores...")
    
    if foresea_otim < 1000:
        errors.append(f"FORESEA muito baixo ({foresea_otim}). Esperado > 1000 para base de ~768 usuários")
    else:
        print(f"    ✓ FORESEA ({foresea_otim:,}) está em range plausível")
    
    if terceiros_otim < 100:
        print(f"    ⚠️  TERCEIROS ({terceiros_otim:,}) está baixo. Verificar se há usuários terceiros na base")
    else:
        print(f"    ✓ TERCEIROS ({terceiros_otim:,}) está em range plausível")
    
    if todos_otim <= foresea_otim:
        errors.append(f"TODOS ({todos_otim}) deveria ser > FORESEA ({foresea_otim})")
    else:
        print(f"    ✓ TODOS ({todos_otim:,}) > FORESEA ({foresea_otim:,})")
    
    # Teste 4: Detectar usuários de integração
    print("\n[5] Verificando identificação de usuários de integração...")
    
    try:
        with open('c:\\Users\\esilva\\OneDrive - FORESEA\\Documentos\\04 - APPS\\CHECKUSER\\output\\consolidated\\license_decision_plan.csv', 'r', encoding='utf-8-sig') as f:
            content = f.read()
            
        wsoracle_count = content.count('WSORACLE')
        
        if wsoracle_count > 0:
            print(f"    ✓ Encontrados {wsoracle_count} registros WSORACLE no CSV")
            
            if 'INTEGRACAO' in content:
                print(f"    ✓ Categoria INTEGRACAO está sendo aplicada")
            else:
                errors.append("Categoria INTEGRACAO não encontrada no CSV. Usuários WSORACLE não estão sendo classificados corretamente")
        else:
            print(f"    ⚠️  Nenhum usuário WSORACLE encontrado (esperado ~7)")
    
    except FileNotFoundError:
        print("    ⚠️  Arquivo license_decision_plan.csv não encontrado")
    
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
        print("\n✅ SUCESSO - AppPoints variam corretamente entre escopos!")
        print("\nRESUMO DOS CÁLCULOS:")
        print(f"  • FORESEA (Otimizado):    {results['foresea']['otimizado']:>6,} AppPoints")
        print(f"  • TERCEIROS (Otimizado):  {results['terceiros']['otimizado']:>6,} AppPoints")
        print(f"  • INTEGRAÇÃO (Otimizado): {results['integracao']['otimizado']:>6,} AppPoints")
        print(f"  • TODOS (Otimizado):      {results['todos']['otimizado']:>6,} AppPoints")
        print("\n  ✓ Filtros de escopo estão aplicando cálculos corretos")
        print("  ✓ Valores são consistentes e plausíveis")
        return True


if __name__ == '__main__':
    success = validate_scope_calculations()
    sys.exit(0 if success else 1)
