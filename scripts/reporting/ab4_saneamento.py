# scripts/reporting/ab4_saneamento.py
from .html_helpers import fmt_br


def _br_number(n):
    """Formata número no padrão brasileiro: 1.447 ao invés de 1,447"""
    return f"{n:,}".replace(',', '.')


def _ad_status_badge(value):
    """Converte status AD (bool/string) em badge HTML com contraste consistente."""
    if isinstance(value, bool):
        return '<span class="badge badge-success">Ativo</span>' if value else '<span class="badge badge-danger">Inativo</span>'

    if value is None:
        return '<span class="badge badge-neutral">N/A</span>'

    value_str = str(value).strip().upper()
    if value_str in {'ATIVO', 'ACTIVE', 'TRUE', '1', 'ENABLED'}:
        return '<span class="badge badge-success">Ativo</span>'
    if value_str in {'INATIVO', 'INACTIVE', 'FALSE', '0', 'DISABLED'}:
        return '<span class="badge badge-danger">Inativo</span>'

    return '<span class="badge badge-neutral">N/A</span>'


def render_tab_saneamento(sanity_data):
    """
    Renders the 'Saneamento de Identidades' tab content.
    Uses pre-computed sanity analysis data from sanity_analyzer.py.
    """
    if not sanity_data:
        return """
    <div id="tab-saneamento" class="container tab-content">
        <div class="card">
            <h2>Saneamento de Identidades - AD vs Maximo</h2>
            <p>Nenhum dado de saneamento disponível.</p>
        </div>
    </div>
    """

    stats = sanity_data['stats']
    analises = sanity_data['analises']

    return f"""
    <div id="tab-saneamento" class="container tab-content">
        <div class="card">
            <h2 class="card-header">Saneamento de Identidades - AD vs Maximo</h2>
            <p class="card-desc">Comparação entre usuários do Active Directory e Maximo para identificação de inconsistências.</p>

            <div class="stats-grid" style="margin-bottom: 1rem;">
                <div class="stat-card border-accent" onclick="filterByType('all')" id="card-all" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(stats['total_ad'])}</div>
                    <div class="stat-title">Usuários no AD</div>
                    <div class="stat-subtitle">Fonte da verdade</div>
                </div>
                <div class="stat-card border-success" onclick="filterByType('match')" id="card-match" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(stats['match_email'])}</div>
                    <div class="stat-title">Match por Email</div>
                    <div class="stat-subtitle">Mesmo email em ambos</div>
                </div>
                <div class="stat-card border-danger" onclick="filterByType('ad_only')" id="card-ad_only" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(stats['only_ad'])}</div>
                    <div class="stat-title">Apenas no AD</div>
                    <div class="stat-subtitle">Sem correspondência no Maximo</div>
                </div>
                <div class="stat-card border-warning" onclick="filterByType('maximo_only')" id="card-maximo_only" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(stats['only_maximo'])}</div>
                    <div class="stat-title">Apenas no Maximo</div>
                    <div class="stat-subtitle">Sem correspondência no AD</div>
                </div>
                <div class="stat-card border-secondary" onclick="filterByType('name_divergence')" id="card-name_divergence" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(stats['name_divergences'])}</div>
                    <div class="stat-title">Divergências de Nome</div>
                    <div class="stat-subtitle">Mesmo email, nomes diferentes</div>
                </div>
                <div class="stat-card border-neutral" onclick="filterByType('multi_userid')" id="card-multi_userid" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(stats['multi_userid'])}</div>
                    <div class="stat-title">Múltiplos USERIDs</div>
                    <div class="stat-subtitle">Mesmo email, IDs diferentes</div>
                </div>
                <div class="stat-card border-primary" onclick="filterByType('prefix_match')" id="card-prefix_match" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(stats['prefix_match'])}</div>
                    <div class="stat-title">Match por USERID</div>
                    <div class="stat-subtitle">Prefixos correspondem</div>
                </div>
                <div class="stat-card border-accent" onclick="filterByType('no_match')" id="card-no_match" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(stats['no_match'])}</div>
                    <div class="stat-title">Sem Match</div>
                    <div class="stat-subtitle">No Maximo</div>
                </div>
                <div class="stat-card border-neutral" title="Usuários do Maximo sem email cadastrado, mas cujo USERID bate com o prefixo de um email do AD. Detalhamento completo na aba Excel 14_Maximo_Sem_Email_Match (não replicado nesta tabela por volume).">
                    <div class="stat-value">{_br_number(stats.get('maximo_sem_email_match', 0))}</div>
                    <div class="stat-title">Maximo Sem Email, c/ Match no AD</div>
                    <div class="stat-subtitle">Ver aba Excel 14</div>
                </div>
                <div class="stat-card stat-card-danger" onclick="filterByType('ad_disabled_ativo')" id="card-ad_disabled_ativo" style="cursor: pointer;">
                    <div class="stat-value" style="color: var(--danger);">{_br_number(stats.get('ad_disabled_ativos_maximo', 0))}</div>
                    <div class="stat-title">AD Desabilitado + Maximo Ativo</div>
                    <div class="stat-subtitle">Risco de auditoria</div>
                </div>
            </div>

            <div class="search-container">
                <input type="text" id="searchSaneamento" class="search-bar" placeholder="Buscar por nome ou e-mail..." onkeyup="filterSaneamentoTable()">
                <select id="filterTipo" class="filter-select" onchange="filterSaneamentoTable()">
                    <option value="">Todos os Tipos</option>
                    <option value="ad_only">Apenas no AD</option>
                    <option value="maximo_only">Apenas no Maximo</option>
                    <option value="match">Match Perfeito</option>
                    <option value="ad_disabled_ativo">AD Desabilitado + Maximo Ativo</option>
                </select>
                <button class="btn-export" onclick="filterByType('all')">Limpar Filtro</button>
                <button class="btn-export" onclick="exportSaneamentoCSV()">Exportar CSV</button>
            </div>

            <p class="card-footnote">
                Cada categoria abaixo mostra até 100–200 registros de amostra (os totais reais estão nos cartões acima). Para a lista completa de qualquer categoria, use o relatório Excel (abas 10 a 14).
            </p>

            <div class="table-responsive">
                <table id="table-saneamento">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>E-mail</th>
                            <th>Tipo</th>
                            <th>Status AD</th>
                            <th>Grupos AD</th>
                            <th>Ação Recomendada</th>
                        </tr>
                    </thead>
                    <tbody>
                        {_render_saneamento_rows(analises, sanity_data.get('ad_by_email', {}))}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Seção de Auditoria: AD Desabilitado + Maximo Ativo -->
        {_render_auditoria_desabilitados(analises.get('ad_disabled_ativos_maximo', []))}
        
        <div class="card">
            <h2 class="card-header">Regras de Saneamento</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                <div class="legend-box">
                    <h3>Remover do AD</h3>
                    <ul class="legend-list">
                        <li>Usuário inativo há mais de 90 dias</li>
                        <li>Conta desabilitada (Enabled = False)</li>
                        <li>Sem acesso a sistemas críticos</li>
                        <li>Grupos apenas de acesso genérico</li>
                    </ul>
                </div>
                <div class="legend-box">
                    <h3>Revisar</h3>
                    <ul class="legend-list">
                        <li>Usuário com múltiplos grupos</li>
                        <li>Licenças Office 365 E3/E1</li>
                        <li>Acesso a módulos críticos O&G</li>
                        <li>Contas de parceiros/terceiros</li>
                    </ul>
                </div>
                <div class="legend-box">
                    <h3>Manter</h3>
                    <ul class="legend-list">
                        <li>Usuários ativos com login recente</li>
                        <li>Acesso a sistemas críticos (Maximo, PTW)</li>
                        <li>Grupos de segurança específicos</li>
                        <li>Licenças Premium Auth/Conc</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """


