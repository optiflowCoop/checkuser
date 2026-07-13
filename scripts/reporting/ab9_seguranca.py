# scripts/reporting/ab9_seguranca.py
"""Aba dedicada à auditoria de Segregação de Funções (SoD): grupos e
usuários com permissão simultânea de EMISSOR e APROVADOR nas aplicações de
Compras (Requisição, Ordem de Compra, Requisição Simplificada)."""
from .html_helpers import render_table


def _br_number(n):
    return f"{n:,}".replace(',', '.')


def _dedupe_group_conflicts(group_conflicts):
    """Consolida os conflitos de Nível 1 por (GROUPNAME, APP), listando em
    quais dos 7 ambientes o grupo existe — em vez de repetir a mesma linha
    uma vez por ambiente, mostra o problema estrutural de forma única."""
    by_key = {}
    for gc in group_conflicts:
        key = (gc['GROUPNAME'], gc['APP'])
        entry = by_key.setdefault(key, {
            'GROUPNAME': gc['GROUPNAME'],
            'APP_LABEL': gc['APP_LABEL'],
            'DESCRIPTION': gc.get('DESCRIPTION', ''),
            'ENVIRONMENTS': set(),
            'OPCOES_EMISSOR': set(),
            'OPCOES_APROVADOR': set(),
        })
        entry['ENVIRONMENTS'].add(gc['ENVIRONMENT'])
        entry['OPCOES_EMISSOR'].update(gc['OPCOES_EMISSOR'].split('; '))
        entry['OPCOES_APROVADOR'].update(gc['OPCOES_APROVADOR'].split('; '))
        if not entry['DESCRIPTION'] and gc.get('DESCRIPTION'):
            entry['DESCRIPTION'] = gc['DESCRIPTION']

    result = []
    for entry in by_key.values():
        emissor = '/'.join(sorted(entry['OPCOES_EMISSOR']))
        aprovador = '/'.join(sorted(entry['OPCOES_APROVADOR']))
        result.append({
            'GROUPNAME': entry['GROUPNAME'],
            'APP_LABEL': entry['APP_LABEL'],
            'DESCRIPTION': entry['DESCRIPTION'],
            'AMBIENTES': '; '.join(sorted(entry['ENVIRONMENTS'])),
            'QTD_AMBIENTES': len(entry['ENVIRONMENTS']),
            'OPCOES_EMISSOR': emissor,
            'OPCOES_APROVADOR': aprovador,
            'RECOMENDACAO': (
                f"Dividir {entry['GROUPNAME']} em dois grupos: um mantendo apenas "
                f"{emissor} (emissor) e outro apenas {aprovador} (aprovador); "
                "realocar cada usuário conforme o papel real que exerce."
            ),
        })
    return sorted(result, key=lambda x: (-x['QTD_AMBIENTES'], x['APP_LABEL'], x['GROUPNAME']))


