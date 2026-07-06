# scripts/reporting/ab9_indicadores.py
# Módulo de Relatórios - Indicadores Mensais Consolidados IBM MAXIMO

from datetime import datetime
import json
import csv
from pathlib import Path

# Dados reais são carregados de consolidated_{tipo}_indicadores.csv
INDICADORES_DATA_FALLBACK = {}

CATEGORIAS = {
    "work_orders": {"nome": "📋 Work Orders", "descricao": "Ordens de Serviço", "cor": "#2563eb"},
    "moc":        {"nome": "🔄 MOC",            "descricao": "Gestão de Mudanças", "cor": "#f59e0b"},
    "ptw":        {"nome": "📜 PTWs",           "descricao": "Permissão de Trabalho", "cor": "#10b981"},
    "loto":       {"nome": "🔒 LOTO",           "descricao": "Isolamento de Energias Perigosas", "cor": "#ef4444"}
}

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
MESES_COMPLETO = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

UNIDADES_ORDER = ["ODN1", "ODN2", "N06", "N08", "N09", "HTQ", "POL", "PGA", "PGB", "PGC", "BASE"]

# Mapeamento de SITEID para unidade
SITEID_TO_UNIDADE = {
    "ODN1": "ODN1",
    "ODN2": "ODN2", 
    "N06": "N06",
    "N08": "N08",
    "N09": "N09",
    "HTQ": "HTQ",
    "POL": "POL",
    "PGA": "PGA",
    "PGB": "PGB",
    "PGC": "PGC",
    "BASE": "BASE"
}

# Cache global para dados
_indicadores_cache = None

