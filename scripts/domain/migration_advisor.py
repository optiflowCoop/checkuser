"""
scripts/domain/migration_advisor.py
Analisa dados de AD e Maximo e gera recomendações de migração/remoção/limpeza
para a migração Maximo 7.6 → MAS 9.

O entregável responde, por usuário, às 3 perguntas do negócio:
1. Deve migrar? (tipo/ação)
2. A qual grupo de segurança deve pertencer? (grupos atuais por ambiente +
   grupo padrão recomendado pelo cargo, via role_standardization)
3. Quais acessos pode ter? (grupos Maximo atuais, que são o mecanismo de
   acesso; auditoria detalhada de permissão por grupo está nas abas de SoD)

Reescrito em 2026-07-11 após auditoria independente que encontrou:
- [CRITICO] match só por email ignorava 92,7% dos USERIDs do Maximo (sem
  PRIMARYEMAIL): 782 usuários AD com USERID = prefixo do email recebiam
  "CRIAR_NO_MAXIMO" mesmo JÁ EXISTINDO no Maximo (449 deles ATIVOS).
  Corrigido com cascata email → prefixo (convenção da empresa:
  adamsantos@foresea.com → USERID ADAMSANTOS).
- [CRITICO] a saída não tinha nenhum campo de grupo/acesso — não respondia
  2 das 3 perguntas do entregável. Corrigido (grupos_maximo,
  grupo_recomendado_mas9, cargo).
- [ALTO] o arquivo de AD desabilitados nunca era carregado (o consolidado
  só tem Enabled=true) — a categoria REMOVER estava estruturalmente vazia e
  o caso mais grave (desligado no AD porém ATIVO no Maximo) era invisível.
- [ALTO] VERIFICAR_AD era 91% ruído de contas 100% inativas, e MAXADMIN
  (conta de serviço) aparecia como "criar no AD". Corrigido com blocklist
  de contas de serviço + separação ativo (verificar) vs inativo (limpeza).
- [MEDIO] envs e status eram dois sets independentes pareados por posição
  na renderização (pareamento fabricado). Corrigido: pares env:status reais.
- [MEDIO] combinações de status não mapeadas (ex.: NEWREG) sumiam sem
  recomendação. Corrigido com ramo REVISAR_STATUS.
"""
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'

ENV_ALIAS = {'NORBE06': 'N06', 'NORBE08': 'N08', 'NORBE09': 'N09',
             'BASE-UNP': 'BASE', 'OP-BASE': 'BASE', 'ODRL-SP': 'BASE'}

ACTIVE_STATUSES = {'ACTIVE', 'ATIVO', 'ENABLED'}
INACTIVE_STATUSES = {'INACTIVE', 'INATIVO', 'DISABLED'}

# Contas que não são pessoas — não entram em recomendação de migração de
# usuário; recebem categoria própria para decisão explícita (a auditoria
# encontrou MAXADMIN sendo recomendado para "criação no AD").
SERVICE_ACCOUNTS = {'MAXADMIN', 'MAXREG', 'MXINTADM', 'HELPDESK', 'MAXIMO', 'ITEAM'}
# Contas genéricas de rig, ex.: ODN1001, HTQ001 — padrão unidade+dígitos.
RIG_ACCOUNT_RE = re.compile(r'^(ODN|HTQ|N0\d|POL|PRIO|OOG)[A-Z]*\d{3,4}$')


def detect_delimiter(path: Path):
    """Detecta automaticamente o delimitador de um CSV."""
    with path.open('r', encoding='utf-8-sig') as f:
        first_line = f.readline()
    if ';' in first_line:
        return ';'
    return ','


def load_csv(path: Path):
    if not path.exists():
        return []
    delim = detect_delimiter(path)
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delim))


def _is_service_account(userid):
    return userid in SERVICE_ACCOUNTS or bool(RIG_ACCOUNT_RE.match(userid))


def _load_recommended_group_by_title():
    """Cargo normalizado -> grupo padrão recomendado, reutilizando o motor de
    padronização (role_standardization). Falha de forma silenciosa e segura:
    se os dados de permissão completa ainda não foram extraídos, o campo
    grupo_recomendado_mas9 simplesmente fica vazio."""
    try:
        from scripts.domain.role_standardization import analyze_role_standardization, _normalize_title_key
    except Exception:
        return {}, None
    try:
        result = analyze_role_standardization()
    except Exception:
        return {}, None
    mapping = {
        t['CARGO_NORMALIZADO']: t['GRUPO_PADRAO_RECOMENDADO']
        for t in result.get('role_targets', [])
        if t.get('GRUPO_PADRAO_RECOMENDADO')
    }
    return mapping, _normalize_title_key


