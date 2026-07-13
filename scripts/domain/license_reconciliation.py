"""
scripts/domain/license_reconciliation.py
Cenário Conciliado de licenciamento MAS 9 — a ÚNICA fonte de P50/P95/P100
usada em todo o dashboard/Excel (unificação de 2026-07-11: antes havia 3
cálculos concorrentes e divergentes — o card desta aba, o simulador de
cenários da mesma aba, e as abas Eventos Críticos/Peak Contributors —
porque cada um lia uma população e uma lógica de licença diferente).

Metodologia (decisões de negócio confirmadas pelo usuário):
1. POPULAÇÃO CONCILIADA: usuário ATIVO no Maximo E conciliado com uma conta
   ATIVA no AD, em cascata: e-mail exato → prefixo do e-mail = USERID
   (convenção da empresa) → nome completo normalizado (1º + último nome,
   sem acentos/conectores).
2. PRESENÇA AJUSTADA POR ROTAÇÃO OFFSHORE (2026-07-11): logar no sistema
   não significa "consumindo licença o tempo todo" — a operação offshore
   trabalha em regime de embarque/folga (turmas), então medir presença
   dividindo horas logadas pelos 90 dias corridos SUBESTIMA quem está
   plenamente ativo durante o embarque. Detectamos o próprio padrão de
   rotação nos dados: agrupamos os dias com login de cada pessoa em BLOCOS
   (gap entre logins de até 3 dias ainda conta como o mesmo bloco/embarque;
   gap maior fecha o bloco). Medido nos dados reais: os blocos se concentram
   fortemente entre 13-15 dias — a assinatura de um rodízio 14x14 — e as
   lacunas entre blocos também se concentram em 14-15 dias (a folga). A
   presença de cada pessoa é horas logadas ÷ horas dos SEUS PRÓPRIOS blocos
   (a janela em que ela estava de fato disponível), não os 90 dias inteiros.
   Contas de sistema/serviço (login quase todo santo dia) não têm blocos
   detectáveis — o cálculo já reflete isso naturalmente (bloco ≈ período
   inteiro, presença ≈ a mesma de antes).
3. LICENÇA ESTATÍSTICA (break-even econômico): Authorized reserva o custo
   24/7; Concurrent só paga quando logado. Authorized só compensa se a
   presença AJUSTADA exceder custo_auth/custo_conc — 33,3% para PREMIUM
   (5/15) e 30% para BASE (3/10).
4. EXCEÇÃO DE NEGÓCIO: título crítico (Coordenador/Supervisor/Gerente/OIM/
   Chefe/Diretor) com presença ajustada >10% mantém Authorized — quem
   aprova não pode ser bloqueado por pool cheio.
5. TERCEIROS ATIVOS (não conciliados com AD mas com login real em 90 dias —
   equipe embarcada de contratadas): MANTIDOS no dimensionamento como
   Concurrent com o entitlement vigente (decisão do usuário 2026-07-11:
   eles seguem operando no MAS 9). Não conciliados SEM login em 90d ficam
   fora (não migram; limpeza).
6. ESCOPOS: mesma classificação por DOMAIN_CATEGORY usada no resto do
   dashboard (foresea = FORESEA/PARCEIRO; integracao = INTEGRACAO;
   terceiros = qualquer outro domínio válido; sem_dominio fica fora dos
   escopos nomeados mas entra no "todos").

Saídas: métricas P50/P95/P100 por escopo (foresea/terceiros/integracao/
todos) — usadas por Cenários de AppPoints, Eventos Críticos e Peak
Contributors —, lista por usuário, e CSV
`output/consolidated/cenario_conciliado_licencas.csv`.
"""
import csv
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'

ACTIVE_STATUSES = {'ACTIVE', 'ATIVO', 'ENABLED'}
LOOKBACK_DAYS = 90
SESSION_MINUTES = 60
TOTAL_HOURS = LOOKBACK_DAYS * 24
CRITICAL_TITLE_KEYWORDS = ('SUPERVISOR', 'SUPERV', 'COORDENADOR', 'COORD',
                           'GERENTE', 'DIRETOR', 'OIM', 'CHEFE')
