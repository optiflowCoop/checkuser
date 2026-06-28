# Pipeline e Arquitetura

## Visão Geral do Pipeline (v3.1)

O Pipeline de Governança de Identidades e Otimização de Licenças é orquestrado automaticamente pelo executável `run_pipeline.py`.

```text
┌─────────────────────────────────────────────────────────────────┐
│                      PIPELINE COMPLETO (11 ETAPAS)              │
└─────────────────────────────────────────────────────────────────┘

1. scripts/run_db2cli_queries.py
   → Executa queries em cada ambiente
   → Gera arquivos brutos na pasta output/raw/

2. scripts/consolidate_outputs.py
   → Parseia e consolida resultados por query
   → Gera consolidated_*.csv na pasta output/consolidated/

3. src/consolidate_user_access.py
   → Junta maxuser + person + email + groupuser + maxgroup
   → Traz inteligência humana (NOMES, EMAILS, LOGINS)
   → Gera consolidated_user_access.csv

4. src/normalize.py
   → Limpeza textual e tipificação de classes (HUMAN, TECHNICAL, TEST)
   → Gera consolidated_user_access_normalized.csv
   → Gera consolidated_user_identity.csv

5. src/cross_env_userid_reuse.py
   → Localiza TODOS os USERIDs repetidos entre ambientes

6. src/login_conflicts.py
   → Localiza logins associados a múltiplas pessoas

7. src/identity_classification.py
   → Aplica Score Ponderado e Regras Anti-Merge Automático
   → Gera identity_collisions_enriched.csv (Fila de Saneamento)

8. src/consolidate_license_footprint.py
   → Análise de licenciamento AppPoints
   → Gera consolidated_license_footprint.csv

9. src/analyze_usage.py ⭐ ATUALIZADO v3.1
   → Análise de uso real com LocationSite correto
   → Consolida LoginTracking de múltiplas fontes
   → Classifica Onshore/Offshore baseado em LocationSite
   → Gera usage_analysis_phase3.csv

10. integrate_usage_data.py ⭐ NOVO
    → Integra análise de uso no XLSX final
    → Atualiza LOCATION e OPERATIONAL_PRESENCE
    → Valida dados antes de salvar

11. scripts/generate_risk_report.py
    → Cria relatórios HTML/Excel de Gestão Executiva
    → Gera maximo_risk_and_optimization_workbook.xlsx
    → Inclui dados corrigidos de LocationSite
```

---

## Fluxo de Dados Consolidados

### Entrada (Input)
- `maxuser_*.csv` - Identidades por ambiente (DB2)
- `persongroupview_*.csv` - Cargos, departamentos e **LocationSite** ⭐
- `consolidated_logintracking.csv` - LoginTracking consolidado
- `DadosTabelas/LOGINTRACKING_*.csv` - Logs recentes baixados ⭐ NOVO

### Processamento
```
Identidades → Normalizados → Classificados → Analisados → Licenciados → Relatórios
   ↓            ↓               ↓              ↓             ↓            ↓
 13k+       Tipificados    Colisões      Usage       AppPoints      Dashboard
 usuários   HUMAN/TEST    DO_NOT_MERGE   Phase3      Decision        HTML/Excel
```

### Saída (Output)
- `consolidated/` - Dados consolidados processados
  - `usage_analysis_phase3.csv` - Análise de uso com **LOCATION** ✅
  - `consolidated_persongroupview.csv` - Dados de localização
  - `identity_collisions_enriched.csv` - Fila de saneamento
  
- `reports/` - Relatórios finais
  - `maximo_risk_and_optimization_workbook.xlsx` - Dados corrigidos ✅
  - `maximo_identity_sanity_report.html` - Dashboard executivo

---

## Como Rodar

### 1. Via One-Click (Recomendado)

**Powershell / CMD:**
```powershell
python run_pipeline.py
```

### 2. Pular Extração do DB2 (usar RAW existente)

```powershell
python run_pipeline.py --skip-extract
```

### 3. Apenas Phase 3 (Análise de Uso)

```powershell
python src/analyze_usage.py
python integrate_usage_data.py
```

### 4. Apenas Geração de Relatório

```powershell
python scripts/generate_risk_report.py
```

---

## Alterações Recentes (v3.1)

### 1. src/analyze_usage.py
- ✅ Novo suporte para parse de data: `YYYY-MM-DD-HH.MM.SS`
- ✅ Extrai LocationSite do PersonGroupView
- ✅ Consolida LoginTracking de múltiplas fontes (373k+ registros)
- ✅ Classifica Onshore/Offshore baseado em LocationSite
- ✅ Calcula DAYS_SINCE_LAST corretamente

### 2. Novo: integrate_usage_data.py
- ✅ Integra dados de análise de uso no XLSX final
- ✅ Adiciona coluna LOCATION se não existir
- ✅ Atualiza OPERATIONAL_PRESENCE corretamente
- ✅ Valida dados antes de salvar (768 registros atualizados)

### 3. Dados Consolidados
- ✅ 13.272 usuários processados
- ✅ 373.123 registros de LoginTracking
- ✅ 8.645 registros PersonGroupView
- ✅ Classificação ONSHORE/OFFSHORE baseada em dados reais

---

## Exemplo: ALESSANDROCORREA

**Antes (v3.0):**
```
LOCATION: [VAZIO]
OPERATIONAL_PRESENCE: [INDEFINIDO]
DAYS_SINCE_LAST: 999
```

**Depois (v3.1):**
```
LOCATION: N08 ✅ (do PersonGroupView)
OPERATIONAL_PRESENCE: OFFSHORE ✅
LOGIN_COUNT_90D: 1623
DAYS_SINCE_LAST: 15 ✅
USER_TIER: OFFSHORE_STD
```

---

## Troubleshooting

### Pipeline falha na etapa 9 (analyze_usage)
**Problema**: Falta arquivo `consolidated_logintracking.csv`
**Solução**: Executar `extrair_logintrack.bat` primeiro

### LOCATION mostra como UNKNOWN
**Problema**: PersonGroupView não tem LocationSite
**Solução**: Verificar `consolidated_persongroupview.csv`

### Parse de data com erro
**Problema**: Formato esperado não reconhecido
**Solução**: Verificar formato em `LOGINTRACKING_*.csv` (deve ser `YYYY-MM-DD-HH.MM.SS`)

---

## Monitoramento

**Arquivos a verificar após execução:**
```
output/consolidated/
├── usage_analysis_phase3.csv          (13k linhas com LOCATION)
├── consolidated_persongroupview.csv   (8.6k linhas)
└── consolidated_logintracking.csv     (356k linhas)

output/reports/
├── maximo_risk_and_optimization_workbook.xlsx (768 linhas atualizadas)
└── maximo_identity_sanity_report.html (dashboard)
```

**Validações Automáticas:**
- ✅ Arquivo CSV válido
- ✅ Colunas obrigatórias presentes
- ✅ LOCATION preenchido (768 registros)
- ✅ OPERATIONAL_PRESENCE classificado
- ✅ DAYS_SINCE_LAST calculado

---

**Documentação atualizada:** Junho 2026  
**Versão:** 3.1  
**Status:** ✅ Pronto para Produção
