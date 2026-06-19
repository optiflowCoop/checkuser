# Pipeline e Comandos Sugeridos

## Visão Geral do Pipeline (MVP 2.0)

O Pipeline da Fase de **Identity Discovery & Ambiguity Detection** é orquestrado automaticamente pelo executável `run_pipeline.bat` ou rodando o arquivo `run_pipeline.py`.

Abaixo a arquitetura exata de como ele funciona por baixo dos panos:

```text
1. scripts/run_db2cli_queries.py
   -> executa queries em cada ambiente
   -> gera arquivos brutos (.txt ou csv) na pasta output/raw/

2. scripts/consolidate_outputs.py
   -> parseia e consolida resultados por query (Trata os arquivos tabulados DB2CLI para CSV)
   -> gera consolidated_*.csv na pasta output/consolidated/

3. src/consolidate_user_access.py
   -> junta maxuser + person + email + groupuser + maxgroup
   -> Traz a inteligência humana de NOMES, EMAILS e LOGINS para o escopo
   -> gera consolidated_user_access.csv na pasta output/consolidated/

4. src/normalize.py
   -> limpeza textual e tipificação de classes de conta (HUMAN, TECHNICAL, TEST via REGEX)
   -> gera consolidated_user_access_normalized.csv e consolidated_user_identity.csv

5. src/cross_env_userid_reuse.py
   -> Localiza ativamente TODOS os USERIDs repetidos entre ambientes cruzados.

6. src/login_conflicts.py
   -> Localiza logins associados a multiplas pessoas (Ex: SSO bottleneck)

7. src/identity_classification.py
   -> Aplica o Score Ponderado e as Regras Conservadoras Anti-Merge Automático
   -> Ex: Se Names e Emails forem diferentes com USERID igual, ele trava como "DO_NOT_MERGE".
   -> gera a "Fila de Saneamento Master": identity_collisions_enriched.csv 

8. src/consolidate_license_footprint.py
   -> (Feature latente de Licenciamento / AppPoints)
   -> gera consolidated_license_footprint.csv na pasta output/consolidated/

9. scripts/generate_risk_report.py
   -> cria relatórios HTML/Excel de Gestão Executiva orientados a Saneamento de Identidade
   -> gera maximo_identity_sanity_report.html
   -> gera maximo_identity_sanity_workbook.xlsx na pasta output/reports/
```

## Como Rodar (One-Click)

Execute a partir da raiz do projeto (`C:\Users\esilva\OneDrive - FORESEA\Documentos\04 - APPS\CHECKUSER`):

**Via Powershell / CMD:**
```powershell
python run_pipeline.py
```

**Se você quiser rodar SEM fazer os selects lentos no Banco DB2 (Utilizando o RAW que ja extraiu):**
```powershell
python run_pipeline.py --skip-extract
```