CRITICAL_MIN_PRESENCE = 0.10
# Gap (dias) entre dias-com-login que ainda conta como o mesmo bloco de
# embarque — calibrado nos dados reais (ver ROTATION_BLOCK_GAP_DAYS).
ROTATION_BLOCK_GAP_DAYS = 3
COST = {('PREMIUM', 'AUTHORIZED'): 5, ('PREMIUM', 'CONCURRENT'): 15,
        ('BASE', 'AUTHORIZED'): 3, ('BASE', 'CONCURRENT'): 10}
SCOPES = ('foresea', 'terceiros', 'integracao', 'todos')

# Contas de integração/serviço com regra de negócio fixa (confirmada pelo
# usuário 2026-07-11): sempre Premium Authorized = 5 pts, sem passar pelo
# cálculo estatístico de presença (não são pessoas com padrão de uso a
# avaliar — são integrações que precisam de acesso garantido) e sempre no
# escopo "integracao", independente do domínio de e-mail. Existem outras
# contas de padrão semelhante (ex.: HELPDESK, ITEAM) sem regra confirmada
# ainda — não incluídas aqui até confirmação explícita.
FIXED_PREMIUM_AUTHORIZED_ACCOUNTS = {'WSORACLE', 'MAXADMIN', 'MAXREG'}

# Correções pontuais de escopo confirmadas pelo usuário 2026-07-11 (a
# classificação por DOMAIN_CATEGORY errava a identidade real da conta):
# ITEAM é usuário de suporte da TERCEIRIZADA, não FORESEA — mantém o
# cálculo estatístico normal de licença, só corrige o escopo. HELPDESK
# ("só visualiza, não faz nada") foi CONFIRMADO como BASE CONCURRENT — já
# é o resultado do modelo, sem necessidade de override.
SCOPE_OVERRIDES = {'ITEAM': 'terceiros'}


def load_csv(path: Path):
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        first = f.readline()
        delim = ';' if ';' in first else ','
        f.seek(0)
        return list(csv.DictReader(f, delimiter=delim))


def _norm_name_tokens(s):
    s = ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c)).upper()
    return [t for t in s.split() if t not in ('DE', 'DA', 'DO', 'DOS', 'DAS', 'E') and len(t) > 1]


def _parse_dt(s):
    s = (s or '').strip()
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s[:26], fmt)
        except ValueError:
            pass
    return None


def _percentile(sorted_vals, pct):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * pct / 100.0
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _scope_from_domain_category(domain_category):
    category = (domain_category or '').strip().upper()
    if category in ('FORESEA', 'PARCEIRO'):
        return 'foresea'
    if category == 'INTEGRACAO':
        return 'integracao'
    if category and category != 'SEM DOMINIO':
        return 'terceiros'
    return None  # SEM DOMINIO: fora dos escopos nomeados, dentro de "todos"


def _eligible_hours(login_days):
    """Agrupa dias-com-login em blocos de rotação (gap <= 3 dias) e retorna
    o total de horas elegíveis = soma do span de cada bloco (não só os dias
    com login — o bloco inteiro, já que a pessoa está embarcada mesmo em
    dias sem necessidade de acessar o sistema)."""
    if not login_days:
        return 0, 0
    days = sorted(login_days)
    blocks = [[days[0], days[0]]]
    for d in days[1:]:
        if (d - blocks[-1][1]).days <= ROTATION_BLOCK_GAP_DAYS:
            blocks[-1][1] = d
        else:
            blocks.append([d, d])
    total_days = sum((b[1] - b[0]).days + 1 for b in blocks)
    return total_days * 24, len(blocks)


