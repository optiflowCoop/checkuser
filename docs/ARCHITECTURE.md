# 🏗️ ARQUITETURA - Source-of-Truth e Consolidação de Dados

## 1. Princípios Arquiteturais

### 1.1 Source-of-Truth (Fonte de Verdade)

**Problema antigo:**
- LOCATION era deduzido de múltiplas fontes (inconsistente)
- Palavras-chave genéricas causavam classificações erradas
- Falta de fonte oficial para determinar alocação real

**Solução (v3.1):**
```
PersonGroupView.LocationSite
       ↓
  [Única fonte]
       ↓
  LOCATION (N08, ODN1, etc.)
       ↓
  OPERATIONAL_PRESENCE (OFFSHORE/ONSHORE)
```

**Benefício:**
- ✅ Uma única fonte de verdade
- ✅ Sem ambiguidades
- ✅ Facilita auditoria e conformidade

---

## 2. Fluxo de Dados Consolidados

### 2.1 Entrada (Multiple Sources)

```
┌─────────────────────────────────────────────────────┐
│                   FONTE DE DADOS                     │
├─────────────────────────────────────────────────────┤
│                                                       │
│  DB2 (consolidado_*.csv):                           │
│  ├─ maxuser_*.csv (identidades)                    │
│  ├─ persongroupview_*.csv (roles + LocationSite) ⭐│
│  └─ consolidated_logintracking.csv (356k logins)   │
│                                                       │
│  Local (DadosTabelas/): ⭐ NOVO                    │
│  └─ LOGINTRACKING_*.csv (16k novos logins)        │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 Processamento (11 Etapas)

```
Step 1-8: Identidade e Baseline (sem mudanças)
   ↓
   Usuários normalizados e classificados

Step 9: ANALYZE_USAGE (REFATORIZADO v3.1) ⭐
   ├─ INPUT:
   │  ├─ consolidated_logintracking.csv (356k)
   │  ├─ DadosTabelas/LOGINTRACKING_*.csv (16k)
   │  └─ consolidated_persongroupview.csv (8.6k)
   │
   ├─ PROCESSAMENTO:
   │  ├─ Consolida 373k+ logins
   │  ├─ Parse: YYYY-MM-DD-HH.MM.SS ✅
   │  ├─ Extrai LocationSite → LOCATION
   │  ├─ Classifica Onshore/Offshore
   │  └─ Calcula DAYS_SINCE_LAST
   │
   └─ OUTPUT:
      └─ usage_analysis_phase3.csv (13.272 linhas com LOCATION)

Step 10: INTEGRATE_USAGE_DATA (NOVO v3.1) ⭐
   ├─ INPUT:
   │  ├─ usage_analysis_phase3.csv
   │  └─ maximo_risk_and_optimization_workbook.xlsx
   │
   ├─ PROCESSAMENTO:
   │  ├─ Valida dados
   │  ├─ Adiciona coluna LOCATION se não existir
   │  ├─ Atualiza LOCATION (768 registros)
   │  ├─ Atualiza OPERATIONAL_PRESENCE
   │  └─ Salva backup automático
   │
   └─ OUTPUT:
      └─ maximo_risk_and_optimization_workbook.xlsx ✅

Step 11: GENERATE_RISK_REPORT (sem mudanças)
   └─ Gera HTML + Excel finais
```

### 2.3 Saída (Final Output)

```
┌──────────────────────────────────────────────┐
│         OUTPUT/CONSOLIDATED/                 │
├──────────────────────────────────────────────┤
│                                              │
│ usage_analysis_phase3.csv ✅                │
│ ├─ Coluna LOCATION (N08, ODN1, etc.)      │
│ ├─ OPERATIONAL_PRESENCE (OFFSHORE/ONSHORE)│
│ └─ DAYS_SINCE_LAST (calculado correto)    │
│                                              │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│         OUTPUT/REPORTS/                      │
├──────────────────────────────────────────────┤
│                                              │
│ maximo_risk_and_optimization_workbook.xlsx ✅
│ ├─ Sheet "2_LicenseDecisionPlan":          │
│ │  ├─ Coluna LOCATION (768 atualizados)   │
│ │  ├─ Coluna OPERATIONAL_PRESENCE         │
│ │  └─ Dados consistentes com PersonGroupView
│ │                                          │
│ └─ Dashboard HTML com dados corretos       │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 3. Correções Implementadas (v3.1)

### 3.1 LocationSite como Source-of-Truth

**Antes:**
```python
# Tentava deduzir de múltiplas fontes
row_str = " ".join(str(v).lower() for v in row.values())
for k in offshore_keywords:
    if k in row_str:
        # Resultado ambíguo, múltiplas matches
```

**Depois:**
```python
# PersonGroupView é único source
location_site = row.get('locationsite', '').strip()
if location_site:
    # Usa LocationSite diretamente
    presence_map[email]['location'] = location_site
    # Classifica baseado no LocationSite
```

**Benefício:**
- ✅ Não ambíguo
- ✅ Auditável
- ✅ Rastreável até PersonGroupView

### 3.2 Parse de Data Corrigido

**Problema:**
```
Input: 2026-06-09-20.15.26.370000
Antes: split('.')[0] → "2026-06-09" ❌ (data incompleta!)
Depois: rsplit('.', 1)[0] → "2026-06-09-20.15.26" ✅
```

**Impacto:**
- DAYS_SINCE_LAST calculado corretamente
- ALESSANDROCORREA: 15 dias (não 999)

### 3.3 Consolidação de LoginTracking

