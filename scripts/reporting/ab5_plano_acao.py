# scripts/reporting/ab5_plano_acao.py
from .html_helpers import render_table


def render_tab_tabela(app_points_rows):
    """Renders the 'Plano de Ação' tab content."""
    return f"""
    <div id="tab-tabela" class="container tab-content">
        <div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">
            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: var(--primary);">📋 Plano de Ação Mestre e Fatores de Escala</h3>
                <button class="btn-export" onclick="exportTableToCSV('table-apppoints', 'Planejamento_Capacity_Maximo.csv')">
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 4px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                    Exportar para Excel (CSV)
                </button>
            </div>
            <div class="search-container">
                <input type="text" id="searchAppPoints" class="search-bar" onkeyup="filterAppPoints()" placeholder="Pesquisar por ID, Nome, Cargo...">
                <select id="filterRec" class="filter-select" onchange="filterAppPoints()">
                    <option value="">💡 Filtro de Ação</option>
                    <option value="INATIVO">🔴 Inativos (>90d)</option>
                    <option value="DOWNGRADE">🟡 Requer Downgrade (Premium p/ Base)</option>
                    <option value="P/ CONCURRENT">🔵 Escala Offshore (Concurrent)</option>
                    <option value="CONFIRMADO">🟢 Autorizado Fixo (Authorized)</option>
                </select>
                <select id="filterEnt" class="filter-select" onchange="filterAppPoints()">
                    <option value="">🔰 Todos Níveis (Entitlement)</option>
                    <option value="PREMIUM">Premium</option>
                    <option value="BASE">Base</option>
                </select>
            </div>
            {render_table(['USERID', 'Nome', 'Recomendação', 'Entitlement', 'Licença To-Be', 'AppPoints Ref.', 'Fator Analytics', 'Logins 90d', 'Unidade', 'Cargo'], app_points_rows, 'table-apppoints', 'filterable-app-table')}
        </div>
    </div>
    """