def analyze_license_reconciliation():
    ad_rows = load_csv(IN_DIR / 'consolidated_ad_users.csv')
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    login_rows = load_csv(IN_DIR / 'consolidated_logintracking_from_sources.csv')
    plan = load_csv(IN_DIR / 'license_decision_plan.csv')
    email_rows = load_csv(IN_DIR / 'consolidated_email.csv')

    # ---- AD ativo: índices de conciliação ----
    ad_emails = {r.get('mail', '').strip().lower() for r in ad_rows if r.get('mail', '').strip()}
    ad_prefix = {e.split('@')[0].upper() for e in ad_emails}
    ad_names = set()
    for r in ad_rows:
        toks = _norm_name_tokens(r.get('DisplayName', ''))
        if len(toks) >= 2:
            ad_names.add((toks[0], toks[-1]))

    # PERSONID -> USERIDs (para juntar consolidated_email.csv, indexado por
    # PERSONID, ao USERID usado no resto desta função). Fallback: quando o
    # PERSONID do e-mail não bate com nenhuma identidade, ele próprio é
    # tentado como USERID (convenção da empresa: USERID == PERSONID na
    # maioria dos casos).
    userids_by_personid = defaultdict(set)
    for r in identities:
        uid = (r.get('USERID') or '').strip().upper()
        pid = (r.get('PERSONID') or '').strip().upper()
        if uid and pid:
            userids_by_personid[pid].add(uid)

    # ---- Maximo: identidade agregada por USERID ----
    info_by_uid = defaultdict(lambda: {'emails': set(), 'names': set(), 'active': False, 'titles': set()})
    for r in identities:
        uid = (r.get('USERID') or '').strip().upper()
        if not uid:
            continue
        d = info_by_uid[uid]
        if (r.get('PRIMARYEMAIL') or '').strip():
            d['emails'].add(r['PRIMARYEMAIL'].strip().lower())
        if (r.get('DISPLAYNAME') or '').strip():
            d['names'].add(r['DISPLAYNAME'].strip())
        if (r.get('STATUS') or '').strip().upper() in ACTIVE_STATUSES:
            d['active'] = True
        if (r.get('TITLE') or '').strip():
            d['titles'].add(r['TITLE'].strip())

    # consolidated_user_identity.csv.PRIMARYEMAIL fica vazio na maioria das
    # linhas — o e-mail real vive em consolidated_email.csv, indexado por
    # PERSONID (auditoria 2026-07-13: sem isto, pelo menos 109 funcionários
    # com e-mail certo no AD ficavam sem match e eram tratados como terceiro
    # ativo em vez de conciliado).
    for r in email_rows:
        pid = (r.get('PERSONID') or '').strip().upper()
        email = (r.get('EMAILADDRESS') or '').strip().lower()
        if not pid or not email:
            continue
        for uid in (userids_by_personid.get(pid) or {pid}):
            if uid in info_by_uid:
                info_by_uid[uid]['emails'].add(email)

    def reconcile(uid, d):
        if any(e in ad_emails for e in d['emails']):
            return 'EMAIL'
        if uid in ad_prefix:
            return 'PREFIXO'
        for dn in d['names']:
            toks = _norm_name_tokens(dn)
            if len(toks) >= 2 and (toks[0], toks[-1]) in ad_names:
                return 'NOME'
        return None

    reconciled = {}
    for uid, d in info_by_uid.items():
        if not d['active']:
            continue
        m = reconcile(uid, d)
        if m:
            reconciled[uid] = m

    # ---- Entitlement + escopo vigentes (license_decision_plan.csv) ----
    ent_by_uid = {}
    scope_by_uid = {}
    for r in plan:
        uid = (r.get('USERID') or '').strip().upper().replace(' ', '')
        if not uid:
            continue
        if uid not in ent_by_uid:
            ent = (r.get('ENTITLEMENT') or '').strip().upper()
            ent_by_uid[uid] = 'PREMIUM' if ent == 'PREMIUM' else 'BASE'
        if uid not in scope_by_uid:
            scope_by_uid[uid] = _scope_from_domain_category(r.get('DOMAIN_CATEGORY'))

    # ---- Logintracking 90d: dias e horas ativas por usuário (sessão 60 min) ----
    max_dt = None
    events = []
    for r in login_rows:
        if (r.get('ATTEMPTRESULT') or '').strip().upper() != 'LOGIN':
            continue
        dt = _parse_dt(r.get('ATTEMPTDATE'))
        if not dt:
            continue
        uid = (r.get('USERID') or '').strip().upper().replace(' ', '')
        events.append((uid, dt))
        if max_dt is None or dt > max_dt:
            max_dt = dt

    user_hours = defaultdict(set)       # horas com login (para custo Concurrent, real)
    user_login_days = defaultdict(set)  # dias com login (para detectar blocos de rotação)
    if max_dt:
        window_start = max_dt - timedelta(days=LOOKBACK_DAYS)
        session_delta = timedelta(minutes=SESSION_MINUTES)
        for uid, dt in events:
            if dt < window_start:
                continue
            user_login_days[uid].add(dt.date())
            end = dt + session_delta
            b = dt.replace(minute=0, second=0, microsecond=0)
            while b <= end:
                user_hours[uid].add(b)
                b += timedelta(hours=1)

    def is_critical(uid):
        return any(any(k in t.upper() for k in CRITICAL_TITLE_KEYWORDS)
                   for t in info_by_uid[uid]['titles'])

    def build_row(uid, populacao, match):
        hours = len(user_hours.get(uid, set()))
        eligible_hours, n_blocos = _eligible_hours(user_login_days.get(uid, set()))
        presence_calendario = hours / TOTAL_HOURS
        presence = (hours / eligible_hours) if eligible_hours else 0.0

        if uid in FIXED_PREMIUM_AUTHORIZED_ACCOUNTS:
            # Regra de negócio fixa (conta de integração/serviço) — não
            # passa pelo break-even estatístico nem pelo escopo por domínio.
            ent, econ, final, scope = 'PREMIUM', 'AUTHORIZED', 'AUTHORIZED', 'integracao'
        else:
            ent = ent_by_uid.get(uid, 'BASE')
            scope = SCOPE_OVERRIDES.get(uid) or scope_by_uid.get(uid) or 'sem_dominio'
            breakeven = COST[(ent, 'AUTHORIZED')] / COST[(ent, 'CONCURRENT')]
            if populacao == 'TERCEIRO_ATIVO':
                final = econ = 'CONCURRENT'
            else:
                econ = 'AUTHORIZED' if presence > breakeven else 'CONCURRENT'
                final = 'AUTHORIZED' if (econ == 'CONCURRENT' and is_critical(uid)
                                         and presence > CRITICAL_MIN_PRESENCE) else econ
        return {
            'POPULACAO': populacao,
            'USERID': uid,
            'MATCH': match,
            'SCOPE': scope,
            'ENTITLEMENT': ent,
            'HORAS_ATIVAS_90D': hours,
            'QTD_BLOCOS_ROTACAO': n_blocos,
            'HORAS_ELEGIVEIS_ROTACAO': eligible_hours,
            'PRESENCA_PCT': round(presence * 100, 1),
            'PRESENCA_CALENDARIO_PCT': round(presence_calendario * 100, 1),
            'TITULO_CRITICO': is_critical(uid),
            'LICENCA_ECONOMICA': econ,
            'LICENCA_FINAL': final,
            'CUSTO': COST[(ent, final)],
            'CARGO': ' | '.join(sorted(info_by_uid[uid]['titles'])),
        }

    rows_out = [build_row(uid, 'CONCILIADO', reconciled[uid]) for uid in sorted(reconciled)]
    for uid, d in sorted(info_by_uid.items()):
        if not d['active'] or uid in reconciled:
            continue
        if not user_hours.get(uid):
            continue  # sem uso real: não migra, não dimensiona (limpeza)
        rows_out.append(build_row(uid, 'TERCEIRO_ATIVO', ''))

    # ---- NEM por escopo — fonte única para todo o dashboard/Excel ----
    lic_by_uid = {r['USERID']: r for r in rows_out}
    licensed_uids = set(lic_by_uid)

    def nem_for(uids, with_hourly_series=False):
        # Composição de população deste recorte específico — usada para os
        # cards ficarem 100% reativos ao escopo (antes só P95/P100 mudavam;
        # "conciliados"/"authorized/concurrent"/"reserva" ficavam fixos no
        # total geral mesmo com um escopo nomeado selecionado).
        pop_conciliados = sum(1 for u in uids if lic_by_uid[u]['POPULACAO'] == 'CONCILIADO')
        pop_terceiros_ativos = sum(1 for u in uids if lic_by_uid[u]['POPULACAO'] == 'TERCEIRO_ATIVO')
        pop_authorized = sum(1 for u in uids if lic_by_uid[u]['LICENCA_FINAL'] == 'AUTHORIZED')
        pop_concurrent = sum(1 for u in uids if lic_by_uid[u]['LICENCA_FINAL'] == 'CONCURRENT')
        auth_reserve = sum(lic_by_uid[u]['CUSTO'] for u in uids if lic_by_uid[u]['LICENCA_FINAL'] == 'AUTHORIZED')
        hourly_conc = defaultdict(float)
        hourly_users = defaultdict(int)
        for u in uids:
            r = lic_by_uid[u]
            if r['LICENCA_FINAL'] != 'CONCURRENT':
                continue
            for h in user_hours.get(u, set()):
                hourly_conc[h] += r['CUSTO']
                hourly_users[h] += 1
        pop_stats = {'conciliados': pop_conciliados, 'terceiros_ativos': pop_terceiros_ativos,
                     'authorized': pop_authorized, 'concurrent': pop_concurrent}
        if not hourly_conc:
            empty = {'p50': round(auth_reserve), 'p95': round(auth_reserve), 'p100': round(auth_reserve),
                    'reserva_authorized': round(auth_reserve), 'peak_hour': None, 'peak_contributors': [],
                    'peak_breakdown': [], **pop_stats}
            if with_hourly_series:
                empty['hourly_series'] = []
            return empty
        vals = sorted(auth_reserve + v for v in hourly_conc.values())
        peak_hour = max(hourly_conc, key=hourly_conc.get)
        peak_uids = [u for u in uids if lic_by_uid[u]['LICENCA_FINAL'] == 'CONCURRENT'
                    and peak_hour in user_hours.get(u, set())]
        contributors = sorted(
            [{'userid': u, 'app_points': lic_by_uid[u]['CUSTO'],
              'license_type': f"{lic_by_uid[u]['ENTITLEMENT']}_{lic_by_uid[u]['LICENCA_FINAL']}",
              'scope': lic_by_uid[u]['SCOPE']}
             for u in peak_uids],
            key=lambda c: -c['app_points'])
        # Quebra por categoria (escopo x tipo de licença) — mais informativa
        # que um "top 20" onde todo mundo empata no mesmo valor por pessoa
        # (Premium Concurrent = sempre 15 pts, Base Concurrent = sempre 10).
        breakdown_counts = defaultdict(lambda: {'qtd': 0, 'pts': 0})
        for c in contributors:
            key = (c['scope'], c['license_type'])
            breakdown_counts[key]['qtd'] += 1
            breakdown_counts[key]['pts'] += c['app_points']
        peak_breakdown = sorted(
            [{'scope': k[0], 'license_type': k[1], 'qtd': v['qtd'], 'pts': v['pts']}
             for k, v in breakdown_counts.items()],
            key=lambda b: -b['pts'])
        result = {
            'p50': round(_percentile(vals, 50)),
            'p95': round(_percentile(vals, 95)),
            'p100': round(max(vals)),
            'reserva_authorized': round(auth_reserve),
            'peak_hour': peak_hour.strftime('%Y-%m-%d %H:00') if peak_hour else None,
            'peak_contributors': contributors,
            'peak_breakdown': peak_breakdown,
            **pop_stats,
        }
        if with_hourly_series:
            result['hourly_series'] = [
                {'hour': h.strftime('%Y-%m-%d %H:00'), 'users': hourly_users[h],
                 'points_concurrent': round(hourly_conc[h]), 'points_nem': round(auth_reserve + hourly_conc[h])}
                for h in sorted(hourly_conc)
            ]
        return result

    conciliados = [r for r in rows_out if r['POPULACAO'] == 'CONCILIADO']
    terceiros = [r for r in rows_out if r['POPULACAO'] == 'TERCEIRO_ATIVO']
    conciliados_uids = {r['USERID'] for r in conciliados}

    nem_by_scope = {}
    for scope in ('foresea', 'terceiros', 'integracao'):
        nem_by_scope[scope] = nem_for({u for u in licensed_uids if lic_by_uid[u]['SCOPE'] == scope}, with_hourly_series=True)
    nem_by_scope['todos'] = nem_for(licensed_uids, with_hourly_series=True)
    nem_conciliado_todos = nem_for(conciliados_uids)

    stats = {
        'maximo_ativos_total': sum(1 for d in info_by_uid.values() if d['active']),
        'conciliados': len(conciliados),
        'conciliados_por_email': sum(1 for r in conciliados if r['MATCH'] == 'EMAIL'),
        'conciliados_por_prefixo': sum(1 for r in conciliados if r['MATCH'] == 'PREFIXO'),
        'conciliados_por_nome': sum(1 for r in conciliados if r['MATCH'] == 'NOME'),
        'conciliados_authorized': sum(1 for r in conciliados if r['LICENCA_FINAL'] == 'AUTHORIZED'),
        'conciliados_concurrent': sum(1 for r in conciliados if r['LICENCA_FINAL'] == 'CONCURRENT'),
        'terceiros_ativos': len(terceiros),
        'nao_conciliados_sem_uso': (sum(1 for d in info_by_uid.values() if d['active'])
                                    - len(conciliados) - len(terceiros)),
        'reserva_authorized': nem_conciliado_todos['reserva_authorized'],
        'nem_conciliado': nem_conciliado_todos,
        'nem_realista': nem_by_scope['todos'],
        'nem_by_scope': nem_by_scope,
        'peak_hour': nem_by_scope['todos']['peak_hour'],
        'peak_contributors': nem_by_scope['todos']['peak_contributors'],
        'peak_breakdown': nem_by_scope['todos']['peak_breakdown'],
    }

    # ---- Persistir CSV ----
    out = IN_DIR / 'cenario_conciliado_licencas.csv'
    try:
        with out.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            w.writeheader()
            w.writerows(rows_out)
    except (PermissionError, OSError):
        pass

    return {'stats': stats, 'rows': rows_out}


