"""
scripts/domain/role_standardization.py
Especificação de padronização de acesso para entregar à terceirizada: para
cada cargo (normalizado entre unidades), qual grupo de segurança padrão ele
deve ter em TODAS as unidades — e quais grupos de hoje são, na prática, o
mesmo papel com nomes diferentes por unidade (ex.: HTQ_MATERIALS_COORDINATOR
/ POL_MATERIALS_COORDINATOR / PRIO_MATERIALS_COORDINATOR).

Diferente de group_baseline.py (que descreve o desvio de HOJE dentro da
própria unidade, por cargo+ambiente separadamente): aqui o objetivo é
PRESCRITIVO e único para toda a empresa — um cargo, um conjunto padrão de
grupos, em qualquer unidade.

Metodologia (2 etapas):

1. Clusterização de grupos por permissão real (não por nome): duas
   permissões completas (todas as aplicações, extraídas de
   `consolidated_applicationauth_full.csv`, ambiente BASE) são consideradas
   "o mesmo papel" se a similaridade de Jaccard entre seus conjuntos de
   (APP, OPTIONNAME) for >= 95%. Isso comprovou, com dado real, que
   HTQ_MATERIALS_COORDINATOR / POL_MATERIALS_COORDINATOR /
   PRIO_MATERIALS_COORDINATOR são ~99.7-99.9% idênticos entre si — cópias
   por unidade do mesmo papel — mas só ~85% parecidos com
   OOG_MATERIALS_COORDINATOR, que é um papel realmente diferente (não é
   candidato a fusão, mesmo com nome parecido). Threshold alto (95%)
   deliberadamente conservador: prefere deixar de fora um caso ambíguo a
   recomendar fusão de dois grupos com escopo de acesso diferente.

2. Normalização de cargo: muitos títulos já vêm como "PT/EN" numa só string
   (ex.: "ENCARREGADO DE PLATAFORMA/TOOLPUSHER") — normalizamos removendo
   acento/caixa e comparando o conjunto de tokens (ordem não importa), o que
   também casa variantes com a ordem invertida ("EN/PT"). Cargos sem par
   PT/EN explícito na string não são fundidos automaticamente com seu
   equivalente no outro idioma (exigiria dicionário manual de sinônimos, não
   construído aqui) — aparecem como cargos distintos e devem ser revisados
   manualmente antes do envio à terceirizada.

Para cada cargo normalizado, olhamos os grupos que as pessoas ATIVAS com
aquele cargo realmente têm hoje (todas as unidades), mapeados para o grupo
canônico do cluster (etapa 1). Se todo mundo cai no mesmo grupo canônico:
"CONSISTENTE". Se cai em grupos diferentes por unidade: "INCONSISTENTE" —
com o detalhamento de quem tem o quê, para a terceirizada decidir e
padronizar.
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'

# consolidated_user_identity.csv usa ENV_DB com nomes longos (NORBE06/08/09)
# enquanto groupuser/maxgroup/applicationauth usam os códigos curtos
# (N06/N08/N09) — sem este alias, o cruzamento por (ambiente, userid) falha
# silenciosamente para essas 3 unidades.
ENV_ALIAS = {'NORBE06': 'N06', 'NORBE08': 'N08', 'NORBE09': 'N09',
             'BASE-UNP': 'BASE', 'OP-BASE': 'BASE', 'ODRL-SP': 'BASE'}

ACTIVE_STATUSES = {'ACTIVE', 'ATIVO', 'ENABLED'}
EXCLUDED_GROUPS = {'MAXADMIN'}
SIMILARITY_THRESHOLD = 0.95


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


def _strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def _normalize_title_key(title):
    """Chave de agrupamento: maiúsculas, sem acento, tokens separados por
    '/' ordenados (casa 'PT/EN' e 'EN/PT'). Não funde sinônimos sem barra
    explícita — isso é uma limitação conhecida, documentada no módulo."""
    t = _strip_accents(title).upper().strip()
    parts = sorted(p.strip() for p in t.split('/') if p.strip())
    return tuple(parts) if parts else (t,)


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _cluster_groups_by_permission(signature_by_group, threshold=SIMILARITY_THRESHOLD):
    """Union-find: agrupa GROUPNAMEs cujo conjunto de permissões (APP,
    OPTIONNAME) tem similaridade de Jaccard >= threshold."""
    groups = sorted(signature_by_group.keys())
    parent = {g: g for g in groups}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i, a in enumerate(groups):
        for b in groups[i + 1:]:
            if _jaccard(signature_by_group[a], signature_by_group[b]) >= threshold:
                union(a, b)

    clusters = defaultdict(list)
    for g in groups:
        clusters[find(g)].append(g)
    return clusters


def _pick_canonical_name(members):
    """Prefere um nome com prefixo OOG_ (convenção já usada para papéis
    corporativos/compartilhados nesta instalação); senão, o nome mais curto."""
    oog = [m for m in members if m.startswith('OOG_')]
    if oog:
        return sorted(oog, key=len)[0]
    return sorted(members, key=len)[0]


def analyze_role_standardization():
    appauth_full_rows = load_csv(IN_DIR / 'consolidated_applicationauth_full.csv')
    groupusers = load_csv(IN_DIR / 'consolidated_groupuser.csv')
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    persongroupview_rows = load_csv(IN_DIR / 'consolidated_persongroupview.csv')
    maxgroups = load_csv(IN_DIR / 'consolidated_maxgroup.csv')

    # ---- Etapa 1: assinatura de permissão por grupo (BASE, ~97% real) ----
    signature_by_group = defaultdict(set)
    for r in appauth_full_rows:
        if r.get('ENVIRONMENT', '').strip() != 'BASE':
            continue
        grp = r.get('GROUPNAME', '').strip().upper()
        app = r.get('APP', '').strip().upper()
        opt = r.get('OPTIONNAME', '').strip().upper()
        if grp:
            signature_by_group[grp].add((app, opt))

    group_desc = {}
    for g in maxgroups:
        if g.get('ENVIRONMENT', '').strip() != 'BASE':
            continue
        name = g.get('GROUPNAME', '').strip().upper()
        if name:
            group_desc[name] = g.get('DESCRIPTION', '').strip()

    clusters = _cluster_groups_by_permission(signature_by_group)
    canonical_by_group = {}
    duplicate_clusters = []
    for members in clusters.values():
        canonical = _pick_canonical_name(members)
        for m in members:
            canonical_by_group[m] = canonical
        if len(members) > 1:
            # Sinaliza clusters onde os nomes sugerem NÍVEIS de privilégio
            # diferentes (ADM/ADMIN vs demais, LEITURA/READ vs demais) mas a
            # permissão real é quase igual — isso não deveria acontecer e
            # merece revisão explícita antes de simplesmente unificar
            # (auditoria 2026-07-11: OOG_COGNOS_LEITURA é 100% idêntico ao
            # OOG_COGNOS_ADM — o "read only" tem as mesmas permissões do ADM).
            has_privilege_mismatch = (
                (any('ADM' in m for m in members) and any('ADM' not in m for m in members))
                or (any('LEITURA' in m or 'READ' in m for m in members)
                    and any('LEITURA' not in m and 'READ' not in m for m in members))
            )
            # Sinaliza clusters onde os nomes-função divergem (ex.:
            # ASSET_COORDINATOR vs ENGINEER_COORDINATOR, ~97% similares em
            # permissão mas papéis nominalmente distintos, com delta real de
            # MOC) — fusão automática seria arriscada; a terceirizada deve
            # decidir com a área se são de fato o mesmo papel.
            def _core_name(m):
                core = re.sub(r'^(HTQ_|POL_|PRIO_|OOG_|ODN1_|ODN2_|N06_|N08_|N09_)', '', m)
                return re.sub(r'_(HTQ|POL|PRIO|YARD|TR)$', '', core)
            has_name_mismatch = len({_core_name(m) for m in members}) > 1 and not has_privilege_mismatch
            duplicate_clusters.append({
                'CANONICO': canonical,
                'MEMBROS': sorted(members),
                'QTD_MEMBROS': len(members),
                'DESCRICOES': '; '.join(f"{m}={group_desc.get(m, '')}" for m in sorted(members) if group_desc.get(m)),
                'ALERTA_PRIVILEGIO_DIFERENTE': has_privilege_mismatch,
                'ALERTA_NOMES_DIVERGENTES': has_name_mismatch,
            })

    # ---- Cargo/título por PERSONID (mesma técnica das outras análises) ----
    title_by_personid = {}
    for r in persongroupview_rows:
        pid = r.get('personid', '').strip().upper()
        title = r.get('title', '').strip()
        if pid and title and pid not in title_by_personid:
            title_by_personid[pid] = title

    user_info = {}
    for u in identities:
        env = u.get('ENV_DB', '').strip()
        env = ENV_ALIAS.get(env, env)
        uid = u.get('USERID', '').strip().upper()
        if not uid:
            continue
        key = (env, uid)
        info = user_info.setdefault(key, {'status': '', 'title': '', 'personid': '', 'displayname': ''})
        if u.get('STATUS', '').strip():
            info['status'] = u.get('STATUS', '').strip()
        if not info['title'] and u.get('TITLE', '').strip():
            info['title'] = u.get('TITLE', '').strip()
        if not info['personid'] and u.get('PERSONID', '').strip():
            info['personid'] = u.get('PERSONID', '').strip().upper()
        if not info['displayname'] and u.get('DISPLAYNAME', '').strip():
            info['displayname'] = u.get('DISPLAYNAME', '').strip()

    user_groups = defaultdict(set)
    for gu in groupusers:
        env = gu.get('ENVIRONMENT', '').strip()
        uid = gu.get('USERID', '').strip().upper()
        group = gu.get('GROUPNAME', '').strip().upper()
        if uid and group:
            user_groups[(env, uid)].add(group)

    def resolved_title(info):
        pid = info.get('personid', '')
        return (title_by_personid.get(pid, '') or info.get('title', '')).strip()

    # Frequência GLOBAL de cada grupo canônico entre TODAS as pessoas ativas
    # (qualquer cargo) — usada para excluir grupos "universais" (acesso
    # básico, ex.: MAXEVERYONE 100%, OOG_PTW_ISSUER 89%, OOG_ALL_DRILLING
    # 59%) da escolha de "grupo padrão do cargo". Sem isso, o grupo mais
    # comum em QUALQUER cargo acaba sendo sempre o mesmo grupo universal,
    # escondendo o grupo que de fato distingue o cargo (ex.: para "Superv.
    # de Materiais Offshore", o que importa é OOG_MATERIALS_COORDINATOR /
    # HTQ_MATERIALS_COORDINATOR, não OOG_ALL_DRILLING que quase todo mundo
    # tem de qualquer forma).
    active_keys_all = [k for k, info in user_info.items() if info['status'].upper() in ACTIVE_STATUSES]
    total_active = len(active_keys_all)
    global_group_counts = Counter()
    for k in active_keys_all:
        for g in (user_groups.get(k, set()) - EXCLUDED_GROUPS):
            global_group_counts[canonical_by_group.get(g, g)] += 1
    UNIVERSAL_GROUP_THRESHOLD = 0.30
    universal_canonical_groups = {
        g for g, c in global_group_counts.items() if total_active and c / total_active >= UNIVERSAL_GROUP_THRESHOLD
    }

    # título normalizado -> {raw_titles: set, membros: [(env, uid, título_bruto)]}
    title_cohorts = defaultdict(lambda: {'raw_titles': set(), 'members': []})
    for (env, uid), info in user_info.items():
        if info['status'].upper() not in ACTIVE_STATUSES:
            continue
        title = resolved_title(info)
        if not title:
            continue
        key = _normalize_title_key(title)
        title_cohorts[key]['raw_titles'].add(title)
        title_cohorts[key]['members'].append((env, uid))

    role_targets = []
    for key, cohort in title_cohorts.items():
        members = cohort['members']
        if len(members) < 2:
            continue  # cargo único demais para propor padrão — sem par de comparação
        # grupo(s) canônico(s) que cada pessoa tem hoje, por ambiente
        canonical_groups_by_env = defaultdict(Counter)
        raw_groups_by_env = defaultdict(set)
        for (env, uid) in members:
            groups = user_groups.get((env, uid), set()) - EXCLUDED_GROUPS
            raw_groups_by_env[env].update(groups)
            for g in groups:
                canon = canonical_by_group.get(g, g)
                canonical_groups_by_env[env][canon] += 1

        # grupo canônico mais comum entre TODOS os membros (independente de
        # unidade), IGNORANDO grupos universais (acesso básico que não
        # distingue o cargo — ver universal_canonical_groups acima).
        overall_counts = Counter()
        for env_counts in canonical_groups_by_env.values():
            overall_counts.update(env_counts)
        distinctive_counts = Counter({
            g: c for g, c in overall_counts.items() if g not in universal_canonical_groups
        })
        if not distinctive_counts:
            # só teve grupo universal — cargo sem grupo próprio identificável hoje
            role_targets.append({
                'CARGO_NORMALIZADO': ' / '.join(key),
                'TITULOS_BRUTOS_ENCONTRADOS': '; '.join(sorted(cohort['raw_titles'])),
                'QTD_PESSOAS': len(members),
                'AMBIENTES': '; '.join(sorted(canonical_groups_by_env.keys())),
                'GRUPO_PADRAO_RECOMENDADO': '',
                'DESCRICAO_GRUPO_PADRAO': '',
                'CONSISTENTE_ENTRE_UNIDADES': False,
                'UNIDADES_SEM_O_GRUPO_PADRAO': '',
                'ACAO': 'Nenhum grupo específico do cargo identificado hoje (só acesso básico/universal) — definir grupo próprio com Suprimentos/Manutenção local.',
            })
            continue
        target_group, target_count = distinctive_counts.most_common(1)[0]

        # consistência: todo ambiente onde o cargo existe tem o grupo alvo
        # como o mais comum ali (ou pelo menos presente)?
        envs_with_cargo = sorted(canonical_groups_by_env.keys())
        envs_missing_target = [
            env for env in envs_with_cargo
            if canonical_groups_by_env[env].get(target_group, 0) == 0
        ]
        consistente = len(envs_missing_target) == 0

        role_targets.append({
            'CARGO_NORMALIZADO': ' / '.join(key),
            'TITULOS_BRUTOS_ENCONTRADOS': '; '.join(sorted(cohort['raw_titles'])),
            'QTD_PESSOAS': len(members),
            'AMBIENTES': '; '.join(envs_with_cargo),
            'GRUPO_PADRAO_RECOMENDADO': target_group,
            'DESCRICAO_GRUPO_PADRAO': group_desc.get(target_group, ''),
            'CONSISTENTE_ENTRE_UNIDADES': consistente,
            'UNIDADES_SEM_O_GRUPO_PADRAO': '; '.join(envs_missing_target),
            'ACAO': (
                'Nenhuma — já padronizado.' if consistente else
                f"Atribuir {target_group} às pessoas com este cargo em: {', '.join(envs_missing_target)}."
            ),
        })

    stats = {
        'total_grupos_distintos': len(signature_by_group),
        'total_clusters_duplicados': len(duplicate_clusters),
        'total_grupos_em_clusters_duplicados': sum(c['QTD_MEMBROS'] for c in duplicate_clusters),
        'total_cargos_normalizados_com_amostra': len(role_targets),
        'total_cargos_inconsistentes': sum(1 for r in role_targets if not r['CONSISTENTE_ENTRE_UNIDADES']),
    }

    return {
        'stats': stats,
        'duplicate_group_clusters': sorted(duplicate_clusters, key=lambda x: -x['QTD_MEMBROS']),
        'role_targets': sorted(role_targets, key=lambda x: (x['CONSISTENTE_ENTRE_UNIDADES'], -x['QTD_PESSOAS'])),
    }


def print_summary(result):
    s = result['stats']
    print(f"\n[PADRONIZACAO] Grupos distintos analisados (permissao completa, BASE): {s['total_grupos_distintos']}")
    print(f"[PADRONIZACAO] Clusters de grupos duplicados/quase-identicos (>=95% similares): {s['total_clusters_duplicados']}"
          f" ({s['total_grupos_em_clusters_duplicados']} grupos envolvidos)")
    print(f"[PADRONIZACAO] Cargos normalizados com amostra para comparacao: {s['total_cargos_normalizados_com_amostra']}")
    print(f"[PADRONIZACAO]   -> INCONSISTENTES entre unidades (acesso raro por cargo difere por unidade): {s['total_cargos_inconsistentes']}")


if __name__ == '__main__':
    result = analyze_role_standardization()
    print_summary(result)
