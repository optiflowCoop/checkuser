# scripts/reporting/ab6_alocacao.py


def render_allocation_detail(allocation_data):
    """Renderiza o detalhamento do saneamento de alocação (Maximo 9) na Aba 6.
    Exibe colunas individuais por ambiente: logins em cada um dos ultimos 90 dias.
    """
    if not allocation_data:
        return ""
    stats = allocation_data['stats']
    analises = allocation_data['analises']

    ENV_COLS = ['BASE', 'ODN1', 'ODN2', 'N06', 'N08', 'N09', 'HTQ', 'POL', 'OUTROS']

    rows_html = ""
    for a in analises:  # TODOS os usuarios (sem limite)
        suggested = ', '.join(a['suggested_accounts'])
        detail = a.get('env_logins_detail', {})
        env_cells = ''.join(f'<td style="text-align:center;">{detail.get(e, 0)}</td>' for e in ENV_COLS)

        status_badge = '<span class="badge badge-success">Ativo</span>' if a['status'] == 'ACTIVE' else '<span class="badge badge-danger">Inativo</span>'

        if len(a['suggested_accounts']) > 1:
            suggest_badge = f'<span class="badge badge-warning">Multi ({len(a["suggested_accounts"])})</span>'
        else:
            suggest_badge = '<span class="badge badge-success">Unico</span>'

        rows_html += f"""
            <tr>
                <td>{a['userid']}</td>
                <td>{a['displayname'][:40]}</td>
                <td>{status_badge}</td>
                <td style="text-align:center;">{a['total_logins_90d']}</td>
                <td>{a['allocation_primary'] or 'N/A'}</td>
                {env_cells}
                <td>{suggest_badge}</td>
                <td>{suggested[:80]}</td>
                <td>{a['reason'][:100]}</td>
            </tr>"""

    env_headers = ''.join(f'<th style="text-align:center;">{e}</th>' for e in ENV_COLS)

    return f"""
    <div id="tab-alloc-detail" class="container tab-content">
        <div class="card">
            <h2 class="card-header">Saneamento de Alocação (Maximo 9) — Detalhamento</h2>
            <p class="card-desc">
                Histórico de logins dos últimos 90 dias por ambiente e sugestão de criação de conta.
                Janela: {stats['window_start']} a {stats['window_end']} | {len(analises)} usuários.
            </p>
            <div class="search-container">
                <input type="text" id="searchAlloc" class="search-bar" placeholder="Buscar por USERID ou nome..." onkeyup="filterAllocTable()">
                <button class="btn-export" onclick="exportAllocCSV()">Exportar CSV</button>
            </div>
            <div class="table-responsive">
                <table id="table-alloc-detail">
                    <thead>
                        <tr>
                            <th>USERID</th>
                            <th>Nome</th>
                            <th>Status</th>
                            <th style="text-align:center;">Total</th>
                            <th>Alocacao</th>
                            {env_headers}
                            <th>Sugestao</th>
                            <th>Contas Sugeridas</th>
                            <th>Motivo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            <p class="card-footnote">
                Sugestão baseada no local de alocação (locationsite/DEFSITE) + ambientes com &gt;= {stats['min_secundario']} acessos nos últimos 90 dias.
                Exemplo: "BASE 150 | ODN2 40 | N06 30" significa 150 logins no ambiente BASE, 40 no ODN2, 30 no N06.
            </p>
        </div>
    </div>
    <script>
        function filterAllocTable() {{
            const input = document.getElementById("searchAlloc").value.toUpperCase();
            const table = document.getElementById("table-alloc-detail");
            if (!table) return;
            for (let i = 1; i < table.rows.length; i++) {{
                const row = table.rows[i];
                if (!row || !row.cells) continue;
                const userid = row.cells[0] ? row.cells[0].textContent.toUpperCase() : '';
                const nome = row.cells[1] ? row.cells[1].textContent.toUpperCase() : '';
                const match = userid.includes(input) || nome.includes(input);
                row.style.display = match ? "" : "none";
            }}
        }}
        function exportAllocCSV() {{
            const table = document.getElementById("table-alloc-detail");
            if (!table) return;
            const csv = [];
            const headers = ["USERID","Nome","Status","Total_Logins","Alocacao","BASE","ODN1","ODN2","N06","N08","N09","HTQ","POL","OUTROS","Sugestao","Contas_Sugeridas","Motivo"];
            csv.push(headers.join(";"));
            for (let i = 1; i < table.rows.length; i++) {{
                const row = table.rows[i];
                if (row.style.display === "none") continue;
                const rowData = [];
                for (let j = 0; j < row.cells.length; j++) {{
                    rowData.push('"' + row.cells[j].textContent.trim().replace(/"/g, '""') + '"');
                }}
                csv.push(rowData.join(";"));
            }}
            const csvFile = new Blob(["\\uFEFF" + csv.join("\\n")], {{type: "text/csv;charset=utf-8;"}});
            const link = document.createElement("a");
            link.download = "saneamento_alocacao_" + new Date().toISOString().split('T')[0] + ".csv";
            link.href = window.URL.createObjectURL(csvFile);
            link.style.display = "none";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}
    </script>
    """