def print_summary(result):
    s = result['stats']
    print(f"[CONCILIADO] Maximo ativos: {s['maximo_ativos_total']} | conciliados AD ativo: {s['conciliados']} "
          f"(email {s['conciliados_por_email']}, prefixo {s['conciliados_por_prefixo']}, nome {s['conciliados_por_nome']})")
    print(f"[CONCILIADO] Licenca estatistica (presenca ajustada por rotacao): {s['conciliados_authorized']} AUTHORIZED "
          f"(reserva {s['reserva_authorized']} pts) + {s['conciliados_concurrent']} CONCURRENT")
    print(f"[CONCILIADO] Terceiros ativos mantidos (Concurrent): {s['terceiros_ativos']} | "
          f"nao conciliados sem uso (limpeza): {s['nao_conciliados_sem_uso']}")
    nc, nr = s['nem_conciliado'], s['nem_realista']
    print(f"[CONCILIADO] NEM so-conciliados: P50={nc['p50']:,} P95={nc['p95']:,} P100={nc['p100']:,}")
    print(f"[CONCILIADO] NEM realista (+terceiros, TODOS os escopos): P50={nr['p50']:,} P95={nr['p95']:,} P100={nr['p100']:,} (teto 1.200)")
    for scope in ('foresea', 'terceiros', 'integracao'):
        v = s['nem_by_scope'][scope]
        print(f"[CONCILIADO]   escopo {scope}: P50={v['p50']:,} P95={v['p95']:,} P100={v['p100']:,}")


if __name__ == '__main__':
    print_summary(analyze_license_reconciliation())
