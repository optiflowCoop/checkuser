import json
import subprocess
import sys
from pathlib import Path
import tempfile
import os
import time

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

queries_to_run = only_query if only_query else cfg.get('queries', [])
# -----------------------------------------

connections = cfg.get('connections') or []

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

summary = []
for conn in connections:
    env = conn.get('env_db') or conn.get('name')
    connstr = f"DATABASE={conn.get('database')};HOSTNAME={conn.get('hostname')};PORT={conn.get('port')};PROTOCOL={conn.get('protocol','TCPIP')};UID={conn.get('username')};PWD={conn.get('password')};"
    
    for qname in queries_to_run:
        # Resolve query
        try:
            import sys; sys.path.insert(0, str(ROOT/'src')); from queries import resolve_query
            sql = resolve_query(qname)
        except Exception as exc:
            sql = qname
            
        tf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql', dir=ROOT)
        tf.write(sql.rstrip().rstrip(';') + ';\n')
        tf.flush()
        tf.close()
        
        outpath = OUTDIR / f"{env}_{qname}.txt"
        cmd = [str(DB2CLI), 'execsql', '-connstring', connstr, '-inputsql', tf.name, '-outfile', str(outpath)]
        
        # RETRY LOGIC
        attempt = 1
        success = False
        last_error = ""
        
        while attempt <= MAX_RETRIES and not success:
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                rc = proc.returncode
                if rc == 0:
                    success = True
                    summary.append({'env': env, 'query': qname, 'rc': rc, 'outfile': str(outpath)})
                else:
                    last_error = proc.stderr[:400]
                    print(f"[{attempt}/{MAX_RETRIES}] Retry {env}_{qname} due to Return Code {rc}...")
                    time.sleep(RETRY_DELAY)
                    attempt += 1
            except subprocess.TimeoutExpired as e:
                last_error = f"Timed out after 300s"
                print(f"[{attempt}/{MAX_RETRIES}] Retry {env}_{qname} due to Timeout...")
                time.sleep(RETRY_DELAY)
                attempt += 1
            except Exception as e:
                last_error = str(e)
                print(f"[{attempt}/{MAX_RETRIES}] Retry {env}_{qname} due to Error: {last_error}")
                time.sleep(RETRY_DELAY)
                attempt += 1
                
        if not success:
            summary.append({'env': env, 'query': qname, 'error': last_error, 'outfile': str(outpath)})
            
        try:
            os.remove(tf.name)
        except OSError:
            pass

for s in summary:
    if 'error' in s:
        print(f"{s['env']} {s['query']}: ERROR {s['error']}")
    else:
        status = 'OK' if s.get('rc',1)==0 else f"RC={s.get('rc')}"
        print(f"{s['env']} {s['query']}: {status} -> {s['outfile']}")

print('\nDone. Outputs in output/raw/ folder.')