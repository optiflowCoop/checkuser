# scripts/reporting/ab2_governanca.py
from .html_helpers import render_table, fmt_br


def _br_number(n):
    """Formata número no padrão brasileiro: 1.447 ao invés de 1,447"""
    return f"{n:,}".replace(',', '.')


def _truncation_note(shown, total, csv_hint=''):
    """
    Aviso visível quando a tabela do dashboard mostra só uma amostra do total real
    (ex.: 200 de 1.582 linhas). Sem isto, o corte fica silencioso e parece que a
    tabela contém todos os registros. O CSV completo está disponível no Excel.
    """
    if total <= shown:
        return ''
    hint = f' {csv_hint}' if csv_hint else ''
    return (
        f'<p style="font-size: 0.85rem; color: #b45309; background: #fffbeb; '
        f'border: 1px solid #fde68a; border-radius: 6px; padding: 0.5rem 0.75rem; margin: 0.5rem 0 0 0;">'
        f'⚠️ Mostrando {_br_number(shown)} de {_br_number(total)} registros nesta tabela.{hint} '
        f'A lista completa está no relatório Excel.</p>'
    )


def render_allocation_summary(allocation_data):
    """Renderiza o resumo do saneamento de alocação (Maximo 9) na Aba 2."""
    if not allocation_data:
        return ""
    stats = allocation_data['stats']
    return f"""
        <div class="card" style="border-left: 4px solid #7c3aed; background-image: linear-gradient(to right, #ffffff, #f5f3ff);">
            <div class="card-header" style="border:none; margin-bottom:0.5rem;">
                <div>
                    <h2 style="margin:0; color:#7c3aed;">🧭 Saneamento de Alocação (Maximo 9) — Resumo</h2>
                    <p style="font-size: 0.9rem; color: #64748b; font-weight: normal; margin-top: 4px;">
                        Histórico de logins dos últimos 90 dias por ambiente e sugestão de onde criar a conta do usuário.
                        Janela: {stats['window_start']} a {stats['window_end']}.
                    </p>
                </div>
            </div>
            <div class="stats-grid" style="margin-bottom: 1rem;">
                <div class="stat-card" style="border-bottom: 4px solid var(--accent);">
                    <div class="stat-value">{_br_number(stats['total_users'])}</div>
                    <div class="stat-title">Usuários Analisados</div>
                    <div class="stat-subtitle">Base + inativos</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--success);">
                    <div class="stat-value">{_br_number(stats['users_with_logins_90d'])}</div>
                    <div class="stat-title">Com Login 90d</div>
                    <div class="stat-subtitle">Uso recente</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--neutral);">
                    <div class="stat-value">{_br_number(stats['users_inactive'])}</div>
                    <div class="stat-title">Inativos</div>
                    <div class="stat-subtitle">No Maximo</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid #7c3aed;">
                    <div class="stat-value">{_br_number(stats['users_multi_env'])}</div>
                    <div class="stat-title">Multi-Ambiente</div>
                    <div class="stat-subtitle">Conta em >1 unidade</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--warning);">
                    <div class="stat-value">{_br_number(stats['total_suggested_accounts'])}</div>
                    <div class="stat-title">Contas Sugeridas</div>
                    <div class="stat-subtitle">Soma das alocações</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--danger);">
                    <div class="stat-value">{stats['min_secundario']}</div>
                    <div class="stat-title">Min. Acessos</div>
                    <div class="stat-subtitle">Ambiente secundário</div>
                </div>
            </div>
            <p style="font-size: 0.85rem; color: #64748b;">
                <strong>Regra:</strong> ambiente de alocação = <em>locationsite</em> (persongroupview) > DEFSITE > ENV_DB.
                Ambientes secundários exigem ao menos <strong>{stats['min_secundario']}</strong> acessos nos últimos 90 dias para sugerir criação de conta.
                Veja o detalhamento completo na <strong>Aba 5 (Detalhamento de Alocação)</strong> e no Excel (aba 21/22).
            </p>
        </div>
    """


def render_tab_gov(gov_tables, allocation_data=None):
    """Renders the 'Governança & Saneamento' tab content."""
    alloc_html = render_allocation_summary(allocation_data) if allocation_data else ""
    return f"""
    <div id="tab-gov" class="container tab-content">
        <div class="card" style="background-color: #ffffff; border-color: #cbd5e1;">
            <h3 style="margin-top: 0; color: var(--primary);">🔍 Filtro Interativo de Risco Lógico</h3>
            <div class="search-container">
                <input type="text" id="searchGov" class="search-bar" onkeyup="filterGovTable()" placeholder="Pesquisar por ID, Nome, Email...">
                <select id="selGovDec" class="filter-select" onchange="filterGovTable()">
                    <option value="">⚖️ Todas as Decisões</option>
                    <option value="PESSOAS DIFERENTES">🔴 ALTO - PESSOAS DIFERENTES</option>
                    <option value="REQUER REVISÃO">🟡 MÉDIO - REQUER REVISÃO</option>
                    <option value="POSSÍVEL MESMA PESSOA">🟢 BAIXO - POSSÍVEL MESMA PESSOA</option>
                </select>
            </div>
        </div>
        {alloc_html}
        <div class="card">
            <h2 class="card-header">Top Divergências de Segurança (Matriz Base vs Sonda)</h2>
            <div class="type-analysis-grid">{gov_tables['title_divergence_html']}</div>
        </div>
        <div class="card">
            <h2 class="card-header">Conflitos de Multi-Ambiente (Cross-Env)</h2>
            {render_table(['USERID', 'Bases Encontradas', 'Nomes de Exibição', 'Conclusão'], gov_tables['cross_env_rows'], 'table-cross-env', 'gov-table')}
            {_truncation_note(len(gov_tables['cross_env_rows']), gov_tables.get('cross_env_total', len(gov_tables['cross_env_rows'])), 'Ver aba Excel <strong>4_ReusoUSERID_CrossEnv</strong>.')}
        </div>
        <div class="card">
            <h2 class="card-header">Colisões de Active Directory (LOGINID)</h2>
            {render_table(['LOGINID AD', 'Bases', 'USERIDs', 'Nomes Cadastrados'], gov_tables['login_conflicts_rows'], 'table-login-conflicts', 'gov-table')}
            {_truncation_note(len(gov_tables['login_conflicts_rows']), gov_tables.get('login_conflicts_total', len(gov_tables['login_conflicts_rows'])), 'Ver aba Excel <strong>5_ConflitosLoginID</strong>.')}
        </div>
        <div class="card">
            <div style="display:flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); margin-bottom: 1.5rem; padding-bottom: 0.75rem;">
                <h2 style="margin:0; color: var(--secondary); font-size: 1.4rem; font-weight: 600;">Fila de Resolução Consolidada</h2>
                <button class="btn-export" style="background-color: var(--secondary);" onclick="exportTableToCSV('table-worklist', 'Backlog_Governanca.csv')">Exportar Backlog (linhas visíveis)</button>
            </div>
            {render_table(['ID Bruto', 'Nome', 'Hipótese Sistêmica', 'Decisão / Ação'], gov_tables['worklist_rows'], 'table-worklist', 'gov-table')}
            {_truncation_note(len(gov_tables['worklist_rows']), gov_tables.get('worklist_total', len(gov_tables['worklist_rows'])), 'Ver aba Excel <strong>6_FilaSaneamento</strong>.')}
        </div>
    </div>
    """