def _load_indicadores_from_csv(ano=None, mes_inicio=1, mes_fim=12):
    """Carrega indicadores reais dos arquivos consolidados, filtrando por período"""
    global _indicadores_cache
    
    # Usa cache se já carregado
    if _indicadores_cache is not None:
        data = _indicadores_cache
    else:
        # Usa o diretório raiz do projeto
        root = Path(__file__).resolve().parent.parent.parent
        consolidated_dir = root / 'output' / 'consolidated'
        
        data = {}
        
        # Processa Work Orders
        wo_file = consolidated_dir / 'consolidated_workorder_indicadores.csv'
        if wo_file.exists():
            with open(wo_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    siteid = row.get('SITEID', '').strip()
                    row_ano = row.get('ANO', '').strip()
                    mes = int(row.get('MES', 0))
                    total = int(row.get('TOTAL', 0))
                    
                    if row_ano and mes:
                        if row_ano not in data:
                            data[row_ano] = {}
                        if 'work_orders' not in data[row_ano]:
                            data[row_ano]['work_orders'] = {}
                        unidade = SITEID_TO_UNIDADE.get(siteid, siteid)
                        if unidade not in data[row_ano]['work_orders']:
                            data[row_ano]['work_orders'][unidade] = {}
                        data[row_ano]['work_orders'][unidade][mes] = total
        
        # Processa MOC
        moc_file = consolidated_dir / 'consolidated_moc_indicadores.csv'
        if moc_file.exists():
            with open(moc_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    siteid = row.get('SITEID', '').strip()
                    row_ano = row.get('ANO', '').strip()
                    mes = int(row.get('MES', 0))
                    total = int(row.get('TOTAL', 0))
                    
                    if row_ano and mes:
                        if row_ano not in data:
                            data[row_ano] = {}
                        if 'moc' not in data[row_ano]:
                            data[row_ano]['moc'] = {}
                        unidade = SITEID_TO_UNIDADE.get(siteid, siteid)
                        if unidade not in data[row_ano]['moc']:
                            data[row_ano]['moc'][unidade] = {}
                        data[row_ano]['moc'][unidade][mes] = total
        
        # Processa PTWs
        ptw_file = consolidated_dir / 'consolidated_ptw_indicadores.csv'
        if ptw_file.exists():
            with open(ptw_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    siteid = row.get('SITEID', '').strip()
                    row_ano = row.get('ANO', '').strip()
                    mes = int(row.get('MES', 0))
                    total = int(row.get('TOTAL', 0))
                    
                    if row_ano and mes:
                        if row_ano not in data:
                            data[row_ano] = {}
                        if 'ptw' not in data[row_ano]:
                            data[row_ano]['ptw'] = {}
                        unidade = SITEID_TO_UNIDADE.get(siteid, siteid)
                        if unidade not in data[row_ano]['ptw']:
                            data[row_ano]['ptw'][unidade] = {}
                        data[row_ano]['ptw'][unidade][mes] = total
        
        # Processa LOTO
        loto_file = consolidated_dir / 'consolidated_loto_indicadores.csv'
        if loto_file.exists():
            with open(loto_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    siteid = row.get('SITEID', '').strip()
                    row_ano = row.get('ANO', '').strip()
                    mes = int(row.get('MES', 0))
                    total = int(row.get('TOTAL', 0))
                    
                    if row_ano and mes:
                        if row_ano not in data:
                            data[row_ano] = {}
                        if 'loto' not in data[row_ano]:
                            data[row_ano]['loto'] = {}
                        unidade = SITEID_TO_UNIDADE.get(siteid, siteid)
                        if unidade not in data[row_ano]['loto']:
                            data[row_ano]['loto'][unidade] = {}
                        data[row_ano]['loto'][unidade][mes] = total
        
        _indicadores_cache = data
    
    # Aplica filtros
    if ano or mes_inicio > 1 or mes_fim < 12:
        filtered = {}
        for a, cat_data in data.items():
            if ano and a != ano:
                continue
            filtered[a] = {}
            for cat, unid_data in cat_data.items():
                filtered[a][cat] = {}
                for u, mes_data in unid_data.items():
                    filtered[a][cat][u] = {m: v for m, v in mes_data.items() if mes_inicio <= m <= mes_fim}
        return filtered
    
    return data


def _get_valor(valores, mes):
    """Retorna valor ou 0 se None ou não existir"""
    if valores is None:
        return 0
    v = valores.get(mes)
    return v if v is not None else 0


def _fmt(val):
    """Formata número com separador de milhar pt-BR"""
    if val is None:
        return "0"
    return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _get_ano_atual():
    """Retorna o ano mais recente disponível nos dados"""
    real_data = _load_indicadores_from_csv()
    if real_data:
        anos = sorted(real_data.keys(), reverse=True)
        return anos[0] if anos else "2026"
    return "2026"


def _get_mes_atual():
    """Retorna o mês anterior ao atual (para relatório fechado)"""
    hoje = datetime.now()
    if hoje.month == 1:
        return 12
    return hoje.month - 1


def _get_indicadores_data(ano=None, mes_inicio=1, mes_fim=12):
    """Retorna os dados de indicadores (reais ou fallback)"""
    real_data = _load_indicadores_from_csv(ano, mes_inicio, mes_fim)
    if real_data:
        return real_data
    return INDICADORES_DATA_FALLBACK


def render_tab_indicadores(data=None):
    """Renderiza a aba de Indicadores Mensais Consolidados"""
    data = data or {}
    
    INDICADORES_DATA = _get_indicadores_data()
    
    anos_disponiveis = sorted(INDICADORES_DATA.keys())
    ano_atual = data.get('ano', _get_ano_atual())
    mes_atual = data.get('mes', _get_mes_atual())
    
    if ano_atual not in INDICADORES_DATA:
        ano_atual = _get_ano_atual()
    
    data_ano = INDICADORES_DATA.get(ano_atual, {})

    return f"""
<div id="tab-indicadores" class="container tab-content">
    <div class="card">
        <h2 class="card-header" style="border-bottom-color: var(--accent);">
            📊 Relatório de Indicadores Consolidado Mensal
            <span style="font-size: 0.8rem; color: #64748b; font-weight: normal;">
                IBM MAXIMO - Foresea
            </span>
        </h2>
        
        <div style="display: flex; align-items: center; gap: 2rem; flex-wrap: wrap; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <label style="font-weight: 600; color: var(--secondary);">Ano:</label>
                <div style="display: flex; gap: 0.3rem;">
                    {''.join(f'''
                    <button class="ano-btn {'active' if a == ano_atual else ''}" 
                            onclick="changeIndicadorAno('{a}')" 
                            id="anoBtn_{a}"
                            style="background: {'var(--accent)' if a == ano_atual else 'white'}; 
                                   color: {'white' if a == ano_atual else 'var(--secondary)'}; 
                                   border: 2px solid var(--accent); 
                                   padding: 8px 18px; 
                                   border-radius: 6px; 
                                   font-weight: 600; 
                                   cursor: pointer;
                                   transition: all 0.2s;">
                        {a}
                    </button>
                    ''' for a in anos_disponiveis)}
                </div>
            </div>
            
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <label style="font-weight: 600; color: var(--secondary);">Mês:</label>
            <select id="mesSelector" onchange="changeIndicadorMes()"
                    style="padding: 8px 16px; border: 2px solid var(--accent); border-radius: 6px; 
                           font-size: 1rem; font-weight: 600; background: white; cursor: pointer;
                           min-width: 160px;">
                <option value="">Selecione o mês...</option>
                {''.join(f'<option value="{m}" {"selected" if m == mes_atual else ""}>{MESES[m-1]} - {MESES_COMPLETO[m]}</option>' for m in range(1, 13))}
            </select>
        </div>
            
            <div style="margin-left: auto; font-size: 1rem; font-weight: 600; color: var(--primary); padding: 8px 16px; border-radius: 6px;">
                Período: <span style="color: var(--accent);">Jan/{ano_atual}</span> a <span style="color: var(--accent);">{MESES[mes_atual - 1]}/{ano_atual}</span>
            </div>
            
            <button onclick="exportIndicadoresExcel()" 
                    style="background: #10b981; color: white; border: none; padding: 10px 20px; 
                           border-radius: 6px; font-size: 0.95rem; font-weight: bold; cursor: pointer;
                           transition: background 0.2s; display: flex; align-items: center; gap: 0.5rem;">
                📥 Exportar Excel
            </button>
        </div>
        
        <div class="stats-grid" style="margin-bottom: 1.5rem;">
            {_render_resumo_rapido(data_ano, mes_atual)}
        </div>
        
        <div style="font-size: 0.85rem; color: #64748b; padding: 0.8rem 1rem; background: #f1f5f9; border-radius: 6px; margin-bottom: 1.5rem;">
            <strong>Nota:</strong> Os números representam a quantidade de registros gerados no sistema, 
            não representa obrigatoriamente os processos que tiveram andamento dentro das unidades.
        </div>
    </div>
    
    {''.join(_render_categoria(cat_key, cat_info, data_ano, ano_atual, mes_atual) for cat_key, cat_info in CATEGORIAS.items())}
    
    <div class="card">
        <h2 class="card-header">📈 Tendências Mensais</h2>
        <div class="charts-container">
            <div class="chart-box"><canvas id="chartTendenciaWO"></canvas></div>
            <div class="chart-box"><canvas id="chartTendenciaMOC"></canvas></div>
            <div class="chart-box"><canvas id="chartTendenciaPTW"></canvas></div>
            <div class="chart-box"><canvas id="chartTendenciaLOTO"></canvas></div>
        </div>
    </div>
</div>
"""


def _render_resumo_rapido(data_ano, mes_limite):
    cards = ""
    for cat_key, cat_info in CATEGORIAS.items():
        total_cat = 0
        for u, v in data_ano.get(cat_key, {}).items():
            if v:
                for m in range(1, mes_limite + 1):
                    val = v.get(m)
                    if val is not None:
                        total_cat += val
        
        cor = cat_info["cor"]
        cards += f"""
        <div class="stat-card" style="border-bottom: 4px solid {cor};">
            <div class="stat-title">{cat_info['nome']}</div>
            <div class="stat-value" style="color: {cor};">{_fmt(total_cat)}</div>
            <div class="stat-subtitle">Acumulado Jan a {MESES[mes_limite - 1]}</div>
        </div>
        """
    return cards


def _render_categoria(cat_key, cat_info, data_ano, ano_atual, mes_limite):
    unidade_data = data_ano.get(cat_key, {})
    cor = cat_info["cor"]
    
    unidades = [u for u in UNIDADES_ORDER if u in unidade_data]
    meses_lista = [m for m in range(1, mes_limite + 1) if _tem_dados_categoria_mes(unidade_data, m)]
    
    if not meses_lista:
        return f"""
<div class="card">
    <h2 class="card-header" style="border-bottom-color: {cor};">
        {cat_info['nome']} <span style="font-size: 0.85rem; color: #64748b; font-weight: normal;">{cat_info['descricao']} - {ano_atual}</span>
    </h2>
    <p style="color: #64748b; text-align: center; padding: 2rem;">Nenhum dado disponível para o período selecionado.</p>
</div>
"""
    
    tabela = _render_tabela_indicador(unidade_data, unidades, meses_lista)
    
    totais_mes = {}
    for mes in meses_lista:
        totais_mes[mes] = sum(_get_valor(unidade_data[u], mes) for u in unidades)
    
    total_geral = sum(totais_mes.values())
    qtd_meses = len(meses_lista)
    media_geral = round(total_geral / qtd_meses, 1) if qtd_meses else 0
    
    mes_maior = max(totais_mes, key=totais_mes.get) if totais_mes else 1
    mes_menor = min(totais_mes, key=totais_mes.get) if totais_mes else 1

    return f"""
<div class="card">
    <h2 class="card-header" style="border-bottom-color: {cor};">
        {cat_info['nome']} 
        <span style="font-size: 0.85rem; color: #64748b; font-weight: normal;">
            {cat_info['descricao']} - {ano_atual}
        </span>
    </h2>
    
    <div class="stats-grid" style="margin-bottom: 1.5rem;">
        <div class="stat-card" style="border-bottom: 4px solid {cor};">
            <div class="stat-title">Total Acumulado</div>
            <div class="stat-value" style="color: {cor};">{_fmt(total_geral)}</div>
            <div class="stat-subtitle">Jan/{ano_atual} a {MESES[mes_limite - 1]}/{ano_atual}</div>
        </div>
        <div class="stat-card" style="border-bottom: 4px solid {cor};">
            <div class="stat-title">Média Mensal</div>
            <div class="stat-value" style="color: {cor};">{_fmt(media_geral)}</div>
            <div class="stat-subtitle">{qtd_meses} meses analisados</div>
        </div>
        <div class="stat-card" style="border-bottom: 4px solid var(--success);">
            <div class="stat-title">Mês com Maior Registro</div>
            <div class="stat-value" style="color: var(--success); font-size: 1.4rem;">{MESES[mes_maior - 1]}</div>
            <div class="stat-subtitle">{_fmt(totais_mes[mes_maior])} registros</div>
        </div>
        <div class="stat-card" style="border-bottom: 4px solid var(--danger);">
            <div class="stat-title">Mês com Menor Registro</div>
            <div class="stat-value" style="color: var(--danger); font-size: 1.4rem;">{MESES[mes_menor - 1]}</div>
            <div class="stat-subtitle">{_fmt(totais_mes[mes_menor])} registros</div>
        </div>
    </div>
    
    <h3 style="font-size: 1rem; color: var(--secondary); margin-bottom: 1rem;">
        📋 Detalhamento por Unidade
    </h3>
    <div class="table-responsive">
        {tabela}
    </div>
</div>
"""


def _tem_dados_categoria_mes(unidade_data, mes):
    for u, v in unidade_data.items():
        if v and v.get(mes) is not None:
            return True
    return False


def _render_tabela_indicador(unidade_data, unidades_lista, meses_lista):
    rows = []
    
    for unidade in unidades_lista:
        valores = unidade_data[unidade]
        cells = [f'<td><strong>{unidade}</strong></td>']
        
        soma = 0
        count = 0
        for mes in meses_lista:
            v = _get_valor(valores, mes)
            cells.append(f'<td style="text-align: center;">{_fmt(v)}</td>')
            soma += v
            count += 1
        
        media = round(soma / count, 1) if count else 0
        cells.append(f'<td style="text-align: center; font-weight: 600;">{_fmt(media)}</td>')
        cells.append(f'<td style="text-align: center; font-weight: 700; color: var(--primary);">{_fmt(soma)}</td>')
        rows.append(f"<tr>{''.join(cells)}</tr>")
    
    total_cells = ['<td><strong>Total</strong></td>']
    totais_mes = []
    for mes in meses_lista:
        tm = sum(_get_valor(unidade_data[u], mes) for u in unidades_lista)
        total_cells.append(f'<td style="text-align: center; font-weight: 700; background: #f1f5f9;">{_fmt(tm)}</td>')
        totais_mes.append(tm)
    
    media_final = round(sum(totais_mes) / len(totais_mes), 1) if totais_mes else 0
    total_final = sum(totais_mes)
    
    total_cells.append(f'<td style="text-align: center; font-weight: 700; background: #f1f5f9;">{_fmt(media_final)}</td>')
    total_cells.append(f'<td style="text-align: center; font-weight: 700; background: #f1f5f9;">{_fmt(total_final)}</td>')
    rows.append(f"<tr style='border-top: 2px solid var(--accent);'>{''.join(total_cells)}</tr>")

    colunas = ["Unidade"] + [MESES[m - 1] for m in meses_lista] + ["Média", "Total"]
    header = "".join(f'<th style="text-align: center;">{c}</th>' for c in colunas)
    
    return f"""
<table id="tabelaIndicadores">
    <thead><tr>{header}</tr></thead>
    <tbody>{''.join(rows)}</tbody>
</table>
"""


def render_tab_indicadores_scripts():
    INDICADORES_DATA = _get_indicadores_data()
    
    anos_disponiveis = sorted(INDICADORES_DATA.keys())
    
    dados_graficos = {}
    for ano in anos_disponiveis:
        data_ano = INDICADORES_DATA[ano]
        dados_graficos[ano] = {}
        
        for cat_key in CATEGORIAS:
            unidade_data = data_ano.get(cat_key, {})
            unidades = [u for u in UNIDADES_ORDER if u in unidade_data and unidade_data[u] is not None]
            
            meses_set = set()
            for u in unidades:
                v = unidade_data[u]
                if v is not None:
                    meses_set.update(v.keys())
            meses_lista = sorted(meses_set)
            
            totais_mes = []
            rotulos_mes = []
            for mes in meses_lista:
                totais_mes.append(sum(_get_valor(unidade_data[u], mes) for u in unidades))
                rotulos_mes.append(MESES[mes - 1])
            
            dados_graficos[ano][cat_key] = {
                "totais_mes": totais_mes,
                "rotulos_mes": rotulos_mes
            }
    
    dados_json = json.dumps(dados_graficos)
    
    return f"""
<script>
    let indicadorData = {dados_json};
    let indicadorAnoAtual = '{_get_ano_atual()}';
    let indicatorCharts = {{}};

    function changeIndicadorAno(ano) {{
        indicadorAnoAtual = ano;
        
        document.querySelectorAll('.ano-btn').forEach(btn => {{
            btn.style.background = btn.id === 'anoBtn_' + ano ? 'var(--accent)' : 'white';
            btn.style.color = btn.id === 'anoBtn_' + ano ? 'white' : 'var(--secondary)';
        }});

        const url = new URL(window.location.href);
        url.searchParams.set('ano', ano);
        url.searchParams.set('tab', 'indicadores');
        window.location.href = url.toString();
    }}
    
    function changeIndicadorMes() {{
        const mes = document.getElementById('mesSelector').value;
        if (!mes) return;
        
        const url = new URL(window.location.href);
        url.searchParams.set('mes', mes);
        url.searchParams.set('tab', 'indicadores');
        window.location.href = url.toString();
    }}
    
    function exportIndicadoresExcel() {{
        const table = document.getElementById('tabelaIndicadores');
        if (!table) return;
        
        let csv = [];
        const rows = table.querySelectorAll('tr');
        
        for (let i = 0; i < rows.length; i++) {{
            const row = [], cols = rows[i].querySelectorAll('td, th');
            for (let j = 0; j < cols.length; j++) {{
                row.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');
            }}
            csv.push(row.join(';'));
        }}
        
        const csvFile = new Blob(['\\uFEFF' + csv.join('\\n')], {{type: 'text/csv;charset=utf-8;'}});
        const link = document.createElement('a');
        link.download = 'indicadores_maximo_' + indicadorAnoAtual + '.csv';
        link.href = window.URL.createObjectURL(csvFile);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }}

    function initIndicadorCharts() {{
        const data = indicadorData[indicadorAnoAtual];
        if (!data) return;

        const chartCfgs = [
            {{ id: 'chartTendenciaWO', cat: 'work_orders', cor: '#2563eb', label: 'Work Orders' }},
            {{ id: 'chartTendenciaMOC', cat: 'moc', cor: '#f59e0b', label: 'MOC' }},
            {{ id: 'chartTendenciaPTW', cat: 'ptw', cor: '#10b981', label: 'PTWs' }},
            {{ id: 'chartTendenciaLOTO', cat: 'loto', cor: '#ef4444', label: 'LOTO' }}
        ];

        chartCfgs.forEach(cfg => {{
            const canvas = document.getElementById(cfg.id);
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const catData = data[cfg.cat];
            if (!catData || !catData.totais_mes) return;

            if (indicatorCharts[cfg.id]) {{
                indicatorCharts[cfg.id].destroy();
            }}

            indicatorCharts[cfg.id] = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: catData.rotulos_mes,
                    datasets: [{{
                        label: cfg.label + ' ' + indicadorAnoAtual,
                        data: catData.totais_mes,
                        borderColor: cfg.cor,
                        backgroundColor: cfg.cor + '20',
                        borderWidth: 3,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        title: {{ display: true, text: cfg.label, font: {{ size: 13 }} }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Quantidade' }} }},
                        x: {{ title: {{ display: true, text: 'Mês' }} }}
                    }}
                }}
            }});
        }});
    }}

    // Renderiza gráficos quando a aba ficar visível
    function renderIndicadorCharts() {{
        const tab = document.getElementById('tab-indicadores');
        if (tab && (tab.style.display === 'block' || tab.classList.contains('active'))) {{
            initIndicadorCharts();
        }}
    }}
    
    // Patch na função openTab para renderizar gráficos
    document.addEventListener('DOMContentLoaded', function() {{
        // Guarda referência original
        const originalOpenTab = window.openTab;
        
        // Override para adicionar renderização de gráficos
        window.openTab = function(evt, tabName) {{
            originalOpenTab(evt, tabName);
            if (tabName === 'tab-indicadores') {{
                setTimeout(renderIndicadorCharts, 200);
            }}
        }};
    }});
</script>
"""

# Script para abrir aba correta via URL params
def render_tab_indicadores_init():
    """Script para abrir a aba correta baseado no parâmetro ?tab=indicadores"""
    return """
<script>
    (function() {
        const urlParams = new URLSearchParams(window.location.search);
        const tabParam = urlParams.get('tab');
        if (tabParam === 'indicadores') {
            const tabBtn = document.querySelector('button[onclick*="tab-indicadores"]');
            if (tabBtn) {
                const evt = new MouseEvent('click', { bubbles: true });
                tabBtn.dispatchEvent(evt);
            }
        }
    })();
</script>
"""