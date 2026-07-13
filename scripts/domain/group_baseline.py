"""
scripts/domain/group_baseline.py
Recomendação de "perfil de acesso" por cargo: para cada título (cargo) com
amostra suficiente de pessoas ativas (em qualquer ambiente), calcula qual
conjunto de grupos de segurança é o padrão (baseline) para aquele cargo, e
compara com o que cada pessoa individualmente tem — sinalizando EXCESSO
(grupos que ela tem e o cargo normalmente não tem, risco de acesso indevido)
e FALTA (grupos que o cargo normalmente tem e ela não tem, possível bloqueio
operacional).

Diferente do PAPEL_RECOMENDADO da auditoria de SoD (security_audit.py), que
só arbitra qual lado de um conflito emissor/aprovador manter dentro de
Compras — aqui o objetivo é o desenho de acesso como um todo (todos os
grupos do Maximo), não só as 3 aplicações de Compras.

Cohort por (ambiente, cargo), não por cargo global: testamos agrupar só por
cargo (ignorando o ambiente) esperando amostras maiores, mas os dados
mostraram o oposto do que a intuição sugere — mesmo grupos com o mesmo nome
(ex.: OOG_PTW_ISSUER) aparecem em uma fração pequena e inconsistente das
pessoas do mesmo cargo quando espalhadas entre as 7 unidades (cada rig
monta sua própria composição de grupos por equipe operacional). O baseline
real é por unidade: "Auxiliar de Plataforma no ODN2" tem um padrão de grupos
consistente; "Auxiliar de Plataforma" em geral, não. Por isso o cohort é
(ambiente, cargo) — a amostra por cohort é menor, mas o baseline resultante
é o que de fato reflete a operação de cada unidade.
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'

# consolidated_user_identity.csv usa ENV_DB com nomes longos (NORBE06/08/09)
# enquanto groupuser/maxgroup usam os códigos curtos (N06/N08/N09) — sem
# este alias, o cruzamento por (ambiente, userid) falha silenciosamente para
# essas 3 unidades (grupos daquela pessoa somem, cohort/baseline os ignora).
ENV_ALIAS = {'NORBE06': 'N06', 'NORBE08': 'N08', 'NORBE09': 'N09',
             'BASE-UNP': 'BASE', 'OP-BASE': 'BASE', 'ODRL-SP': 'BASE'}

ACTIVE_STATUSES = {'ACTIVE', 'ATIVO', 'ENABLED'}
# MAXADMIN nunca deve ser "padrão" de um cargo, por mais frequente que seja —
# é sempre um caso de revisão individual (ver aba de MAXADMIN da auditoria de SoD).
EXCLUDED_GROUPS = {'MAXADMIN'}

MIN_COHORT_SIZE = 3        # amostra mínima (pessoas ativas c/ mesmo cargo, no mesmo ambiente) p/ confiar no baseline
BASELINE_THRESHOLD = 0.6   # grupo precisa aparecer em >=60% do cohort p/ virar "padrão do cargo"
UNIVERSAL_THRESHOLD = 0.9  # grupo em >=90% de TODOS os usuários ativos (qualquer cargo/ambiente) é acesso básico, não "excesso" de ninguém


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


def _load_title_by_personid(persongroupview_rows):
    """PERSONID -> título, sem restringir por ambiente (mesmo racional do
    security_audit.py: o cargo costuma estar registrado em só um dos 7
    ambientes, mesmo para gente com conta em vários)."""
    title_by_personid = {}
    for r in persongroupview_rows:
        pid = r.get('personid', '').strip().upper()
        title = r.get('title', '').strip()
        if pid and title and pid not in title_by_personid:
            title_by_personid[pid] = title
    return title_by_personid


def analyze_group_baseline():
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    groupusers = load_csv(IN_DIR / 'consolidated_groupuser.csv')
    persongroupview_rows = load_csv(IN_DIR / 'consolidated_persongroupview.csv')

    title_by_personid = _load_title_by_personid(persongroupview_rows)

    # (env, userid) -> {status, title, personid, displayname}
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

    # (env, userid) -> set(groupname)
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

    active_keys = [k for k, info in user_info.items() if info['status'].upper() in ACTIVE_STATUSES]

    # env -> grupos "universais": comuns a quase todo mundo ativo daquele
    # ambiente, independente do cargo — acesso básico (ex.: self-service),
    # não deve contar como excesso de ninguém.
    active_by_env = defaultdict(list)
    for (env, uid) in active_keys:
        active_by_env[env].append(uid)

    group_active_count_by_env = defaultdict(Counter)
    for (env, uid) in active_keys:
        for g in user_groups.get((env, uid), set()):
            group_active_count_by_env[env][g] += 1

    universal_groups_by_env = {}
    for env, uids in active_by_env.items():
        total = len(uids)
        if total == 0:
            continue
        universal_groups_by_env[env] = {
            g for g, c in group_active_count_by_env[env].items() if c / total >= UNIVERSAL_THRESHOLD
        }

    # (env, título) -> lista de userids ativos com aquele cargo naquele ambiente
    cohorts = defaultdict(list)
    for (env, uid) in active_keys:
        info = user_info[(env, uid)]
        title = resolved_title(info)
        if not title:
            continue
        cohorts[(env, title)].append(uid)

    baseline_by_cohort = {}
    for (env, title), uids in cohorts.items():
        n = len(uids)
        if n < MIN_COHORT_SIZE:
            continue
        counts = Counter()
        for uid in uids:
            for g in user_groups.get((env, uid), set()):
                if g in EXCLUDED_GROUPS:
                    continue
                counts[g] += 1
        baseline = {g for g, c in counts.items() if c / n >= BASELINE_THRESHOLD}
        if not baseline:
            continue
        baseline_by_cohort[(env, title)] = {'n': n, 'baseline': baseline}

    # ---- Perfil por cargo+ambiente (visão agregada) ----
    profile_rows = []
    for (env, title), cohort in baseline_by_cohort.items():
        profile_rows.append({
            'ENVIRONMENT': env,
            'TITLE': title,
            'QTD_PESSOAS': cohort['n'],
            'GRUPOS_PADRAO': '; '.join(sorted(cohort['baseline'])),
            'QTD_GRUPOS_PADRAO': len(cohort['baseline']),
        })

    # ---- Desvios por pessoa (excesso e falta vs. o baseline do cargo dela) ----
    deviation_rows = []
    for (env, uid) in active_keys:
        info = user_info[(env, uid)]
        title = resolved_title(info)
        if not title:
            continue
        cohort = baseline_by_cohort.get((env, title))
        if not cohort:
            continue
        current = user_groups.get((env, uid), set())
        universal = universal_groups_by_env.get(env, set())
        faltantes = sorted(cohort['baseline'] - current)
        excesso = sorted(g for g in (current - cohort['baseline']) if g not in universal and g not in EXCLUDED_GROUPS)
        if not faltantes and not excesso:
            continue
        deviation_rows.append({
            'ENVIRONMENT': env,
            'USERID': uid,
            'DISPLAYNAME': info.get('displayname', ''),
            'TITLE': title,
            'COHORT_SIZE': cohort['n'],
            'GRUPOS_FALTANTES': '; '.join(faltantes),
            'GRUPOS_EXCESSO': '; '.join(excesso),
            'QTD_FALTANTES': len(faltantes),
            'QTD_EXCESSO': len(excesso),
        })

    stats = {
        'total_cohorts_com_baseline': len(baseline_by_cohort),
        'total_titulos_distintos': len({title for (_env, title) in baseline_by_cohort}),
        'total_pessoas_com_desvio': len(deviation_rows),
        'total_pessoas_com_excesso': sum(1 for r in deviation_rows if r['QTD_EXCESSO'] > 0),
        'total_pessoas_com_falta': sum(1 for r in deviation_rows if r['QTD_FALTANTES'] > 0),
    }

    return {
        'stats': stats,
        'profile_rows': sorted(profile_rows, key=lambda x: -x['QTD_PESSOAS']),
        'deviation_rows': sorted(deviation_rows, key=lambda x: (-x['QTD_EXCESSO'], -x['QTD_FALTANTES'])),
    }


def print_summary(result):
    s = result['stats']
    print(f"\n[PERFIL DE CARGO] Cohorts (ambiente+cargo) com baseline confiável (n>={MIN_COHORT_SIZE}): {s['total_cohorts_com_baseline']}")
    print(f"[PERFIL DE CARGO] Cargos distintos cobertos: {s['total_titulos_distintos']}")
    print(f"[PERFIL DE CARGO] Pessoas com algum desvio do baseline do cargo: {s['total_pessoas_com_desvio']}")
    print(f"[PERFIL DE CARGO]   -> com excesso de acesso: {s['total_pessoas_com_excesso']}")
    print(f"[PERFIL DE CARGO]   -> com falta de acesso: {s['total_pessoas_com_falta']}")


if __name__ == '__main__':
    result = analyze_group_baseline()
    print_summary(result)
