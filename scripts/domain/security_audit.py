# scripts/domain/security_audit.py
"""
Auditoria de segregação de funções (SoD) em Compras: identifica grupos e
usuários que acumulam permissão de EMISSOR (criar/submeter) e APROVADOR
(aprovar) na mesma aplicação Maximo — Requisição de Compra (PLUSGPR), Ordem
de Compra (PLUSGPO) e Requisição Simplificada/Almoxarifado (CREATEDR).

Fonte: APPLICATIONAUTH (GROUPNAME, APP, OPTIONNAME) — não SECURITYRESTRICT,
que é apenas regra de campo (readonly/hidden), sem relação com autoridade de
aprovação.
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'

# consolidated_user_identity.csv usa ENV_DB com nomes longos (NORBE06/08/09)
# enquanto toda a extração de segurança (groupuser/maxgroup/applicationauth/
# siteauth) usa os códigos curtos (N06/N08/N09) — sem este alias, o cruzamento
# por (ambiente, userid) falha silenciosamente para essas 3 unidades (volta
# dict vazio), deixando TITLE/DISPLAYNAME/STATUS em branco para gente com
# conflito de SoD ali. BASE/HTQ/ODN1/ODN2 já usam o mesmo nome nos dois lados.
ENV_ALIAS = {'NORBE06': 'N06', 'NORBE08': 'N08', 'NORBE09': 'N09',
             'BASE-UNP': 'BASE', 'OP-BASE': 'BASE', 'ODRL-SP': 'BASE'}

APP_LABELS = {
    'PLUSGPR': 'Requisição de Compra (PR)',
    'PLUSGPO': 'Ordem de Compra (PO)',
    'CREATEDR': 'Requisição Simplificada/Almoxarifado',
}
# WAPPR ("Waiting Approval") é a ação de SUBMETER para aprovação — do lado de
# quem emite, não de quem aprova.
ISSUER_OPTIONS = {'INSERT', 'SAVE', 'WAPPR'}
APPROVER_OPTIONS = {'APPR', 'APPROVE', 'UNAPPROVE'}
# MAXADMIN tem acesso total por natureza — não entra na lista de conflitos,
# mas seus membros são reportados separadamente (governança de superusuário).
EXCLUDED_GROUPS = {'MAXADMIN'}

# Hierarquia de senioridade offshore O&G (heurística de especialista, MAS 9):
# usada apenas para RANKING RELATIVO dentro do mesmo cluster conflitante
# (mesmo ambiente + mesmo grupo/par de grupos + mesma app) — não é uma regra
# absoluta de "este cargo sempre aprova". Serve para sugerir, dentro de um
# grupo que precisa ser dividido, qual pessoa é a candidata mais natural a
# manter a aprovação, como ponto de partida para a liderança da unidade
# decidir. Tier 1 = mais sênior.
SENIORITY_TIERS = [
    (1, ('SUPERINTENDENTE', 'COMANDANTE', 'OIM', 'MASTER', 'GERENTE', 'DIRETOR')),
    (2, ('CHEFE', 'CHIEF', 'COORDENADOR', 'COORDINATOR')),
    (3, ('SUBCHEFE', 'SUPERVISOR', 'ENCARREGADO', 'TOOLPUSHER', 'DECKPUSHER',
         'IMEDIATO', 'MESTRE', 'BOSUN', 'ENGENHEIRO', 'INSPETOR')),
    (4, ('TECNICO', 'TEC ', 'OPERADOR', 'DPO', 'TORRISTA', 'DERRICKMAN', 'ALMOXARIFE')),
    (5, ('ASSISTENTE', 'AUXILIAR')),
]


def _seniority_tier(title):
    """Menor número = mais sênior. None = cargo desconhecido/sem match."""
    if not title:
        return None
    t = title.upper()
    for tier, keywords in SENIORITY_TIERS:
        if any(kw in t for kw in keywords):
            return tier
    return None


def _load_title_by_personid(persongroupview_rows):
    """PERSONID -> título, sem restringir por ambiente. O mesmo indivíduo
    pode ter o cargo registrado em apenas UM dos 7 ambientes mesmo tendo
    conta (e o conflito de SoD) em outro — restringir por ambiente aqui
    reduzia a cobertura de 78% para 10% nos testes."""
    title_by_personid = {}
    for r in persongroupview_rows:
        pid = r.get('personid', '').strip().upper()
        title = r.get('title', '').strip()
        if pid and title and pid not in title_by_personid:
            title_by_personid[pid] = title
    return title_by_personid


def _load_person_info_by_personid(persongroupview_rows):
    """PERSONID -> {title, status, displayname}, sem restringir por
    ambiente (mesma lógica de _load_title_by_personid). Usado para mostrar
    cargo/status/nome junto das evidências reais na tela — sem isso, um caso
    como "estagiário inativo aprovou R$1M sozinho" fica escondido atrás de um
    USERID puro."""
    info_by_personid = {}
    for r in persongroupview_rows:
        pid = r.get('personid', '').strip().upper()
        if not pid:
            continue
        info = info_by_personid.setdefault(pid, {'title': '', 'status': '', 'displayname': ''})
        if not info['title'] and r.get('title', '').strip():
            info['title'] = r.get('title', '').strip()
        if not info['displayname'] and r.get('displayname', '').strip():
            info['displayname'] = r.get('displayname', '').strip()
        if r.get('status', '').strip():
            info['status'] = r.get('status', '').strip()
    return info_by_personid


def _recommend_role_assignments(user_conflicts, personid_by_env_userid, title_by_personid):
    """Para cada cluster (ambiente + grupos emissor/aprovador + app), sugere
    quem é o candidato mais natural a manter APROVADOR (o de maior
    senioridade aparente no cluster) — os demais ficam como sugestão de
    EMISSOR. Quando ninguém no cluster tem cargo conhecido, ou quando o único
    sinal disponível já é de nível operacional, não força um palpite:
    marca indefinição explícita para revisão manual local. Muta cada dict de
    user_conflicts em memória (adiciona PAPEL_RECOMENDADO/JUSTIFICATIVA_PAPEL)."""
    clusters = defaultdict(list)
    for c in user_conflicts:
        key = (c['ENVIRONMENT'], c['GRUPOS_EMISSOR'], c['GRUPOS_APROVADOR'], c['APP'])
        clusters[key].append(c)

    def title_for(c):
        pid = personid_by_env_userid.get((c['ENVIRONMENT'], c['USERID']), c['USERID'])
        return title_by_personid.get(pid, '') or c.get('TITLE', '')

    for members in clusters.values():
        tiered = [(_seniority_tier(title_for(m)), m) for m in members]
        known = [(t, m) for t, m in tiered if t is not None]
        if not known or min(t for t, _m in known) >= 4:
            for m in members:
                m['PAPEL_RECOMENDADO'] = 'INDEFINIDO'
                m['JUSTIFICATIVA_PAPEL'] = (
                    'Nenhum integrante deste grupo/site tem cargo de liderança identificado — '
                    'decisão deve ser tomada localmente por quem gerencia esta unidade.'
                )
            continue
        best_tier = min(t for t, _m in known)
        for t, m in tiered:
            title = title_for(m)
            if t == best_tier:
                m['PAPEL_RECOMENDADO'] = 'APROVADOR (sugestão)'
                m['JUSTIFICATIVA_PAPEL'] = (
                    "Cargo mais sênior identificado neste grupo/site"
                    + (f" ({title})" if title else "") + ". Sugestão inicial — confirmar com a liderança local."
                )
            else:
                m['PAPEL_RECOMENDADO'] = 'EMISSOR (sugestão)'
                m['JUSTIFICATIVA_PAPEL'] = (
                    (f"Cargo ({title}) de nível mais operacional que o líder identificado no mesmo grupo/site."
                     if title else
                     "Sem cargo identificado; outro integrante do mesmo grupo/site tem cargo mais sênior conhecido.")
                    + " Sugestão inicial — confirmar com a liderança local."
                )


def detect_delimiter(path: Path):
    with path.open('r', encoding='utf-8-sig') as f:
        first_line = f.readline()
    return ';' if ';' in first_line else ','


def load_csv(path: Path):
    if not path.exists():
        return []
    delim = detect_delimiter(path)
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delim))


def _load_real_evidence():
    """Casos REAIS e documentados (não permissão teórica): a mesma pessoa
    submeteu (PR WAPPR) e aprovou (PR APPR) a MESMA Requisição de Compra, com
    número de documento, valor e datas — extraído de WFTRANSACTION (log de
    workflow) x PR (cabeçalho do documento), últimos 365 dias, 7 ambientes.
    PO não tem essa evidência disponível: WFTRANSACTION não registra
    transações de workflow para OWNERTABLE='PO' nesta instalação.

    Os 7 "ambientes" replicam a MESMA base de PR/WFTRANSACTION (confirmado:
    mesmo PRNUM, mesmo SITEID, mesmo PERSONID, timestamps idênticos ao
    microssegundo em todos os 7) — provavelmente um banco de compras central
    espelhado em cada servidor de site. Sem deduplicar, cada caso real apareceria
    ~7x e infracionaria o total em ~7x. Deduplicamos por
    (SITEID, PRNUM, PERSONID, DATA_SUBMISSAO, DATA_APROVACAO); ENVIRONMENT não
    é reportado nesta evidência por não ser um eixo real de distinção aqui.

    Severidade (procedimento oficial "Tutorial de Criação de PR no Maximo":
    aprovação inicia no Coordenador de Manutenção e, acima de um limite de
    valor, passa obrigatoriamente pelo Engenheiro de Ativos — roteamento
    logado como ACTIONPERFORMED='OOG_PRWENG' no WFTRANSACTION):
      - CRITICO: o sistema EXIGIU a 2ª instância (OOG_PRWENG disparou para
        esta PR) e, mesmo assim, a mesma pessoa concluiu submissão E
        aprovação sozinha — o controle de 2 pessoas foi contornado.
      - REVISAR_REGRA: nenhum roteamento para 2ª instância foi disparado —
        aprovação em instância única, possivelmente dentro do desenho para
        valores abaixo do limite. Ainda vale revisar se o limite está
        calibrado corretamente, mas não é uma violação confirmada do
        controle de 2 pessoas.
    """
    rows = load_csv(IN_DIR / 'consolidated_pr_sod_evidence.csv')
    seen = set()
    evidence = []
    for r in rows:
        key = (
            r.get('SITEID', '').strip(), r.get('PRNUM', '').strip(),
            r.get('PERSONID', '').strip().upper(),
            r.get('DATA_SUBMISSAO', '').strip(), r.get('DATA_APROVACAO', '').strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        try:
            valor = float(r.get('TOTALCOST', '0').strip() or 0)
        except ValueError:
            valor = 0.0
        roteado = r.get('ROTEADO_2A_INSTANCIA', '').strip().upper() == 'SIM'
        evidence.append({
            'SITEID': r.get('SITEID', '').strip(),
            'PRNUM': r.get('PRNUM', '').strip(),
            'DESCRIPTION': r.get('DESCRIPTION', '').strip(),
            'TOTALCOST': valor,
            'STATUS': r.get('STATUS', '').strip(),
            'REQUESTEDBY': r.get('REQUESTEDBY', '').strip(),
            'PERSONID': r.get('PERSONID', '').strip().upper(),
            'DATA_SUBMISSAO': r.get('DATA_SUBMISSAO', '').strip(),
            'DATA_APROVACAO': r.get('DATA_APROVACAO', '').strip(),
            'ROTEADO_2A_INSTANCIA': roteado,
            'SEVERIDADE': 'CRITICO' if roteado else 'REVISAR_REGRA',
        })
    return evidence


def _load_self_approval_evidence():
    """Casos ainda mais diretos que _load_real_evidence(): a pessoa que
    REALMENTE solicitou o item (campo customizado PR.OOG_REQUESTEDBY — quem
    pediu de fato, diferente do REQUESTEDBY genérico que costuma ser a conta
    compartilhada do rig) é a MESMA que aprovou (PR APPR) — autoaprovação da
    própria compra, independente de qualquer nuance de alçada por valor.
    Extraído apenas de BASE: os 7 bancos de compras replicam a mesma base
    (confirmado por PRNUM/PERSONID/timestamps idênticos em todos os 7); BASE
    sozinha já reflete a realidade das unidades.
    """
    rows = load_csv(IN_DIR / 'consolidated_pr_self_approval.csv')
    evidence = []
    for r in rows:
        try:
            valor = float(r.get('TOTALCOST', '0').strip() or 0)
        except ValueError:
            valor = 0.0
        roteado = r.get('ROTEADO_2A_INSTANCIA', '').strip().upper() == 'SIM'
        evidence.append({
            'SITEID': r.get('SITEID', '').strip(),
            'PRNUM': r.get('PRNUM', '').strip(),
            'DESCRIPTION': r.get('DESCRIPTION', '').strip(),
            'TOTALCOST': valor,
            'STATUS': r.get('STATUS', '').strip(),
            'SOLICITANTE_REAL': r.get('SOLICITANTE_REAL', '').strip().upper(),
            'PERSONID_APROVOU': r.get('PERSONID_APROVOU', '').strip().upper(),
            'DATA_APROVACAO': r.get('DATA_APROVACAO', '').strip(),
            'ROTEADO_2A_INSTANCIA': roteado,
            'SEVERIDADE': 'CRITICO' if roteado else 'REVISAR_REGRA',
        })
    return evidence


def _load_pr_po_same_approver():
    """Teste de cadeia PR -> PO: a mesma pessoa que aprovou a PR
    (WFTRANSACTION ACTIONPERFORMED='PR APPR') também é quem disparou a
    criação da PO a partir dela (ACTIONPERFORMED='OOG_CREAPOGRP', ligado à
    mesma PR via PRLINE.PONUM). Diferente da alçada de valor da Suprimentos
    (Comprador/Coordenador/Gerente de Suprimentos — ver metodologia), este é
    um teste de papel: quem aprova a requisição não deveria ser quem gera o
    pedido de compra dela.

    Verificado contra os 2.670 eventos históricos de OOG_CREAPOGRP (toda a
    base, sem filtro de data): 0 sobreposições de pessoa — controle limpo na
    prática, não um teste que não roda. Mantido como camada ativa (não texto
    estático) para acusar automaticamente se isso mudar no futuro.

    Não tentamos usar PO.PURCHASEAGENT / PO.CHANGEBY como evidência de
    autoaprovação em PO: 6.798 de 7.761 POs aprovadas nos últimos 365 dias
    têm CHANGEBY=MAXADMIN (processo em lote), e ao excluir MAXADMIN o
    cruzamento PURCHASEAGENT=CHANGEBY zera — é 100% ruído de automação, não
    sinal real de aprovação humana.
    """
    rows = load_csv(IN_DIR / 'consolidated_pr_po_same_approver.csv')
    evidence = []
    for r in rows:
        try:
            valor = float(r.get('TOTALCOST', '0').strip() or 0)
        except ValueError:
            valor = 0.0
        evidence.append({
            'SITEID': r.get('SITEID', '').strip(),
            'PRNUM': r.get('PRNUM', '').strip(),
            'DESCRIPTION': r.get('DESCRIPTION', '').strip(),
            'TOTALCOST': valor,
            'STATUS': r.get('STATUS', '').strip(),
            'PERSONID': r.get('PERSONID', '').strip().upper(),
            'DATA_APROVACAO_PR': r.get('DATA_APROVACAO_PR', '').strip(),
            'DATA_CRIACAO_PO': r.get('DATA_CRIACAO_PO', '').strip(),
            'PONUM_GERADA': r.get('PONUM_GERADA', '').strip(),
        })
    return evidence


def _build_site_scope(maxgroups, siteauth_rows):
    """(env, groupname) -> 'ALL' (AUTHALLSITES=1) ou set(siteids autorizados).
    Usado para confrontar se um par emissor/aprovador em grupos DIFERENTES
    realmente se sobrepõe no mesmo site — um usuário pode ter grupo emissor
    numa unidade e, por embarque em outra sonda, grupo aprovador em unidade
    diferente; isso não é conflito real porque ele nunca acumula os dois
    poderes no mesmo local.
    """
    authallsites = {}
    for g in maxgroups:
        env = g.get('ENVIRONMENT', '').strip()
        name = g.get('GROUPNAME', '').strip().upper()
        authallsites[(env, name)] = g.get('AUTHALLSITES', '').strip() == '1'

    sites_by_group = defaultdict(set)
    for s in siteauth_rows:
        env = s.get('ENVIRONMENT', '').strip()
        name = s.get('GROUPNAME', '').strip().upper()
        site = s.get('SITEID', '').strip()
        if site:
            sites_by_group[(env, name)].add(site)

    def scope(env, name):
        if authallsites.get((env, name), False):
            return 'ALL'
        return sites_by_group.get((env, name), set())

    return scope


def _groups_overlap_by_site(site_scope, env, issuer_groups, approver_groups):
    """True se algum par (grupo emissor, grupo aprovador) se sobrepõe no
    mesmo site — ou se algum dos dois lados é AUTHALLSITES=1 (sobrepõe com
    qualquer coisa por definição)."""
    for ig in issuer_groups:
        ig_scope = site_scope(env, ig)
        for ag in approver_groups:
            ag_scope = site_scope(env, ag)
            if ig_scope == 'ALL' or ag_scope == 'ALL':
                return True
            if ig_scope & ag_scope:
                return True
    return False


def analyze_security_audit():
    appauth = load_csv(IN_DIR / 'consolidated_applicationauth.csv')
    groupusers = load_csv(IN_DIR / 'consolidated_groupuser.csv')
    maxgroups = load_csv(IN_DIR / 'consolidated_maxgroup.csv')
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    siteauth_rows = load_csv(IN_DIR / 'consolidated_siteauth.csv')
    persongroupview_rows = load_csv(IN_DIR / 'consolidated_persongroupview.csv')
    site_scope = _build_site_scope(maxgroups, siteauth_rows)
    title_by_personid = _load_title_by_personid(persongroupview_rows)
    person_info_by_personid = _load_person_info_by_personid(persongroupview_rows)

    group_desc = {}
    for g in maxgroups:
        env = g.get('ENVIRONMENT', '').strip()
        name = g.get('GROUPNAME', '').strip().upper()
        if name:
            group_desc[(env, name)] = g.get('DESCRIPTION', '').strip()

    # (env, userid) -> {title, displayname, status}. Pega o primeiro valor
    # não vazio encontrado — a identidade pode ter múltiplas linhas por conta
    # de fontes diferentes (maxuser/person/persongroupview) mescladas.
    user_info = {}
    # (env, userid) -> personid, para juntar com persongroupview por PERSONID
    # (não por ambiente — a mesma pessoa costuma ter o cargo registrado em só
    # um dos 7 ambientes, mesmo tendo conta/conflito de SoD em outro).
    personid_by_env_userid = {}
    for u in identities:
        env = u.get('ENV_DB', '').strip()
        env = ENV_ALIAS.get(env, env)
        uid = u.get('USERID', '').strip().upper()
        if not uid:
            continue
        key = (env, uid)
        info = user_info.setdefault(key, {'title': '', 'displayname': '', 'status': ''})
        if not info['title'] and u.get('TITLE', '').strip():
            info['title'] = u.get('TITLE', '').strip()
        if not info['displayname'] and u.get('DISPLAYNAME', '').strip():
            info['displayname'] = u.get('DISPLAYNAME', '').strip()
        pid = u.get('PERSONID', '').strip().upper()
        if pid and key not in personid_by_env_userid:
            personid_by_env_userid[key] = pid
        if u.get('STATUS', '').strip():
            info['status'] = u.get('STATUS', '').strip()

    # (env, groupname, app) -> {optionname, ...}
    group_app_options = defaultdict(set)
    for r in appauth:
        env = r.get('ENVIRONMENT', '').strip()
        group = r.get('GROUPNAME', '').strip().upper()
        app = r.get('APP', '').strip().upper()
        opt = r.get('OPTIONNAME', '').strip().upper()
        if group and app and opt:
            group_app_options[(env, group, app)].add(opt)

    # ---- NÍVEL 1: grupos que, isoladamente, já são emissor E aprovador ----
    group_conflicts = []
    for (env, group, app), opts in group_app_options.items():
        if group in EXCLUDED_GROUPS:
            continue
        issuer_opts = opts & ISSUER_OPTIONS
        approver_opts = opts & APPROVER_OPTIONS
        if issuer_opts and approver_opts:
            group_conflicts.append({
                'ENVIRONMENT': env,
                'GROUPNAME': group,
                'APP': app,
                'APP_LABEL': APP_LABELS.get(app, app),
                'DESCRIPTION': group_desc.get((env, group), ''),
                'OPCOES_EMISSOR': '; '.join(sorted(issuer_opts)),
                'OPCOES_APROVADOR': '; '.join(sorted(approver_opts)),
                'RECOMENDACAO': (
                    f"Dividir {group} em dois grupos: um mantendo apenas "
                    f"{'/'.join(sorted(issuer_opts))} (emissor) e outro apenas "
                    f"{'/'.join(sorted(approver_opts))} (aprovador); realocar cada "
                    "usuário conforme o papel real que exerce."
                ),
            })

    # (env, app) -> {groupname, ...} com capacidade de emissor / aprovador
    issuer_groups_by_app = defaultdict(set)
    approver_groups_by_app = defaultdict(set)
    for (env, group, app), opts in group_app_options.items():
        if group in EXCLUDED_GROUPS:
            continue
        if opts & ISSUER_OPTIONS:
            issuer_groups_by_app[(env, app)].add(group)
        if opts & APPROVER_OPTIONS:
            approver_groups_by_app[(env, app)].add(group)

    # (env, userid) -> {groupname, ...}
    user_groups = defaultdict(set)
    for gu in groupusers:
        env = gu.get('ENVIRONMENT', '').strip()
        uid = gu.get('USERID', '').strip().upper()
        group = gu.get('GROUPNAME', '').strip().upper()
        if uid and group:
            user_groups[(env, uid)].add(group)

    apps_seen = {app for (_env, app) in set(issuer_groups_by_app) | set(approver_groups_by_app)}

    # ---- NÍVEL 2: usuários com emissor+aprovador, no mesmo grupo ou em grupos diferentes ----
    user_conflicts = []
    for (env, uid), groups in user_groups.items():
        for app in apps_seen:
            issuer_groups = groups & issuer_groups_by_app.get((env, app), set())
            approver_groups = groups & approver_groups_by_app.get((env, app), set())
            if not (issuer_groups and approver_groups):
                continue
            origem = 'MESMO_GRUPO' if (issuer_groups & approver_groups) else 'GRUPOS_DIFERENTES'

            # Um usuário pode ter grupo emissor numa unidade e, por embarque em
            # outra sonda, grupo aprovador numa unidade diferente — isso NÃO é
            # conflito real, pois ele nunca acumula os dois poderes no mesmo
            # site. Só se aplica a GRUPOS_DIFERENTES: no MESMO_GRUPO os dois
            # poderes já vêm do mesmo grupo, logo do(s) mesmo(s) site(s) por
            # definição.
            if origem == 'GRUPOS_DIFERENTES' and not _groups_overlap_by_site(site_scope, env, issuer_groups, approver_groups):
                continue

            info = user_info.get((env, uid), {})
            user_conflicts.append({
                'ENVIRONMENT': env,
                'USERID': uid,
                'DISPLAYNAME': info.get('displayname', ''),
                'TITLE': info.get('title', ''),
                'STATUS': info.get('status', ''),
                'APP': app,
                'APP_LABEL': APP_LABELS.get(app, app),
                'GRUPOS_EMISSOR': '; '.join(sorted(issuer_groups)),
                'GRUPOS_APROVADOR': '; '.join(sorted(approver_groups)),
                'ORIGEM_CONFLITO': origem,
                'RECOMENDACAO': (
                    'Grupo já nasce conflitante — ver correção estrutural (Nível 1).'
                    if origem == 'MESMO_GRUPO' else
                    'Confirmado: os grupos emissor e aprovador se sobrepõem no mesmo site '
                    '(via SITEAUTH/AUTHALLSITES). Definir com a liderança qual papel este '
                    'usuário deve manter, e removê-lo do grupo do outro papel.'
                ),
            })

    # ---- Recomendação de papel por cargo (heurística de senioridade) ----
    _recommend_role_assignments(user_conflicts, personid_by_env_userid, title_by_personid)

    # ---- Governança MAXADMIN: quem tem acesso total, por ambiente ----
    maxadmin_users = []
    for (env, uid), groups in user_groups.items():
        if 'MAXADMIN' in groups:
            info = user_info.get((env, uid), {})
            maxadmin_users.append({
                'ENVIRONMENT': env,
                'USERID': uid,
                'DISPLAYNAME': info.get('displayname', ''),
                'TITLE': info.get('title', ''),
                'STATUS': info.get('status', ''),
            })

    active_statuses = {'ACTIVE', 'ATIVO', 'ENABLED'}
    distinct_users_any_status = {c['USERID'] for c in user_conflicts}
    distinct_users_active = {c['USERID'] for c in user_conflicts if c['STATUS'].upper() in active_statuses}
    distinct_users_by_app_active = {
        app: {c['USERID'] for c in user_conflicts if c['APP'] == app and c['STATUS'].upper() in active_statuses}
        for app in apps_seen
    }

    # Valor somado por PR ÚNICA (site+número), não por caso: uma PR
    # resubmetida N vezes pela mesma pessoa gera N casos no WFTRANSACTION,
    # mas o valor do documento só existe uma vez — somar por caso inflava o
    # total (auditoria 2026-07-11: 2.063 casos = 2.057 PRs, ~0,1% de
    # inflação; 23 críticos = 22 PRs).
    def _sum_by_unique_pr(evidence):
        seen, total = set(), 0.0
        for e in evidence:
            k = (e['SITEID'], e['PRNUM'])
            if k in seen:
                continue
            seen.add(k)
            total += e['TOTALCOST']
        return total

    # ---- Evidência real: casos DOCUMENTADOS (não teóricos) de emissor=aprovador ----
    real_evidence = _load_real_evidence()
    real_evidence_people = {e['PERSONID'] for e in real_evidence if e['PERSONID']}
    real_evidence_total_value = _sum_by_unique_pr(real_evidence)
    critical_evidence = [e for e in real_evidence if e['SEVERIDADE'] == 'CRITICO']
    critical_evidence_people = {e['PERSONID'] for e in critical_evidence if e['PERSONID']}
    critical_evidence_value = _sum_by_unique_pr(critical_evidence)

    # ---- Autoaprovação direta: solicitante real = aprovador (BASE apenas) ----
    self_approval_evidence = _load_self_approval_evidence()
    self_approval_people = {e['SOLICITANTE_REAL'] for e in self_approval_evidence if e['SOLICITANTE_REAL']}
    self_approval_value = _sum_by_unique_pr(self_approval_evidence)

    # ---- Enriquecer evidências com cargo/status/nome da pessoa, para que um
    # caso como "estagiário inativo aprovou sozinho R$1M" fique visível na
    # tela sem precisar cruzar com outra planilha. Campos prefixados com
    # "_PESSOA" para não colidir com o STATUS do próprio documento PR.
    for e in real_evidence:
        info = person_info_by_personid.get(e['PERSONID'], {})
        e['TITULO_PESSOA'] = info.get('title', '')
        e['STATUS_PESSOA'] = info.get('status', '')
        e['NOME_PESSOA'] = info.get('displayname', '')
    for e in self_approval_evidence:
        info = person_info_by_personid.get(e['SOLICITANTE_REAL'], {})
        e['TITULO_PESSOA'] = info.get('title', '')
        e['STATUS_PESSOA'] = info.get('status', '')
        e['NOME_PESSOA'] = info.get('displayname', '')

    # ---- Cadeia PR -> PO: mesma pessoa aprovou a PR e gerou a PO dela ----
    pr_po_chain_evidence = _load_pr_po_same_approver()
    pr_po_chain_people = {e['PERSONID'] for e in pr_po_chain_evidence if e['PERSONID']}
    pr_po_chain_value = sum(e['TOTALCOST'] for e in pr_po_chain_evidence)
    for e in pr_po_chain_evidence:
        info = person_info_by_personid.get(e['PERSONID'], {})
        e['TITULO_PESSOA'] = info.get('title', '')
        e['STATUS_PESSOA'] = info.get('status', '')
        e['NOME_PESSOA'] = info.get('displayname', '')

    # ---- PO (Ordem de Compra) — recorte dedicado do Nível 1/2 já calculado ----
    po_group_conflicts = [g for g in group_conflicts if g['APP'] == 'PLUSGPO']
    po_user_conflicts = [c for c in user_conflicts if c['APP'] == 'PLUSGPO']
    po_user_conflicts_active = [
        c for c in po_user_conflicts
        if c['ORIGEM_CONFLITO'] == 'GRUPOS_DIFERENTES' or c['STATUS'].upper() in active_statuses
    ]

    return {
        'stats': {
            'total_real_evidence_cases': len(real_evidence),
            'total_real_evidence_people': len(real_evidence_people),
            'total_real_evidence_value': real_evidence_total_value,
            # Subconjunto onde o sistema exigiu 2ª instância (OOG_PRWENG) e,
            # mesmo assim, a mesma pessoa completou submissão + aprovação —
            # violação confirmada do controle de 2 pessoas, não uma questão
            # de calibração de limite de valor.
            'total_critical_evidence_cases': len(critical_evidence),
            'total_critical_evidence_people': len(critical_evidence_people),
            'total_critical_evidence_value': critical_evidence_value,
            # Autoaprovação direta (solicitante real = aprovador) — o teste
            # mais direto de todos, independente de qualquer nuance de
            # alçada/valor. Extraído só de BASE (~97% de cobertura real).
            'total_self_approval_cases': len(self_approval_evidence),
            'total_self_approval_people': len(self_approval_people),
            'total_self_approval_value': self_approval_value,
            'total_group_conflicts': len(group_conflicts),
            # Linhas cruas (usuário x ambiente x app) — infladas por contas
            # inativas e por pessoas com conta em vários dos 7 ambientes.
            'total_user_conflict_rows': len(user_conflicts),
            'total_user_conflicts_mesmo_grupo': sum(1 for c in user_conflicts if c['ORIGEM_CONFLITO'] == 'MESMO_GRUPO'),
            'total_user_conflicts_grupos_diferentes': sum(1 for c in user_conflicts if c['ORIGEM_CONFLITO'] == 'GRUPOS_DIFERENTES'),
            # Números que importam para a gestão: pessoas reais, únicas, e só as ativas.
            'distinct_users_any_status': len(distinct_users_any_status),
            'distinct_users_active': len(distinct_users_active),
            'distinct_users_active_by_app': {app: len(u) for app, u in distinct_users_by_app_active.items()},
            'total_maxadmin_users': len(maxadmin_users),
            'envs_covered': sorted({env for (env, _group, _app) in group_app_options}),
            # PO (Ordem de Compra) — mesmo recorte de Nível 1/2, isolado por app.
            'total_po_group_conflicts': len({g['GROUPNAME'] for g in po_group_conflicts}),
            'total_po_user_conflicts_active': len({c['USERID'] for c in po_user_conflicts_active}),
            # Cadeia PR->PO (mesma pessoa aprovou a PR e gerou a PO): checado
            # contra 2.670 eventos históricos de OOG_CREAPOGRP, 0 sobreposições.
            'total_pr_po_chain_cases': len(pr_po_chain_evidence),
            'total_pr_po_chain_people': len(pr_po_chain_people),
            'total_pr_po_chain_value': pr_po_chain_value,
        },
        'group_conflicts': sorted(group_conflicts, key=lambda x: (x['APP'], x['ENVIRONMENT'], x['GROUPNAME'])),
        'user_conflicts': sorted(user_conflicts, key=lambda x: (x['APP'], x['ENVIRONMENT'], x['USERID'])),
        'maxadmin_users': sorted(maxadmin_users, key=lambda x: (x['ENVIRONMENT'], x['USERID'])),
        'real_evidence': sorted(real_evidence, key=lambda x: x['DATA_SUBMISSAO'], reverse=True),
        'self_approval_evidence': sorted(self_approval_evidence, key=lambda x: x['DATA_APROVACAO'], reverse=True),
        'po_group_conflicts': sorted(po_group_conflicts, key=lambda x: (x['ENVIRONMENT'], x['GROUPNAME'])),
        'po_user_conflicts': sorted(po_user_conflicts_active, key=lambda x: (x['ENVIRONMENT'], x['USERID'])),
        'pr_po_chain_evidence': sorted(pr_po_chain_evidence, key=lambda x: x['DATA_APROVACAO_PR'], reverse=True),
    }


def print_summary(result):
    s = result['stats']
    print(f"\n[SEGURANCA] Ambientes cobertos: {s['envs_covered']}")
    print(f"[SEGURANCA] Grupos com conflito emissor/aprovador (Nivel 1 - estrutural): {s['total_group_conflicts']}")
    print(f"[SEGURANCA] Linhas usuario x ambiente x app com conflito (Nivel 2, bruto): {s['total_user_conflict_rows']}"
          f" (mesmo grupo: {s['total_user_conflicts_mesmo_grupo']}, grupos diferentes: {s['total_user_conflicts_grupos_diferentes']})")
    print(f"[SEGURANCA] Pessoas UNICAS com conflito (qualquer status): {s['distinct_users_any_status']}")
    print(f"[SEGURANCA] Pessoas UNICAS ATIVAS com conflito: {s['distinct_users_active']} -> por app: {s['distinct_users_active_by_app']}")
    print(f"[SEGURANCA] Usuarios com acesso MAXADMIN (fora do escopo de conflito): {s['total_maxadmin_users']}")
    print(f"[SEGURANCA] EVIDENCIA REAL (documentada, ultimos 365 dias): {s['total_real_evidence_cases']} casos, "
          f"{s['total_real_evidence_people']} pessoas distintas, USD {s['total_real_evidence_value']:,.2f} envolvidos")
    print(f"[SEGURANCA]   -> CRITICO (sistema exigiu 2a instancia e mesma pessoa aprovou sozinha): "
          f"{s['total_critical_evidence_cases']} casos, {s['total_critical_evidence_people']} pessoas, "
          f"USD {s['total_critical_evidence_value']:,.2f}")
    print(f"[SEGURANCA] AUTOAPROVACAO DIRETA (solicitante real = aprovador, so BASE): "
          f"{s['total_self_approval_cases']} casos, {s['total_self_approval_people']} pessoas, "
          f"USD {s['total_self_approval_value']:,.2f}")
    print(f"[SEGURANCA] PO (Ordem de Compra) - recorte dedicado: {s['total_po_group_conflicts']} grupos conflitantes, "
          f"{s['total_po_user_conflicts_active']} pessoas ativas afetadas")
    print(f"[SEGURANCA] CADEIA PR->PO (mesma pessoa aprovou a PR e gerou a PO): "
          f"{s['total_pr_po_chain_cases']} casos, {s['total_pr_po_chain_people']} pessoas, "
          f"USD {s['total_pr_po_chain_value']:,.2f}")


if __name__ == '__main__':
    result = analyze_security_audit()
    print_summary(result)
