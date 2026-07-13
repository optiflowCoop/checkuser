"""
scripts/domain/sanity_analyzer.py
Analisa e compara identidades entre AD (fonte da verdade) e Maximo.
Detecta divergências de nome, múltiplos USERIDs, conflitos de domínio, etc.
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IN_DIR = ROOT / 'output' / 'consolidated'


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


def normalize_name(name):
    """Normaliza nome para comparação: remove acentos, espaços duplos, maiúsculas/minúsculas, pontuação. Sempre recebe str, trata None/set/list."""
    if not name:
        return ''
    if isinstance(name, (set, list)):
        # Pega primeiro valor não vazio
        name = next(iter(x for x in name if x), '')
    name = str(name).strip().upper()
    import unicodedata
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    name = re.sub(r'\s+', ' ', name)
    name = name.replace('.', '').replace(',', '').replace('-', ' ').replace('  ', ' ')
    return name.strip()



def extract_email_prefix(email):
    """Extrai o prefixo do email (parte antes do @) como possível USERID."""
    if not email or '@' not in str(email):
        return ''
    return str(email).split('@')[0].strip().lower()


def extract_domain(email):
    """Extrai o domínio do email."""
    if not email or '@' not in str(email):
        return 'SEM DOMINIO'
    return str(email).split('@')[1].strip().lower()


def analyze_sanity():
    """
    Análise completa de saneamento de identidades.
    Retorna dicionário com todas as análises.
    """
    # 1. Carregar dados do AD (fonte da verdade)
    ad_rows = load_csv(IN_DIR / 'consolidated_ad_users.csv')
    
    # 1.1 Carregar usuários desativados do AD (lista específica para auditoria)
    ad_disabled_rows = load_csv(ROOT / 'adUsers' / 'adUsersdesabilitadas.csv')
    print(f"[AD] {len(ad_rows)} usuarios carregados")
    print(f"[AD] {len(ad_disabled_rows)} usuarios desativados")
    if ad_rows:
        print(f"   Colunas AD: {list(ad_rows[0].keys())}")
        print(f"   Exemplo AD: {list(ad_rows[0].items())[:3]}")
    
    # 2. Carregar dados do Maximo (identities + access)
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    access_rows = load_csv(IN_DIR / 'consolidated_user_access_normalized.csv') or load_csv(IN_DIR / 'consolidated_user_access.csv')
    
    print(f"[MAXIMO] {len(identities)} registros")
    if identities:
        print(f"   Colunas Identities: {list(identities[0].keys())}")
    print(f"[MAXIMO] {len(access_rows)} registros")
    
    # ============================================================
    # CONSTRUIR MAPAS DO AD
    # ============================================================
    # AD: email -> {displayname, givenname, surname, enabled, groups}
    ad_by_email = {}
    ad_by_prefix = {}  # prefixo do email -> AD record
    
    for r in ad_rows:
        email = r.get('mail', '').strip().lower()
        if email:
            displayname = r.get('DisplayName', '').strip()
            givenname = r.get('GivenName', '').strip()
            surname = r.get('Surname', '').strip()
            enabled = r.get('Enabled', '').strip().lower() == 'true'
            groups = r.get('MemberOf', '').strip()
            
            ad_by_email[email] = {
                'email': email,
                'displayname': displayname,
                'givenname': givenname,
                'surname': surname,
                'enabled': enabled,
                'groups_count': len(groups.split(', ')) if groups else 0,
                'groups': groups,
                'domain': extract_domain(email),
                'prefix': extract_email_prefix(email),
            }
            
            prefix = extract_email_prefix(email)
            if prefix and prefix not in ad_by_prefix:
                ad_by_prefix[prefix] = ad_by_email[email]
    
    print(f"   AD emails unicos: {len(ad_by_email)}")
    print(f"   AD prefixos unicos: {len(ad_by_prefix)}")
    
    # ============================================================
    # 1.2 IDENTIFICAR USUÁRIOS DESATIVADOS NO AD
    # ============================================================
    ad_disabled_by_email = {}
    for r in ad_disabled_rows:
        email = r.get('mail', '').strip().lower()
        if email and '@' in email:
            ad_disabled_by_email[email] = {
                'email': email,
                'displayname': r.get('DisplayName', '').strip(),
                'givenname': r.get('GivenName', '').strip(),
                'surname': r.get('Surname', '').strip(),
                'enabled': False,  # Todos são desativados
                'groups': r.get('MemberOf', '').strip(),
                'groups_count': len(r.get('MemberOf', '').strip().split(', ')) if r.get('MemberOf', '').strip() else 0,
                'domain': extract_domain(email),
                'prefix': extract_email_prefix(email),
            }
    
    print(f"   AD Desabilitados com email valido: {len(ad_disabled_by_email)}")
    
    # ============================================================
    # 1.3 REMOVER USUARIOS DUPLICADOS (desabilitados que tambem estao habilitados)
    # ============================================================
    # Se um usuario esta no arquivo de desabilitados, remover do de habilitados
    disabled_emails = set(ad_disabled_by_email.keys())
    for email in disabled_emails:
        if email in ad_by_email:
            del ad_by_email[email]
    
    print(f"   AD emails apos remover duplicados: {len(ad_by_email)}")
    
    # ============================================================
    # CONSTRUIR MAPAS DO MAXIMO
    # ============================================================
    # Maximo: email -> lista de {userid, displayname, env, status}
    # APENAS USUÁRIOS COM EMAIL VÁLIDO (comparáveis no saneamento)
    maximo_by_email = defaultdict(list)
    maximo_by_userid = {}  # USERID -> {displayname, envs, statuses, email, comparable}
    
    for r in identities:
        email = r.get('PRIMARYEMAIL', '').strip().lower()
        userid = r.get('USERID', '').strip().upper()
        displayname = r.get('DISPLAYNAME', '').strip()
        env = r.get('ENV_DB', '').strip()
        status = r.get('STATUS', '').strip()
        firstname = r.get('FIRSTNAME', '').strip()
        lastname = r.get('LASTNAME', '').strip()
        title = r.get('TITLE', '').strip()
        persongroup = r.get('PERSONGROUP', '').strip()
        
        # APENAS emails válidos (com @) são comparáveis
        is_comparable = bool(email and '@' in email)
        
        if is_comparable:
            maximo_by_email[email].append({
                'userid': userid,
                'displayname': displayname,
                'firstname': firstname,
                'lastname': lastname,
                'env': env,
                'status': status,
                'title': title,
                'persongroup': persongroup,
                'domain': extract_domain(email),
                'prefix': extract_email_prefix(email),
            })
        
        if userid:
            if userid not in maximo_by_userid:
                maximo_by_userid[userid] = {
                    'userid': userid,
                    'displaynames': set(),
                    'emails': set(),
                    'envs': set(),
                    'statuses': set(),
                    'env_status': {},  # ambiente -> status, para saber ONDE especificamente está ativo
                    'titles': set(),
                    'persongroups': set(),
                    'comparable': is_comparable,
                }
            mx = maximo_by_userid[userid]
            if displayname:
                mx['displaynames'].add(displayname)
            if email:
                mx['emails'].add(email)
            if env:
                mx['envs'].add(env)
            if status:
                mx['statuses'].add(status)
            if env and status:
                # Mesmo ambiente pode repetir por linha duplicada; mantém o status
                # mais "grave" (ACTIVE) se houver divergência entre linhas.
                prev = mx['env_status'].get(env)
                if not prev or status.upper() in ('ACTIVE', 'ATIVO', 'ENABLED'):
                    mx['env_status'][env] = status
            if title:
                mx['titles'].add(title)
            if persongroup:
                mx['persongroups'].add(persongroup)
            # Atualizar comparable se tiver email
            if is_comparable:
                mx['comparable'] = True
    
    print(f"   Maximo emails unicos (comparaveis): {len(maximo_by_email)}")
    print(f"   Maximo USERIDs unicos: {len(maximo_by_userid)}")
    print(f"   Maximo USERIDs comparaveis: {sum(1 for mx in maximo_by_userid.values() if mx['comparable'])}")

    # Checagem de cobertura: o Maximo tem 7 ambientes. Se algum estiver faltando
    # aqui, esta auditoria de AD x Maximo está incompleta silenciosamente — ex.:
    # usuários desativados no AD ainda ativos em um ambiente ausente nunca aparecerão.
    envs_presentes = sorted({e for mx in maximo_by_userid.values() for e in mx['envs'] if e})
    print(f"   Ambientes Maximo cobertos por esta auditoria ({len(envs_presentes)}): {envs_presentes}")
    
    # ============================================================
    # ANÁLISE 1: MATCH POR EMAIL (apenas usuários comparáveis)
    # ============================================================
    ad_emails_set = set(ad_by_email.keys())
    maximo_emails_set = set(maximo_by_email.keys())
    
    match_emails = ad_emails_set & maximo_emails_set
    only_ad_emails = ad_emails_set - maximo_emails_set
    only_maximo_emails = maximo_emails_set - ad_emails_set
    
    print(f"\n[METRICAS] Match por email (apenas comparaveis):")
    print(f"   Match: {len(match_emails)}")
    print(f"   Apenas no AD: {len(only_ad_emails)}")
    print(f"   Apenas no Maximo: {len(only_maximo_emails)}")
    
    # ============================================================
    # ANÁLISE 2: DIVERGÊNCIAS DE NOME (mesmo email, nomes diferentes)
    # ============================================================
    name_divergences = []
    for email in sorted(match_emails):
        ad_user = ad_by_email[email]
        ad_name_norm = normalize_name(ad_user['displayname'])
        
        maximo_users = maximo_by_email[email]
        maximo_names = set()
        for mu in maximo_users:
            if mu['displayname']:
                maximo_names.add(normalize_name(mu['displayname']))
        
        # Verificar se o nome do AD é diferente de algum nome do Maximo
        if maximo_names and ad_name_norm not in maximo_names:
            name_divergences.append({
                'email': email,
                'ad_displayname': ad_user['displayname'],
                'ad_givenname': ad_user['givenname'],
                'ad_surname': ad_user['surname'],
                'maximo_names': ' | '.join(sorted(m for m in maximo_names if m)),
                'maximo_userids': ' | '.join(sorted(mu['userid'] for mu in maximo_users if mu['userid'])),
                'maximo_envs': ' | '.join(sorted(set(mu['env'] for mu in maximo_users if mu['env']))),
                'maximo_statuses': ' | '.join(sorted(set(mu['status'] for mu in maximo_users if mu['status']))),
                'domain': ad_user['domain'],
                'ad_enabled': ad_user['enabled'],
                'ad_groups_count': ad_user['groups_count'],
                'tipo': 'DIVERGENCIA_NOME',
            })
    
    print(f"\n[DIVERG] Divergencias de nome (mesmo email): {len(name_divergences)}")
    
    # ============================================================
    # ANÁLISE 3: MÚLTIPLOS USERIDs para o mesmo email no Maximo
    # ============================================================
    multi_userid = []
    for email in sorted(match_emails):
        maximo_users = maximo_by_email[email]
        userids = set(mu['userid'] for mu in maximo_users if mu['userid'])
        if len(userids) > 1:
            ad_user = ad_by_email[email]
            multi_userid.append({
                'email': email,
                'ad_displayname': ad_user['displayname'],
                'qtd_userids': len(userids),
                'userids': ' | '.join(sorted(userids)),
                'envs': ' | '.join(sorted(set(mu['env'] for mu in maximo_users if mu['env']))),
                'statuses': ' | '.join(sorted(set(mu['status'] for mu in maximo_users if mu['status']))),
                'domain': ad_user['domain'],
                'tipo': 'MULTIPLOS_USERIDS',
            })
    
    print(f"[MULTI] Multiplos USERIDs por email: {len(multi_userid)}")
    
    # ============================================================
    # ANÁLISE 4: MATCH POR PREFIXO (USERID do AD vs Maximo)
    # ============================================================
    # Usuários do AD sem email no Maximo: tentar match por prefixo do email
    prefix_match = []
    no_match = []
    
    for email in sorted(only_ad_emails):
        ad_user = ad_by_email[email]
        prefix = ad_user['prefix']
        
        # Procurar USERID no Maximo que corresponda ao prefixo
        # APENAS se o USERID for comparável (tem email válido)
        if prefix.upper() in maximo_by_userid:
            mx = maximo_by_userid[prefix.upper()]
            if mx['comparable']:
                prefix_match.append({
                    'email': email,
                    'ad_displayname': ad_user['displayname'],
                    'maximo_userid': prefix.upper(),
                    'maximo_displaynames': ' | '.join(sorted(mx['displaynames'])),
                    'maximo_envs': ' | '.join(sorted(mx['envs'])),
                    'maximo_statuses': ' | '.join(sorted(mx['statuses'])),
                    'maximo_emails': ' | '.join(sorted(mx['emails'])),
                    'domain': ad_user['domain'],
                    'ad_enabled': ad_user['enabled'],
                    'ad_groups_count': ad_user['groups_count'],
                    'tipo': 'MATCH_PREFIXO',
                })
            else:
                # USERID existe mas não é comparável (sem email)
                no_match.append({
                    'email': email,
                    'ad_displayname': ad_user['displayname'],
                    'ad_givenname': ad_user['givenname'],
                    'ad_surname': ad_user['surname'],
                    'prefix': prefix,
                    'domain': ad_user['domain'],
                    'ad_enabled': ad_user['enabled'],
                    'ad_groups_count': ad_user['groups_count'],
                    'tipo': 'SEM_MATCH_MAXIMO',
                })
        else:
            no_match.append({
                'email': email,
                'ad_displayname': ad_user['displayname'],
                'ad_givenname': ad_user['givenname'],
                'ad_surname': ad_user['surname'],
                'prefix': prefix,
                'domain': ad_user['domain'],
                'ad_enabled': ad_user['enabled'],
                'ad_groups_count': ad_user['groups_count'],
                'tipo': 'SEM_MATCH_MAXIMO',
            })
    
    print(f"[PREFIX] Match por prefixo (USERID): {len(prefix_match)}")
    print(f"[NOMATCH] Sem match no Maximo: {len(no_match)}")
    
    # ============================================================
    # ANÁLISE 5: USUÁRIOS NO MAXIMO SEM EMAIL (comparar por USERID)
    # ============================================================
    # Usuários do Maximo que não tem email mas tem USERID que corresponde a um prefixo do AD
    maximo_sem_email_match = []
    maximo_sem_email_nomatch = []
    
    for userid, mx in maximo_by_userid.items():
        if not mx['emails']:  # Sem email cadastrado
            # Verificar se o USERID corresponde a algum prefixo do AD
            prefix_lower = userid.lower()
            if prefix_lower in ad_by_prefix:
                ad_user = ad_by_prefix[prefix_lower]
                maximo_sem_email_match.append({
                    'userid': userid,
                    'maximo_displaynames': ' | '.join(sorted(mx['displaynames'])),
                    'maximo_envs': ' | '.join(sorted(mx['envs'])),
                    'maximo_statuses': ' | '.join(sorted(mx['statuses'])),
                    'maximo_titles': ' | '.join(sorted(mx['titles'])),
                    'ad_email': ad_user['email'],
                    'ad_displayname': ad_user['displayname'],
                    'ad_enabled': ad_user['enabled'],
                    'ad_groups_count': ad_user['groups_count'],
                    'tipo': 'MAXIMO_SEM_EMAIL_COM_MATCH_AD',
                })
            else:
                maximo_sem_email_nomatch.append({
                    'userid': userid,
                    'maximo_displaynames': ' | '.join(sorted(mx['displaynames'])),
                    'maximo_envs': ' | '.join(sorted(mx['envs'])),
                    'maximo_statuses': ' | '.join(sorted(mx['statuses'])),
                    'tipo': 'MAXIMO_SEM_EMAIL_SEM_MATCH_AD',
                })
    
    print(f"[MAXIMO SEM EMAIL] Com match no AD: {len(maximo_sem_email_match)}")
    print(f"[MAXIMO SEM EMAIL] Sem match no AD: {len(maximo_sem_email_nomatch)}")
    
    # ============================================================
    # ANÁLISE 6: USUÁRIOS DESATIVADOS NO AD MAS ATIVOS NO MAXIMO
    # Apenas usuários com STATUS = ACTIVE no Maximo
    # ============================================================
    ad_disabled_ativos_maximo = []
    for email, ad_user in ad_disabled_by_email.items():
        # Verificar se este email existe no Maximo
        if email in maximo_by_email:
            maximo_users = maximo_by_email[email]
            # Filtrar apenas usuários ATIVOS no Maximo
            usuarios_ativos = [mu for mu in maximo_users if mu['status'].upper() in ['ACTIVE', 'ATIVO', 'ENABLED']]
            if usuarios_ativos:
                todos_envs = sorted(set(mu['env'] for mu in maximo_users if mu['env']))
                envs_ativos = sorted(set(mu['env'] for mu in usuarios_ativos if mu['env']))
                ad_disabled_ativos_maximo.append({
                    'email': email,
                    'ad_displayname': ad_user['displayname'],
                    'ad_givenname': ad_user['givenname'],
                    'ad_surname': ad_user['surname'],
                    'ad_groups_count': ad_user['groups_count'],
                    'ad_groups': ad_user['groups'],
                    'maximo_userids': ' | '.join(sorted(set(mu['userid'] for mu in usuarios_ativos if mu['userid']))),
                    'maximo_envs': ' | '.join(envs_ativos),
                    'maximo_envs_total': ' | '.join(todos_envs),
                    'qtd_envs_ativos_de_total': f"{len(envs_ativos)}/{len(todos_envs)}",
                    'maximo_statuses': ' | '.join(sorted(set(mu['status'] for mu in usuarios_ativos if mu['status']))),
                    'maximo_names': ' | '.join(sorted(set(mu['displayname'] for mu in usuarios_ativos if mu['displayname']))),
                    'domain': ad_user['domain'],
                    'qtd_ativos_maximo': len(usuarios_ativos),
                })
    
    # ============================================================
    # ANÁLISE 6b: USUÁRIOS DESATIVADOS NO AD MAS ATIVOS NO MAXIMO (por USERID ou NOME)
    # Quando não tem email no Maximo, usar score de similaridade
    # ============================================================
    # Palavras conectoras comuns em nomes PT-BR: contá-las como "palavra em comum"
    # gera falsos positivos entre pessoas totalmente diferentes (ex.: "...DE MOURA..."
    # bate com "...DE OLIVEIRA..." só pela palavra "DE"). Excluídas do score de nome.
    NAME_STOPWORDS = {'DE', 'DA', 'DO', 'DAS', 'DOS', 'E'}
    ad_disabled_sem_email = []
    for email, ad_user in ad_disabled_by_email.items():
        # Se já foi encontrado por email, pular
        if email in maximo_by_email:
            continue

        ad_given_norm = normalize_name(ad_user['givenname'])
        ad_given_words = set(ad_given_norm.split()) - NAME_STOPWORDS

        # Procurar por USERID igual
        prefix = ad_user['prefix']
        if prefix.upper() in maximo_by_userid:
            mx = maximo_by_userid[prefix.upper()]
            # Só é um alerta real se este USERID estiver ATIVO em algum ambiente do
            # Maximo — sem este filtro, usuários já inativos no Maximo também
            # apareciam na lista de "desativado no AD mas ativo no Maximo" (falso positivo).
            mx_statuses_upper = {s.upper() for s in mx['statuses']}
            # Prefixo de email igual a um USERID pode ser coincidência entre pessoas
            # diferentes (USERIDs do Maximo costumam ser gerados por padrão de nome).
            # Exige que o primeiro nome do AD apareça em algum nome do Maximo para
            # esse USERID antes de tratar como o mesmo indivíduo.
            mx_all_words = {w for name in mx['displaynames'] for w in normalize_name(name).split()} - NAME_STOPWORDS
            given_name_matches = bool(ad_given_words) and ad_given_words.issubset(mx_all_words)
            if mx['comparable'] and given_name_matches and (mx_statuses_upper & {'ACTIVE', 'ATIVO', 'ENABLED'}):
                # Encontrou match por USERID, com nome consistente, ativo em pelo menos um ambiente
                envs_ativos = sorted(e for e, s in mx['env_status'].items() if s.upper() in ('ACTIVE', 'ATIVO', 'ENABLED'))
                todos_envs = sorted(mx['envs'])
                ad_disabled_sem_email.append({
                    'email': email,
                    'ad_displayname': ad_user['displayname'],
                    'ad_givenname': ad_user['givenname'],
                    'ad_surname': ad_user['surname'],
                    'ad_groups_count': ad_user['groups_count'],
                    'ad_groups': ad_user['groups'],
                    'maximo_userids': mx['userid'],
                    'maximo_envs': ' | '.join(envs_ativos),
                    'maximo_envs_total': ' | '.join(todos_envs),
                    'qtd_envs_ativos_de_total': f"{len(envs_ativos)}/{len(todos_envs)}",
                    'maximo_statuses': ' | '.join(sorted(mx['statuses'])),
                    'maximo_names': ' | '.join(sorted(mx['displaynames'])),
                    'domain': ad_user['domain'],
                    'qtd_ativos_maximo': len(mx['statuses']),
                    'match_type': 'USERID',
                })
                continue
        
        # Procurar por nome similar (score)
        ad_name_norm = normalize_name(ad_user['displayname'])
        ad_given_norm = normalize_name(ad_user['givenname'])
        ad_given_words = set(ad_given_norm.split()) - NAME_STOPWORDS
        best_match = None
        best_score = 0

        for userid, mx in maximo_by_userid.items():
            for mx_name in mx['displaynames']:
                mx_name_norm = normalize_name(mx_name)
                # Calcula similaridade por palavras em comum, ignorando conectores
                # (DE/DA/DOS/...) que geram falso positivo entre sobrenomes distintos.
                ad_words = set(ad_name_norm.split()) - NAME_STOPWORDS
                mx_words = set(mx_name_norm.split()) - NAME_STOPWORDS
                common_words = ad_words & mx_words
                score = len(common_words)

                # Exige que o primeiro nome do AD também apareça no nome do Maximo —
                # sem isso, dois sobrenomes parecidos (ex.: "...CRUZ DOURADO" vs
                # "...MOURA CRUZ") já bastavam para virar "match" mesmo sendo pessoas
                # diferentes.
                given_name_matches = bool(ad_given_words) and ad_given_words.issubset(mx_words)

                if score >= 3 and given_name_matches and score > best_score:
                    best_match = mx
                    best_score = score
        
        if best_match and ({s.upper() for s in best_match['statuses']} & {'ACTIVE', 'ATIVO', 'ENABLED'}):
            envs_ativos = sorted(e for e, s in best_match['env_status'].items() if s.upper() in ('ACTIVE', 'ATIVO', 'ENABLED'))
            todos_envs = sorted(best_match['envs'])
            ad_disabled_sem_email.append({
                'email': email,
                'ad_displayname': ad_user['displayname'],
                'ad_givenname': ad_user['givenname'],
                'ad_surname': ad_user['surname'],
                'ad_groups_count': ad_user['groups_count'],
                'ad_groups': ad_user['groups'],
                'maximo_userids': best_match['userid'],
                'maximo_envs': ' | '.join(envs_ativos),
                'maximo_envs_total': ' | '.join(todos_envs),
                'qtd_envs_ativos_de_total': f"{len(envs_ativos)}/{len(todos_envs)}",
                'maximo_statuses': ' | '.join(sorted(best_match['statuses'])),
                'maximo_names': ' | '.join(sorted(best_match['displaynames'])),
                'domain': ad_user['domain'],
                'qtd_ativos_maximo': len(best_match['statuses']),
                'match_type': f'NOME (score: {best_score})',
            })
    
    # Adicionar os encontrados por USERID/nome à lista principal
    ad_disabled_ativos_maximo.extend(ad_disabled_sem_email)

    # Nota: este print tinha sido movido para ANTES da extensão por USERID/nome
    # (Análise 6b) em uma versão anterior — sempre reportava só o match por email
    # exato (tipicamente 0, já que a maioria dos usuários do Maximo não tem email
    # cadastrado), escondendo os matches por USERID/nome que a Análise 6b encontra.
    print(f"\n[ALERTA] Usuarios desativados no AD mas ativos no Maximo: {len(ad_disabled_ativos_maximo)}")
    match_por_email = sum(1 for x in ad_disabled_ativos_maximo if 'match_type' not in x)
    match_por_userid = sum(1 for x in ad_disabled_ativos_maximo if x.get('match_type') == 'USERID')
    match_por_nome = sum(1 for x in ad_disabled_ativos_maximo if str(x.get('match_type', '')).startswith('NOME'))
    print(f"   Por email exato: {match_por_email} | Por USERID: {match_por_userid} | Por nome (requer revisão manual): {match_por_nome}")

    # ============================================================
    # ANÁLISE 7: DIVERGÊNCIAS DE DOMÍNIO
    # ============================================================
    domain_divergences = []
    for email in sorted(match_emails):
        ad_user = ad_by_email[email]
        ad_domain = ad_user['domain']
        
        maximo_users = maximo_by_email[email]
        for mu in maximo_users:
            if mu['domain'] != ad_domain:
                domain_divergences.append({
                    'email': email,
                    'ad_displayname': ad_user['displayname'],
                    'ad_domain': ad_domain,
                    'maximo_domain': mu['domain'],
                    'maximo_userid': mu['userid'],
                    'maximo_env': mu['env'],
                    'maximo_status': mu['status'],
                    'tipo': 'DOMINIO_DIVERGENTE',
                })
    
    print(f"[DOMINIO] Divergencias de dominio: {len(domain_divergences)}")
    
    # ============================================================
    # MONTAR RESULTADO FINAL
    # ============================================================
    result = {
        'stats': {
            'total_ad': len(ad_rows),
            'total_ad_disabled': len(ad_disabled_rows),
            'total_maximo_identities': len(identities),
            'total_maximo_userids': len(maximo_by_userid),
            'match_email': len(match_emails),
            'only_ad': len(only_ad_emails),
            'only_maximo': len(only_maximo_emails),
            'name_divergences': len(name_divergences),
            'multi_userid': len(multi_userid),
            'prefix_match': len(prefix_match),
            'no_match': len(no_match),
            'maximo_sem_email_match': len(maximo_sem_email_match),
            'maximo_sem_email_nomatch': len(maximo_sem_email_nomatch),
            'domain_divergences': len(domain_divergences),
            'ad_disabled_ativos_maximo': len(ad_disabled_ativos_maximo),
        },
        'ad_by_email': ad_by_email,
        'ad_disabled_by_email': ad_disabled_by_email,
        'maximo_by_email': dict(maximo_by_email),
        'maximo_by_userid': maximo_by_userid,
        'analises': {
            'match_emails': sorted(match_emails),
            'only_ad_emails': sorted(only_ad_emails),
            'only_maximo_emails': sorted(only_maximo_emails),
            'name_divergences': name_divergences,
            'multi_userid': multi_userid,
            'prefix_match': prefix_match,
            'no_match': no_match,
            'maximo_sem_email_match': maximo_sem_email_match,
            'maximo_sem_email_nomatch': maximo_sem_email_nomatch,
            'domain_divergences': domain_divergences,
            'ad_disabled_ativos_maximo': ad_disabled_ativos_maximo,
        }
    }
    
    return result


def print_summary(result):
    """Imprime resumo da análise."""
    s = result['stats']
    print("\n" + "=" * 80)
    print("RESUMO DA ANALISE DE SANEAMENTO DE IDENTIDADES")
    print("=" * 80)
    print(f"\n[METRICAS] VISAO GERAL:")
    print(f"   Total AD: {s['total_ad']}")
    print(f"   Total AD Desabilitados: {s['total_ad_disabled']}")
    print(f"   Total Maximo (identities): {s['total_maximo_identities']}")
    print(f"   Total Maximo (USERIDs unicos): {s['total_maximo_userids']}")
    
    print(f"\n[OK] MATCH POR EMAIL:")
    print(f"   Match perfeito: {s['match_email']}")
    print(f"   Apenas no AD: {s['only_ad']}")
    print(f"   Apenas no Maximo: {s['only_maximo']}")
    
    print(f"\n[ALERTA] DIVERGENCIAS:")
    print(f"   Nomes diferentes (mesmo email): {s['name_divergences']}")
    print(f"   Multiplos USERIDs (mesmo email): {s['multi_userid']}")
    print(f"   Dominios divergentes: {s['domain_divergences']}")
    
    print(f"\n[LINK] MATCH POR PREFIXO (USERID):")
    print(f"   Match encontrado: {s['prefix_match']}")
    print(f"   Sem match no Maximo: {s['no_match']}")
    
    print(f"\n[INFO] MAXIMO SEM EMAIL:")
    print(f"   Com match no AD: {s['maximo_sem_email_match']}")
    print(f"   Sem match no AD: {s['maximo_sem_email_nomatch']}")
    
    print(f"\n[CRITICO] AUDITORIA - AD DESABILITADO + MAXIMO ATIVO:")
    print(f"   Usuarios desativados no AD mas ativos no Maximo: {s['ad_disabled_ativos_maximo']}")


if __name__ == '__main__':
    result = analyze_sanity()
    print_summary(result)