def analyze_migration():
    """Analisa e gera recomendações de migração/remoção/limpeza.
    Retorna lista de recomendações."""
    ad_rows = load_csv(IN_DIR / 'consolidated_ad_users.csv')
    ad_disabled_rows = load_csv(ROOT / 'adUsers' / 'adUsersdesabilitadas.csv')
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    groupusers = load_csv(IN_DIR / 'consolidated_groupuser.csv')

    print(f"[MIGRACAO] Analisando migracoes:")
    print(f"   AD habilitados: {len(ad_rows)} usuarios")
    print(f"   AD desabilitados: {len(ad_disabled_rows)} usuarios")
    print(f"   Identities: {len(identities)} registros")
    print(f"   Groupuser: {len(groupusers)} registros")

    # ============================================================
    # CONSTRUIR MAPAS
    # ============================================================

    def build_ad_map(rows, enabled_default):
        by_email = {}
        for r in rows:
            email = r.get('mail', '').strip().lower()
            if email and '@' in email:
                enabled_raw = r.get('Enabled', '').strip().lower()
                by_email[email] = {
                    'email': email,
                    'displayname': r.get('DisplayName', '').strip(),
                    'enabled': enabled_raw == 'true' if enabled_raw else enabled_default,
                    'groups': r.get('MemberOf', '').strip(),
                    'groups_count': len(r.get('MemberOf', '').split(', ')) if r.get('MemberOf') else 0,
                }
        return by_email

    ad_by_email = build_ad_map(ad_rows, enabled_default=True)
    # Desabilitados vêm de arquivo separado; se um email aparecer nos dois,
    # o cadastro habilitado prevalece (extração mais recente/autoritativa).
    for email, info in build_ad_map(ad_disabled_rows, enabled_default=False).items():
        if email not in ad_by_email:
            info['enabled'] = False
            ad_by_email[email] = info

    # Maximo: USERID -> dados agregados. env_status preserva o vínculo real
    # ambiente→status (a renderização antiga pareava dois sets independentes
    # por posição, fabricando pares que não existiam).
    maximo_by_userid = defaultdict(lambda: {
        'emails': set(),
        'displaynames': set(),
        'envs': set(),
        'statuses': set(),
        'env_status': defaultdict(set),
        'titles': set(),
    })

    for r in identities:
        userid = r.get('USERID', '').strip().upper()
        if not userid:
            continue
        email = r.get('PRIMARYEMAIL', '').strip().lower()
        displayname = r.get('DISPLAYNAME', '').strip()
        env = r.get('ENV_DB', '').strip().upper()
        env = ENV_ALIAS.get(env, env)
        status = r.get('STATUS', '').strip().upper()
        title = r.get('TITLE', '').strip()

        mx = maximo_by_userid[userid]
        if email:
            mx['emails'].add(email)
        if displayname:
            mx['displaynames'].add(displayname)
        if env:
            mx['envs'].add(env)
            if status:
                mx['env_status'][env].add(status)
        if status:
            mx['statuses'].add(status)
        if title:
            mx['titles'].add(title)

    # Índices para matching O(1) (antes: scan linear de 9.892 USERIDs por
    # cada um dos ~6.000 emails AD).
    userids_by_email = defaultdict(set)
    for uid, mx in maximo_by_userid.items():
        for email in mx['emails']:
            userids_by_email[email].add(uid)

    # Grupos Maximo atuais por usuário: "ENV: g1, g2 | ENV2: g3"
    groups_by_env_user = defaultdict(set)
    for gu in groupusers:
        env = gu.get('ENVIRONMENT', '').strip().upper()
        env = ENV_ALIAS.get(env, env)
        uid = gu.get('USERID', '').strip().upper()
        group = gu.get('GROUPNAME', '').strip().upper()
        if uid and group:
            groups_by_env_user[(env, uid)].add(group)

    def grupos_maximo_de(uid, envs):
        parts = []
        for env in sorted(envs):
            gs = groups_by_env_user.get((env, uid))
            if gs:
                parts.append(f"{env}: {', '.join(sorted(gs))}")
        return ' | '.join(parts)

    recommended_by_title, normalize_title_key = _load_recommended_group_by_title()

    def grupo_recomendado_de(mx):
        if not normalize_title_key:
            return ''
        for title in sorted(mx['titles']):
            key = ' / '.join(normalize_title_key(title))
            grupo = recommended_by_title.get(key)
            if grupo:
                return grupo
        return ''

    def env_status_pairs(mx):
        return ' | '.join(
            f"{env}:{'/'.join(sorted(sts))}"
            for env, sts in sorted(mx['env_status'].items())
        )

    # ============================================================
    # ANÁLISE
    # ============================================================
    recommendations = []
    matched_userids = set()

    def base_rec(tipo, prioridade, userid, email, ad_user, mx, match_por, motivo, acao,
                 status_ad, status_maximo):
        return {
            'tipo': tipo,
            'prioridade': prioridade,
            'userid': userid,
            'email': email,
            'nome_ad': ad_user['displayname'] if ad_user else 'N/A',
            'nome_maximo': ' | '.join(sorted(mx['displaynames'])) if mx else 'N/A',
            'status_ad': status_ad,
            'status_maximo': status_maximo,
            'envs': ' | '.join(sorted(mx['envs'])) if mx else 'N/A',
            'envs_detalhe': env_status_pairs(mx) if mx else '',
            'status_maximo_detalhe': ' | '.join(sorted(mx['statuses'])) if mx else '',
            'grupos_ad': ad_user['groups_count'] if ad_user else 0,
            'cargo': ' | '.join(sorted(mx['titles'])) if mx else '',
            'grupos_maximo': grupos_maximo_de(userid, mx['envs']) if mx else '',
            'grupo_recomendado_mas9': grupo_recomendado_de(mx) if mx else '',
            'match_por': match_por,
            'motivo': motivo,
            'acao': acao,
        }

    # 1. Usuários do AD: match por email, depois por prefixo do email = USERID
    #    (convenção da empresa; a auditoria mediu 782 usuários "só no AD" que
    #    na verdade existiam no Maximo por essa convenção, 449 ativos).
    for email, ad_user in sorted(ad_by_email.items()):
        matched = set(userids_by_email.get(email, set()))
        match_por = 'EMAIL'
        if not matched:
            prefix = email.split('@')[0].upper()
            if prefix in maximo_by_userid:
                matched = {prefix}
                match_por = 'PREFIXO_EMAIL'

        if not matched:
            # AD sem correspondência no Maximo
            if not ad_user['enabled']:
                recommendations.append(base_rec(
                    'REMOVER', 'BAIXA', 'N/A', email, ad_user, None, '',
                    'Usuário desabilitado no AD e não existe no Maximo. Nada a migrar; remover do AD se aplicável.',
                    'Remover do AD', 'INATIVO', 'NÃO EXISTE'))
            else:
                recommendations.append(base_rec(
                    'CRIAR_NO_MAXIMO', 'MEDIA', 'N/A', email, ad_user, None, '',
                    'Usuário ativo no AD mas não existe no Maximo (nem por email, nem por prefixo=USERID). Avaliar criação no MAS 9.',
                    'Avaliar criação no MAS 9', 'ATIVO', 'NÃO EXISTE'))
            continue

        for userid in sorted(matched):
            matched_userids.add(userid)
            mx = maximo_by_userid[userid]
            norm_statuses = {s.strip().upper() for s in mx['statuses']}
            is_active_maximo = bool(norm_statuses & ACTIVE_STATUSES)
            is_inactive_maximo = bool(norm_statuses & INACTIVE_STATUSES) and not is_active_maximo

            if _is_service_account(userid):
                recommendations.append(base_rec(
                    'CONTA_SERVICO', 'MEDIA', userid, email, ad_user, mx, match_por,
                    'Conta de serviço/genérica — não é pessoa. Definir explicitamente o tratamento na migração MAS 9.',
                    'Decidir tratamento (conta de serviço)',
                    'ATIVO' if ad_user['enabled'] else 'INATIVO',
                    'ATIVO' if is_active_maximo else ('INATIVO' if is_inactive_maximo else 'INDEFINIDO')))
            elif is_active_maximo and not ad_user['enabled']:
                # O caso mais grave: desligado da empresa, acesso vivo no Maximo.
                recommendations.append(base_rec(
                    'REMOVER', 'ALTA', userid, email, ad_user, mx, match_por,
                    'DESLIGADO no AD porém ATIVO no Maximo — risco de acesso indevido. NÃO migrar; desativar antes do MAS 9.',
                    'Desativar no Maximo (não migrar)', 'INATIVO', 'ATIVO'))
            elif is_inactive_maximo and not ad_user['enabled']:
                recommendations.append(base_rec(
                    'REMOVER', 'MEDIA', userid, email, ad_user, mx, match_por,
                    'Inativo no AD e no Maximo. Não migrar; remover de ambos.',
                    'Remover do AD e Maximo (não migrar)', 'INATIVO', 'INATIVO'))
            elif is_inactive_maximo and ad_user['enabled']:
                recommendations.append(base_rec(
                    'MIGRAR', 'MEDIA', userid, email, ad_user, mx, match_por,
                    'Ativo no AD mas inativo no Maximo. Decidir com o gestor: reativar e migrar, ou não migrar.',
                    'Reativar e migrar, ou não migrar', 'ATIVO', 'INATIVO'))
            elif is_active_maximo and ad_user['enabled']:
                # A população-alvo da migração: quem vai para o MAS 9.
                recommendations.append(base_rec(
                    'MANTER', 'BAIXA', userid, email, ad_user, mx, match_por,
                    'Ativo no AD e no Maximo — população que migra para o MAS 9, com os grupos indicados nas colunas de grupo.',
                    'Migrar para MAS 9 (grupos indicados)', 'ATIVO', 'ATIVO'))
            else:
                # Status não mapeado (NEWREG, DELETED, vazio...) — antes sumia
                # silenciosamente sem recomendação nenhuma.
                recommendations.append(base_rec(
                    'REVISAR_STATUS', 'MEDIA', userid, email, ad_user, mx, match_por,
                    f"Status do Maximo fora do vocabulário conhecido ({' | '.join(sorted(norm_statuses)) or 'vazio'}). Revisar manualmente antes de decidir a migração.",
                    'Revisar status manualmente',
                    'ATIVO' if ad_user['enabled'] else 'INATIVO', 'INDEFINIDO'))

    # 2. Usuários apenas no Maximo (sem match no AD por email nem prefixo)
    for userid, mx in sorted(maximo_by_userid.items()):
        if userid in matched_userids:
            continue
        if mx['emails'] and any(e in ad_by_email for e in mx['emails']):
            continue  # já tratado no passo 1 via e-mail de outro registro

        norm_statuses = {s.strip().upper() for s in mx['statuses']}
        is_active_maximo = bool(norm_statuses & ACTIVE_STATUSES)
        email = sorted(mx['emails'])[0] if mx['emails'] else '(sem email)'

        if _is_service_account(userid):
            recommendations.append(base_rec(
                'CONTA_SERVICO', 'MEDIA', userid, email, None, mx, '',
                'Conta de serviço/genérica sem correspondência no AD — não é pessoa. Definir tratamento na migração MAS 9.',
                'Decidir tratamento (conta de serviço)', 'NÃO EXISTE',
                'ATIVO' if is_active_maximo else 'INATIVO'))
        elif is_active_maximo:
            recommendations.append(base_rec(
                'VERIFICAR_AD', 'ALTA', userid, email, None, mx, '',
                'ATIVO no Maximo sem correspondência no AD (nem email, nem prefixo). Identificar a pessoa antes de migrar — pode ser conta órfã.',
                'Identificar dono / verificar AD', 'NÃO EXISTE', 'ATIVO'))
        elif mx['emails']:
            # Inativo e com email mas sem AD: não migrar; ruído antes ia para
            # VERIFICAR_AD (91% da categoria, medido na auditoria).
            recommendations.append(base_rec(
                'REMOVER', 'BAIXA', userid, email, None, mx, '',
                'Inativo no Maximo e sem correspondência no AD. Não migrar; candidata a limpeza.',
                'Não migrar (limpeza)', 'NÃO EXISTE', 'INATIVO'))
        # Inativos sem email e sem AD: não geram linha (milhares de contas
        # históricas — não migram e não têm ação além da limpeza em massa).

    # Ordenar por prioridade
    prioridade_order = {'ALTA': 0, 'MEDIA': 1, 'BAIXA': 2}
    recommendations.sort(key=lambda x: (prioridade_order.get(x['prioridade'], 3), x['tipo'], x['userid']))

    print(f"\n[MIGRACAO] Recomendacoes geradas: {len(recommendations)}")
    for tipo in ['REMOVER', 'MIGRAR', 'MANTER', 'CRIAR_NO_MAXIMO', 'VERIFICAR_AD', 'CONTA_SERVICO', 'REVISAR_STATUS']:
        count = sum(1 for r in recommendations if r['tipo'] == tipo)
        if count > 0:
            print(f"   {tipo}: {count}")
    match_prefix = sum(1 for r in recommendations if r.get('match_por') == 'PREFIXO_EMAIL')
    print(f"   (matches por prefixo email=USERID: {match_prefix})")

    return recommendations


def print_summary(recommendations):
    """Imprime resumo das recomendações."""
    print("\n" + "=" * 80)
    print("RESUMO DE RECOMENDACOES DE MIGRACAO")
    print("=" * 80)

    for tipo in ['REMOVER', 'MIGRAR', 'MANTER', 'CRIAR_NO_MAXIMO', 'VERIFICAR_AD', 'CONTA_SERVICO', 'REVISAR_STATUS']:
        items = [r for r in recommendations if r['tipo'] == tipo]
        if not items:
            continue

        print(f"\n{tipo} ({len(items)}):")
        for r in items[:5]:
            print(f"  - {r['email']}: {r['motivo'][:60]}")
        if len(items) > 5:
            print(f"  ... e mais {len(items) - 5}")


if __name__ == '__main__':
    recommendations = analyze_migration()
    print_summary(recommendations)