def _render_saneamento_rows(analises, ad_by_email):
    """Renderiza as linhas da tabela de saneamento usando dados pré-computados."""
    rows = []
    
    # 1. Divergências de Nome (prioridade alta) - data-tipo="name_divergence"
    for d in analises['name_divergences'][:200]:
        status_badge = _ad_status_badge(d.get('ad_enabled'))
        acao = '<span class="badge badge-critical">Divergência Nome</span>'
        
        rows.append(f"""
            <tr data-tipo="name_divergence" data-email="{d['email'].lower()}">
                <td>{d['ad_displayname']}</td>
                <td>{d['email']}</td>
                <td><span class="badge badge-critical">Nome Divergente</span></td>
                <td>{status_badge}</td>
                <td>{d['ad_groups_count']} grupos</td>
                <td>{acao}<br><small>Maximo: {d['maximo_names'][:80]}</small></td>
            </tr>
        """)
    
    # 2. Múltiplos USERIDs - data-tipo="multi_userid"
    for d in analises['multi_userid'][:100]:
        status_badge = _ad_status_badge(d.get('ad_enabled', True))
        acao = '<span class="badge badge-high">Múltiplos IDs</span>'
        
        rows.append(f"""
            <tr data-tipo="multi_userid" data-email="{d['email'].lower()}">
                <td>{d['ad_displayname']}</td>
                <td>{d['email']}</td>
                <td><span class="badge badge-high">Múltiplos USERIDs</span></td>
                <td>{status_badge}</td>
                <td>{d.get('ad_groups_count', 'N/A')}</td>
                <td>{acao}<br><small>IDs: {d['userids'][:60]}</small></td>
            </tr>
        """)
    
    # 3. Apenas no AD (only_ad) - data-tipo="ad_only" (corresponde ao card "Apenas no AD")
    # Usa os mesmos dados de no_match + prefix_match para totalizar only_ad
    for d in analises['no_match'][:200]:
        status_badge = _ad_status_badge(d.get('ad_enabled'))
        
        if not d['ad_enabled']:
            acao = '<span class="badge badge-danger">Remover</span>'
        elif d['ad_groups_count'] > 20:
            acao = '<span class="badge badge-warning">Revisar Grupos</span>'
        else:
            acao = '<span class="badge badge-neutral">Analisar</span>'
        
        rows.append(f"""
            <tr data-tipo="ad_only" data-email="{d['email'].lower()}">
                <td>{d['ad_displayname']}</td>
                <td>{d['email']}</td>
                <td><span class="badge badge-danger">Apenas AD</span></td>
                <td>{status_badge}</td>
                <td>{d['ad_groups_count']} grupos</td>
                <td>{acao}</td>
            </tr>
        """)
    
    # 3b. Sem Match no Maximo - data-tipo="no_match" (corresponde ao card "Sem Match")
    for d in analises['no_match'][:200]:
        status_badge = _ad_status_badge(d.get('ad_enabled'))
        
        if not d['ad_enabled']:
            acao = '<span class="badge badge-danger">Remover</span>'
        elif d['ad_groups_count'] > 20:
            acao = '<span class="badge badge-warning">Revisar Grupos</span>'
        else:
            acao = '<span class="badge badge-neutral">Analisar</span>'
        
        rows.append(f"""
            <tr data-tipo="no_match" data-email="{d['email'].lower()}">
                <td>{d['ad_displayname']}</td>
                <td>{d['email']}</td>
                <td><span class="badge badge-danger">Apenas AD</span></td>
                <td>{status_badge}</td>
                <td>{d['ad_groups_count']} grupos</td>
                <td>{acao}</td>
            </tr>
        """)
    
    # 4. Match por Email - data-tipo="match" (corresponde ao card "Match por Email")
    for email in analises['match_emails'][:100]:
        ad_user = ad_by_email.get(email, {})
        nome = ad_user.get('displayname', 'N/A') if ad_user else 'N/A'
        enabled = ad_user.get('enabled', True) if ad_user else True
        groups_count = ad_user.get('groups_count', 0) if ad_user else 0
        
        status_badge = _ad_status_badge(enabled)
        acao = '<span class="badge badge-success">OK</span>'
        
        rows.append(f"""
            <tr data-tipo="match" data-email="{email.lower()}">
                <td>{nome}</td>
                <td>{email}</td>
                <td><span class="badge badge-success">Match Email</span></td>
                <td>{status_badge}</td>
                <td>{groups_count} grupos</td>
                <td>{acao}</td>
            </tr>
        """)
    
    # 5. Apenas no Maximo - data-tipo="maximo_only"
    for d in analises['only_maximo_emails'][:100]:
        rows.append(f"""
            <tr data-tipo="maximo_only" data-email="{d.lower()}">
                <td>N/A</td>
                <td>{d}</td>
                <td><span class="badge badge-warning">Apenas Maximo</span></td>
                <td><span class="badge badge-neutral">N/A</span></td>
                <td>N/A</td>
                <td><span class="badge badge-warning">Verificar AD</span></td>
            </tr>
        """)
    
    # 6. Match por Prefixo (USERID) - data-tipo="prefix_match"
    for d in analises['prefix_match'][:100]:
        status_badge = _ad_status_badge(d.get('ad_enabled'))
        acao = '<span class="badge badge-success">Match OK</span>'
        
        rows.append(f"""
            <tr data-tipo="prefix_match" data-email="{d['email'].lower()}">
                <td>{d['ad_displayname']}</td>
                <td>{d['email']}</td>
                <td><span class="badge badge-success">Match USERID</span></td>
                <td>{status_badge}</td>
                <td>{d['ad_groups_count']} grupos</td>
                <td>{acao}<br><small>USERID: {d['maximo_userid']}</small></td>
            </tr>
        """)
    
    return '\n'.join(rows)


