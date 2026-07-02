# scripts/reporting/ab7_saneamento.py
from .html_helpers import fmt_br


def _br_number(n):
    """Formata número no padrão brasileiro: 1.447 ao invés de 1,447"""
    return f"{n:,}".replace(',', '.')


def render_tab_saneamento(sanity_data):
    """
    Renders the 'Saneamento de Identidades' tab content.
    Uses pre-computed sanity analysis data from sanity_analyzer.py.
    """
    if not sanity_data:
        return """
    <div id="tab-saneamento" class="container tab-content">
        <div class="card">
            <h2>🧹 Saneamento de Identidades - AD vs Maximo</h2>
            <p>Nenhum dado de saneamento disponível.</p>
        </div>
    </div>
    """
    
    stats = sanity_data['stats']
    analises = sanity_data['analises']
    
    return f"""
    <div id="tab-saneamento" class="container tab-content">
        <div class="card" style="border-left: 4px solid var(--warning); background-image: linear-gradient(to right, #ffffff, #f8fafc);">
            <div class="card-header" style="border:none; margin-bottom:0.5rem;">
                <div>
                    <h2 style="margin:0; color:var(--warning);">🧹 Saneamento de Identidades - AD vs Maximo</h2>
                    <p style="font-size: 0.9rem; color: #64748b; font-weight: normal; margin-top: 4px;">Comparação entre usuários do Active Directory e Maximo para identificação de inconsistências.</p>
                </div>
            </div>
            
            <div class="stats-grid" style="margin-bottom: 1rem;">
                <div class="stat-card" style="border-bottom: 4px solid var(--accent); cursor: pointer;" onclick="filterByType('all')" id="card-all">
                    <div class="stat-value">{_br_number(stats['total_ad'])}</div>
                    <div class="stat-title">Usuários no AD</div>
                    <div class="stat-subtitle">Fonte da verdade</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--success); cursor: pointer;" onclick="filterByType('match')" id="card-match">
                    <div class="stat-value">{_br_number(stats['match_email'])}</div>
                    <div class="stat-title">Match por Email</div>
                    <div class="stat-subtitle">Mesmo email em ambos</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--danger); cursor: pointer;" onclick="filterByType('ad_only')" id="card-ad_only">
                    <div class="stat-value">{_br_number(stats['only_ad'])}</div>
                    <div class="stat-title">Apenas no AD</div>
                    <div class="stat-subtitle">Sem correspondência no Maximo</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--warning); cursor: pointer;" onclick="filterByType('maximo_only')" id="card-maximo_only">
                    <div class="stat-value">{_br_number(stats['only_maximo'])}</div>
                    <div class="stat-title">Apenas no Maximo</div>
                    <div class="stat-subtitle">Sem correspondência no AD</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid #7c3aed; cursor: pointer;" onclick="filterByType('name_divergence')" id="card-name_divergence">
                    <div class="stat-value">{_br_number(stats['name_divergences'])}</div>
                    <div class="stat-title">Divergências de Nome</div>
                    <div class="stat-subtitle">Mesmo email, nomes diferentes</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid #ec4899; cursor: pointer;" onclick="filterByType('multi_userid')" id="card-multi_userid">
                    <div class="stat-value">{_br_number(stats['multi_userid'])}</div>
                    <div class="stat-title">Múltiplos USERIDs</div>
                    <div class="stat-subtitle">Mesmo email, IDs diferentes</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid #f97316; cursor: pointer;" onclick="filterByType('prefix_match')" id="card-prefix_match">
                    <div class="stat-value">{_br_number(stats['prefix_match'])}</div>
                    <div class="stat-title">Match por USERID</div>
                    <div class="stat-subtitle">Prefixos correspondem</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid #06b6d4; cursor: pointer;" onclick="filterByType('no_match')" id="card-no_match">
                    <div class="stat-value">{_br_number(stats['no_match'])}</div>
                    <div class="stat-title">Sem Match</div>
                    <div class="stat-subtitle">No Maximo</div>
                </div>
            </div>
            
            <div class="search-container">
                <input type="text" id="searchSaneamento" class="search-bar" placeholder="🔍 Buscar por nome ou e-mail..." onkeyup="filterSaneamentoTable()">
                <select id="filterTipo" class="filter-select" onchange="filterSaneamentoTable()">
                    <option value="">Todos os Tipos</option>
                    <option value="ad_only">Apenas no AD</option>
                    <option value="maximo_only">Apenas no Maximo</option>
                    <option value="match">Match Perfeito</option>
                </select>
                <button class="btn-export" onclick="filterByType('all')" style="background-color: #64748b;">🔄 Limpar Filtro</button>
                <button class="btn-export" onclick="exportSaneamentoCSV()">📥 Exportar CSV</button>
            </div>
            
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
        
        <div class="card" style="border-top: 4px solid var(--accent);">
            <h2 class="card-header" style="border:none; margin-bottom:0.5rem;">📋 Regras de Saneamento</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                <div class="legend-box" style="border-left: 3px solid var(--danger);">
                    <h3>❌ Remover do AD</h3>
                    <ul class="legend-list">
                        <li>Usuário inativo há mais de 90 dias</li>
                        <li>Conta desabilitada (Enabled = False)</li>
                        <li>Sem acesso a sistemas críticos</li>
                        <li>Grupos apenas de acesso genérico</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid var(--warning);">
                    <h3>⚠️ Revisar</h3>
                    <ul class="legend-list">
                        <li>Usuário com múltiplos grupos</li>
                        <li>Licenças Office 365 E3/E1</li>
                        <li>Acesso a módulos críticos O&G</li>
                        <li>Contas de parceiros/terceiros</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid #10b981;">
                    <h3>✅ Manter</h3>
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
        status_badge = '<span class="badge badge-success">Ativo</span>' if d['ad_enabled'] else '<span class="badge badge-danger">Inativo</span>'
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
        status_badge = '<span class="badge badge-success">Ativo</span>' if d.get('ad_enabled', True) else '<span class="badge badge-danger">Inativo</span>'
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
        status_badge = '<span class="badge badge-success">Ativo</span>' if d['ad_enabled'] else '<span class="badge badge-danger">Inativo</span>'
        
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
        status_badge = '<span class="badge badge-success">Ativo</span>' if d['ad_enabled'] else '<span class="badge badge-danger">Inativo</span>'
        
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
        
        status_badge = '<span class="badge badge-success">Ativo</span>' if enabled else '<span class="badge badge-danger">Inativo</span>'
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
        status_badge = '<span class="badge badge-success">Ativo</span>' if d['ad_enabled'] else '<span class="badge badge-danger">Inativo</span>'
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
            const table = document.getElementById("table-saneamento");
            if (!table) return;
            
            // Se há filtro de card ativo, usar ele; senão usar o select
            const effectiveFilter = currentFilter !== 'all' ? currentFilter : tipoFilter;
            
            for (let i = 1; i < table.rows.length; i++) {
                const row = table.rows[i];
                const email = row.getAttribute('data-email') || '';
                const tipo = row.getAttribute('data-tipo') || '';
                
                const matchSearch = email.includes(input) || row.cells[0].textContent.toUpperCase().includes(input);
                const matchTipo = effectiveFilter === "" || tipo === effectiveFilter.toLowerCase();
                
                row.style.display = (matchSearch && matchTipo) ? "" : "none";
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