def render_metodologia():
    return """
    <div class="card">
        <h2 class="card-header">Metodologia</h2>
        <ol style="line-height: 1.8; padding-left: 1.4rem;">
            <li>O Maximo registra, na tabela interna <code>APPLICATIONAUTH</code>, cada combinação de
                <strong>grupo de segurança + aplicação + permissão</strong> concedida.</li>
            <li>Nas 3 aplicações de Compras — Requisição (<code>PLUSGPR</code>), Ordem de Compra
                (<code>PLUSGPO</code>) e Requisição Simplificada (<code>CREATEDR</code>) — separamos as
                permissões em dois papéis: <strong>Emissor</strong> (<code>INSERT</code>, <code>SAVE</code>,
                <code>WAPPR</code> = submeter para aprovação) e <strong>Aprovador</strong>
                (<code>APPR</code>/<code>APPROVE</code>, <code>UNAPPROVE</code>).</li>
            <li>Para cada grupo, em cada uma das 7 bases, verificamos se ele tem <strong>pelo menos uma
                permissão de Emissor E pelo menos uma de Aprovador na mesma aplicação</strong>. Isso não é
                estimativa — é leitura direta do que o grupo permite fazer.</li>
            <li>Os dados vêm de extração direta do banco de produção Maximo dos 7 ambientes, cruzados com
                <code>GROUPUSER</code> (quem está em cada grupo) e <code>MAXGROUP</code> (descrição do grupo).</li>
            <li><code>MAXADMIN</code> foi excluído da lista de conflito — administrador de sistema ter
                acesso total é esperado e tratado separadamente na tabela de Governança de Superusuário abaixo.</li>
            <li><strong>Evidência real (não teórica):</strong> além de mapear quem <em>poderia</em> fazer as
                duas coisas, cruzamos o histórico de workflow (<code>WFTRANSACTION</code>, que registra quem
                de fato clicou em cada ação) com a Requisição de Compra (<code>PR</code>) para achar casos
                onde a mesma pessoa realmente submeteu <strong>e</strong> aprovou o mesmo documento — com
                número da requisição, valor e datas. Isso confirma que o risco não é apenas de desenho, já
                aconteceu na prática.</li>
            <li><strong>Deduplicação:</strong> os 7 bancos de compras retornaram o mesmo PRNUM, mesma pessoa e
                timestamps idênticos ao microssegundo — ou seja, replicam a mesma base de dados de compras.
                Sem deduplicar por (site, PR, pessoa, datas), cada caso real apareceria ~7x e infracionaria os
                números abaixo. Já removido: os totais mostrados são de casos únicos.</li>
            <li><strong>Confronto por unidade (site):</strong> um usuário pode ter grupo emissor numa unidade
                e, por embarque temporário em outra sonda, grupo aprovador numa unidade diferente — isso
                <em>não</em> seria conflito real, pois ele nunca acumularia os dois poderes no mesmo local.
                Por isso, os casos de "Nível 2 — grupos diferentes" só entram na lista depois de confrontar a
                autorização por site de cada grupo (<code>SITEAUTH</code>/<code>AUTHALLSITES</code> do
                <code>MAXGROUP</code>) — só ficam se o grupo emissor e o grupo aprovador realmente se
                sobrepõem no mesmo site.</li>
            <li><strong>Papel sugerido por pessoa:</strong> para cada grupo/site que precisa ser dividido,
                indicamos um candidato natural a manter a aprovação — o cargo mais sênior identificado dentro
                daquele mesmo grupo/site (cargo vem do PERSONGROUPVIEW do Maximo, cruzado por pessoa em
                qualquer um dos 7 ambientes). Isto é uma <strong>heurística de hierarquia offshore O&amp;G,
                não uma regra estatística nem uma decisão automática</strong> — é ponto de partida para a
                liderança local confirmar. Quando ninguém no grupo/site tem cargo de liderança identificado,
                marcamos "Indefinido" em vez de arriscar um palpite.</li>
            <li><strong>Severidade (procedimento oficial "Tutorial de Criação de PR"):</strong> a alçada de
                aprovação é iniciada no Coordenador de Manutenção e, acima de um limite de valor, passa
                obrigatoriamente pelo Engenheiro de Ativos — roteamento logado no sistema como
                <code>OOG_PRWENG</code>. Por isso, nem todo caso de "mesma pessoa submeteu e aprovou" é
                violação: <strong>Crítico</strong> = o sistema exigiu a 2ª instância e mesmo assim uma só
                pessoa completou tudo; <strong>Revisar regra</strong> = instância única, possivelmente dentro
                do desenho para valores abaixo do limite.</li>
            <li><strong>Autoaprovação direta (o teste mais direto):</strong> a tabela <code>PR</code> tem um
                campo próprio, <code>OOG_REQUESTEDBY</code>, que registra quem <em>de fato</em> pediu o item —
                diferente do campo genérico <code>REQUESTEDBY</code>, que costuma ser só a conta compartilhada
                do rig. Quando essa mesma pessoa também aparece como quem aprovou (<code>PR APPR</code>), é
                autoaprovação da própria compra — não depende de nenhuma nuance de alçada ou valor. Extraído
                apenas do ambiente BASE, que replica ~97% dos dados reais das unidades.</li>
            <li><strong>Por que PO (Ordem de Compra) não tem uma camada de evidência real como a PR:</strong>
                verificamos e <code>WFTRANSACTION</code> tem <strong>zero</strong> linhas para
                <code>OWNERTABLE='PO'</code> em toda a base — este Maximo não registra quem clicou
                submeter/aprovar em PO. Também testamos <code>PO.PURCHASEAGENT</code> (comprador responsável)
                contra <code>PO.CHANGEBY</code> (quem alterou por último): bateu em 87% das PO aprovadas, mas
                ao excluir a conta <code>MAXADMIN</code> o número foi a zero — é 100% um processo em lote
                automatizado, não sinal real de autoaprovação humana. Por isso, para PO só reportamos o
                Nível 1/2 estrutural (grupos e pessoas com o conflito), na seção dedicada abaixo.</li>
            <li><strong>Cadeia PR → PO (novo teste):</strong> a tabela <code>PRLINE</code> liga a PR à PO
                gerada a partir dela (<code>PRLINE.PONUM</code>), e o próprio <code>WFTRANSACTION</code> da PR
                registra quem disparou essa conversão (<code>ACTIONPERFORMED='OOG_CREAPOGRP'</code>).
                Testamos se a mesma pessoa que aprovou a PR (<code>PR APPR</code>) também foi quem gerou a PO
                — contra os 2.670 eventos históricos de conversão, <strong>0 sobreposições</strong>: controle
                limpo na prática. A camada fica ativa (não é só um texto) para acusar automaticamente se isso
                mudar.</li>
            <li><strong>Moeda dos valores (auditoria 2026-07-11):</strong> 100% das PRs dos últimos 365 dias
                têm <code>CURRENCYCODE='USD'</code> (16.912 de 16.912, verificado direto no banco). Todos os
                valores de documento exibidos nesta aba são <strong>dólares americanos (USD)</strong>, não
                reais. Os totais também são somados por <strong>PR única</strong> (site + número): uma PR
                resubmetida N vezes pela mesma pessoa gera N casos no histórico de workflow, mas o valor do
                documento conta uma vez só.</li>
            <li><strong>Leitura correta do número de CREATEDR (Requisição Simplificada):</strong> a maior
                parte das pessoas do Nível 2 vem de <code>CREATEDR</code> — mas isso é um <em>problema de
                desenho da aplicação</em>, não centenas de anomalias individuais: <strong>todos os grupos</strong>
                que têm qualquer acesso a CREATEDR recebem o pacote completo (criar + submeter + aprovar juntos),
                incluindo grupos de equipe inteira como <code>OOG_DEPARTMENT_TEAM</code>. A correção é uma só
                (separar as permissões no desenho dos grupos da aplicação), não caso a caso — use o filtro por
                aplicação da tabela do Nível 2 para ver PR e PO isoladamente, onde o conflito é mais restrito e
                individual.</li>
            <li><strong>Nota de governança (não é achado de SoD):</strong> a norma corporativa de aquisições
                (FORESEA-DZ-022) define alçada de aprovação de PO por faixa de valor (Comprador → Coordenador
                de Suprimentos → Gerente de Suprimentos → Gerente Executivo de Suprimentos → VPE de
                Suprimentos). Não encontramos grupo de segurança no Maximo correspondente a essa hierarquia —
                os grupos que hoje aprovam PO são de Coordenação de Materiais/Manutenção por unidade, não de
                Suprimentos por valor. Ou essa alçada é controlada fora do Maximo, ou não está tecnicamente
                reforçada no sistema — vale confirmar com Suprimentos, é um ponto separado do SoD emissor x
                aprovador.</li>
        </ol>
    </div>
    """


