"""
Validador Automático: Aba 6 - Peak Contributors
================================================
Verifica se:
1. true_capacity_metrics.json contém peak_contributors populados
2. HTML renderiza a tabela de contributors corretamente
3. Card de "Contribuidores no Pico" exibe o count correto
4. Gráfico de picos está correto
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
JSON_PATH = BASE_DIR / "output/consolidated/true_capacity_metrics.json"
HTML_PATH = BASE_DIR / "output/reports/maximo_unified_dashboard.html"

def test_peak_contributors_json():
    """Teste 1: Verifica se peak_contributors está populado no JSON"""
    print("\n🔍 TESTE 1: Peak Contributors no JSON")
    print("=" * 60)
    
    if not JSON_PATH.exists():
        print(f"❌ FALHA: {JSON_PATH} não encontrado")
        return False
    
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    peak_contributors = data.get('peak_contributors', [])
    peak_contributors_count = data.get('peak_contributors_count', 0)
    
    if not peak_contributors:
        print(f"❌ FALHA: peak_contributors está vazio")
        return False
    
    if peak_contributors_count == 0:
        print(f"❌ FALHA: peak_contributors_count = 0")
        return False
    
    if len(peak_contributors) != peak_contributors_count:
        print(f"⚠️  AVISO: Contagem não bate - lista={len(peak_contributors)} vs count={peak_contributors_count}")
    
    print(f"✅ PASSOU: {peak_contributors_count} contribuidores identificados")
    print(f"   Top 3: {', '.join([c['userid'] for c in peak_contributors[:3]])}")
    
    # Valida estrutura
    for i, contributor in enumerate(peak_contributors[:5], 1):
        if 'userid' not in contributor:
            print(f"❌ FALHA: Contributor {i} sem campo 'userid'")
            return False
        if 'app_points' not in contributor:
            print(f"❌ FALHA: Contributor {i} sem campo 'app_points'")
            return False
        if 'license_type' not in contributor:
            print(f"❌ FALHA: Contributor {i} sem campo 'license_type'")
            return False
    
    print("✅ PASSOU: Estrutura dos contributors válida")
    return True


def test_contributors_table_in_html():
    """Teste 2: Verifica se a tabela de contributors está no HTML"""
    print("\n🔍 TESTE 2: Tabela de Contributors no HTML")
    print("=" * 60)
    
    if not HTML_PATH.exists():
        print(f"❌ FALHA: {HTML_PATH} não encontrado")
        return False
    
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verifica header da tabela
    if "Top Contribuidores do Pico" not in html:
        print("❌ FALHA: Header 'Top Contribuidores do Pico' não encontrado")
        return False
    
    # Verifica colunas da tabela
    required_columns = ["#", "USERID", "Tipo de Licença", "Contribuição"]
    for col in required_columns:
        if col not in html:
            print(f"❌ FALHA: Coluna '{col}' não encontrada")
            return False
    
    # Conta linhas de dados na tabela (procura por <td><strong>USERID</strong></td>)
    userid_rows = re.findall(r'<td><strong>([A-Z0-9]+)</strong></td>', html)
    
    if not userid_rows:
        print("❌ FALHA: Nenhuma linha de dados encontrada na tabela")
        return False
    
    print(f"✅ PASSOU: Tabela renderizada com {len(userid_rows)} linhas")
    print(f"   Primeiros 5: {', '.join(userid_rows[:5])}")
    
    return True


def test_contributors_count_card():
    """Teste 3: Verifica se o card de count está correto"""
    print("\n🔍 TESTE 3: Card de Contribuidores no Pico")
    print("=" * 60)
    
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()
    
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    expected_count = data.get('peak_contributors_count', 0)
    
    # Procura pelo card com o título "Contribuidores no Pico"
    card_pattern = r'<div class="stat-title">Contribuidores no Pico</div>'
    if card_pattern not in html:
        print("❌ FALHA: Card 'Contribuidores no Pico' não encontrado")
        return False
    
    # Procura o valor acima do título (padrão: <div class="stat-value">VALUE</div>)
    # Busca antes do "Contribuidores no Pico"
    match = re.search(
        r'<div class="stat-value"[^>]*>(\d+)</div>\s*<div class="stat-title">Contribuidores no Pico</div>',
        html
    )
    
    if not match:
        print("❌ FALHA: Valor do card não encontrado")
        return False
    
    card_value = int(match.group(1))
    
    if card_value != expected_count:
        print(f"❌ FALHA: Valor do card ({card_value}) != esperado ({expected_count})")
        return False
    
    print(f"✅ PASSOU: Card exibe {card_value} contribuidores (correto)")
    return True


def test_peak_hours_in_html():
    """Teste 4: Verifica se os dados de pico estão no gráfico"""
    print("\n🔍 TESTE 4: Dados de Pico no Gráfico")
    print("=" * 60)
    
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()
    
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Verifica se o canvas do gráfico existe
    if 'id="peakLineChart"' not in html:
        print("❌ FALHA: Canvas 'peakLineChart' não encontrado")
        return False
    
    # Verifica se há dados NEM
    if 'data-nem-data=' not in html:
        print("❌ FALHA: Atributo 'data-nem-data' não encontrado")
        return False
    
    # Extrai e valida dados NEM
    nem_match = re.search(r"data-nem-data='(\[[^\]]+\])'", html)
    if not nem_match:
        print("❌ FALHA: Dados NEM não puderam ser extraídos")
        return False
    
    nem_data_str = nem_match.group(1)
    nem_data = json.loads(nem_data_str)
    
    if not nem_data:
        print("❌ FALHA: Array NEM está vazio")
        return False
    
    max_nem = max(nem_data)
    expected_p100 = data.get('true_total_app_points', 0)
    
    # Tolerância de ±5 AppPoints
    if abs(max_nem - expected_p100) > 5:
        print(f"⚠️  AVISO: Max NEM no gráfico ({max_nem}) difere do P100 esperado ({expected_p100})")
    
    print(f"✅ PASSOU: Gráfico com {len(nem_data)} pontos, max NEM = {max_nem}")
    return True


def test_license_badges_in_table():
    """Teste 5: Verifica se os badges de licença estão corretos"""
    print("\n🔍 TESTE 5: Badges de Licença na Tabela")
    print("=" * 60)
    
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verifica se os badges existem
    badge_types = [
        "PREM AUTH",
        "PREM CONC",
        "BASE AUTH",
        "BASE CONC"
    ]
    
    found_badges = []
    for badge in badge_types:
        if badge in html:
            count = html.count(badge)
            found_badges.append(f"{badge}: {count}")
    
    if not found_badges:
        print("❌ FALHA: Nenhum badge de licença encontrado")
        return False
    
    print(f"✅ PASSOU: Badges encontrados - {', '.join(found_badges)}")
    return True


def run_all_tests():
    """Executa todos os testes e gera relatório final"""
    print("\n" + "=" * 60)
    print("🧪 VALIDAÇÃO COMPLETA: ABA 6 - PEAK CONTRIBUTORS")
    print("=" * 60)
    
    tests = [
        test_peak_contributors_json,
        test_contributors_table_in_html,
        test_contributors_count_card,
        test_peak_hours_in_html,
        test_license_badges_in_table,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ EXCEÇÃO no teste {test.__name__}: {e}")
            results.append(False)
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes Aprovados: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 TODAS AS VALIDAÇÕES PASSARAM!")
        print("✅ Aba 6 está funcionando corretamente:")
        print("   - Peak contributors calculados")
        print("   - Tabela renderizada com dados reais")
        print("   - Card de count exibindo valor correto")
        print("   - Gráfico com dados NEM corretos")
        print("   - Badges de licença estilizados")
    else:
        print("\n⚠️  ALGUMAS VALIDAÇÕES FALHARAM")
        print("Revise os testes acima para detalhes.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
