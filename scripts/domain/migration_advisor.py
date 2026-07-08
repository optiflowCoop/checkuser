"""
scripts/domain/migration_advisor.py
Analisa dados de AD e Maximo e gera recomendações de migração/remoção/limpeza.
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict

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


def analyze_migration():
    """
    Analisa e gera recomendações de migração/remoção/limpeza.
    Retorna lista de recomendações.
    """
    # Carregar dados
    ad_rows = load_csv(IN_DIR / 'consolidated_ad_users.csv')
    identities = load_csv(IN_DIR / 'consolidated_user_identity.csv')
    access_rows = load_csv(IN_DIR / 'consolidated_user_access_normalized.csv') or load_csv(IN_DIR / 'consolidated_user_access.csv')
    
    print(f"📥 Analisando migrações:")
    print(f"   AD: {len(ad_rows)} usuários")
    print(f"   Identities: {len(identities)} registros")
    print(f"   Access: {len(access_rows)} registros")
    
    # ============================================================
    # CONSTRUIR MAPAS
    # ============================================================
    
    # AD: email -> {displayname, enabled, groups}
    ad_by_email = {}
    for r in ad_rows:
        email = r.get('mail', '').strip().lower()
        if email and '@' in email:
            ad_by_email[email] = {
                'email': email,
                'displayname': r.get('DisplayName', '').strip(),
                'enabled': r.get('Enabled', '').strip().lower() == 'true',
                'groups': r.get('MemberOf', '').strip(),
                'groups_count': len(r.get('MemberOf', '').split(', ')) if r.get('MemberOf') else 0,
            }
    
    # Maximo: USERID -> {emails, displaynames, envs, statuses}
    maximo_by_userid = defaultdict(lambda: {
        'emails': set(),
        'displaynames': set(),
        'envs': set(),
        'statuses': set(),
    })
    
    for r in identities:
        userid = r.get('USERID', '').strip().upper()
        email = r.get('PRIMARYEMAIL', '').strip().lower()
        displayname = r.get('DISPLAYNAME', '').strip()
        env = r.get('ENV_DB', '').strip()
        status = r.get('STATUS', '').strip().upper()
        
        if userid:
            if email:
                maximo_by_userid[userid]['emails'].add(email)
            if displayname:
                maximo_by_userid[userid]['displaynames'].add(displayname)
            if env:
                # Normalizar NORBE06/08/09 -> N06/N08/N09
                env_norm = env.upper().strip()
                mapping = {'NORBE06': 'N06', 'NORBE08': 'N08', 'NORBE09': 'N09', 'BASE-UNP': 'BASE', 'OP-BASE': 'BASE', 'ODRL-SP': 'BASE'}
                env_norm = mapping.get(env_norm, env_norm)
                maximo_by_userid[userid]['envs'].add(env_norm)
            if status:
                maximo_by_userid[userid]['statuses'].add(status)
    
    # ============================================================
    # ANÁLISE DE MIGRAÇÃO
    # ============================================================
    recommendations = []
    
    # 1. Usuários no AD e Maximo (match por email) - verificar status
    for email, ad_user in ad_by_email.items():
        # Procurar USERID no Maximo por email (qualquer status)
        maximo_users = [uid for uid, data in maximo_by_userid.items() if email in data['emails']]
        
        if maximo_users:
            # Usuário existe em ambos
            for userid in maximo_users:
                mx = maximo_by_userid[userid]
                statuses = mx['statuses']

                # Verificar status no Maximo (NORMALIZADO)
                norm_statuses = {s.strip().upper() for s in statuses}
                is_active_maximo = any(s in ('ACTIVE', 'ATIVO', 'ENABLED') for s in norm_statuses)
                is_inactive_maximo = any(s in ('INACTIVE', 'INATIVO', 'DISABLED') for s in norm_statuses) and not is_active_maximo
                
                if is_inactive_maximo and not ad_user['enabled']:
                    # Inativo em ambos - REMOVER
                    recommendations.append({
                        'tipo': 'REMOVER',
                        'prioridade': 'ALTA',
                        'userid': userid,
                        'email': email,
                        'nome_ad': ad_user['displayname'],
                        'nome_maximo': ' | '.join(sorted(mx['displaynames'])),
                        'status_ad': 'INATIVO',
                        'status_maximo': 'INATIVO',
                        'envs': ' | '.join(sorted(mx['envs'])),
                        'status_maximo_detalhe': ' | '.join(sorted(mx['statuses'])),
                        'grupos_ad': ad_user['groups_count'],
                        'motivo': 'Inativo no AD e no Maximo. Remover de ambos.',
                        'acao': 'Remover do AD e Maximo',
                    })
                elif is_inactive_maximo and ad_user['enabled']:
                    # Inativo no Maximo mas ativo no AD - MIGRAR/REATIVAR
                    recommendations.append({
                        'tipo': 'MIGRAR',
                        'prioridade': 'MEDIA',
                        'userid': userid,
                        'email': email,
                        'nome_ad': ad_user['displayname'],
                        'nome_maximo': ' | '.join(sorted(mx['displaynames'])),
                        'status_ad': 'ATIVO',
                        'status_maximo': 'INATIVO',
                        'envs': ' | '.join(sorted(mx['envs'])),
                        'status_maximo_detalhe': ' | '.join(sorted(mx['statuses'])),
                        'grupos_ad': ad_user['groups_count'],
                        'motivo': 'Ativo no AD mas inativo no Maximo. Verificar necessidade de acesso.',
                        'acao': 'Reativar no Maximo ou remover acesso',
                    })
                elif is_active_maximo and ad_user['enabled']:
                    # Ativo em ambos - MANTER
                    recommendations.append({
                        'tipo': 'MANTER',
                        'prioridade': 'BAIXA',
                        'userid': userid,
                        'email': email,
                        'nome_ad': ad_user['displayname'],
                        'nome_maximo': ' | '.join(sorted(mx['displaynames'])),
                        'status_ad': 'ATIVO',
                        'status_maximo': 'ATIVO',
                        'envs': ' | '.join(sorted(mx['envs'])),
                        'status_maximo_detalhe': ' | '.join(sorted(mx['statuses'])),
                        'grupos_ad': ad_user['groups_count'],
                        'motivo': 'Ativo em ambos os sistemas. Nenhuma ação necessária.',
                        'acao': 'Nenhuma ação',
                    })
    
    # 2. Usuários apenas no AD (sem match no Maximo)
    for email, ad_user in ad_by_email.items():
        maximo_users = [uid for uid, data in maximo_by_userid.items() if email in data['emails']]
        if not maximo_users:
            if not ad_user['enabled']:
                recommendations.append({
                    'tipo': 'REMOVER',
                    'prioridade': 'ALTA',
                    'userid': 'N/A',
                    'email': email,
                    'nome_ad': ad_user['displayname'],
                    'nome_maximo': 'N/A',
                    'status_ad': 'INATIVO',
                    'status_maximo': 'NÃO EXISTE',
                    'envs': 'N/A',
                    'grupos_ad': ad_user['groups_count'],
                    'motivo': 'Usuário inativo no AD e não existe no Maximo. Remover do AD.',
                    'acao': 'Remover do AD',
                })
            else:
                recommendations.append({
                    'tipo': 'CRIAR_NO_MAXIMO',
                    'prioridade': 'MEDIA',
                    'userid': 'N/A',
                    'email': email,
                    'nome_ad': ad_user['displayname'],
                    'nome_maximo': 'N/A',
                    'status_ad': 'ATIVO',
                    'status_maximo': 'NÃO EXISTE',
                    'envs': 'N/A',
                    'grupos_ad': ad_user['groups_count'],
                    'motivo': 'Usuário ativo no AD mas não existe no Maximo. Avaliar criação.',
                    'acao': 'Criar usuário no Maximo',
                })
    
    # 3. Usuários apenas no Maximo (sem match no AD) - APENAS com email válido
    for userid, mx in maximo_by_userid.items():
        # Verificar se algum email deste USERID está no AD
        has_match = any(email in ad_by_email for email in mx['emails'])
        
        # Apenas processar se tiver email válido
        if not has_match and mx['emails']:
            # Pegar o primeiro email para exibir
            email = list(mx['emails'])[0]
            statuses = ' | '.join(sorted(mx['statuses']))
            
            recommendations.append({
                'tipo': 'VERIFICAR_AD',
                'prioridade': 'MEDIA',
                'userid': userid,
                'email': email,
                'nome_ad': 'N/A',
                'nome_maximo': ' | '.join(sorted(mx['displaynames'])),
                'status_ad': 'NÃO EXISTE',
                'status_maximo': statuses,
                'envs': ' | '.join(sorted(mx['envs'])),
                'status_maximo_detalhe': ' | '.join(sorted(mx['statuses'])),
                'grupos_ad': 0,
                'motivo': 'Usuário existe no Maximo mas não no AD. Verificar se deve ser criado no AD.',
                'acao': 'Verificar necessidade de criação no AD',
            })
    
    # Ordenar por prioridade
    prioridade_order = {'ALTA': 0, 'MEDIA': 1, 'BAIXA': 2}
    recommendations.sort(key=lambda x: (prioridade_order.get(x['prioridade'], 3), x['tipo']))
    
    print(f"\n📊 Recomendações geradas: {len(recommendations)}")
    for tipo in ['REMOVER', 'MIGRAR', 'MANTER', 'CRIAR_NO_MAXIMO', 'VERIFICAR_AD']:
        count = sum(1 for r in recommendations if r['tipo'] == tipo)
        if count > 0:
            print(f"   {tipo}: {count}")
    
    return recommendations


def print_summary(recommendations):
    """Imprime resumo das recomendações."""
    print("\n" + "=" * 80)
    print("RESUMO DE RECOMENDAÇÕES DE MIGRAÇÃO")
    print("=" * 80)
    
    for tipo in ['REMOVER', 'MIGRAR', 'MANTER', 'CRIAR_NO_MAXIMO', 'VERIFICAR_AD']:
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