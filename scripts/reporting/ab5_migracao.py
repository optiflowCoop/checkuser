# scripts/reporting/ab5_migracao.py


def _br_number(n):
    """Formata número no padrão brasileiro: 1.447 ao invés de 1,447"""
    return f"{n:,}".replace(',', '.')


def render_tab_migracao(migration_data, allocation_data=None):
    """
    Renders the 'Recomendações de Migração' tab content.
    Shows consolidated recommendations for user migration/removal/cleanup.
    """
    if not migration_data:
        return """
    <div id="tab-migracao" class="container tab-content">
        <div class="card">
            <h2>Recomendações de Migração</h2>
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
        <div class="card">
            <h2 class="card-header">Recomendações de Migração</h2>
            <p class="card-desc">Análise consolidada de ações necessárias para sincronizar AD e Maximo.</p>

            <div class="stats-grid" style="margin-bottom: 1rem;">
                <div class="stat-card border-accent" onclick="filterByTypeMigracao('all')" id="card-migracao-all" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(sum(tipo_counts.values()))}</div>
                    <div class="stat-title">Total</div>
                    <div class="stat-subtitle">Todas as recomendações</div>
                </div>
                <div class="stat-card border-danger" onclick="filterByTypeMigracao('remover')" id="card-remover" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(tipo_counts.get('REMOVER', 0))}</div>
                    <div class="stat-title">Remover</div>
                    <div class="stat-subtitle">Usuários inativos em ambos</div>
                </div>
                <div class="stat-card border-warning" onclick="filterByTypeMigracao('migrar')" id="card-migrar" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(tipo_counts.get('MIGRAR', 0))}</div>
                    <div class="stat-title">Migrar/Reativar</div>
                    <div class="stat-subtitle">Ativos no AD, inativos no Maximo</div>
                </div>
                <div class="stat-card border-success" onclick="filterByTypeMigracao('manter')" id="card-manter" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(tipo_counts.get('MANTER', 0))}</div>
                    <div class="stat-title">Manter</div>
                    <div class="stat-subtitle">Ativos em ambos sistemas</div>
                </div>
                <div class="stat-card border-primary" onclick="filterByTypeMigracao('criar_no_maximo')" id="card-criar_no_maximo" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(tipo_counts.get('CRIAR_NO_MAXIMO', 0))}</div>
                    <div class="stat-title">Criar no Maximo</div>
                    <div class="stat-subtitle">Ativos no AD, não existem no Maximo</div>
                </div>
                <div class="stat-card border-secondary" onclick="filterByTypeMigracao('verificar_ad')" id="card-verificar_ad" style="cursor: pointer;">
                    <div class="stat-value">{_br_number(tipo_counts.get('VERIFICAR_AD', 0))}</div>
                    <div class="stat-title">Verificar AD</div>
                    <div class="stat-subtitle">Existem no Maximo, não no AD</div>
                </div>
            </div>

            <div class="search-container">
                <input type="text" id="searchMigracao" class="search-bar" placeholder="Buscar por nome, e-mail ou USERID..." onkeyup="filterMigracaoTable()">
                <select id="filterTipoMigracao" class="filter-select" onchange="filterMigracaoTable()">
                    <option value="">Todos os Tipos</option>
                    <option value="REMOVER">Remover</option>
                    <option value="MIGRAR">Migrar/Reativar</option>
                    <option value="MANTER">Migrar p/ MAS 9</option>
                    <option value="CRIAR_NO_MAXIMO">Criar no Maximo</option>
                    <option value="VERIFICAR_AD">Verificar AD</option>
                    <option value="CONTA_SERVICO">Conta de Serviço</option>
                    <option value="REVISAR_STATUS">Revisar Status</option>
                </select>
                <button class="btn-export" onclick="filterByTypeMigracao('all')">Limpar Filtro</button>
                <button class="btn-export" onclick="exportMigracaoCSV()">Exportar CSV</button>
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
                            <th>Cargo</th>
                            <th>Grupos Maximo Atuais</th>
                            <th>Grupo Recomendado (MAS 9)</th>
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

        <div class="card">
            <h2 class="card-header">Regras de Migração</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                <div class="legend-box">
                    <h3>Remover</h3>
                    <ul class="legend-list">
                        <li>Usuário inativo no AD e no Maximo</li>
                        <li>Conta desabilitada há mais de 90 dias</li>
                        <li>Sem acesso a sistemas críticos</li>
                        <li>Grupos apenas de acesso genérico</li>
                    </ul>
                </div>
                <div class="legend-box">
                    <h3>Migrar/Reativar</h3>
                    <ul class="legend-list">
                        <li>Ativo no AD mas inativo no Maximo</li>
                        <li>Usuário com múltiplos USERIDs no Maximo</li>
                        <li>Divergência de nome entre AD e Maximo</li>
                        <li>Verificar necessidade de acesso</li>
                    </ul>
                </div>
                <div class="legend-box">
                    <h3>Manter</h3>
                    <ul class="legend-list">
                        <li>Ativo em ambos os sistemas</li>
                        <li>Nomes e emails consistentes</li>
                        <li>Acesso a sistemas críticos</li>
                        <li>Grupos de segurança válidos</li>
                    </ul>
                </div>
                <div class="legend-box">
                    <h3>Criar no Maximo</h3>
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
        tipo_badge = {
            'REMOVER': '<span class="badge badge-danger">Remover</span>',
            'MIGRAR': '<span class="badge badge-warning">Migrar</span>',
            'MANTER': '<span class="badge badge-success">Migrar p/ MAS 9</span>',
            'CRIAR_NO_MAXIMO': '<span class="badge badge-medium">Criar no Maximo</span>',
            'VERIFICAR_AD': '<span class="badge badge-neutral">Verificar AD</span>',
            'CONTA_SERVICO': '<span class="badge badge-warning">Conta de Serviço</span>',
            'REVISAR_STATUS': '<span class="badge badge-neutral">Revisar Status</span>',
        }.get(r['tipo'], '<span class="badge badge-neutral">N/A</span>')

        prioridade_badge = {
            'ALTA': '<span class="badge badge-danger">Alta</span>',
            'MEDIA': '<span class="badge badge-warning">Média</span>',
            'BAIXA': '<span class="badge badge-success">Baixa</span>',
        }.get(r['prioridade'], '<span class="badge badge-neutral">N/A</span>')

        status_ad_raw = (r.get('status_ad') or '').strip().upper()
        if status_ad_raw in ('ATIVO', 'ACTIVE', 'ENABLED'):
            status_ad = '<span class="badge badge-success">Ativo</span>'
        elif status_ad_raw in ('INATIVO', 'INACTIVE', 'DISABLED'):
            status_ad = '<span class="badge badge-danger">Inativo</span>'
        else:
            status_ad = '<span class="badge badge-neutral">N/A</span>'

        status_maximo_raw = (r.get('status_maximo') or '').strip().upper()
        if status_maximo_raw in ('ATIVO', 'ACTIVE', 'ENABLED'):
            status_maximo = '<span class="badge badge-success">Ativo</span>'
        elif status_maximo_raw in ('INATIVO', 'INACTIVE', 'DISABLED'):
            status_maximo = '<span class="badge badge-danger">Inativo</span>'
        else:
            status_maximo = '<span class="badge badge-neutral">N/A</span>'

        # Detalhe de ambientes com status: usa os pares REAIS env:status que o
        # advisor agora emite (envs_detalhe, ex. "BASE:ACTIVE | N09:INACTIVE").
        # O código antigo zipava dois sets independentes por posição — a
        # auditoria mediu 228 recomendações com pares fabricados errados.
        ambientes_detalhe = 'N/A'
        envs_detalhe = r.get('envs_detalhe') or ''
        if envs_detalhe:
            detalhes = []
            for pair in envs_detalhe.split('|'):
                pair = pair.strip()
                if not pair:
                    continue
                env, _, st = pair.partition(':')
                st = st.strip().upper()
                if any(x in st for x in ('ATIVO', 'ACTIVE', 'ENABLED')) and not any(x in st for x in ('INATIVO', 'INACTIVE', 'DISABLED')):
                    badge = '<span class="badge badge-success">Ativo</span>'
                elif any(x in st for x in ('INATIVO', 'INACTIVE', 'DISABLED')):
                    badge = f'<span class="badge badge-danger">{st if "/" in st else "Inativo"}</span>'
                else:
                    badge = f'<span class="badge badge-neutral">{st or "N/A"}</span>'
                detalhes.append(f"{env.strip()} {badge}")
            ambientes_detalhe = '<br>'.join(detalhes)
        elif r.get('envs'):
            ambientes_detalhe = str(r['envs'])

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
                <td>{ambientes_detalhe}</td>
                <td>{(r.get('cargo') or '')[:40]}</td>
                <td title="{(r.get('grupos_maximo') or '').replace('"', '&quot;')}">{(r.get('grupos_maximo') or '')[:80]}</td>
                <td><strong>{r.get('grupo_recomendado_mas9') or ''}</strong></td>
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
            filterMigracaoTable();
        }

        function filterMigracaoTable() {
            const input = document.getElementById("searchMigracao").value.toUpperCase();
            const tipoFilter = document.getElementById("filterTipoMigracao").value.toUpperCase();
            const table = document.getElementById("table-migracao");
            if (!table) return;
            const effectiveFilter = currentFilterMigracao !== 'all' ? currentFilterMigracao : tipoFilter;
            for (let i = 1; i < table.rows.length; i++) {
                const row = table.rows[i];
                const email = row.getAttribute('data-email') || '';
                const tipo = row.getAttribute('data-tipo') || '';
                const matchSearch = email.includes(input)
                    || (row.cells[2] && row.cells[2].textContent.toUpperCase().includes(input))
                    || (row.cells[3] && row.cells[3].textContent.toUpperCase().includes(input))
                    || (row.cells[4] && row.cells[4].textContent.toUpperCase().includes(input))
                    || (row.cells[5] && row.cells[5].textContent.toUpperCase().includes(input));
                const matchTipo = effectiveFilter === "" || tipo.toUpperCase() === effectiveFilter.toUpperCase();
                row.style.display = (matchSearch && matchTipo) ? "" : "none";
            }
        }

        function exportMigracaoCSV() {
            const table = document.getElementById("table-migracao");
            const csv = [];
            const headers = ["Tipo", "Prioridade", "USERID", "E-mail", "Nome AD", "Nome Maximo", "Status AD", "Status Maximo", "Ambientes", "Grupos AD", "Motivo", "Ação"];
            csv.push(headers.join(";"));
            for (let i = 1; i < table.rows.length; i++) {
                const row = table.rows[i];
                if (row.style.display === "none") continue;
                const rowData = [];
                for (let j = 0; j < row.cells.length; j++) {
                    rowData.push('"' + row.cells[j].textContent.trim().replace(/"/g, '""') + '"');
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