def render_perfil_cargo_section(group_baseline_data):
    """Seção 'Perfil de Acesso por Cargo': para cargos com amostra suficiente
    de pares na mesma unidade, compara os grupos de cada pessoa com o padrão
    do cargo ali — sinaliza excesso (grupo que ela tem e o cargo normalmente
    não tem) e falta (grupo que o cargo tem e ela não tem). Diferente do
    'Papel Sugerido' do Nível 2 (que só arbitra emissor x aprovador dentro de
    um conflito de Compras), isto cobre todos os grupos do Maximo."""
    if not group_baseline_data:
        return ''

    stats = group_baseline_data.get('stats', {})
    deviation_rows = group_baseline_data.get('deviation_rows', [])
    profile_rows = group_baseline_data.get('profile_rows', [])

    deviation_table_rows = []
    for d in deviation_rows:
        deviation_table_rows.append(
            f'<tr><td>{d["ENVIRONMENT"]}</td><td>{d["USERID"]}</td><td>{d["DISPLAYNAME"]}</td>'
            f'<td>{d["TITLE"]}</td><td>{d["COHORT_SIZE"]}</td>'
            f'<td>{d["GRUPOS_EXCESSO"] or "—"}</td><td>{d["GRUPOS_FALTANTES"] or "—"}</td></tr>'
        )

    profile_table_rows = [
        [p['ENVIRONMENT'], p['TITLE'], p['QTD_PESSOAS'], p['QTD_GRUPOS_PADRAO'], p['GRUPOS_PADRAO']]
        for p in profile_rows
    ]

    return f"""
    <div class="card" id="secao-perfil-cargo">
        <h2 class="card-header">Perfil de Acesso por Cargo — Excesso e Falta de Grupos</h2>
        <p class="card-desc">Para cargos com pelo menos 3 pessoas ativas na mesma unidade, calculamos o
        conjunto de grupos que é o padrão daquele cargo ali (grupo que ≥60% dos pares tem) e
        comparamos com o que cada pessoa individualmente possui. Diferente do "Papel Sugerido"
        do Nível 2 acima (que só decide quem fica como emissor/aprovador dentro de um conflito de Compras já
        identificado): isto cobre todos os grupos do Maximo, não só os de Compras.</p>
        <p class="card-footnote">Cobertura é naturalmente pequena: cargo tem dado em ~57%
        das contas ativas, e a maioria dos {_br_number(stats.get('total_titulos_distintos', 0))} cargos com
        amostra confiável tem só 3-8 pares na mesma unidade — número reportado é o que os dados sustentam com
        confiança, não uma cobertura completa da base.</p>
        <div class="stats-grid" style="margin-bottom: 1rem;">
            <div class="stat-card">
                <div class="stat-value">{_br_number(stats.get('total_cohorts_com_baseline', 0))}</div>
                <div class="stat-title">Cargos com Baseline Confiável</div>
            </div>
            <div class="stat-card border-danger">
                <div class="stat-value">{_br_number(stats.get('total_pessoas_com_excesso', 0))}</div>
                <div class="stat-title">Pessoas com Excesso de Acesso</div>
            </div>
            <div class="stat-card border-warning">
                <div class="stat-value">{_br_number(stats.get('total_pessoas_com_falta', 0))}</div>
                <div class="stat-title">Pessoas com Falta de Acesso</div>
            </div>
        </div>
        <h3 style="margin-top:1rem;">Pessoas com Desvio do Baseline do Cargo ({_br_number(len(deviation_rows))})</h3>
        <div class="search-container">
            <input type="text" id="searchPerfilCargo" class="search-bar" onkeyup="filterPerfilCargoTable()" placeholder="Pesquisar por USERID, nome, cargo...">
        </div>
        <div class="table-responsive">
            <table id="table-perfil-cargo" class="gov-table">
                <thead><tr><th>Ambiente</th><th>USERID</th><th>Nome</th><th>Cargo</th><th>Pares no Cargo</th>
                <th>Excesso (tem, cargo normalmente não tem)</th><th>Falta (cargo tem, ela não tem)</th></tr></thead>
                <tbody>{''.join(deviation_table_rows) if deviation_table_rows else '<tr><td colspan="7" style="text-align:center; color:#64748b;">Nenhum desvio encontrado.</td></tr>'}</tbody>
            </table>
        </div>
        <h3 style="margin-top:1.2rem;">Perfil (Baseline) por Cargo/Unidade ({_br_number(len(profile_rows))})</h3>
        {render_table(['Ambiente', 'Cargo', 'Qtd Pessoas', 'Qtd Grupos Padrão', 'Grupos Padrão'], profile_table_rows, 'table-perfil-cargo-baseline', 'gov-table')}
    </div>
    """


