# scripts/reporting/ab8_migracao.py
from .html_helpers import fmt_br


def _br_number(n):
    """Formata número no padrão brasileiro: 1.447 ao invés de 1,447"""
    return f"{n:,}".replace(',', '.')


def render_tab_migracao(migration_data):
    """
    Renders the 'Recomendações de Migração' tab content.
    Shows consolidated recommendations for user migration/removal/cleanup.
    """
    if not migration_data:
        return """
    <div id="tab-migracao" class="container tab-content">
        <div class="card">
            <h2>🚀 Recomendações de Migração</h2>
            <p>Nenhuma recomendação de migração disponível.</p>
        </div>
    </div>
    """
    
    # Contar por tipo
    tipo_counts = {}
    for r in migration_data:
        tipo = r['tipo']
        tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
    
    # Contar por prioridade
    prioridade_counts = {}
    for r in migration_data:
        prioridade = r['prioridade']
        prioridade_counts[prioridade] = prioridade_counts.get(prioridade, 0) + 1
    
    return f"""
    <div id="tab-migracao" class="container tab-content">
        <div class="card" style="border-left: 4px solid var(--success); background-image: linear-gradient(to right, #ffffff, #f8fafc);">
            <div class="card-header" style="border:none; margin-bottom:0.5rem;">
                <div>
                    <h2 style="margin:0; color:var(--success);">🚀 Recomendações de Migração</h2>
                    <p style="font-size: 0.9rem; color: #64748b; font-weight: normal; margin-top: 4px;">Análise consolidada de ações necessárias para sincronizar AD e Maximo.</p>
                </div>
            </div>
            
            <div class="stats-grid" style="margin-bottom: 1rem;">
                <div class="stat-card" style="border-bottom: 4px solid var(--accent); cursor: pointer;" onclick="filterByTypeMigracao('all')" id="card-all">
                    <div class="stat-value">{_br_number(sum(tipo_counts.values()))}</div>
                    <div class="stat-title">Total</div>
                    <div class="stat-subtitle">Todas as recomendações</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--danger); cursor: pointer;" onclick="filterByTypeMigracao('remover')" id="card-remover">
                    <div class="stat-value">{_br_number(tipo_counts.get('REMOVER', 0))}</div>
                    <div class="stat-title">Remover</div>
                    <div class="stat-subtitle">Usuários inativos em ambos</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--warning); cursor: pointer;" onclick="filterByTypeMigracao('migrar')" id="card-migrar">
                    <div class="stat-value">{_br_number(tipo_counts.get('MIGRAR', 0))}</div>
                    <div class="stat-title">Migrar/Reativar</div>
                    <div class="stat-subtitle">Ativos no AD, inativos no Maximo</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid var(--success); cursor: pointer;" onclick="filterByTypeMigracao('manter')" id="card-manter">
                    <div class="stat-value">{_br_number(tipo_counts.get('MANTER', 0))}</div>
                    <div class="stat-title">Manter</div>
                    <div class="stat-subtitle">Ativos em ambos sistemas</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid #2563eb; cursor: pointer;" onclick="filterByTypeMigracao('criar_no_maximo')" id="card-criar_no_maximo">
                    <div class="stat-value">{_br_number(tipo_counts.get('CRIAR_NO_MAXIMO', 0))}</div>
                    <div class="stat-title">Criar no Maximo</div>
                    <div class="stat-subtitle">Ativos no AD, não existem no Maximo</div>
                </div>
                <div class="stat-card" style="border-bottom: 4px solid #7c3aed; cursor: pointer;" onclick="filterByTypeMigracao('verificar_ad')" id="card-verificar_ad">
                    <div class="stat-value">{_br_number(tipo_counts.get('VERIFICAR_AD', 0))}</div>
                    <div class="stat-title">Verificar AD</div>
                    <div class="stat-subtitle">Existem no Maximo, não no AD</div>
                </div>
            </div>
            
            <div class="search-container">
                <input type="text" id="searchMigracao" class="search-bar" placeholder="🔍 Buscar por nome, e-mail ou USERID..." onkeyup="filterMigracaoTable()">
                <select id="filterTipoMigracao" class="filter-select" onchange="filterMigracaoTable()">
                    <option value="">Todos os Tipos</option>
                    <option value="REMOVER">Remover</option>
                    <option value="MIGRAR">Migrar/Reativar</option>
                    <option value="MANTER">Manter</option>
                    <option value="CRIAR_NO_MAXIMO">Criar no Maximo</option>
                    <option value="VERIFICAR_AD">Verificar AD</option>
                </select>
                <button class="btn-export" onclick="filterByTypeMigracao('all')" style="background-color: #64748b;">🔄 Limpar Filtro</button>
                <button class="btn-export" onclick="exportMigracaoCSV()">📥 Exportar CSV</button>
            </div>
            
            <div class="table-responsive">
                <table id="table-migracao">
                    <thead>
                        <tr>
                            <th>Tipo</th>
                            <th>Prioridade</th>
                            <th>USERID</th>
                            <th>E-mail</th>
                            <th>Nome AD</th>
                            <th>Nome Maximo</th>
                            <th>Status AD</th>
                            <th>Status Maximo</th>
                            <th>Ambientes</th>
                            <th>Grupos AD</th>
                            <th>Motivo</th>
                            <th>Ação Recomendada</th>
                        </tr>
                    </thead>
                    <tbody>
                        {_render_migracao_rows(migration_data)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card" style="border-top: 4px solid var(--accent);">
            <h2 class="card-header" style="border:none; margin-bottom:0.5rem;">📋 Regras de Migração</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                <div class="legend-box" style="border-left: 3px solid var(--danger);">
                    <h3>❌ Remover</h3>
                    <ul class="legend-list">
                        <li>Usuário inativo no AD e no Maximo</li>
                        <li>Conta desabilitada há mais de 90 dias</li>
                        <li>Sem acesso a sistemas críticos</li>
                        <li>Grupos apenas de acesso genérico</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid var(--warning);">
                    <h3>⚠️ Migrar/Reativar</h3>
                    <ul class="legend-list">
                        <li>Ativo no AD mas inativo no Maximo</li>
                        <li>Usuário com múltiplos USERIDs no Maximo</li>
                        <li>Divergência de nome entre AD e Maximo</li>
                        <li>Verificar necessidade de acesso</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid #10b981;">
                    <h3>✅ Manter</h3>
                    <ul class="legend-list">
                        <li>Ativo em ambos os sistemas</li>
                        <li>Nomes e emails consistentes</li>
                        <li>Acesso a sistemas críticos</li>
                        <li>Grupos de segurança válidos</li>
                    </ul>
                </div>
                <div class="legend-box" style="border-left: 3px solid var(--accent);">
                    <h3>🆕 Criar no Maximo</h3>
                    <ul class="legend-list">
                        <li>Usuário ativo no AD mas não existe no Maximo</li>
                        <li>Avaliar necessidade de acesso</li>
                        <li>Verificar perfil e grupos</li>
                        <li>Definir licença adequada</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """


