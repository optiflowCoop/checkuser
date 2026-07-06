#!/usr/bin/env python3
"""
Identificação INTELIGENTE do ambiente real do usuário.

Lógica:
1. Inferir ambiente do CLIENTHOST (odrl-odn2-sv013 -> ODN2, odrl-n06-sv013 -> N06, etc.)
2. Contar logins por ambiente nos últimos 60 dias
3. O ambiente com MAIS logins é o ambiente "real"
4. Exceções: usuários de suporte (logam em todos os ambientes)
"""
import csv
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "output" / "consolidated"

# Environment alias mapping
ENV_ALIAS = {'N06': 'NORBE06', 'N08': 'NORBE08', 'N09': 'NORBE09'}

def canon_env(v):
    """Canonicalize environment name."""
    v = (v or '').strip()
    return ENV_ALIAS.get(v, v)

def infer_env_from_clienthost(clienthost):
    """
    Infer environment from CLIENTHOST hostname.
    Returns: (env, is_shared_server)
    - env: the inferred environment or None
    - is_shared_server: True if the server is shared (odrl-sp-sv013) or IP
    """
    if not clienthost:
        return None, False
    
    host = clienthost.strip().upper()
    
    # IP addresses - não podemos inferir ambiente
    # IPs como 10.119.35.59, 10.117.120.28, etc.
    if host.replace('.', '').isdigit():
        return None, True  # IP - não inferir ambiente
    
    # Padrão odrl-sp-sv013.foresea.com - SERVIDOR COMPARTILHADO
    if 'ODRL-SP-SV' in host:
        return None, True  # Servidor compartilhado - não inferir ambiente
    
    # Servidores específicos de ambiente
    if 'ODRL-ODN2-SV' in host:
        return 'ODN2', False
    if 'ODRL-ODN1-SV' in host:
        return 'ODN1', False
    if 'ODRL-ODN3-SV' in host:
        return 'ODN3', False
    if 'ODRL-ODN4-SV' in host:
        return 'ODN4', False
    
    if 'ODRL-N06-SV' in host:
        return 'N06', False
    if 'ODRL-N08-SV' in host:
        return 'N08', False
    if 'ODRL-N09-SV' in host:
        return 'N09', False
    
    if 'ODRL-HTQ-SV' in host:
        return 'HTQ', False
    if 'ODRL-POL-SV' in host:
        return 'POL', False
    if 'ODRL-PGA-SV' in host:
        return 'PGA', False
    if 'ODRL-PGB-SV' in host:
        return 'PGB', False
    
    # Padrão OD2-, OD1-, ON06- (máquinas específicas)
    if host.startswith('OD2-') or '-OD2-' in host:
        return 'ODN2', False
    if host.startswith('OD1-') or '-OD1-' in host:
        return 'ODN1', False
    if host.startswith('ON06-') or '-N06-' in host:
        return 'N06', False
    if host.startswith('ON08-') or '-N08-' in host:
        return 'N08', False
    if host.startswith('ON09-') or '-N09-' in host:
        return 'N09', False
    
    return None, False