def render_padronizacao_section(role_standardization_data):
    """Seção 'Padronização de Acesso para Terceirizada': diferente da seção
    de Perfil de Acesso por Cargo acima (que compara CADA unidade com o
    padrão dela mesma), aqui o objetivo é PRESCRITIVO — um cargo, um grupo
    padrão único para TODAS as unidades, mais os grupos de hoje que são o
    mesmo papel com nomes diferentes por unidade (candidatos a fusão)."""
    if not role_standardization_data:
        return ''

    stats = role_standardization_data.get('stats', {})
    role_targets = role_standardization_data.get('role_targets', [])
    duplicate_clusters = role_standardization_data.get('duplicate_group_clusters', [])

    role_table_rows = []
    for t in role_targets:
        consistente = t['CONSISTENTE_ENTRE_UNIDADES']
        badge = (
            '<span class="badge badge-success">Padronizado</span>' if consistente
            else '<span class="badge badge-critical">Inconsistente</span>'
        )
        role_table_rows.append(
            f'<tr data-consistente="{"SIM" if consistente else "NAO"}">'
            f'<td>{t["CARGO_NORMALIZADO"]}</td><td>{t["QTD_PESSOAS"]}</td><td>{t["AMBIENTES"]}</td>'
            f'<td><strong>{t["GRUPO_PADRAO_RECOMENDADO"] or "—"}</strong></td>'
            f'<td>{badge}</td><td>{t["UNIDADES_SEM_O_GRUPO_PADRAO"] or "—"}</td>'
            f'<td>{t["ACAO"]}</td></tr>'
        )

    cluster_table_rows = []
    for c in duplicate_clusters:
        if c['ALERTA_PRIVILEGIO_DIFERENTE']:
            alerta = '<span class="badge badge-critical">Níveis de privilégio com permissão igual — revisar antes de fundir</span>'
        elif c.get('ALERTA_NOMES_DIVERGENTES'):
            alerta = '<span class="badge badge-warning">Papéis nominalmente distintos — confirmar com a área antes de fundir</span>'
        else:
            alerta = ''
        cluster_table_rows.append(
            [c['CANONICO'], '; '.join(c['MEMBROS']), c['QTD_MEMBROS'], c['DESCRICOES'], alerta]
        )

    return f"""
    <div class="card" id="secao-padronizacao">
        <h2 class="card-header">Padronização de Acesso — Material para a Terceirizada</h2>
        <p class="card-desc">Diferente da seção "Perfil de Acesso por Cargo" acima (que compara cada unidade
        com o padrão dela mesma): aqui o objetivo é definir um único grupo padrão por cargo, igual em
        todas as unidades — a especificação para a terceirizada criar/atribuir os grupos corretos.</p>
        <p class="card-footnote">Metodologia: grupos de unidades diferentes com nomes
        parecidos (ex.: <code>HTQ_MATERIALS_COORDINATOR</code> vs <code>POL_MATERIALS_COORDINATOR</code>) só são
        tratados como "o mesmo grupo" quando a permissão real (todas as aplicações, não só nome) bate em ≥95%
        — evita recomendar fusão de grupos com escopo de acesso diferente só porque o nome é parecido. Cargo é
        normalizado (ex.: "Coordenador de Manutenção" = "Maintenance Coordinator" quando já vêm na mesma string
        PT/EN); cargos sem essa combinação explícita aparecem separados e devem ser revisados manualmente.</p>
        <div class="stats-grid" style="margin-bottom: 1rem;">
            <div class="stat-card">
                <div class="stat-value">{_br_number(stats.get('total_cargos_normalizados_com_amostra', 0))}</div>
                <div class="stat-title">Cargos Analisados</div>
            </div>
            <div class="stat-card border-danger">
                <div class="stat-value">{_br_number(stats.get('total_cargos_inconsistentes', 0))}</div>
                <div class="stat-title">Cargos com Acesso Inconsistente Entre Unidades</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{_br_number(stats.get('total_clusters_duplicados', 0))}</div>
                <div class="stat-title">Clusters de Grupos Duplicados</div>
            </div>
        </div>
        <h3>Grupos Duplicados/Quase-Idênticos (candidatos a fusão)</h3>
        {render_table(['Nome Canônico Sugerido', 'Grupos Equivalentes de Hoje', 'Qtd', 'Descrições', 'Alerta'], cluster_table_rows, 'table-padronizacao-clusters', 'gov-table')}
        <h3 style="margin-top:1.2rem;">Cargo → Grupo Padrão Recomendado ({_br_number(len(role_targets))})</h3>
        <div class="search-container">
            <input type="text" id="searchPadronizacao" class="search-bar" onkeyup="filterPadronizacaoTable()" placeholder="Pesquisar por cargo, grupo...">
            <select id="selPadronizacaoStatus" class="filter-select" onchange="filterPadronizacaoTable()">
                <option value="">Todos</option>
                <option value="NAO">Só Inconsistentes</option>
                <option value="SIM">Só Padronizados</option>
            </select>
        </div>
        <div class="table-responsive">
            <table id="table-padronizacao-cargo" class="gov-table">
                <thead><tr><th>Cargo (normalizado)</th><th>Pessoas</th><th>Unidades</th>
                <th>Grupo Padrão Recomendado</th><th>Status</th><th>Unidades Faltando o Grupo</th><th>Ação</th></tr></thead>
                <tbody>{''.join(role_table_rows)}</tbody>
            </table>
        </div>
    </div>
    """