def _render_migracao_rows(migration_data):
    """Renderiza as linhas da tabela de migração."""
    rows = []
    
    for r in migration_data:
        # Badge de tipo
        tipo_badge = {
            'REMOVER': '<span class="badge badge-danger">Remover</span>',
            'MIGRAR': '<span class="badge badge-warning">Migrar</span>',
            'MANTER': '<span class="badge badge-success">Manter</span>',
            'CRIAR_NO_MAXIMO': '<span class="badge badge-medium">Criar no Maximo</span>',
            'VERIFICAR_AD': '<span class="badge badge-neutral">Verificar AD</span>',
        }.get(r['tipo'], '<span class="badge badge-neutral">N/A</span>')
        
        # Badge de prioridade
        prioridade_badge = {
            'ALTA': '<span class="badge badge-danger">Alta</span>',
            'MEDIA': '<span class="badge badge-warning">Média</span>',
            'BAIXA': '<span class="badge badge-success">Baixa</span>',
        }.get(r['prioridade'], '<span class="badge badge-neutral">N/A</span>')
        
        # Status badges
        status_ad = '<span class="badge badge-success">Ativo</span>' if r['status_ad'] == 'ATIVO' else '<span class="badge badge-danger">Inativo</span>' if r['status_ad'] == 'INATIVO' else '<span class="badge badge-neutral">N/A</span>' 
        status_maximo = '<span class="badge badge-success">Ativo</span>' if r['status_maximo'] == 'ATIVO' else '<span class="badge badge-danger">Inativo</span>' if r['status_maximo'] == 'INATIVO' else '<span class="badge badge-neutral">N/A</span>' 
        
        rows.append(f"""
            <tr data-tipo="{r['tipo'].lower()}" data-prioridade="{r['prioridade']}" data-email="{r['email'].lower()}">
                <td>{tipo_badge}</td>
                <td>{prioridade_badge}</td>
                <td>{r['userid']}</td>
                <td>{r['email']}</td>
                <td>{r['nome_ad']}</td>
                <td>{r['nome_maximo'][:50]}</td>
                <td>{status_ad}</td>
                <td>{status_maximo}</td>
                <td>{r['envs'][:30] if r['envs'] else 'N/A'}</td>
                <td>{r['grupos_ad']}</td>
                <td>{r['motivo'][:80]}</td>
                <td>{r['acao']}</td>
            </tr>
        """)
    
    return '\n'.join(rows)