def get_user_env_frequency(logintracking_data, days=60):
    """
    Get the frequency of logins per environment for each user.
    Returns: {userid: {env: count, ...}}
    """
    user_env_counts = defaultdict(Counter)
    
    # Calculate cutoff date
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    
    for rec in logintracking_data:
        result = (rec.get('ATTEMPTRESULT') or '').strip().upper()
        if result != 'LOGIN':
            continue
        
        userid = rec.get('USERID', '').strip().upper()
        clienthost = rec.get('CLIENTHOST', '').strip()
        attemptdate = rec.get('ATTEMPTDATE', '').strip()
        
        if not userid or not attemptdate:
            continue
        
        try:
            dt = datetime.strptime(attemptdate, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            continue
        
        # Only consider last N days
        if dt < cutoff:
            continue
        
        # Infer environment from CLIENTHOST
        env, is_shared = infer_env_from_clienthost(clienthost)
        if env and not is_shared:
            user_env_counts[userid][env] += 1
    
    return user_env_counts


def get_intelligent_local_site(user_env_counts, defsite):
    """
    Determine the actual environment based on login frequency.
    
    Rules:
    1. If user logs in to only 1 environment -> that's the local_site
    2. If user logs in to multiple environments:
       - Find the environment with most logins
       - If one environment has >50% of logins -> that's the local_site
       - Otherwise, use DEFSITE (support user)
    """
    if not user_env_counts:
        return defsite, 'no_logins'
    
    total_logins = sum(user_env_counts.values())
    
    # Single environment
    if len(user_env_counts) == 1:
        return list(user_env_counts.keys())[0], 'single_env'
    
    # Multiple environments - find the dominant one
    most_common = user_env_counts.most_common(1)[0]
    dominant_env, dominant_count = most_common
    
    # If one environment has >50% of logins, it's the primary
    if dominant_count / total_logins > 0.5:
        return dominant_env, 'dominant_env'
    
    # Otherwise, user is multi-environment (support) - use DEFSITE
    return defsite, 'multi_env_support'


def main():
    print("=" * 70)
    print("🧠 IDENTIFICAÇÃO INTELIGENTE DO LOCAL_SITE")
    print("=" * 70)
    
    # Load data
    logintracking_path = OUTDIR / "consolidated_logintracking_from_sources.csv"
    maxuser_path = OUTDIR / "consolidated_maxuser.csv"
    
    print("\n📂 Carregando dados...")
    
    with open(logintracking_path, newline='', encoding='utf-8-sig') as f:
        logintracking = list(csv.DictReader(f))
    
    with open(maxuser_path, newline='', encoding='utf-8-sig') as f:
        maxusers = list(csv.DictReader(f))
    
    print(f"  • Logintracking records: {len(logintracking)}")
    print(f"  • Maxuser records: {len(maxusers)}")
    
    # Get environment frequency per user
    print("\n🔍 Analisando frequência de login por ambiente (60 dias)...")
    user_env_counts = get_user_env_frequency(logintracking, days=60)
    print(f"  • Usuários com login nos últimos 60 dias: {len(user_env_counts)}")
    
    # Analyze each user
    results = []
    for mu in maxusers:
        userid = mu.get('USERID', '').strip().upper()
        if not userid:
            continue
        
        defsite = mu.get('DEFSITE', '').strip()
        personid = mu.get('PERSONID', '').strip()
        
        env_counts = user_env_counts.get(userid)
        if env_counts:
            local_site, reason = get_intelligent_local_site(env_counts, defsite)
            total_logins = sum(env_counts.values())
        else:
            local_site = defsite
            reason = 'no_data'
            total_logins = 0
        
        results.append({
            'USERID': userid,
            'PERSONID': personid,
            'DEF_SITE': defsite,
            'LOCAL_SITE': local_site,
            'LOGIN_COUNT_60D': total_logins,
            'SOURCE': reason
        })
    
    # Output results
    output_path = OUTDIR / "intelligent_local_site.csv"
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['USERID', 'PERSONID', 'DEF_SITE', 'LOCAL_SITE', 'LOGIN_COUNT_60D', 'SOURCE']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✅ Arquivo gerado: {output_path}")
    
    # Summary statistics
    env_counts = Counter()
    source_counts = Counter()
    
    for r in results:
        if r['LOCAL_SITE']:
            env_counts[r['LOCAL_SITE']] += 1
        source_counts[r['SOURCE']] += 1
    
    print("\n[ESTATÍSTICAS POR AMBIENTE]")
    for env, count in sorted(env_counts.items(), key=lambda x: -x[1]):
        print(f"  • {env}: {count} usuários")
    
    print("\n[FONTE DOS DADOS]")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"  • {source}: {count} usuários")
    
    # Check for discrepancies
    discrepancies = [r for r in results if r['DEF_SITE'] and r['LOCAL_SITE'] and r['DEF_SITE'] != r['LOCAL_SITE']]
    
    print(f"\n[DISCREPÂNCIAS]")
    print(f"  ⚠️ {len(discrepancies)} usuários com DEFSITE ≠ LOCAL_SITE")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()