def render_tab_seguranca(security_audit_data, group_baseline_data=None, role_standardization_data=None):
    if not security_audit_data:
        return """
        <div id="tab-seguranca" class="container tab-content">
            <div class="card"><p>Dados de segurança não disponíveis. Execute a extração de
            <code>applicationauth</code> e rode o pipeline novamente.</p></div>
        </div>
        """

    stats = security_audit_data['stats']
    group_rows_data = _dedupe_group_conflicts(security_audit_data['group_conflicts'])
    group_table_rows = [
        [g['GROUPNAME'], g['APP_LABEL'], g['AMBIENTES'], g['QTD_AMBIENTES'],
         g['OPCOES_EMISSOR'], g['OPCOES_APROVADOR'], g['DESCRIPTION'], g['RECOMENDACAO']]
        for g in group_rows_data
    ]

    # A combinação de 2 grupos (GRUPOS_DIFERENTES) é uma categoria rara e
    # sempre relevante — mantida na tabela mesmo se o STATUS da identidade
    # estiver em branco (comum em contas de serviço com cadastro incompleto,
    # ex.: ITEAM). Sem isto, o card "Por Combinação de 2 Grupos" contava um
    # número que a tabela abaixo nunca conseguia mostrar.
    active_user_rows = [
        c for c in security_audit_data['user_conflicts']
        if c['ORIGEM_CONFLITO'] == 'GRUPOS_DIFERENTES'
        or c.get('STATUS', '').strip().upper() in ('ACTIVE', 'ATIVO', 'ENABLED')
    ]
    shown_users = active_user_rows[:300]
    PAPEL_BADGE = {
        'APROVADOR (sugestão)': '<span class="badge badge-success">Aprovador</span>',
        'EMISSOR (sugestão)': '<span class="badge badge-neutral">Emissor</span>',
        'INDEFINIDO': '<span class="badge badge-warning">Indefinido</span>',
    }
    user_table_rows = []
    for c in shown_users:
        origem = c['ORIGEM_CONFLITO']
        papel = c.get('PAPEL_RECOMENDADO', 'INDEFINIDO')
        justificativa = c.get('JUSTIFICATIVA_PAPEL', '').replace('"', '&quot;')
        user_table_rows.append(
            f'<tr data-origem="{origem}">'
            f'<td>{c["ENVIRONMENT"]}</td><td>{c["USERID"]}</td><td>{c["DISPLAYNAME"]}</td>'
            f'<td>{c["TITLE"]}</td><td>{c["APP_LABEL"]}</td><td>{c["GRUPOS_EMISSOR"]}</td>'
            f'<td>{c["GRUPOS_APROVADOR"]}</td>'
            f'<td>{"Mesmo Grupo" if origem == "MESMO_GRUPO" else "Grupos Diferentes"}</td>'
            f'<td title="{justificativa}">{PAPEL_BADGE.get(papel, papel)}</td>'
            f'<td>{c["RECOMENDACAO"]}</td></tr>'
        )

    by_app = stats.get('distinct_users_active_by_app', {})
    app_badges = ''.join(
        f'<span style="background:var(--danger-bg,#fef2f2); color:var(--danger); border:1px solid var(--danger); '
        f'border-radius:6px; padding:0.2rem 0.6rem; font-size:0.8rem; margin-right:0.4rem;">'
        f'{app} · {_br_number(qtd)} pessoas ativas</span>'
        for app, qtd in sorted(by_app.items())
    )

    truncation_html = ''
    if len(active_user_rows) > len(shown_users):
        truncation_html = (
            f'<p class="card-footnote">'
            f'Mostrando {_br_number(len(shown_users))} de {_br_number(len(active_user_rows))} pessoas (ativas + casos raros de combinação de grupos). '
            f'Lista completa no Excel, aba <strong>19_SoD_Pessoas</strong>.</p>'
        )

    self_approval_evidence = security_audit_data.get('self_approval_evidence', [])
    self_approval_table_rows = []
    for e in self_approval_evidence:
        status_pessoa = e.get('STATUS_PESSOA', '')
        status_pessoa_html = (
            f'<span class="badge badge-neutral">{status_pessoa}</span>' if status_pessoa.strip().upper() in ('ACTIVE', 'ATIVO', 'ENABLED')
            else f'<span class="badge badge-warning">{status_pessoa or "?"}</span>'
        )
        self_approval_table_rows.append(
            f'<tr>'
            f'<td>{e["SITEID"]}</td><td>{e["PRNUM"]}</td><td>{e["DESCRIPTION"]}</td>'
            f'<td>USD {e["TOTALCOST"]:,.2f}</td><td>{e["STATUS"]}</td>'
            f'<td><strong>{e["SOLICITANTE_REAL"]}</strong></td>'
            f'<td>{e.get("NOME_PESSOA", "")}</td><td>{e.get("TITULO_PESSOA", "")}</td><td>{status_pessoa_html}</td>'
            f'<td>{e["DATA_APROVACAO"][:19]}</td></tr>'
        )

    real_evidence = security_audit_data.get('real_evidence', [])
    # Casos CRÍTICOS (sistema exigiu 2ª instância e mesma pessoa aprovou
    # sozinha) primeiro — são o achado mais grave e o mais raro (~1%).
    real_evidence_sorted = sorted(real_evidence, key=lambda e: e.get('SEVERIDADE') != 'CRITICO')
    shown_evidence = real_evidence_sorted[:150]
    SEVERIDADE_BADGE = {
        'CRITICO': '<span class="badge badge-critical">Crítico</span>',
        'REVISAR_REGRA': '<span class="badge badge-neutral">Revisar regra</span>',
    }
    evidence_table_rows = []
    for e in shown_evidence:
        sev = e.get('SEVERIDADE', 'REVISAR_REGRA')
        status_pessoa = e.get('STATUS_PESSOA', '')
        status_pessoa_html = (
            f'<span class="badge badge-neutral">{status_pessoa}</span>' if status_pessoa.strip().upper() in ('ACTIVE', 'ATIVO', 'ENABLED')
            else f'<span class="badge badge-warning">{status_pessoa or "?"}</span>'
        )
        evidence_table_rows.append(
            f'<tr data-severidade="{sev}">'
            f'<td>{SEVERIDADE_BADGE.get(sev, sev)}</td>'
            f'<td>{e["SITEID"]}</td><td>{e["PRNUM"]}</td><td>{e["DESCRIPTION"]}</td>'
            f'<td>USD {e["TOTALCOST"]:,.2f}</td><td>{e["STATUS"]}</td><td>{e["PERSONID"]}</td>'
            f'<td>{e.get("NOME_PESSOA", "")}</td><td>{e.get("TITULO_PESSOA", "")}</td><td>{status_pessoa_html}</td>'
            f'<td>{e["DATA_SUBMISSAO"][:19]}</td><td>{e["DATA_APROVACAO"][:19]}</td></tr>'
        )
    evidence_truncation_html = ''
    if len(real_evidence) > len(shown_evidence):
        evidence_truncation_html = (
            f'<p class="card-footnote">'
            f'Mostrando {_br_number(len(shown_evidence))} de {_br_number(len(real_evidence))} casos documentados '
            f'(últimos 365 dias). Lista completa no Excel, aba <strong>20_SoD_Evidencias</strong>.</p>'
        )

    maxadmin_rows = security_audit_data.get('maxadmin_users', [])
    maxadmin_table_rows = [
        [m['ENVIRONMENT'], m['USERID'], m['DISPLAYNAME'], m['TITLE'], m['STATUS']]
        for m in maxadmin_rows
    ]

    # ---- PO (Ordem de Compra) — recorte dedicado do Nível 1/2 ----
    po_group_rows_data = _dedupe_group_conflicts(security_audit_data.get('po_group_conflicts', []))
    po_group_table_rows = [
        [g['GROUPNAME'], g['AMBIENTES'], g['QTD_AMBIENTES'],
         g['OPCOES_EMISSOR'], g['OPCOES_APROVADOR'], g['DESCRIPTION'], g['RECOMENDACAO']]
        for g in po_group_rows_data
    ]
    po_user_conflicts = security_audit_data.get('po_user_conflicts', [])
    po_user_table_rows = []
    for c in po_user_conflicts:
        origem = c['ORIGEM_CONFLITO']
        papel = c.get('PAPEL_RECOMENDADO', 'INDEFINIDO')
        justificativa = c.get('JUSTIFICATIVA_PAPEL', '').replace('"', '&quot;')
        po_user_table_rows.append(
            f'<tr>'
            f'<td>{c["ENVIRONMENT"]}</td><td>{c["USERID"]}</td><td>{c["DISPLAYNAME"]}</td>'
            f'<td>{c["TITLE"]}</td><td>{c["GRUPOS_EMISSOR"]}</td><td>{c["GRUPOS_APROVADOR"]}</td>'
            f'<td>{"Mesmo Grupo" if origem == "MESMO_GRUPO" else "Grupos Diferentes"}</td>'
            f'<td title="{justificativa}">{PAPEL_BADGE.get(papel, papel)}</td></tr>'
        )

    # ---- Cadeia PR -> PO: mesma pessoa aprovou a PR e gerou a PO dela ----
    pr_po_chain_evidence = security_audit_data.get('pr_po_chain_evidence', [])
    pr_po_chain_table_rows = []
    for e in pr_po_chain_evidence:
        pr_po_chain_table_rows.append(
            f'<tr>'
            f'<td>{e["SITEID"]}</td><td>{e["PRNUM"]}</td><td>{e["PONUM_GERADA"]}</td>'
            f'<td>{e["DESCRIPTION"]}</td><td>USD {e["TOTALCOST"]:,.2f}</td>'
            f'<td><strong>{e["PERSONID"]}</strong></td><td>{e.get("NOME_PESSOA", "")}</td>'
            f'<td>{e.get("TITULO_PESSOA", "")}</td>'
            f'<td>{e["DATA_APROVACAO_PR"][:19]}</td><td>{e["DATA_CRIACAO_PO"][:19]}</td></tr>'
        )

    return f"""
    <div id="tab-seguranca" class="container tab-content">
        <div class="card">
            <h2 class="card-header">Segregação de Funções — Emissor x Aprovador (Compras)</h2>
            <p class="card-desc">Clique num card para ir direto à tabela correspondente.</p>
            <div class="stats-grid" style="margin-bottom: 1rem;">
                <div class="stat-card sod-clickable border-danger" onclick="sodGoTo('secao-nivel1')">
                    <div class="stat-value">{_br_number(len(group_rows_data))}</div>
                    <div class="stat-title">Grupos Conflitantes</div>
                    <div class="stat-subtitle">Nível 1 — ver tabela abaixo</div>
                </div>
                <div class="stat-card sod-clickable border-danger" id="card-sod-todos" onclick="sodFilterUsers('all', this)">
                    <div class="stat-value">{_br_number(stats['distinct_users_active'])}</div>
                    <div class="stat-title">Pessoas Ativas Afetadas</div>
                    <div class="stat-subtitle">Nível 2 — ver tabela abaixo</div>
                </div>
                <div class="stat-card sod-clickable border-warning" id="card-sod-combo" onclick="sodFilterUsers('GRUPOS_DIFERENTES', this)">
                    <div class="stat-value">{_br_number(stats['total_user_conflicts_grupos_diferentes'])}</div>
                    <div class="stat-title">Por Combinação de 2 Grupos</div>
                    <div class="stat-subtitle">Filtrar Nível 2 por este tipo</div>
                </div>
                <div class="stat-card sod-clickable border-accent" onclick="sodGoTo('secao-padronizacao')">
                    <div class="stat-value">{_br_number((role_standardization_data or {}).get('stats', {}).get('total_cargos_inconsistentes', 0))}</div>
                    <div class="stat-title">Cargos com Acesso Inconsistente</div>
                    <div class="stat-subtitle">Padronização para Terceirizada — ver tabela abaixo</div>
                </div>
                <div class="stat-card sod-clickable border-neutral" onclick="sodGoTo('secao-maxadmin')">
                    <div class="stat-value">{_br_number(stats['total_maxadmin_users'])}</div>
                    <div class="stat-title">Usuários MAXADMIN</div>
                    <div class="stat-subtitle">Fora do escopo — ver tabela abaixo</div>
                </div>
                <div class="stat-card sod-clickable border-warning" onclick="sodGoTo('secao-po')">
                    <div class="stat-value">{_br_number(stats.get('total_po_group_conflicts', 0))}</div>
                    <div class="stat-title">PO — Conflitos Dedicados</div>
                    <div class="stat-subtitle">{_br_number(stats.get('total_po_user_conflicts_active', 0))} pessoas ativas — ver tabela abaixo</div>
                </div>
                <div class="stat-card sod-clickable border-danger" onclick="sodGoTo('secao-perfil-cargo')">
                    <div class="stat-value">{_br_number((group_baseline_data or {}).get('stats', {}).get('total_pessoas_com_excesso', 0))}</div>
                    <div class="stat-title">Excesso de Acesso por Cargo</div>
                    <div class="stat-subtitle">Perfil de Acesso por Cargo — ver tabela abaixo</div>
                </div>
                <div class="stat-card sod-clickable stat-card-danger" onclick="sodGoTo('secao-evidencia')">
                    <div class="stat-value">{_br_number(stats.get('total_critical_evidence_cases', 0))}</div>
                    <div class="stat-title">Casos Críticos Confirmados</div>
                    <div class="stat-subtitle">USD {stats.get('total_critical_evidence_value', 0):,.2f}, {_br_number(stats.get('total_critical_evidence_people', 0))} pessoas — sistema exigiu 2ª instância e não teve</div>
                </div>
                <div class="stat-card sod-clickable stat-card-danger" onclick="sodGoTo('secao-autoaprovacao')">
                    <div class="stat-value">{_br_number(stats.get('total_self_approval_cases', 0))}</div>
                    <div class="stat-title">Autoaprovação Direta</div>
                    <div class="stat-subtitle">USD {stats.get('total_self_approval_value', 0):,.2f}, {_br_number(stats.get('total_self_approval_people', 0))} pessoas — solicitante real aprovou a própria compra</div>
                </div>
            </div>
            <div>{app_badges}</div>
        </div>

        {render_metodologia()}

        <div class="card" id="secao-autoaprovacao">
            <h2 class="card-header">Autoaprovação Direta — Solicitante Aprovou a Própria Compra</h2>
            <p class="card-desc">O achado mais direto de toda a auditoria: a tabela <code>PR</code> tem um campo próprio
            (<code>OOG_REQUESTEDBY</code>) que registra quem de fato pediu o item — diferente do campo genérico
            <code>REQUESTEDBY</code>, que normalmente é só a conta compartilhada do rig (ex.: <code>ODN1001</code>). Aqui, essa
            mesma pessoa também aprovou (<code>PR APPR</code>) — não depende de nenhuma nuance de alçada ou limite de valor.
            Extraído apenas do ambiente BASE (~97% de cobertura real das unidades).</p>
            <div class="table-responsive">
                <table id="table-sod-self-approval" class="gov-table">
                    <thead><tr><th>Site</th><th>PR</th><th>Descrição</th><th>Valor (USD)</th><th>Status</th>
                    <th>Solicitante = Aprovador</th><th>Nome</th><th>Título/Cargo</th><th>Status Pessoa</th>
                    <th>Aprovou em</th></tr></thead>
                    <tbody>{''.join(self_approval_table_rows)}</tbody>
                </table>
            </div>
        </div>

        <div class="card" id="secao-evidencia">
            <h2 class="card-header">Evidência Real — Casos Documentados</h2>
            <p class="card-desc">Requisições de compra reais onde a mesma pessoa submeteu (<code>PR WAPPR</code>)
            e aprovou (<code>PR APPR</code>) o mesmo documento — com número, valor e datas, extraído do
            histórico de workflow do próprio Maximo. Últimos 365 dias. Os 7 bancos replicam a mesma base de
            compras (confirmado por timestamps idênticos ao microssegundo) — já deduplicado, cada caso conta uma vez.
            Não cobre PO: o workflow de PO não é registrado nesta tabela de histórico nesta instalação.</p>
            <p class="card-desc"><strong>Crítico</strong>: conforme o procedimento oficial (Tutorial de Criação de PR),
            o sistema roteou esta PR para a 2ª instância (Engenheiro de Ativos) — mesmo assim, a mesma pessoa que submeteu
            também aprovou, sem um segundo revisor real. <strong>Revisar regra</strong>: nenhum roteamento de 2ª instância foi
            disparado — aprovação em instância única, possivelmente dentro do desenho para valores abaixo do limite; ainda
            vale checar se o limite está calibrado corretamente.</p>
            <div class="search-container">
                <input type="text" id="searchSoDEvidence" class="search-bar" onkeyup="filterSoDEvidenceTable()" placeholder="Pesquisar por PR, pessoa, descrição...">
                <select id="selSoDEvidenceSev" class="filter-select" onchange="filterSoDEvidenceTable()">
                    <option value="">Todas as Severidades</option>
                    <option value="CRITICO">Crítico</option>
                    <option value="REVISAR_REGRA">Revisar regra</option>
                </select>
            </div>
            <div class="table-responsive">
                <table id="table-sod-evidence" class="gov-table">
                    <thead><tr><th>Severidade</th><th>Site</th><th>PR</th><th>Descrição</th><th>Valor (USD)</th>
                    <th>Status</th><th>Submeteu E Aprovou (mesma pessoa)</th><th>Nome</th><th>Título/Cargo</th>
                    <th>Status Pessoa</th><th>Submeteu em</th><th>Aprovou em</th></tr></thead>
                    <tbody>{''.join(evidence_table_rows)}</tbody>
                </table>
            </div>
            {evidence_truncation_html}
        </div>

        <div class="card" id="secao-po">
            <h2 class="card-header">Ordem de Compra (PO) — Recorte Dedicado</h2>
            <p class="card-desc">Mesmo Nível 1/2 já calculado acima, isolado só para <code>PLUSGPO</code> — sem
            misturar com PR/Requisição Simplificada. PO não tem camada de evidência real (ver nota na metodologia):
            <code>WFTRANSACTION</code> não registra workflow de PO nesta instalação, e o teste alternativo
            (comprador = quem alterou por último) deu 100% ruído de automação (<code>MAXADMIN</code>).</p>
            <h3 style="margin-top:1.2rem;">Grupos Estruturalmente Conflitantes em PO ({len(po_group_rows_data)})</h3>
            {render_table(['Grupo', 'Ambientes', 'Qtd Ambientes', 'Opções Emissor', 'Opções Aprovador', 'Descrição', 'Recomendação'], po_group_table_rows, 'table-sod-po-groups', 'gov-table') if po_group_table_rows else '<p class="card-desc">Nenhum grupo conflitante encontrado em PO.</p>'}
            <h3 style="margin-top:1.2rem;">Pessoas Ativas com o Conflito em PO ({len(po_user_conflicts)})</h3>
            <div class="table-responsive">
                <table id="table-sod-po-users" class="gov-table">
                    <thead><tr><th>Ambiente</th><th>USERID</th><th>Nome</th><th>Título</th>
                    <th>Grupos Emissor</th><th>Grupos Aprovador</th><th>Origem</th><th>Papel Sugerido</th></tr></thead>
                    <tbody>{''.join(po_user_table_rows) if po_user_table_rows else '<tr><td colspan="8" style="text-align:center; color:#64748b;">Nenhuma pessoa ativa encontrada.</td></tr>'}</tbody>
                </table>
            </div>
        </div>

        <div class="card" id="secao-pr-po-chain">
            <h2 class="card-header">Cadeia PR → PO — Mesma Pessoa Aprovou a PR e Gerou a PO</h2>
            <p class="card-desc">Teste novo: a PR aprovada vira PO (link real via <code>PRLINE.PONUM</code>).
            Verificamos se a mesma pessoa que aprovou a PR (<code>PR APPR</code>) também disparou a criação da
            PO dela (<code>OOG_CREAPOGRP</code>). Checado contra <strong>2.670</strong> conversões históricas de
            PR em PO (toda a base, sem filtro de data).</p>
            {f'<div class="table-responsive"><table id="table-sod-pr-po-chain" class="gov-table"><thead><tr><th>Site</th><th>PR</th><th>PO Gerada</th><th>Descrição</th><th>Valor (USD)</th><th>Pessoa</th><th>Nome</th><th>Título/Cargo</th><th>Aprovou PR em</th><th>Gerou PO em</th></tr></thead><tbody>{"".join(pr_po_chain_table_rows)}</tbody></table></div>' if pr_po_chain_table_rows else '<p class="card-desc">0 casos encontrados — controle limpo na prática: em nenhum dos 2.670 casos verificados a mesma pessoa aprovou a PR e gerou a PO. Camada mantida ativa para acusar automaticamente se isso mudar.</p>'}
        </div>

        <div class="card" id="secao-nivel1">
            <h2 class="card-header">Nível 1 — Grupos Estruturalmente Conflitantes ({len(group_rows_data)} grupos distintos)</h2>
            <p class="card-desc">Estes grupos, por definição, concedem emissão E aprovação na mesma aplicação —
            qualquer pessoa alocada neles nasce com o conflito, independente de qualquer outro grupo que tenha.</p>
            <div class="search-container">
                <input type="text" id="searchSoDGroup" class="search-bar" onkeyup="filterSoDGroupTable()" placeholder="Pesquisar por grupo, aplicação...">
            </div>
            {render_table(['Grupo', 'Aplicação', 'Ambientes', 'Qtd Ambientes', 'Opções Emissor', 'Opções Aprovador', 'Descrição', 'Recomendação'], group_table_rows, 'table-sod-groups', 'gov-table')}
        </div>

        <div class="card" id="secao-nivel2">
            <h2 class="card-header">Nível 2 — Pessoas Reais com o Conflito</h2>
            <p class="card-desc">Usuários que hoje acumulam emissor + aprovador — via um grupo conflitante
            (Nível 1) ou via combinação de dois grupos diferentes, já confrontado por site (essa 2ª categoria
            aparece mesmo com status em branco, comum em contas de serviço). Revisar se as unidades/sites batem
            antes de agir — ver nota de cautela na metodologia acima.</p>
            <div class="search-container">
                <input type="text" id="searchSoDUser" class="search-bar" onkeyup="filterSoDUserTable()" placeholder="Pesquisar por USERID, Nome, Título...">
                <select id="selSoDUserApp" class="filter-select" onchange="filterSoDUserTable()">
                    <option value="">Todas as Aplicações</option>
                    <option value="Requisição de Compra">Requisição de Compra (PR)</option>
                    <option value="Ordem de Compra">Ordem de Compra (PO)</option>
                    <option value="Requisição Simplificada">Requisição Simplificada/Almoxarifado</option>
                </select>
            </div>
            <div class="table-responsive">
                <table id="table-sod-users" class="gov-table">
                    <thead><tr><th>Ambiente</th><th>USERID</th><th>Nome</th><th>Título</th><th>Aplicação</th>
                    <th>Grupos Emissor</th><th>Grupos Aprovador</th><th>Origem</th>
                    <th>Papel Sugerido <span style="font-weight:400; font-size:0.75em;">(passe o mouse)</span></th>
                    <th>Recomendação</th></tr></thead>
                    <tbody>{''.join(user_table_rows)}</tbody>
                </table>
            </div>
            {truncation_html}
        </div>

        {render_perfil_cargo_section(group_baseline_data)}

        {render_padronizacao_section(role_standardization_data)}

        <div class="card" id="secao-maxadmin">
            <h2 class="card-header">Governança de Superusuário — MAXADMIN</h2>
            <p class="card-desc">Usuários com acesso total ao Maximo em cada ambiente. Não é tratado como
            conflito de emissor/aprovador (acesso total é esperado nesse grupo) — mas vale revisar se todos
            realmente precisam desse nível de acesso.</p>
            <div class="search-container">
                <input type="text" id="searchSoDMaxAdmin" class="search-bar" onkeyup="filterSoDMaxAdminTable()" placeholder="Pesquisar por USERID, Nome...">
            </div>
            {render_table(['Ambiente', 'USERID', 'Nome', 'Título', 'Status'], maxadmin_table_rows, 'table-sod-maxadmin', 'gov-table')}
        </div>
    </div>
    """