**Antes:**
```
Apenas: consolidated_logintracking.csv (356.705 registros)
```

**Depois:**
```
Consolidado de 2 fontes:
├─ consolidated_logintracking.csv (356.705)
└─ DadosTabelas/LOGINTRACKING_*.csv (16.414)
= 373.119 registros ✅
```

**Lógica:**
```python
def load_all_logins():
    logins = []
    # Fonte 1: Consolidada
    logins.extend(load_csv(IN_DIR / 'consolidated_logintracking.csv'))
    
    # Fonte 2: Dados Tabelas (NOVO)
    if DADOS_TABELAS_DIR.exists():
        for file in DADOS_TABELAS_DIR.glob('LOGINTRACKING*.csv'):
            logins.extend(load_csv(file))
    
    return logins
```

### 3.4 Classificação Onshore/Offshore Refinada

**Antes:**
```python
# Busca palavras-chave em TODOS os campos
if k in row_str:
    # Ambíguo: múltiplos matches possíveis
```

**Depois:**
```python
# Usa APENAS LocationSite
location_lower = location_site.lower()

# Verifica ONSHORE first
is_onshore = any(k in location_lower for k in ['base-unp', 'og-base', 'base', 'macae'])

# Senão, verifica OFFSHORE
is_offshore = any(k in location_lower for k in ['n06', 'n08', 'n09', 'odn1', 'odn2', 'odn'])
```

---

## 4. Integração de Dados no XLSX (Novo)

### 4.1 Fluxo de Integração

```python
# 1. Carrega análise de uso (13.272 usuários)
usage_data = load_csv(IN_DIR / 'usage_analysis_phase3.csv')
usage_index = {row['USERID']: row for row in usage_data}

# 2. Abre workbook existente
wb = load_workbook(REPORTS_DIR / 'maximo_risk_and_optimization_workbook.xlsx')
ws = wb['2_LicenseDecisionPlan']

# 3. Localiza colunas
userid_col = find_column(ws, 'USERID')
location_col = add_column(ws, 'LOCATION', after='EMAIL')
presence_col = find_or_add_column(ws, 'OPERATIONAL_PRESENCE')

# 4. Atualiza cada linha
for row_idx in range(2, ws.max_row + 1):
    userid = ws.cell(row_idx, userid_col).value
    if userid in usage_index:
        usage = usage_index[userid]
        ws.cell(row_idx, location_col).value = usage['LOCATION']
        ws.cell(row_idx, presence_col).value = usage['OPERATIONAL_PRESENCE']

# 5. Salva
wb.save(workbook_path)
```

### 4.2 Resultado

```
Input: usage_analysis_phase3.csv (13.272 linhas)
Índice criado: 9.764 USERIDs únicos
Workbook processado: 769 linhas (incluindo header)
Registros atualizados: 768 ✅
```

---

## 5. Fluxo Completo: Antes vs Depois

### Antes (v3.0)

```
PersonGroupView
   ↓ (ignorado)
   
LOCATION = [VAZIO]
   ↓
OPERATIONAL_PRESENCE = [INDEFINIDO]
   ↓
XLSX não atualizado ❌
```

### Depois (v3.1)

```
PersonGroupView (LocationSite = N08)
   ↓ (PRIORIDADE 1)
   
Análise de Uso (Phase 3)
   ├─ LOCATION = N08 ✅
   └─ OPERATIONAL_PRESENCE = OFFSHORE ✅
   ↓
Integração XLSX
   ├─ Coluna LOCATION adicionada
   ├─ 768 registros atualizados ✅
   └─ Backup automático salvo ✅
```

---

## 6. Garantias de Qualidade

### 6.1 Validações Implementadas

```python
# 1. CSV válido
def load_csv(path):
    try:
        reader = csv.DictReader(f)
        # Filtra linhas lixo (DUPLICATION, COPYRIGHT, etc.)
    except:
        print(f"❌ CSV inválido: {path}")

# 2. LocationSite não vazio
if not location_site or location_site == 'UNKNOWN':
    presence = 'UNKNOWN'  # Indica falta de dado

# 3. USERID em usage_index
if userid not in usage_index:
    print(f"⚠️ {userid} não encontrado")

# 4. Backup antes de salvar
wb.save(backup_path)
wb.save(final_path)
```

### 6.2 Auditoria

```
Logs de Execução:
✓ Carregados 13.285 registros de usage_analysis_phase3.csv
✓ Carregados 13.285 registros de análise de uso
✓ Índice de usuários criado: 9.764 entries
✓ Mapeamento final: USERID=1, LOCATION=4, OPERATIONAL_PRESENCE=10
✓ 768 registros atualizados com LOCATION e OPERATIONAL_PRESENCE
✅ WORKBOOK ATUALIZADO: maximo_risk_and_optimization_workbook.xlsx
✓ Backup salvo: maximo_risk_and_optimization_workbook_backup.xlsx
```

---

## 7. Próximos Passos (Roadmap)

### Fase 4: Validação AD
```
LOCATION (N08, ODN1, etc.) + OPERATIONAL_PRESENCE (OFFSHORE/ONSHORE)
   ↓
Active Directory Matching
   ↓
Sincronização de Identidades
```

### Fase 5: Migração MAS 9
```
Dados Validados + LOCATION Correto
   ↓
Importação de Usuários
   ↓
Alocação Automática de AppPoints
```

---

**Documentação**: Arquitetura v3.1  
**Data**: Junho 2026  
**Status**: ✅ Implementado
