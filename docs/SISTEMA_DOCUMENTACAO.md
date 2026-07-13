# Documentação Completa do Sistema CHECKUSER

> 📌 Regras de negócio detalhadas de AppPoints e definição de licenças (entitlement, Authorized/Concurrent, recomendações de otimização, motor NEM) foram desmembradas para um documento dedicado: **[REGRAS_APPPOINTS_E_LICENCAS.md](REGRAS_APPPOINTS_E_LICENCAS.md)**. A seção 4 abaixo continua com o resumo; use o documento dedicado como referência definitiva e citável.

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Fluxo de Dados](#fluxo-de-dados)
4. [Regras de Negócio](#regras-de-negócio)
5. [Cálculos e Fórmulas](#cálculos-e-fórmulas)
6. [Parâmetros e Configurações](#parâmetros-e-configurações)
7. [Estrutura de Arquivos](#estrutura-de-arquivos)
8. [Como Executar](#como-executar)
9. [Troubleshooting](#troubleshooting)

---

## 1. Visão Geral

### 1.1 Propósito
O sistema CHECKUSER é uma ferramenta de **Capacity Planning e Governança de Licenças** para o sistema Maximo 9.1 da Foresea. Ele analisa identidades de usuários, consumo de licenças e recomenda otimizações baseadas em dados reais de uso.

### 1.2 Objetivos Principais
- **Visão Executiva**: Dashboard com métricas de capacidade e uso
- **Governança**: Identificação de conflitos e inconsistências de identidades
- **Otimização**: Recomendações de licenciamento baseadas em uso real
- **Simulação**: Cenários de capacidade (P50, P95, P100, Blackout)
- **Rastreabilidade**: Log de todas as decisões e cálculos

### 1.3 Tecnologias Utilizadas
- **Python 3.x**: Backend e processamento
- **Pandas/NumPy**: Análise de dados
- **Chart.js**: Visualizações interativas
- **OpenPyXL**: Geração de relatórios Excel
- **HTML/CSS/JavaScript**: Dashboard web

---

## 2. Arquitetura do Sistema

### 2.1 Camadas

```
┌─────────────────────────────────────────────────────────┐
│                    APRESENTAÇÃO (HTML)                   │
│  - Dashboard Interativo                                 │
│  - 9 Abas (ordem atual, 2026-07-11):                    │
│    1. Painel Operacional                                │
│    2. Governança & Saneamento                           │
│    3. 🔐 Segregação de Funções (SoD) — Compras          │
│    4. Saneamento AD                                     │
│    5. Recomendações de Migração                         │
│    6. Detalhamento de Alocação                          │
│    7. Cenários de AppPoints (fonte única de P50/P95/P100)│
│    8. Peak Contributors                                  │
│    9. Plano de Ação                                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              PROCESSAMENTO (Python)                      │
│  - generate_risk_report.py (Orquestrador)               │
│  - DataProcessor (Lógica de negócio)                    │
│  - Análise de identidades e governança                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  DADOS (CSV/JSON)                        │
│  - consolidated_*.csv (Dados consolidados)              │
│  - true_capacity_metrics.json (Métricas NEM)            │
│  - Configurações (config/*.json)                        │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Componentes Principais

#### 2.2.1 Orquestrador (`generate_risk_report.py`)
**Função**: Coordena todo o fluxo de geração do relatório

**Responsabilidades**:
- Carregar dados consolidados
- Enriquecer perfis de usuário
- Executar simulações de AppPoints
- Calcular métricas de capacidade
- Gerar HTML e Excel

#### 2.2.2 DataProcessor (`html_data_processor.py`)
**Função**: Processar dados para exibição no dashboard

**Responsabilidades**:
- Calcular cenários (As-Is, Saneado, Otimizado)
- Preparar tabelas de governança
- Gerar dados para gráficos
- Aplicar filtros e recomendações

#### 2.2.3 HTML Template (`html_template.py`)
**Função**: Renderizar interface do usuário

**Responsabilidades**:
- Estrutura HTML das 10 abas (ver ordem em 2.1) — cada aba é renderizada por um módulo dedicado em `scripts/reporting/ab1_painel.py` … `ab9_seguranca.py`
- Estilos CSS responsivos
- JavaScript interativo (Chart.js)
- Filtros e exportação

---

## 3. Fluxo de Dados

### 3.1 Pipeline Completo

```
1. EXTRAÇÃO (run_pipeline.py)
   ├─ extrair_baseline.bat → Dados do Maximo (BASELINE)
   └─ extrair_logintrack.bat → Dados de login (LOGINTRACKING)

2. CONSOLIDAÇÃO (scripts/consolidate_*.py)
   ├─ consolidated_user_identity.csv
   ├─ consolidated_user_access.csv
   ├─ consolidated_email.csv
   ├─ consolidated_persongroupview.csv
   └─ consolidated_groupuser.csv

3. ANÁLISE (scripts/)
   ├─ identity_classification.py → Classificação de domínios
   ├─ cross_env_userid_reuse.py → Conflitos multi-ambiente
   ├─ login_conflicts.py → Colisões de LOGINID
   ├─ true_capacity_calculator.py → Métricas NEM
   └─ license_optimizer.py → Otimização de licenças

4. GERAÇÃO DE RELATÓRIO (generate_risk_report.py)
   ├─ license_decision_plan.csv
   ├─ maximo_unified_dashboard.html
   └─ maximo_risk_and_optimization_workbook.xlsx
```

### 3.2 Dados de Entrada

#### 3.2.1 Arquivos Raw
- `DadosTabelas/LOGINTRACKING_*.csv`: Histórico de logins
- `Base Conhecimento/Base/PERSON_*.csv`: Dados cadastrais

#### 3.2.2 Arquivos Consolidados
- `consolidated_user_identity.csv`: Identidades únicas
- `consolidated_user_access.csv`: Acessos por usuário
- `consolidated_email.csv`: Emails cadastrados
- `consolidated_persongroupview.csv`: Vínculo usuário-ambiente
- `consolidated_groupuser.csv`: Grupos por usuário

#### 3.2.3 Arquivos de Configuração
- `config/config.json`: Configurações gerais
- `config/licensing_rules.json`: Regras de licenciamento
- `config/query_catalog.json`: Consultas SQL

---

## 4. Regras de Negócio

### 4.1 Classificação de Domínios

**Arquivo**: `config/config.json` → `foresea_domains`

**Regras**:
- **FORESEA**: Emails @foresea.com
- **PARCEIRO**: Emails @foresea-partner.com
- **TERCEIRO**: Outros domínios válidos
- **SEM DOMINIO**: Emails inválidos ou ausentes

**Implementação**:
```python
def get_user_domain_category(email, domains_config):
    email_lower = email.lower()
    for domain in domains_config['foresea_domains']:
        if email_lower.endswith(domain):
            return 'FORESEA'
    for domain in domains_config['partner_domains']:
        if email_lower.endswith(domain):
            return 'PARCEIRO'
    if '@' in email_lower:
        return 'TERCEIRO'
    return 'SEM DOMINIO'
```

### 4.2 Cálculo de AppPoints

**Fonte canônica**:
- `scripts/config.py` → `get_app_points_config()`
- `scripts/analysis/entitlement.py` → `calculate_app_points()`

**Fatores por Tipo de Licença**:
- **Premium Authorized**: 5 pontos
- **Premium Concurrent**: 15 pontos
- **Base Authorized**: 3 pontos
- **Base Concurrent**: 10 pontos

**Regra de governança**:
- nenhum módulo pode recalcular AppPoints com tabela local/hardcoded divergente
- qualquer custo exibido em HTML, Excel, CSV e NEM deve derivar dessa tabela única


**Fórmula**:
```
Total AppPoints = (PremAuth × 5) + (PremConc × 15) + (BaseAuth × 3) + (BaseConc × 10)
```

**Implementação**:
```python
def calculate_app_points(entitlement, license_model):
    if entitlement == 'PREMIUM' and license_model == 'AUTHORIZED':
        return 5
    elif entitlement == 'PREMIUM' and license_model == 'CONCURRENT':
        return 15
    elif entitlement == 'BASE' and license_model == 'AUTHORIZED':
        return 3
    else:  # BASE + CONCURRENT
        return 10
```

### 4.3 Regras de Otimização

**Arquivo**: `config/licensing_rules.json`

#### 4.3.1 CONFIRMED_AUTHORIZED
**Critérios**:
- Título contém palavras-chave críticas (Supervisor, Coordenador, Diretor, Gerente)
- Uso > 90 logins em 90 dias
- Perfil de uso crítico (POWER)

**Ação**: Manter licença Authorized

#### 4.3.2 MOVE_TO_CONCURRENT
**Critérios**:
- Título não é crítico
- Uso < 30 logins em 90 dias
- Perfil de uso baixo (LIGHT)

**Ação**: Migrar para Concurrent

#### 4.3.3 DOWNGRADE_CANDIDATE
**Critérios**:
- Entitlement atual: PREMIUM
- Uso < 60 logins em 90 dias
- Título não justifica módulos premium

**Ação**: Rebaixar para BASE

#### 4.3.4 INATIVO (>90d)
**Critérios**:
- Último login há mais de 90 dias
- `DAYS_SINCE_LAST > 90`

**Ação**: Remover do plano de licença

#### 4.3.5 REQUER_REVISAO
**Critérios**:
- Sem email cadastrado
- Domínio inválido
- Dados inconsistentes

**Ação**: Revisão manual obrigatória

### 4.4 Cenários de Capacidade

#### 4.4.1 NEM (Non-Exclusive Maximum)
**Definição**: consumo simultâneo real baseado em logintracking e plano de licenças vigente, sem mock e sem aleatoriedade.


**Cálculo**:
```python
# Agrupa logins por hora
hourly_counts = logins.groupby(['DATA', 'HORA']).size()

# Calcula percentis
p50 = np.percentile(hourly_counts, 50)  # Mediana
p95 = np.percentile(hourly_counts, 95)  # Pico seguro
p100 = max(hourly_counts)               # Pico real

# Aplica fatores de escala
scenario_p50 = p50 * fator_escala
scenario_p95 = p95 * fator_escala
scenario_p100 = p100 * fator_escala
```

#### 4.4.2 Fatores de Escala
- **P50 (Cotidiano)**: 1.0x (mediana)
- **P95 (Pico Seguro)**: 1.0x (percentil 95)
- **P100 (Emergência)**: 1.0x (máximo histórico)
- **Blackout**: 1.0x (todos ativos)

**Nota**:
- o consolidado (`todos`) vem do histórico horário real (`true_capacity_metrics.json`)
- na Aba 3, o total otimizado por escopo deve respeitar o escopo selecionado
- quando o motor horário não traz segregação nativa por escopo, a distribuição por escopo é derivada do footprint real de AppPoints do próprio escopo, mantendo o total consolidado real como referência oficial
- o total NEM soma dois componentes por hora: a reserva fixa de AppPoints dos usuários AUTHORIZED (conta em toda hora, estejam logados ou não) + o custo variável dos usuários CONCURRENT efetivamente logados naquela hora
- **Limitações conhecidas** deste cálculo (ver seção 4.6 e `docs/REFATORACAO_2026-07-09.md`): a duração de sessão é assumida em `SESSION_MINUTES = 60` fixos por falta de evento de logout nos dados; não há calendário explícito de escala/rotação offshore (14x14 etc.) — a rotação é capturada implicitamente pelo uso real de login, não por um modelo de turnos.

### 4.6 Limitações Conhecidas do Cálculo NEM

Investigação de 2026-07-09 (ver `docs/REFATORACAO_2026-07-09.md`) validou a matemática do motor NEM e identificou os seguintes pontos que **não são bugs**, mas simplificações necessárias dado os dados disponíveis:

1. **Sem dado de logout**: `consolidated_logintracking_from_sources.csv` só registra eventos de "LOGIN". Não há como medir a duração real de uma sessão. O código assume uma janela fixa de 60 minutos (`SESSION_MINUTES` em `src/true_capacity_calculator.py`) após cada login. Teste com dados reais (2026-07-09): 75% dos intervalos entre logins consecutivos do mesmo usuário ficam dentro dessa janela; ~20% excedem 2h, o que pode subestimar a presença de alguém que ficou trabalhando sem gerar novo evento de login.
2. **Sem calendário de escala/rotação offshore**: o sistema não sabe, a priori, quem está de folga ou embarcado num dado dia. Isso é compensado porque o cálculo de pico usa login **real** hora a hora (não um headcount teórico) — quem está de folga simplesmente não aparece nos dados. Funciona bem para medir o passado; teria menos precisão para *prever* picos futuros sem essa informação.
3. **Reserva Authorized é sempre 100% do tempo**: por definição de negócio ("licença dedicada, disponibilidade garantida 100%"), o custo dos usuários AUTHORIZED entra em toda hora do cálculo, mesmo em horas em que a pessoa não está logada. Isso é intencional, não um bug — mas significa que reclassificar alguém como AUTHORIZED tem impacto fixo e permanente no NEM, independentemente do padrão real de uso dessa pessoa.
4. **Blackout = P100**: no código atual, o cenário "Blackout" é idêntico ao pico histórico (P100), não um multiplicador dele. Documentação histórica de versões anteriores descrevia "Blackout = P100 × 2"; isso nunca foi implementado no código.
5. **Percentis sobre horas com atividade** (auditoria 2026-07-11): P50/P95 são calculados só sobre as horas que tiveram ao menos um login (horas mortas não entram na série). Isso infla o P50 (mediana das horas de operação, não do calendário) mas quase não afeta o P95 — as horas ausentes valeriam o piso da reserva Authorized, abaixo do P95. Como as decisões usam P95, o impacto prático é baixo; documentado por transparência.
6. **Usuários SEM DOMINIO agora entram no total** (correção 2026-07-11): antes eram descartados do cálculo inteiro (569 usuários CONCURRENT não-inativos), subestimando o pico em ~30%. Números vigentes: **P95 = 2.467 e P100 = 2.771 AppPoints** contra teto de 1.200. Eles seguem fora das visões POR ESCOPO (foresea/terceiros/integracao) por não terem e-mail classificável, mas contam no "todos".


### 4.5 Regras de Título Crítico

**Arquivo**: `config/config.json` → `critical_titles`

**Palavras-chave**:
- Supervisores: SUPERVISOR, SUPERV
- Coordenação: COORDENADOR, COORD
- Gerência: GERENTE, GER
- Diretoria: DIRETOR, DIR
- Especialistas: ESPECIALISTA, ESP
- Engenharia: ENGENHEIRO, ENG
- Operações: OPERADOR, OPER

**Lógica**:
```python
def is_critical_title(title, critical_keywords):
    title_upper = title.upper()
    return any(keyword in title_upper for keyword in critical_keywords)
```

### 4.7 Auditoria de Segregação de Funções (SoD) em Compras — Aba 3

**Módulos**: `scripts/domain/security_audit.py`, `group_baseline.py`, `role_standardization.py` · Renderização: `scripts/reporting/ab9_seguranca.py`

Audita conflito de **Emissor x Aprovador** nas 3 aplicações de Compras do Maximo — Requisição de Compra (`PLUSGPR`), Ordem de Compra (`PLUSGPO`) e Requisição Simplificada (`CREATEDR`). Fonte: `APPLICATIONAUTH` (grupo + app + permissão), não `SECURITYRESTRICT` (que é só regra de campo).

**Camadas do teste (da mais teórica à mais direta)**:
1. **Nível 1 — Grupo conflitante**: o grupo, isoladamente, já tem permissão de Emissor (`INSERT`/`SAVE`/`WAPPR`) E Aprovador (`APPR`/`APPROVE`/`UNAPPROVE`) na mesma app.
2. **Nível 2 — Pessoa conflitante**: usuário acumula grupo emissor + aprovador (mesmo grupo, ou grupos diferentes já confrontados por site via `SITEAUTH`/`AUTHALLSITES` — só conta se os dois grupos realmente se sobrepõem na mesma unidade).
3. **Evidência real (não teórica)**: mesma pessoa fez `PR WAPPR` e `PR APPR` na mesma PR, via `WFTRANSACTION` — severidade `CRITICO` se o sistema roteou para 2ª instância (`OOG_PRWENG`) e mesmo assim foi aprovado sozinho; `REVISAR_REGRA` caso contrário.
4. **Autoaprovação direta**: `PR.OOG_REQUESTEDBY` (quem pediu de fato) = quem aprovou — o teste mais direto, extraído só de BASE (~97% de cobertura real, os 7 "ambientes" replicam a mesma base de compras).
5. **PO (Ordem de Compra)**: Nível 1/2 cobre PO normalmente, mas a camada de evidência real **não existe para PO** — `WFTRANSACTION` tem 0 linhas para `OWNERTABLE='PO'` nesta instalação (confirmado por contagem direta), e o teste alternativo (`PO.PURCHASEAGENT` = `PO.CHANGEBY`) deu 100% ruído de automação (processo em lote rodando como `MAXADMIN`, não gente aprovando).
6. **Cadeia PR → PO**: a PR aprovada vira PO via `PRLINE.PONUM`; testamos se a mesma pessoa que aprovou a PR (`PR APPR`) também disparou a criação da PO (`WFTRANSACTION.ACTIONPERFORMED='OOG_CREAPOGRP'`) — checado contra 2.670 conversões históricas, 0 sobreposições (controle limpo).
7. **Perfil de Acesso por Cargo** (`group_baseline.py`): para cargos com ≥3 pessoas ativas na MESMA unidade, calcula o conjunto de grupos que é padrão ali (≥60% dos pares) e sinaliza excesso/falta por pessoa. Cohort é por (ambiente, cargo), não só cargo — dados reais mostram que agrupar ignorando a unidade piora o resultado (o mesmo grupo nominal tem adesão muito inconsistente entre unidades).
8. **Padronização de Acesso** (`role_standardization.py`, material para terceirizada): prescreve **um único grupo padrão por cargo, igual em todas as unidades** — diferente do item 7 (que descreve o desvio de cada unidade contra si mesma). Clusteriza grupos de nomes diferentes por unidade (ex.: `HTQ_MATERIALS_COORDINATOR`/`POL_MATERIALS_COORDINATOR`/`PRIO_MATERIALS_COORDINATOR`) como "o mesmo papel" só quando a permissão real (todas as aplicações, `APPLICATIONAUTH` sem filtro de app) bate em ≥95% (similaridade de Jaccard) — threshold alto deliberado para não fundir grupos com escopo diferente só por nome parecido.

**Armadilha corrigida (importante para qualquer nova análise que cruze `consolidated_user_identity.csv` com `consolidated_groupuser.csv`/`consolidated_maxgroup.csv`)**: `consolidated_user_identity.csv` usa `ENV_DB` com nomes longos (`NORBE06`/`NORBE08`/`NORBE09`), enquanto toda a extração de segurança usa códigos curtos (`N06`/`N08`/`N09`). Sem normalizar (`ENV_ALIAS` em cada módulo), o cruzamento por `(ambiente, userid)` falha silenciosamente para essas 3 unidades — o mesmo padrão já existia em `migration_advisor.py`/`allocation_analyzer.py`, mas faltava em `security_audit.py` (bug pré-existente desde a criação da auditoria SoD) até ser corrigido em 2026-07-11. Corrigir isso, somado à recuperação de extrações de `groupuser`/`maxgroup`/`persongroupview` de ODN2 que haviam falhado silenciosamente por timeout de conexão (nunca reprocessadas), fez o número de "Pessoas Únicas Ativas com Conflito" saltar de 144 para 619 — os números anteriores estavam subcontados, não errados por lógica de regra.

---

## 5. Cálculos e Fórmulas

### 5.1 Métricas de Capacidade

#### 5.1.1 Pico Real (P100)
```python
p100 = max(hourly_app_points_nem.values())
```
**Descrição**: Maior valor de AppPoints simultâneos registrado no logintracking

#### 5.1.2 Pico Seguro (P95)
```python
p95 = np.percentile(hourly_app_points_nem.values(), 95)
```
**Descrição**: Valor que 95% dos dias não ultrapassam

#### 5.1.3 Folga Disponível
```python
folga = contratado - p95
```
**Descrição**: Espaço remanescente antes de atingir o limite contratual

#### 5.1.4 Percentual de Uso
```python
percentual_uso = (p95 / contratado) * 100
```
**Descrição**: Ocupação do contrato baseada no P95

### 5.2 Métricas de Usuário

#### 5.2.1 Fator Analytics
```python
fator_analytics = app_points_ref  # Igual ao AppPoints de referência
```
**Descrição**: Peso do usuário no cenário (usado para compatibilidade)

#### 5.2.2 Logins 90d
```python
login_count_90d = sum(logins_ultimos_90_dias)
```
**Descrição**: Quantidade de logins nos últimos 90 dias

#### 5.2.3 Dias Desde Último Login
```python
days_since_last = (data_atual - ultimo_login).days
```
**Descrição**: Inatividade em dias

### 5.3 Métricas de Domínio

#### 5.3.1 Distribuição por Domínio
```python
domain_counts = {
    'foresea': count(@foresea.com),
    'foresea_partner': count(@foresea-partner.com),
    'other': count(outros_dominios),
    'no_domain': count(sem_dominio)
}
```

### 5.4 Métricas de Governança

#### 5.4.1 Divergências de Título
```python
title_divergence = len(titles_diferentes_por_usuario)
```
**Descrição**: Usuários com títulos diferentes entre ambientes

#### 5.4.2 Cross-Env
```python
cross_env_count = len(usuarios_com_multi_ambiente)
```
**Descrição**: Usuários cadastrados em múltiplos ambientes

#### 5.4.3 Login Conflicts
```python
login_conflicts_count = len(loginids_com_multi_usuario)
```
**Descrição**: LOGINID compartilhado por múltiplos usuários

---

## 6. Parâmetros e Configurações

### 6.1 Arquivo: `config/config.json`

```json
{
  "foresea_domains": ["@foresea.com"],
  "partner_domains": ["@foresea-partner.com"],
  "critical_titles": [
    "SUPERVISOR", "COORDENADOR", "GERENTE", 
    "DIRETOR", "ESPECIALISTA", "ENGENHEIRO"
  ],
  "inactivity_days": 90,
  "ceiling_limit": 1200,
  "authorized_reserved_points": 700
}
```

**Parâmetros**:
- `foresea_domains`: Lista de domínios da Foresea
- `partner_domains`: Lista de domínios de parceiros
- `critical_titles`: Palavras-chave para títulos críticos
- `inactivity_days`: Dias para considerar usuário inativo
- `ceiling_limit`: Limite contratual de AppPoints
- `authorized_reserved_points`: AppPoints reservados para Authorized

### 6.2 Arquivo: `config/licensing_rules.json`

```json
{
  "rules": [
    {
      "name": "CONFIRMED_AUTHORIZED",
      "criteria": {
        "min_logins_90d": 90,
        "critical_title_required": true,
        "usage_profile": "POWER"
      },
      "action": "MANTER_AUTHORIZED"
    },
    {
      "name": "MOVE_TO_CONCURRENT",
      "criteria": {
        "max_logins_90d": 30,
        "critical_title_required": false,
        "usage_profile": "LIGHT"
      },
      "action": "MIGRAR_CONCURRENT"
    }
  ]
}
```

### 6.3 Arquivo: `config/query_catalog.json`

```json
{
  "queries": {
    "user_identity": "SELECT ... FROM MAXIMO.USERID ...",
    "user_access": "SELECT ... FROM MAXIMO.USERACCESS ...",
    "login_tracking": "SELECT ... FROM MAXIMO.LOGINTRACKING ..."
  }
}
```

---

## 7. Estrutura de Arquivos

### 7.1 Diretórios Principais

> Atualizado em 2026-07-09 após auditoria completa e remoção de arquivos obsoletos (scripts de debug/validação pontual, fluxos duplicados/legados, testes ad hoc sem framework). Ver `docs/REFATORACAO_2026-07-09.md` para a lista completa do que foi removido e por quê.

```
CHECKUSER/
├── adUsers/                       # Extratos brutos do AD (fornecidos pela equipe de TI)
│   ├── adUsers.csv                 # Usuários habilitados
│   └── adUsersdesabilitadas.csv    # Usuários desabilitados (fonte da Aba 3 — Saneamento AD)
│
├── config/                        # Configurações do sistema
│   ├── config.json                 # Configurações gerais (ambientes, queries)
│   └── licensing_rules.json        # Regras de licenciamento (lidas por license_optimizer.py)
│
├── docs/                          # Documentação
│   ├── SISTEMA_DOCUMENTACAO.md     # Este arquivo — documentação funcional canônica
│   ├── REGRAS_APPPOINTS_E_LICENCAS.md  # Regras de negócio: AppPoints e definição de licenças
│   ├── CALCULO_APPPOINTS_EXPLICACAO.md # Por que os cenários (As-Is/Saneado/Otimizado) divergem
│   ├── SUMARIO_EXECUTIVO_ABA3.md   # Histórico da correção do simulador de cenários
│   ├── REFATORACAO_2026-07-01.md   # Histórico: unificação de motores de cálculo
│   ├── REFATORACAO_2026-07-09.md   # Histórico: correção do motor NEM + auditoria AD×Maximo
│   ├── EVOLUCAO_ABA2_ALOCACAO.md   # Histórico: feature de saneamento de alocação
│   ├── EVOLUCAO_ABA3_ESCOPO.md     # Histórico: filtros de escopo (FORESEA/TERCEIROS/TODOS)
│   ├── TESTE_VISUAL_ABA3.md        # Checklist manual de teste dos filtros
│   ├── INDICADORES_DOCUMENTACAO.md # Documentação da aba de indicadores (Excel)
│   ├── campos_minimos_ad.md        # Especificação de campos mínimos exigidos do extrato AD
│   └── solicitacao_relacao_ad.md   # Modelo de solicitação do extrato AD à equipe de TI
│
├── output/                        # Dados de saída (gerados pelo pipeline, não versionar manualmente)
│   ├── consolidated/                # Dados consolidados (CSV/JSON)
│   │   ├── consolidated_user_identity.csv
│   │   ├── consolidated_user_access.csv / _normalized.csv
│   │   ├── consolidated_ad_users.csv
│   │   ├── license_decision_plan.csv
│   │   └── true_capacity_metrics.json
│   ├── reports/                     # Relatórios gerados
│   │   ├── maximo_unified_dashboard.html
│   │   └── maximo_risk_and_optimization_workbook.xlsx
│   └── raw/                         # Extratos brutos do DB2 por ambiente (7 ambientes)
│
├── queries/queries.py             # Catálogo de queries SQL usadas por run_db2cli_queries.py
│
├── scripts/                       # Código fonte (orquestração e relatório)
│   ├── generate_risk_report.py     # Orquestrador principal (gera HTML + Excel)
│   ├── run_pipeline.py-adjacent extraction scripts (run_db2cli_queries.py, extract_ad_users.py,
│   │   extract_maximo_users.py, generate_logintrack_from_sources.py, consolidate_outputs.py)
│   ├── config.py                   # Tabela canônica de AppPoints e regras de classificação
│   ├── domain/                      # Análise de domínio
│   │   ├── user.py, identity_analyzer.py, env_normalizer.py
│   │   ├── sanity_analyzer.py        # Cruzamento AD × Maximo (Aba 4 — Saneamento AD)
│   │   ├── migration_advisor.py      # Recomendações de migração (Aba 5)
│   │   ├── allocation_analyzer.py    # Saneamento de alocação (Aba 6)
│   │   ├── security_audit.py         # Auditoria de SoD Emissor x Aprovador em Compras (Aba 3)
│   │   ├── group_baseline.py         # Perfil de Acesso por Cargo: desvio por (ambiente, cargo) — Aba 3
│   │   └── role_standardization.py   # Padronização cargo x grupo único p/ todas unidades (Aba 3, p/ terceirizada)
│   ├── services/                    # Serviços de negócio
│   │   ├── analysis.py               # Análise de governança
│   │   └── app_points.py             # Simulação de AppPoints e classificação de licença (motor vigente)
│   ├── analysis/                    # Regras canônicas
│   │   ├── entitlement.py            # calculate_app_points() — fonte única de custo por licença
│   │   └── classification.py         # Perfil de uso (POWER/LIGHT)
│   └── reporting/                   # Geração de relatório (1 módulo por aba do dashboard)
│       ├── html_builder.py, html_template.py, html_data_processor.py, html_helpers.py
│       ├── ab1_painel.py … ab8_migracao.py
│       └── ab9_seguranca.py          # Aba 3 — SoD, Perfil de Acesso por Cargo, Padronização
│
├── src/                            # Pipeline de identidade e capacidade (chamado por run_pipeline.py)
│   ├── consolidate_user_access.py, normalize.py
│   ├── cross_env_userid_reuse.py, login_conflicts.py, identity_classification.py
│   ├── consolidate_license_footprint.py, analyze_usage.py, license_optimizer.py
│   └── true_capacity_calculator.py   # Motor de cálculo NEM (P50/P95/P100)
│
├── run_pipeline.py                 # Entry point principal (roda os 15 passos do pipeline)
├── requirements.txt
└── README.md
```

**Removido em 2026-07-09** (código morto, fluxo duplicado/legado, ou script de debug sem uso no pipeline — ver `docs/REFATORACAO_2026-07-09.md`): `tests/` (10 scripts ad hoc), `scripts/validate_*.py` (5 scripts), `_check_gov.py`, `_check_norbe.py`, `check_persongroupview.py`, `check_identity.py`, `check_usage.py`, `check_user_access.py`, `scripts/consolidate_logintracking.py`, `src/identity_resolution.py`, `scripts/domain/app_points.py`, `scripts/analysis/licensing.py`, `scripts/intelligent_local_site.py`, `config/query_catalog.json`.

### 7.2 Arquivos de Dados

#### 7.2.1 Entrada (Raw)
- `DadosTabelas/LOGINTRACKING_*.csv`: Histórico de logins do Maximo
- `Base Conhecimento/Base/PERSON_*.csv`: Dados cadastrais de pessoas

#### 7.2.2 Processamento (Consolidated)
- `consolidated_user_identity.csv`: Identidades únicas por USERID
- `consolidated_user_access.csv`: Acessos normalizados
- `consolidated_email.csv`: Emails por usuário
- `consolidated_persongroupview.csv`: Vínculo usuário-ambiente
- `consolidated_groupuser.csv`: Grupos de usuário

#### 7.2.3 Saída (Reports)
- `license_decision_plan.csv`: Plano de ação detalhado
- `maximo_unified_dashboard.html`: Dashboard interativo
- `maximo_risk_and_optimization_workbook.xlsx`: Relatório Excel

---

## 8. Como Executar

### 8.1 Pré-requisitos

```bash
# Python 3.8+
python --version

# Dependências
pip install -r requirements.txt
```

### 8.2 Execução Completa (Pipeline)

```bash
# Opção 1: Script Python
python run_pipeline.py

# Opção 2: Batch Windows
bat\processar_pipeline.bat
```

### 8.3 Execução Apenas do Relatório

```bash
# Gera apenas HTML e Excel (skip extração)
python run_pipeline.py --skip-extract

# Ou diretamente
python scripts/generate_risk_report.py
```

### 8.4 Execução de Etapas Individuais

```bash
# Extrair baseline
python scripts/extract_baseline.py

# Extrair logintracking
python scripts/extract_logintrack.py

# Consolidar dados
python scripts/consolidate_outputs.py

# Calcular capacidade NEM
python src/true_capacity_calculator.py

# Gerar relatório
python scripts/generate_risk_report.py
```

### 8.5 Agendamento (Windows Task Scheduler)

```batch
# bat/gerar_relatorio.bat
python scripts/generate_risk_report.py
```

---

## 9. Troubleshooting

### 9.1 Erro: "Arquivo não encontrado"

**Sintoma**: `FileNotFoundError` ao carregar CSV

**Solução**:
```bash
# Verificar se arquivos existem
dir output\consolidated\*.csv

# Se não existirem, executar pipeline completo
python run_pipeline.py
```

### 9.2 Erro: "LOCATION_SITE vazio"

**Sintoma**: Coluna "Unidade" vazia na Aba 5

**Solução**:
```bash
# Verificar se consolidated_persongroupview.csv existe
dir output\consolidated\consolidated_persongroupview.csv

# Se não existir, executar extração do baseline
python scripts/extract_baseline.py
```

### 9.3 Erro: "Dados inconsistentes na tabela"

**Sintoma**: Colunas com dados trocados ou errados

**Verificação**:
```bash
# Verificar estrutura do CSV
python -c "import csv; from pathlib import Path; p = Path('output/consolidated/license_decision_plan.csv'); rows = list(csv.DictReader(p.open(encoding='utf-8-sig'))); print('Colunas:', list(rows[0].keys()))"
```

### 9.4 Erro: "Chart.js não carrega"

**Sintoma**: Gráficos não aparecem no dashboard

**Solução**:
- Verificar conexão com internet (Chart.js é carregado via CDN)
- Ou baixar Chart.js localmente e atualizar `html_template.py`

### 9.5 Performance Lenta

**Sintoma**: Geração de relatório demora > 5 minutos

**Otimizações**:
```python
# 1. Reduzir período de análise
# Em config.json, ajustar período de logintracking

# 2. Usar apenas escopo FORESEA+PARCEIRO
# Em generate_risk_report.py, comentar outras categorias

# 3. Desabilitar gráficos pesados
# Em html_template.py, reduzir número de data points
```

---

## 10. Glossário

### 10.1 Termos Técnicos

- **AppPoints**: Unidade de medida de consumo de licença
- **NEM**: Non-Exclusive Maximum (máximo não-exclusivo)
- **P50**: Percentil 50 (mediana)
- **P95**: Percentil 95 (pico seguro)
- **P100**: Percentil 100 (máximo absoluto)
- **Authorized**: Licença dedicada (acesso garantido)
- **Concurrent**: Licença compartilhada (pool)
- **Premium**: Entitlement com módulos críticos O&G
- **Base**: Entitlement com módulos padrão

### 10.2 Siglas

- **MAS**: Maximo Asset Management System
- **O&G**: Oil & Gas
- **NEM**: Non-Exclusive Maximum
- **CSV**: Comma-Separated Values
- **JSON**: JavaScript Object Notation
- **HTML**: HyperText Markup Language
- **CDN**: Content Delivery Network

---

## 11. Contato e Suporte

**Desenvolvedor**: Equipe de TI - Foresea  
**Última Atualização**: 2026-07-11  
**Versão**: 2.6.3

---

## 12. Changelog

### v2.6.3 (2026-07-11 — Aba Peak com filtro de escopo real + regras de contas de integração/serviço)
- ✅ **Aba Peak agora tem o MESMO seletor de escopo da aba Cenários de AppPoints** (FORESEA+PARCEIRO/TERCEIROS/INTEGRAÇÃO/TODOS), com gráfico, cards (P100/P95/hora do pico/contribuidores) e tabela de composição **recalculados de verdade** por escopo — não um filtro visual sobre a série de TODOS. `license_reconciliation.py` agora computa série horária, pico e composição próprios para cada um dos 4 escopos. Exemplo real: escopo FORESEA sozinho tem pico de **1.931 pts (P100) às 2026-05-19 14:00 com 87 pessoas simultâneas** — hora e composição bem diferentes do pico de TODOS (2.585 pts, 2026-05-25 07:00, 150 pessoas).
- ✅ **Regra de negócio confirmada pelo usuário — contas de integração/serviço**: `WSORACLE`, `MAXADMIN` e `MAXREG` agora são fixadas como **Premium Authorized = 5 pts cada**, escopo INTEGRAÇÃO, sem passar pelo cálculo estatístico de presença (não são pessoas com padrão de uso a avaliar — são contas de integração com acesso garantido por definição). `ITEAM` corrigido para escopo TERCEIROS (é conta de suporte da própria terceirizada, não FORESEA). `HELPDESK` confirmado como já correto (Base Concurrent — "só visualiza, não faz nada").
- 📄 Constantes `FIXED_PREMIUM_AUTHORIZED_ACCOUNTS` e `SCOPE_OVERRIDES` em `license_reconciliation.py` — outras contas de padrão semelhante (ex.: `HELPDESK`, `ITEAM` antes da correção) não entram em regras automáticas sem confirmação explícita do usuário.

### v2.6.2 (2026-07-11 — Auditoria completa da aba Peak Contributors: gráfico e tabela reconstruídos sobre o Cenário Conciliado)
- 🐛 **[CRÍTICO] O gráfico "Peak Hours" mostrava uma série horária completamente desconectada dos cards acima dele**: os cards de P100/P95/contribuidores já vinham do Cenário Conciliado (reconciliado), mas o gráfico (`concurrency_hourly`/`concurrency_hourly_app_points`/`concurrency_hourly_app_points_nem`) ainda lia `true_capacity_metrics.json` — a série antiga, não reconciliada (chegava a mostrar 200-228 "usuários simultâneos" numa hora em que o card dizia "152 contribuidores no pico"). Corrigido: `license_reconciliation.py` agora expõe a série horária completa (`hourly_series`, escopo TODOS) e `html_data_processor.py` usa exclusivamente essa série no gráfico — o pico do gráfico agora bate exato com os cards (152 usuários, 2.600 AppPoints, mesma hora).
- 🐛 **Tabela "Top Contribuidores do Pico" removida por não fazer sentido** (avaliação do usuário confirmada): listava até 20 pessoas individualmente, mas todo Premium Concurrent vale sempre 15 pts e todo Base Concurrent vale sempre 10 — um "ranking" onde todo mundo empata no mesmo valor não ordena nada de real. Substituída por **"Composição do Pico por Categoria"**: quebra por escopo × tipo de licença com contagem de pessoas e AppPoints por categoria (ex.: 75 Premium Concurrent FORESEA = 1.125 pts, 60 Base Concurrent Sem Domínio = 600 pts) — a informação que de fato importa para dimensionar o pool.
- 📄 Lista individual completa das pessoas no pico continua disponível na aba Excel `8_PeakContributors` (não removida, só não mais duplicada como tabela "top 20" na tela).

### v2.6.1 (2026-07-11 — Card do Cenário Conciliado agora reativo ao escopo + remoção da aba Eventos Críticos)
- 🐛 **Card "Cenário Conciliado" mostrava 2 números fixos (P95 só-conciliados / P95 realista) que competiam com o P95 do simulador logo abaixo** — 3 números de "P95" na mesma tela (usuário reportou: card 1.715/2.235, simulador 1.712 no escopo FORESEA). Corrigido: o card agora tem UM headline reativo, ligado ao MESMO seletor de escopo do simulador (`updateScopeFilter()` atualiza `cardScopedP95`/`cardScopedP100` via JS) — trocar o escopo move os dois juntos, sempre com o mesmo número.
- 🗑️ **Aba "Eventos Críticos" removida** (era a 8ª aba) — avaliação do usuário confirmada: os 4 gatilhos de cenário (P50/P95/P100/Blackout) já eram exatamente os mesmos números do simulador da aba Cenários de AppPoints, sem nenhuma informação adicional. Módulo `ab4_eventos.py` deletado (código morto). Abas renumeradas: Peak Contributors 9→8, Plano de Ação 10→9. Dashboard agora com **9 abas**.

### v2.6.0 (2026-07-11 — Presença ajustada por rotação offshore + fonte única de P50/P95/P100)
- 🔬 **Presença ajustada pelo próprio padrão de rotação offshore** (`license_reconciliation.py`): medir presença dividindo horas logadas por 90 dias corridos subestima quem está plenamente ativo durante o embarque, já que a operação trabalha em regime de turmas (embarque/folga). Detectamos o padrão diretamente nos dados: agrupando os dias de login de cada pessoa em blocos (gap ≤3 dias ainda conta como o mesmo bloco), os blocos se concentram fortemente em **13-15 dias** e as lacunas entre blocos em **14-15 dias** — a assinatura de um rodízio 14x14. Presença agora = horas logadas ÷ horas do(s) bloco(s) da própria pessoa (`HORAS_ELEGIVEIS_ROTACAO`), não os 2.160h do calendário (`PRESENCA_CALENDARIO_PCT`, mantida para comparação). Resultado: 71 → **150 Authorized** (reserva 339 → 700 pts) — mais gente estava, na prática, plenamente ativa durante o embarque do que o cálculo por calendário sugeria.
- 🐛 **Corrigida divergência de P50/P95/P100 entre as abas Cenários de AppPoints, Eventos Críticos e Peak Contributors**: existiam 2 cálculos concorrentes — o antigo `true_capacity_calculator.py` (população e regra de licença do `license_optimizer.py`, sem reconciliação com AD) e o novo Cenário Conciliado — cada um usado por abas diferentes, gerando 3 números diferentes de "P95" na mesma tela. Unificado: `license_reconciliation.py` agora calcula P50/P95/P100 **por escopo** (foresea/terceiros/integração/todos) e essa é a ÚNICA fonte usada em `html_data_processor.py` para as 3 abas. Verificado: mesmo escopo agora mostra o mesmo número nas 3 abas (P95=2.235, P100=2.600, 152 contribuidores, todos batendo exatamente).
- 📊 Números oficiais vigentes (escopo TODOS, presença ajustada por rotação): **P50=1.475, P95=2.235, P100=2.600** contra teto de 1.200.
- 🐛 Corrigido bug residual: `_eligible_hours()` retornava `int` em vez de tupla para usuários sem login algum (TypeError na desestruturação).

### v2.5.1 (2026-07-11 — Consolidação do bloco AD + correção das abas de pico)
- 🐛 **Bug confirmado e corrigido na antiga aba 9_PeakContributors**: o motor NEM truncava a lista de contribuintes do pico em 50 (soma de apenas 750 pts) e reportava `peak_contributors_count=50` como se fosse o total — a soma nunca fechava com o P100. Agora a lista é COMPLETA (174 contribuintes) e a matemática fecha exata: reserva Authorized (1.001) + concurrent dos logados no pico (1.770) = **P100 = 2.771**. Aba renumerada para `8_PeakContributors`.
- 🗑️ **Aba 8_ConcurrentPeak removida** (série horária bruta de 2.158 linhas) — redundante com os Cenários de AppPoints do dashboard, conforme avaliação do usuário.
- ✅ **Bloco de saneamento AD consolidado**: 7 abas de achados (11-17: AD desativado×ativo, divergências de nome, múltiplos USERIDs, match por prefixo, sem match, Maximo sem email, divergência de domínio) fundidas em `10_Saneamento_AD_Achados` com coluna ACHADO filtrável (2.871 linhas; o achado crítico AD_DESATIVADO_MAS_ATIVO destacado em vermelho).
- ✅ **Renumeração completa sem buracos**: workbook final com **25 abas** (0_Indice a 24_Cenario_Conciliado_Usuarios), sequência contínua — era 40+ abas há dois ciclos. Referências cruzadas (índice, resumo consolidado, notas de truncamento no HTML) atualizadas.

### v2.5.0 (2026-07-11 — Cenário Conciliado de licenciamento + consolidação do workbook)
- ✅ **Novo módulo `scripts/domain/license_reconciliation.py` — Cenário Conciliado (dimensionamento oficial MAS 9)**, metodologia aprovada pelo usuário: população licenciável = ativos no Maximo conciliados com conta ATIVA no AD (cascata e-mail → prefixo=USERID → nome completo normalizado); licença definida por **break-even econômico de presença** (Authorized só compensa com presença >30-33% das horas; presença real mediana medida: 6,7%, máx 28% — padrão offshore 14x14), com exceção de negócio para títulos críticos que aprovam; **terceiros de bordo ativos** (não conciliados mas com uso real em 90d) mantidos como Concurrent por decisão de negócio.
- 📊 Números vigentes: 1.630 ativos → 816 conciliados (email 317/prefixo 447/nome 52) + 718 terceiros ativos + 96 sem uso (limpeza). Licença estatística: 71 Authorized (reserva 339 pts) + 745 Concurrent. **NEM só-conciliados P95=1.534 | realista (+terceiros) P95=2.064 | teto 1.200.** Diagnóstico-chave: dos 569 "SEM DOMINIO", 259 são funcionários FORESEA reais sem e-mail no Maximo.
- ✅ Card do cenário na aba "Cenários de AppPoints", detalhe por usuário em `cenario_conciliado_licencas.csv` e no Excel.
- ✅ **Workbook consolidado a pedido do usuário** (menos abas, análise mais fácil): bloco de 17 abas → 9. Fusões: resumos de Migração+SoD+Conciliado → `25_Resumo_Consolidado`; recortes de PO (31/32, subconjuntos filtráveis por APP) eliminados; MAXADMIN fundido em `27_SoD_Pessoas` (coluna TIPO); 3 camadas de evidência → `28_SoD_Evidencias` (coluna CAMADA); baseline por cargo/unidade + padrão global MAS 9 → `29_Cargo_x_Grupos` (coluna UNIDADE). Workbook total: 31 abas.

### v2.4.0 (2026-07-11 — Auditoria independente completa do sistema + correções)
Auditoria formal (matemática, ciência de dados, pipeline e entregável de migração), com agentes de auditoria independentes + verificação empírica direto no banco. Achados e correções:
- 🔴 **[CRÍTICO] Moeda errada em todos os valores de compras**: 100% das 16.912 PRs dos últimos 365 dias têm `CURRENCYCODE='USD'` (verificado no banco), mas o dashboard/Excel rotulava tudo como "R$" — a gravidade dos achados de SoD estava subestimada ~5x (ex.: "R$ 15,7M" é na verdade USD 15,7M). Corrigido em todas as telas/planilhas, com nota metodológica.
- 🔴 **[CRÍTICO] Motor NEM excluía 569 usuários CONCURRENT do cálculo de capacidade**: usuários "SEM DOMINIO" (sem email classificável) eram descartados no filtro de escopo do `true_capacity_calculator.py` — mas licença é consumida por login, com ou sem email. Pico real recalculado: P95 = 2.467 e P100 = 2.771 AppPoints (antes: 1.891/2.166) — o estouro do teto de 1.200 é ~30% pior que o reportado. Correção validada por recalculação independente (bateu exato).
- 🔴 **[CRÍTICO] Entregável de migração não respondia 2 das 3 perguntas do negócio**: `migration_advisor.py` não emitia nenhum campo de grupo/acesso (o CSV de acessos era carregado e descartado). Reescrito: agora cada recomendação traz cargo, grupos Maximo atuais por ambiente e grupo recomendado MAS 9 (via padronização por cargo).
- 🔴 **[CRÍTICO] ~39% da categoria CRIAR_NO_MAXIMO era falsa**: o match AD↔Maximo era só por email, mas 92,7% dos USERIDs não têm e-mail cadastrado — 782 usuários AD com USERID = prefixo do email (convenção da empresa) "não existiam" no Maximo, 449 deles ATIVOS. Corrigido com cascata email → prefixo (1.206 matches recuperados); a população real de migração (ativos em ambos) dobrou de 317 para 766.
- 🟠 **[ALTO] Caso de segurança invisível**: o arquivo de AD desabilitados nunca era carregado pelo advisor — o cruzamento "DESLIGADO no AD porém ATIVO no Maximo" resultava sempre 0. Agora: **50 casos reais** detectados (prioridade ALTA, não migrar, desativar antes do MAS 9).
- 🟠 **[ALTO] VERIFICAR_AD era 91% ruído** (268/294 contas 100% inativas) e MAXADMIN aparecia como "criar no AD". Corrigido: inativos sem AD viram limpeza; contas de serviço (MAXADMIN, MAXREG, HELPDESK, padrão rig `ODN1001`) têm categoria própria CONTA_SERVICO.
- 🟡 **[MÉDIO] Pareamento ambiente×status fabricado**: a aba 8 zipava dois sets independentes por posição (228 recomendações com pares errados medidos). O advisor agora emite pares reais `env:status`.
- 🟡 **[MÉDIO] Status não mapeados sumiam sem recomendação** (ex.: NEWREG): novo tipo REVISAR_STATUS (190 casos).
- 🟡 **[MÉDIO] Valores de SoD somados por caso, não por PR única**: PR resubmetida N vezes somava o valor N vezes (~0,1% de inflação; 23 casos críticos = 22 PRs). Corrigido.
- 🟡 **[MÉDIO] Guarda de extração podre**: `consolidate_outputs.py` agora detecta arquivo raw com erro de conexão DB2 (`SQL30081N`) e imprime alerta com o comando exato de reprocessamento — antes o ambiente sumia silenciosamente (causa-raiz da subcontagem de ODN2).
- 🟡 **[MÉDIO] Reenquadramento de CREATEDR**: os ~600 "conflitos" de Requisição Simplificada são UM problema de desenho (todos os 9 grupos com acesso têm o pacote criar+aprovar completo), não centenas de anomalias individuais — documentado na metodologia da Aba 3.
- 🟡 **[MÉDIO] Alertas de fusão de grupos**: cluster `OOG_ASSET_COORDINATOR`≈`OOG_ENGINEER_COORDINATOR` (97% similares mas papéis nominalmente distintos, com delta real de MOC) agora recebe alerta "confirmar com a área antes de fundir"; e `OOG_COGNOS_LEITURA` é 100% idêntico ao `OOG_COGNOS_ADM` (o "read-only" tem as mesmas permissões do ADM) — alerta de privilégio.
- ✅ **Validado como correto** na auditoria: matemática de dedup do NEM (mesma pessoa N logins/hora = 1; multi-ambiente = 1, correto para licença por usuário; sem dupla contagem Authorized+Concurrent; custo por usuário multi-env usa o maior), dedup 7x da evidência de SoD, confronto por site, e clusterização Jaccard (coesão par-a-par verificada em todos os 6 clusters).

### v2.3.0 (2026-07-11 — Auditoria de Segregação de Funções em Compras, nova Aba 3)
- ✅ **Nova aba dedicada "🔐 Segregação de Funções"** (posição 3, ver seção 4.7): audita conflito Emissor x Aprovador em Compras (PR/PO/Requisição Simplificada) em 3 camadas crescentes de rigor — estrutural (grupo), pessoa real (cruzando `GROUPUSER`), e evidência documentada (`WFTRANSACTION`+`PR`, quem de fato submeteu e aprovou o mesmo documento).
- ✅ **Autoaprovação direta**: novo campo `PR.OOG_REQUESTEDBY` (solicitante real, diferente da conta genérica do rig) cruzado com quem aprovou — 55 casos confirmados, R$ 441 mil, extraído de BASE (~97% de cobertura real).
- ✅ **Severidade por evidência oficial**: `WFTRANSACTION.ACTIONPERFORMED='OOG_PRWENG'` (roteamento para Engenheiro de Ativos, conforme procedimento oficial de aprovação de PR) usado para distinguir violação confirmada (`CRITICO`) de caso a revisar (`REVISAR_REGRA`).
- ✅ **Confronto por site**: conflitos "grupos diferentes" só contam se os grupos emissor/aprovador realmente se sobrepõem no mesmo site (`SITEAUTH`/`MAXGROUP.AUTHALLSITES`) — evita falso positivo de alguém com grupo emissor numa unidade e aprovador em outra (embarque).
- ✅ **PO (Ordem de Compra)**: recorte dedicado do Nível 1/2; confirmado e documentado que a camada de evidência real da PR não é replicável (`WFTRANSACTION` não loga workflow de PO nesta instalação; teste alternativo via `PURCHASEAGENT`/`CHANGEBY` deu 100% ruído de automação/`MAXADMIN`).
- ✅ **Cadeia PR → PO**: novo teste via `PRLINE.PONUM` + `OOG_CREAPOGRP` — mesma pessoa aprovou a PR e gerou a PO dela; 0 casos em 2.670 conversões históricas (controle limpo, camada ativa para acusar automaticamente se mudar).
- ✅ **Perfil de Acesso por Cargo** e **Padronização de Acesso** (material para terceirizada): ver seção 4.7, itens 7-8 — descreve desvio por unidade e prescreve um grupo padrão único por cargo para toda a empresa, com detecção de grupos duplicados por permissão real (não nome).
- 🐛 **Bug corrigido (subcontagem silenciosa)**: `security_audit.py`, `group_baseline.py` e `role_standardization.py` cruzavam `consolidated_user_identity.csv` (`ENV_DB` com nomes longos `NORBE06/08/09`) contra `consolidated_groupuser.csv`/`consolidated_maxgroup.csv` (códigos curtos `N06/N08/N09`) sem normalizar — o mesmo padrão já corrigido em `migration_advisor.py`/`allocation_analyzer.py`, mas ausente na auditoria de SoD desde sua criação. Combinado com extrações de `groupuser`/`maxgroup`/`persongroupview` de ODN2 que haviam falhado por timeout e nunca foram reprocessadas, os números de pessoas ativas com conflito estavam subcontados (144 → 619 após a correção). Ver detalhe completo na seção 4.7.

### v2.2.0 (2026-07-09, continuação — auditoria completa + UX/UI + limpeza)
- ✅ **Correção crítica no fluxo AD × Maximo**: `scripts/extract_ad_users.py` tinha toda a lógica dentro do `else` de um `if __name__ == '__main__':` — quando executado pelo pipeline (como sempre é), não fazia absolutamente nada. `consolidated_ad_users.csv` estava desatualizado sem que ninguém percebesse.
- ✅ **Ambiente ODN2 inteiro desaparecia silenciosamente** do pipeline: a extração de `groupuser`/`persongroupview` para ODN2 falhou (erro de conexão DB2), e `src/consolidate_user_access.py` descartava o ambiente inteiro nesse cenário em vez de aproveitar os dados de `maxuser`/`person` que tinham extraído com sucesso. Corrigido com fallback por ambiente — os 7 ambientes agora aparecem sempre na auditoria AD × Maximo.
- ✅ **Alerta "AD desativado + Maximo ativo" sempre mostrava 0**: o print de diagnóstico rodava *antes* da extensão da lista pelos matches por USERID/nome. Corrigido, e o algoritmo de match por nome foi enrijecido (exige 1º nome em comum, ignora conectores como "de/da/dos") para eliminar falsos positivos — caiu de ~500 matches (majoritariamente ruído) para 20 candidatos revisáveis.
- ✅ Novo campo nas análises: **"ambientes ativos / ambientes totais"** por usuário — deixa explícito o caso "desativado em 6 de 7 unidades, mas ainda ativo em 1", que era o objetivo principal da auditoria solicitada.
- ✅ Nova sheet no Excel (`9b_AD_Desativado_Mas_Ativo`) — esse achado crítico não tinha equivalente no workbook antes, só no HTML.
- ✅ **Auditoria de arquivos obsoletos**: removidos 26 arquivos mortos ou duplicados (testes ad hoc sem framework, scripts de validação pontual de bugs já corrigidos, 2 fluxos legados substituídos por versões modulares, 1 módulo "canônico" que na verdade nunca era importado). Ver `docs/REFATORACAO_2026-07-09.md` para a lista completa.
- ✅ **Filtros corrigidos**: dropdown de Decisão da Aba Governança (vocabulário incompatível com os dados reais), busca da Aba Plano de Ação (procurava na coluna errada), busca da Aba Migração (não considerava nome), filtro de escopo da Aba Peak Contributors (função existia mas não tinha elemento HTML correspondente — implementado de verdade), `id` duplicado entre duas abas, aba de Detalhamento de Alocação sem botão de navegação (existia mas era inacessível).
- ✅ **Inconsistências HTML × Excel**: adicionados avisos visíveis de truncamento em tabelas que mostram só uma amostra (ex.: 200 de 4.413 registros), corrigido texto de card do Painel que dizia excluir "SEM DOMÍNIO" mas na verdade incluía.
- ✅ **Abas reordenadas** por fluxo lógico: Painel → Governança → Saneamento AD → Migração → Detalhamento de Alocação → Cenários de AppPoints → Eventos Críticos → Peak Contributors → Plano de Ação (era: Painel, Governança, AppPoints, Eventos, Plano de Ação, Peak, Saneamento AD, Migração).
- 📄 Novo documento dedicado: `docs/REGRAS_APPPOINTS_E_LICENCAS.md` — regras de negócio completas de AppPoints e definição de licenças, com referência de arquivo:função para cada regra.

### v2.1.0 (2026-07-09)
- ✅ Corrigido bug crítico: `continue` mal posicionado em `html_data_processor.py` excluía todos os usuários BASE dos cenários Saneado/Otimizado (campos "Base Auth"/"Base Conc" sempre zerados) e nunca excluía PREMIUM inativos (deveria excluir)
- ✅ Corrigido `IndentationError` fatal em `src/true_capacity_calculator.py` que impedia o motor de cálculo NEM de executar por completo (e um `NameError` latente que ocorreria mesmo após corrigir a indentação)
- ✅ Corrigida chave `hourly_app_points_nem_by_scope` que era descartada ao montar `concurrency_summary` em `generate_risk_report.py`, fazendo os cenários por escopo caírem num fallback sem diferenciação estatística (P50=P95=P100)
- ✅ Identificado e contornado (não corrigido de forma definitiva) crash de `UnicodeEncodeError` no pipeline Windows que corrompia silenciosamente `consolidated_logintracking_from_sources.csv`
- ✅ Auditoria completa da matemática do cálculo NEM a pedido do usuário: sem duplicidade de pessoa, contas de serviço isoladas corretamente, sem contagem dupla Authorized/Concurrent
- ⚠️ Novo resultado real (escopo TODOS): P95 = 1.586 e P100 = 1.861 AppPoints — **excede o teto contratual de 1.200** (antes o motor não executava e o número exibido era parcial/incompleto)
- 📄 Detalhamento completo em `docs/REFATORACAO_2026-07-09.md`

### v2.0.0 (2026-06-29)
- ✅ Correção completa da Aba 5 (Plano de Ação)
- ✅ Uso de `consolidated_persongroupview.csv` para LOCATION_SITE
- ✅ Lógica de recomendação corrigida (Licença To-Be)
- ✅ Adição de coluna "Unidade" na tabela
- ✅ Textos da Aba 4 (Eventos Críticos) atualizados
- ✅ Layout inline no Simulador de Cenários
- ✅ Coerência total entre abas

### v1.0.0 (2026-06-25)
- ✅ Versão inicial do dashboard
- ✅ 6 abas funcionais
- ✅ Análise de identidades
- ✅ Cálculo de capacidade NEM