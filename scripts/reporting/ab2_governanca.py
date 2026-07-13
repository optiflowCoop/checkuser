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
        f'<p class="card-footnote">'
        f'Mostrando {_br_number(shown)} de {_br_number(total)} registros nesta tabela.{hint} '
        f'Lista completa no relatório Excel.</p>'
    )


def render_allocation_summary(allocation_data):
    """Renderiza o resumo do saneamento de alocação (Maximo 9) na Aba 2."""
    if not allocation_data:
        return ""
    stats = allocation_data['stats']
    return f"""
        <div class="card">
            <h2 class="card-header">Saneamento de Alocação (Maximo 9)</h2>
            <p class="card-desc">
                Histórico de login dos últimos 90 dias por ambiente, usado para sugerir onde criar a conta de
                cada usuário. Janela: {stats['window_start']} a {stats['window_end']}.
            </p>
            <div class="stats-grid" style="margin-bottom: 1rem;">
                <div class="stat-card border-accent">
                    <div class="stat-value">{_br_number(stats['total_users'])}</div>
                    <div class="stat-title">Usuários Analisados</div>
                    <div class="stat-subtitle">Base + inativos</div>
                </div>
                <div class="stat-card border-success">
                    <div class="stat-value">{_br_number(stats['users_with_logins_90d'])}</div>
                    <div class="stat-title">Com Login 90d</div>
                    <div class="stat-subtitle">Uso recente</div>
                </div>
                <div class="stat-card border-neutral">
                    <div class="stat-value">{_br_number(stats['users_inactive'])}</div>
                    <div class="stat-title">Inativos</div>
                    <div class="stat-subtitle">No Maximo</div>
                </div>
                <div class="stat-card border-warning">
                    <div class="stat-value">{_br_number(stats.get('users_status_desconhecido', 0))}</div>
                    <div class="stat-title">STATUS Ausente</div>
                    <div class="stat-subtitle">Extração incompleta — revisar</div>
                </div>
                <div class="stat-card border-secondary">
                    <div class="stat-value">{_br_number(stats['users_multi_env'])}</div>
                    <div class="stat-title">Multi-Ambiente</div>
                    <div class="stat-subtitle">Conta em &gt;1 unidade</div>
                </div>
                <div class="stat-card border-warning">
                    <div class="stat-value">{_br_number(stats['total_suggested_accounts'])}</div>
                    <div class="stat-title">Contas Sugeridas</div>
                    <div class="stat-subtitle">Soma das alocações</div>
                </div>
                <div class="stat-card border-danger">
                    <div class="stat-value">{stats['min_secundario']}</div>
                    <div class="stat-title">Min. Acessos</div>
                    <div class="stat-subtitle">Ambiente secundário</div>
                </div>
            </div>
            <p class="card-footnote">
                Ambiente de alocação = <em>locationsite</em> (persongroupview) &gt; DEFSITE &gt; ENV_DB. Ambientes
                secundários exigem ao menos {stats['min_secundario']} acessos nos últimos 90 dias para sugerir
                criação de conta. Usuários com STATUS ausente na extração NÃO são contados como ativos nem
                inativos — aparecem como REVISAR_STATUS até confirmação manual. Detalhamento completo na aba 5
                (Detalhamento de Alocação) e no Excel (aba 21/22).
            </p>
        </div>
    """


