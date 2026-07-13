import json
import subprocess
import sys
from pathlib import Path
import tempfile
import os
import time

# Console padrão do Windows usa cp1252 e não sabe representar emojis (🎯, ✓, ⚠, ❌)
# usados nos prints abaixo — sem isto, o processo aborta com UnicodeEncodeError e
# a extração de uma query/ambiente inteiro pode parecer "concluída" quando na
# verdade travou no meio, deixando dados parciais sem aviso claro.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONFIG = ROOT / 'config' / 'config.json'
DB2CLI = Path(r"C:\Users\esilva\AppData\Local\Programs\Python\Python313\Lib\site-packages\clidriver\bin\db2cli.exe")
OUTDIR = ROOT / 'output' / 'raw'
OUTDIR.mkdir(parents=True, exist_ok=True)

with open(CONFIG, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

# --- Lógica para rodar query específica ---
only_query = None
data_inicio = "2026-01-01 00:00:00"
data_fim = "2026-12-31 23:59:59"

if '--only-query' in sys.argv:
    try:
        query_index = sys.argv.index('--only-query') + 1
        if query_index < len(sys.argv):
            only_query = [sys.argv[query_index]]
            print(f"🎯 Foco: Rodando apenas a query: {only_query[0]}")
    except (ValueError, IndexError):
        print("❌ Erro: --only-query precisa de um nome de query. Ex: --only-query person")
        sys.exit(1)

# Suporte para múltiplas queries (via --queries)
if '--queries' in sys.argv:
    try:
        query_index = sys.argv.index('--queries') + 1
        if query_index < len(sys.argv):
            only_query = [q.strip() for q in sys.argv[query_index].split(',')]
            print(f"🎯 Foco: Rodando queries: {', '.join(only_query)}")
    except (ValueError, IndexError):
        print("❌ Erro: --queries precisa de nomes separados por vírgula. Ex: --queries person,email")
        sys.exit(1)

# Suporte para parâmetros de data (via --data-inicio e --data-fim)
if '--data-inicio' in sys.argv:
    try:
        idx = sys.argv.index('--data-inicio') + 1
        if idx < len(sys.argv):
            data_inicio = sys.argv[idx]
            print(f"📅 Data início: {data_inicio}")
    except (ValueError, IndexError):
        pass

if '--data-fim' in sys.argv:
    try:
        idx = sys.argv.index('--data-fim') + 1
        if idx < len(sys.argv):
            data_fim = sys.argv[idx]
            print(f"📅 Data fim: {data_fim}")
    except (ValueError, IndexError):
        pass

queries_to_run = only_query if only_query else cfg.get('queries', [])
# -----------------------------------------

# Suporte para restringir a extração a um único ambiente (via --only-env).
# Útil para consultas sobre dados que os 7 bancos replicam entre si (ex.:
# PR/WFTRANSACTION de compras) — extrair dos 7 é ~7x mais lento sem ganhar
# cobertura real. BASE sozinha já reflete ~97% das informações das unidades.
only_env = None
if '--only-env' in sys.argv:
    try:
        idx = sys.argv.index('--only-env') + 1
        if idx < len(sys.argv):
            only_env = sys.argv[idx].strip().upper()
            print(f"🎯 Foco: Rodando apenas no ambiente: {only_env}")
    except (ValueError, IndexError):
        print("❌ Erro: --only-env precisa de um nome de ambiente. Ex: --only-env BASE")
        sys.exit(1)

connections = cfg.get('connections') or []
if only_env:
    connections = [c for c in connections if (c.get('env_db') or c.get('name', '')).upper() == only_env]
    if not connections:
        print(f"❌ Erro: nenhum ambiente '{only_env}' encontrado em config.json")
        sys.exit(1)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

summary = []
total_extractions = len(connections) * len(queries_to_run)

for conn_idx, conn in enumerate(connections, 1):
    env = conn.get('env_db') or conn.get('name')
    connstr = f"DATABASE={conn.get('database')};HOSTNAME={conn.get('hostname')};PORT={conn.get('port')};PROTOCOL={conn.get('protocol','TCPIP')};UID={conn.get('username')};PWD={conn.get('password')};"
    
    total_queries = len(queries_to_run)
    
    print(f"\n{'=' * 100}")
    print(f"[GO-LIVE {conn_idx}/{len(connections)}] Extraindo dados do ambiente: {env}")
    print(f"  Origem: {conn.get('hostname')}:{conn.get('port')}/{conn.get('database')}")
    print(f"  Total de queries: {total_queries}")
    print(f"{'=' * 100}")
    
    for q_idx, qname in enumerate(queries_to_run, 1):
        progress_pct = (q_idx / total_queries) * 100
        
        # Resolve query
        try:
            sys.path.insert(0, str(ROOT/'queries'))
            from queries import resolve_query
            sql = resolve_query(qname, data_inicio, data_fim)
        except Exception as exc:
            print(f"⚠️  Erro ao resolver query '{qname}': {exc}")
            sql = qname
            
        print(f"\n  [{q_idx}/{total_queries}] ({progress_pct:.1f}%) Extraindo: {qname}")
        
        tf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', dir=ROOT)
        tf.write(sql.rstrip().rstrip(';') + ';\n')
        tf.flush()
        tf.close()
        
        outpath = OUTDIR / f"{env}_{qname}.txt"
        # NÃO usar '-outfile' do db2cli.exe: para tabelas largas (muitas colunas,
        # ex. PERSONGROUPVIEW e PERSON) a escrita direto em arquivo do driver
        # trunca o resultado silenciosamente (rc=0, sem erro) — confirmado em
        # auditoria 2026-07-13: PERSONGROUPVIEW perdia ~85% das linhas (12402 ->
        # ~1850) e PERSON ~87% (9942 -> ~1325), enquanto capturar via stdout e
        # escrever o arquivo nós mesmos traz o resultado completo, sem mudar a
        # query nem o formato do arquivo de saída.
        cmd = [str(DB2CLI), 'execsql', '-connstring', connstr, '-inputsql', tf.name]

        # RETRY LOGIC
        attempt = 1
        success = False
        last_error = ""

        while attempt <= MAX_RETRIES and not success:
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                rc = proc.returncode
                if rc == 0:
                    outpath.write_text(proc.stdout, encoding='utf-8', errors='replace')
                    success = True
                    summary.append({'env': env, 'query': qname, 'rc': rc, 'outfile': str(outpath)})
                    print(f"  ✓ Sucesso! Arquivo: {outpath.name}")
                else:
                    last_error = proc.stderr[:400]
                    print(f"  ⚠ [{attempt}/{MAX_RETRIES}] Retry {env}_{qname} due to Return Code {rc}...")
                    time.sleep(RETRY_DELAY)
                    attempt += 1
            except subprocess.TimeoutExpired as e:
                last_error = f"Timed out after 300s"
                print(f"  ⚠ [{attempt}/{MAX_RETRIES}] Retry {env}_{qname} due to Timeout...")
                time.sleep(RETRY_DELAY)
                attempt += 1
            except Exception as e:
                last_error = str(e)
                print(f"  ⚠ [{attempt}/{MAX_RETRIES}] Retry {env}_{qname} due to Error: {last_error}")
                time.sleep(RETRY_DELAY)
                attempt += 1
                
        if not success:
            summary.append({'env': env, 'query': qname, 'error': last_error, 'outfile': str(outpath)})
            print(f"  ✗ Falha após {MAX_RETRIES} tentativas")
            
        try:
            os.remove(tf.name)
        except OSError:
            pass
    
    # Resumo do ambiente
    env_success = sum(1 for s in summary if s.get('env') == env and 'error' not in s)
    env_failed = sum(1 for s in summary if s.get('env') == env and 'error' in s)
    print(f"\n  {'=' * 96}")
    print(f"  Resumo {env}: {env_success} sucesso(s), {env_failed} falha(s)")
    print(f"  {'=' * 96}")

print(f"\n{'=' * 100}")
print(f"RESUMO DA EXTRAÇÃO - {total_extractions} consultas executadas")
print(f"{'=' * 100}")
for s in summary:
    if 'error' in s:
        print(f"  ✗ {s['env']:6s} | {s['query']:20s} | ERROR: {s['error'][:50]}")
    else:
        status = '✓ OK' if s.get('rc',1)==0 else f"✗ RC={s.get('rc')}"
        print(f"  {status} | {s['env']:6s} | {s['query']:20s} | {Path(s['outfile']).name}")

successful = sum(1 for s in summary if 'error' not in s)
failed = sum(1 for s in summary if 'error' in s)
print(f"\nTotal: {successful} sucesso(s), {failed} falha(s)")
print(f"Arquivos salvos em: {OUTDIR}")
print('\nDone.')