def render_tab_seguranca_scripts():
    return """
    <style>
        .sod-clickable { cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
        .sod-clickable:hover { transform: scale(1.03); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }
        .sod-clickable.sod-active { transform: scale(1.05); box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
    </style>
    <script>
        function sodGoTo(sectionId) {
            const el = document.getElementById(sectionId);
            if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
        }

        function sodFilterUsers(origem, cardEl) {
            document.querySelectorAll('#card-sod-todos, #card-sod-combo').forEach(c => c.classList.remove('sod-active'));
            if (cardEl) cardEl.classList.add('sod-active');
            const table = document.getElementById('table-sod-users');
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const matches = (origem === 'all') || (row.getAttribute('data-origem') === origem);
                    row.style.display = matches ? '' : 'none';
                });
            }
            sodGoTo('secao-nivel2');
        }

        function filterSoDEvidenceTable() {
            const input = document.getElementById('searchSoDEvidence');
            const sevSel = document.getElementById('selSoDEvidenceSev');
            if (!input) return;
            const term = input.value.toUpperCase();
            const sevFilter = sevSel ? sevSel.value : '';
            const table = document.getElementById('table-sod-evidence');
            if (!table) return;
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const matchesSearch = row.textContent.toUpperCase().indexOf(term) > -1;
                const matchesSev = !sevFilter || row.getAttribute('data-severidade') === sevFilter;
                row.style.display = (matchesSearch && matchesSev) ? '' : 'none';
            });
        }

        function filterSoDGroupTable() {
            const input = document.getElementById('searchSoDGroup');
            if (!input) return;
            const term = input.value.toUpperCase();
            const table = document.getElementById('table-sod-groups');
            if (!table) return;
            const rows = table.getElementsByTagName('tr');
            for (let i = 1; i < rows.length; i++) {
                rows[i].style.display = rows[i].textContent.toUpperCase().indexOf(term) > -1 ? '' : 'none';
            }
        }

        function filterSoDMaxAdminTable() {
            const input = document.getElementById('searchSoDMaxAdmin');
            if (!input) return;
            const term = input.value.toUpperCase();
            const table = document.getElementById('table-sod-maxadmin');
            if (!table) return;
            const rows = table.getElementsByTagName('tr');
            for (let i = 1; i < rows.length; i++) {
                rows[i].style.display = rows[i].textContent.toUpperCase().indexOf(term) > -1 ? '' : 'none';
            }
        }

        function filterPerfilCargoTable() {
            const input = document.getElementById('searchPerfilCargo');
            if (!input) return;
            const term = input.value.toUpperCase();
            const table = document.getElementById('table-perfil-cargo');
            if (!table) return;
            const rows = table.getElementsByTagName('tr');
            for (let i = 1; i < rows.length; i++) {
                rows[i].style.display = rows[i].textContent.toUpperCase().indexOf(term) > -1 ? '' : 'none';
            }
        }

        function filterPadronizacaoTable() {
            const input = document.getElementById('searchPadronizacao');
            const sel = document.getElementById('selPadronizacaoStatus');
            if (!input) return;
            const term = input.value.toUpperCase();
            const statusFilter = sel ? sel.value : '';
            const table = document.getElementById('table-padronizacao-cargo');
            if (!table) return;
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const matchesSearch = row.textContent.toUpperCase().indexOf(term) > -1;
                const matchesStatus = !statusFilter || row.getAttribute('data-consistente') === statusFilter;
                row.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
            });
        }

        function filterSoDUserTable() {
            const input = document.getElementById('searchSoDUser');
            const appSel = document.getElementById('selSoDUserApp');
            if (!input || !appSel) return;
            const term = input.value.toUpperCase();
            const appFilter = appSel.value;
            const table = document.getElementById('table-sod-users');
            if (!table) return;
            const rows = table.getElementsByTagName('tr');
            for (let i = 1; i < rows.length; i++) {
                const cells = rows[i].getElementsByTagName('td');
                if (!cells.length) continue;
                const text = rows[i].textContent.toUpperCase();
                const appText = cells[4] ? cells[4].textContent : '';
                const matchesSearch = text.indexOf(term) > -1;
                const matchesApp = !appFilter || appText.indexOf(appFilter) > -1;
                rows[i].style.display = (matchesSearch && matchesApp) ? '' : 'none';
            }
        }
    </script>
    """