def render_security_audit_summary(security_audit_data):
    """Renderiza o resumo da auditoria de segregação de funções (Emissor x
    Aprovador em Compras) na Aba 2 — Governança."""
    if not security_audit_data:
        return ""
    stats = security_audit_data['stats']
    by_app = stats.get('distinct_users_active_by_app', {})
    app_badges = ''.join(
        f'<span style="background:var(--danger-bg,#fef2f2); color:var(--danger); border:1px solid var(--danger); '
        f'border-radius:6px; padding:0.2rem 0.6rem; font-size:0.8rem; margin-right:0.4rem;">'
        f'{app} · {_br_number(qtd)}</span>'
        for app, qtd in sorted(by_app.items())
    )
    return f"""
        <div class="card">
            <h2 class="card-header">Segregação de Funções — Emissor x Aprovador (Compras)</h2>
            <p class="card-desc">
                Grupos ou usuários com permissão simultânea de criar/submeter E aprovar Requisição (PR), Ordem de
                Compra (PO) ou Requisição Simplificada. Fonte: APPLICATIONAUTH nos 7 ambientes. MAXADMIN é tratado
                à parte, pois acesso total é esperado nesse grupo.
            </p>
            <div class="stats-grid" style="margin-bottom: 1rem;">
                <div class="stat-card stat-card-danger">
                    <div class="stat-value">{_br_number(stats['total_group_conflicts'])}</div>
                    <div class="stat-title">Grupos Conflitantes</div>
                    <div class="stat-subtitle">Nível 1 — falha estrutural no grupo</div>
                </div>
                <div class="stat-card stat-card-danger">
                    <div class="stat-value">{_br_number(stats['distinct_users_active'])}</div>
                    <div class="stat-title">Pessoas Ativas Afetadas</div>
                    <div class="stat-subtitle">Nível 2 — têm o conflito hoje</div>
                </div>
                <div class="stat-card border-warning">
                    <div class="stat-value">{_br_number(stats['total_user_conflicts_grupos_diferentes'])}</div>
                    <div class="stat-title">Por Combinação de Grupos</div>
                    <div class="stat-subtitle">Emissor + aprovador em grupos distintos</div>
                </div>
                <div class="stat-card border-neutral">
                    <div class="stat-value">{_br_number(stats['total_maxadmin_users'])}</div>
                    <div class="stat-title">Usuários MAXADMIN</div>
                    <div class="stat-subtitle">Acesso total — revisar necessidade</div>
                </div>
            </div>
            <div style="margin-bottom: 0.75rem;">{app_badges}</div>
            <p class="card-footnote">
                Nível 1 (mais crítico): o próprio grupo já concede emissão e aprovação — qualquer pessoa alocada
                nele nasce com o conflito. Nível 2: a pessoa não está em nenhum grupo conflitante isoladamente, mas
                acumula um grupo emissor e um grupo aprovador diferentes. Tabela completa e lista de pessoas
                afetadas na aba Segregação de Funções.
            </p>
        </div>
    """


def render_tab_gov(gov_tables, allocation_data=None, security_audit_data=None):
    """Renders the 'Governança & Saneamento' tab content."""
    alloc_html = render_allocation_summary(allocation_data) if allocation_data else ""
    sod_summary_html = render_security_audit_summary(security_audit_data)
    return f"""
    <div id="tab-gov" class="container tab-content">
        <div class="card">
            <h3 style="margin-top: 0;">Filtro Interativo de Risco Lógico</h3>
            <p class="card-desc">Cruzamento de identidades entre bases (mesmo USERID ou LOGINID em ambientes diferentes),
            classificado por hipótese de risco.</p>
            <div class="search-container">
                <input type="text" id="searchGov" class="search-bar" onkeyup="filterGovTable()" placeholder="Pesquisar por ID, Nome, Email...">
                <select id="selGovDec" class="filter-select" onchange="filterGovTable()">
                    <option value="">Todas as Decisões</option>
                    <option value="PESSOAS DIFERENTES">ALTO - PESSOAS DIFERENTES</option>
                    <option value="REQUER REVISÃO">MÉDIO - REQUER REVISÃO</option>
                    <option value="POSSÍVEL MESMA PESSOA">BAIXO - POSSÍVEL MESMA PESSOA</option>
                </select>
            </div>
        </div>
        {sod_summary_html}
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
                <h2 style="margin:0; font-size: 1.4rem; font-weight: 600;">Fila de Resolução Consolidada</h2>
                <button class="btn-export" onclick="exportTableToCSV('table-worklist', 'Backlog_Governanca.csv')">Exportar Backlog (linhas visíveis)</button>
            </div>
            {render_table(['ID Bruto', 'Nome', 'Hipótese Sistêmica', 'Decisão / Ação'], gov_tables['worklist_rows'], 'table-worklist', 'gov-table')}
            {_truncation_note(len(gov_tables['worklist_rows']), gov_tables.get('worklist_total', len(gov_tables['worklist_rows'])), 'Ver aba Excel <strong>6_FilaSaneamento</strong>.')}
        </div>
    </div>
    """