def _render_ambientes_com_status(envs_ativos_text, envs_total_text):
    """
    Renderiza cada ambiente do Maximo (dos 7 possíveis) com seu status individual —
    Ativo para quem está em envs_ativos_text, Inativo para os demais em envs_total_text.
    Isso deixa explícito o caso de "desativado em 1 ambiente mas ainda ativo em outro".
    """
    total_list = [e.strip() for e in str(envs_total_text or '').split('|') if e.strip()]
    ativos_set = {e.strip() for e in str(envs_ativos_text or '').split('|') if e.strip()}

    if not total_list:
        # Fallback: sem info de total, mostra só os ativos (caso de dados antigos)
        total_list = sorted(ativos_set)

    detalhes = []
    for env in total_list:
        if env in ativos_set:
            badge = '<span class="badge badge-success" style="margin: 2px;">Ativo</span>'
        else:
            badge = '<span class="badge badge-danger" style="margin: 2px;">Inativo</span>'
        detalhes.append(f"{env} {badge}")

    return '<div style="line-height: 1.8;">' + '<br>'.join(detalhes) + '</div>'


def _render_auditoria_desabilitados(ad_disabled_ativos_maximo):
    """Renderiza seção especial de auditoria: usuários desativados no AD mas ativos no Maximo."""
    if not ad_disabled_ativos_maximo:
        return ""
    
    rows = []
    for d in ad_disabled_ativos_maximo:
        # Destacar status do Maximo
        status_maximo = d['maximo_statuses'] if d.get('maximo_statuses') else 'INACTIVE'
        status_badge = '<span class="badge badge-success">Ativo</span>' if 'ACTIVE' in status_maximo.upper() else '<span class="badge badge-warning">Inativo</span>'
        
        # Badge do tipo de match
        match_type = d.get('match_type', 'EMAIL')
        if match_type == 'EMAIL':
            match_badge = '<span class="badge badge-success">E-mail</span>'
        elif match_type == 'USERID':
            match_badge = '<span class="badge badge-warning">USERID</span>'
        else:
            match_badge = f'<span class="badge badge-neutral">Nome (Score)</span>'
        
        # Status AD (sempre Inativo, mas usar o valor real do dicionário)
        ad_status_badge = _ad_status_badge(d.get('ad_enabled', False))
        
        rows.append(f"""
            <tr data-tipo="ad_disabled_ativo" data-email="{d['email'].lower()}">
                <td><strong>{d['ad_displayname']}</strong><br><small>{d['ad_givenname']} {d['ad_surname']}</small></td>
                <td>{d['email']}</td>
                <td>{ad_status_badge}</td>
                <td>{status_badge}</td>
                <td>{d['ad_groups_count']} grupos</td>
                <td>
                    {match_badge}<br>
                    <span class="badge badge-critical">Ação Requerida</span><br>
                    <small><strong>USERIDs:</strong> {d['maximo_userids'][:60]}</small><br>
                    <small><strong>Ambientes ({d.get('qtd_envs_ativos_de_total', '?')} ativos):</strong></small>
                    {_render_ambientes_com_status(d['maximo_envs'], d.get('maximo_envs_total', d['maximo_envs']))}
                </td>
            </tr>
        """)

    return f"""
    <div id="card-auditoria" class="card stat-card-danger" style="margin-top: 2rem;">
        <h2 class="card-header">Auditoria: Usuários Desativados no AD mas com Acesso no Maximo</h2>
        <p class="card-desc">
            Foram identificados <strong>{len(ad_disabled_ativos_maximo)} usuários</strong> com contas desativadas no
            Active Directory mas que ainda possuem acesso ativo no Maximo. Representam risco de auditoria e devem
            ser removidos do Maximo.
        </p>

        <p class="card-footnote">
            <strong>Legenda — Tipo Match (confiança do vínculo AD ↔ Maximo):</strong><br>
            <span class="badge badge-success">E-mail</span> confirmado pelo mesmo e-mail cadastrado nos dois sistemas (alta confiança) &nbsp;|&nbsp;
            <span class="badge badge-warning">USERID</span> prefixo do e-mail do AD bate exatamente com um USERID do Maximo, com nome consistente (confiança média) &nbsp;|&nbsp;
            <span class="badge badge-neutral">Nome (Score)</span> vínculo por similaridade de nome, sem e-mail/USERID em comum (confiança mais baixa — revisar manualmente antes de agir).
            A coluna "Ambientes" mostra em quantos dos ambientes onde a pessoa tem conta ela ainda está ativa.
        </p>

        <div class="table-responsive">
            <table id="table-auditoria" style="width: 100%;">
                <thead>
                    <tr>
                        <th>Nome Completo</th>
                        <th>E-mail</th>
                        <th>Status AD</th>
                        <th>Status Maximo</th>
                        <th>Grupos AD</th>
                        <th>Tipo Match</th>
                        <th>Detalhes Maximo</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>

        <p class="card-footnote">
            <strong>Recomendação:</strong> verificar imediatamente os {len(ad_disabled_ativos_maximo)} usuários listados acima.
            Ações: 1) desativar contas no Maximo; 2) remover grupos de acesso; 3) documentar a remoção para compliance.
        </p>
    </div>
    """