def render_tab_migracao_scripts():
    """Retorna JavaScript específico para a aba de migração."""
    return """
    <script>
        let currentFilterMigracao = 'all';
        
        function filterByTypeMigracao(type) {
            currentFilterMigracao = type;
            console.log('filterByTypeMigracao:', type, 'currentFilterMigracao:', currentFilterMigracao);
            
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
            filterMigracaoTable();
        }
        
        function filterMigracaoTable() {
            const input = document.getElementById("searchMigracao").value.toUpperCase();
            const tipoFilter = document.getElementById("filterTipoMigracao").value.toUpperCase();
            const table = document.getElementById("table-migracao");
            if (!table) return;
            
            // Se há filtro de card ativo, usar ele; senão usar o select
            const effectiveFilter = currentFilterMigracao !== 'all' ? currentFilterMigracao : tipoFilter;
            console.log('filterMigracaoTable:', 'currentFilterMigracao:', currentFilterMigracao, 'effectiveFilter:', effectiveFilter, 'tipoFilter:', tipoFilter);
            
            let visibleCount = 0;
            for (let i = 1; i < table.rows.length; i++) {
                const row = table.rows[i];
                const email = row.getAttribute('data-email') || '';
                const tipo = row.getAttribute('data-tipo') || '';
                
                const matchSearch = email.includes(input) || row.cells[3].textContent.toUpperCase().includes(input) || row.cells[2].textContent.toUpperCase().includes(input);
                // Comparação case-insensitive
                const matchTipo = effectiveFilter === "" || tipo.toUpperCase() === effectiveFilter.toUpperCase();
                
                row.style.display = (matchSearch && matchTipo) ? "" : "none";
                if ((matchSearch && matchTipo)) visibleCount++;
            }
            console.log('Visible rows:', visibleCount);
        }
        
        function exportMigracaoCSV() {
            const table = document.getElementById("table-migracao");
            const csv = [];
            
            // Header
            const headers = ["Tipo", "Prioridade", "USERID", "E-mail", "Nome AD", "Nome Maximo", "Status AD", "Status Maximo", "Ambientes", "Grupos AD", "Motivo", "Ação"];
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
            link.download = "recomendacoes_migracao_" + new Date().toISOString().split('T')[0] + ".csv";
            link.href = window.URL.createObjectURL(csvFile);
            link.style.display = "none";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    </script>
    """