def render_tab_saneamento_scripts():
    """Retorna JavaScript específico para a aba de saneamento."""
    return """
    <script>
        let currentFilter = 'all';
        
        function filterByType(type) {
            currentFilter = type;
            
            // Atualizar visual dos cards
            document.querySelectorAll('.stat-card').forEach(card => {
                card.style.transform = '';
                card.style.boxShadow = '';
            });
            
            if (type !== 'all') {
                const activeCard = document.getElementById('card-' + type);
                if (activeCard) {
                    activeCard.style.transform = 'scale(1.05)';
                    activeCard.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';
                }
            }
            
            // Filtrar tabela
            filterSaneamentoTable();
        }
        
        function filterSaneamentoTable() {
            const input = document.getElementById("searchSaneamento").value.toUpperCase();
            const tipoFilter = document.getElementById("filterTipo").value.toUpperCase();
            
            // Se há filtro de card ativo, usar ele; senão usar o select
            const effectiveFilter = currentFilter !== 'all' ? currentFilter : tipoFilter;
            
            // Mostrar/esconder card de auditoria baseado no filtro
            const cardAuditoria = document.getElementById("card-auditoria");
            if (cardAuditoria) {
                cardAuditoria.style.display = (effectiveFilter === "" || effectiveFilter === "ad_disabled_ativo") ? "block" : "none";
            }
            
            // Filtrar tabela principal
            const tableMain = document.getElementById("table-saneamento");
            if (tableMain) {
                for (let i = 1; i < tableMain.rows.length; i++) {
                    const row = tableMain.rows[i];
                    const email = row.getAttribute('data-email') || '';
                    const tipo = row.getAttribute('data-tipo') || '';
                    
                    const matchSearch = email.includes(input) || row.cells[0].textContent.toUpperCase().includes(input);
                    const matchTipo = effectiveFilter === "" || tipo === effectiveFilter.toLowerCase();
                    
                    row.style.display = (matchSearch && matchTipo) ? "" : "none";
                }
            }
            
            // Filtrar tabela de auditoria
            const tableAudit = document.getElementById("table-auditoria");
            if (tableAudit) {
                for (let i = 1; i < tableAudit.rows.length; i++) {
                    const row = tableAudit.rows[i];
                    const email = row.getAttribute('data-email') || '';
                    const tipo = row.getAttribute('data-tipo') || '';
                    
                    const matchSearch = email.includes(input) || row.cells[0].textContent.toUpperCase().includes(input);
                    const matchTipo = effectiveFilter === "" || tipo === effectiveFilter.toLowerCase();
                    
                    row.style.display = (matchSearch && matchTipo) ? "" : "none";
                }
            }
        }
        
        function exportSaneamentoCSV() {
            const table = document.getElementById("table-saneamento");
            const csv = [];
            
            // Header
            const headers = ["Nome", "E-mail", "Tipo", "Status AD", "Grupos AD", "Ação Recomendada"];
            csv.push(headers.join(";"));
            
            // Rows
            for (let i = 1; i < table.rows.length; i++) {
                const row = table.rows[i];
                if (row.style.display === "none") continue;
                
                const rowData = [];
                for (let j = 0; j < row.cells.length; j++) {
                    const cellText = row.cells[j].textContent.trim();
                    rowData.push('"' + cellText.replace(/"/g, '""') + '"');
                }
                csv.push(rowData.join(";"));
            }
            
            const csvFile = new Blob(["\\uFEFF" + csv.join("\\n")], {type: "text/csv;charset=utf-8;"});
            const link = document.createElement("a");
            link.download = "saneamento_identidades_" + new Date().toISOString().split('T')[0] + ".csv";
            link.href = window.URL.createObjectURL(csvFile);
            link.style.display = "none";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    </script>
    """