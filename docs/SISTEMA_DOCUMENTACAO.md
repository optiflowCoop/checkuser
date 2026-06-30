# Documentação Completa do Sistema CHECKUSER

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
│  - 6 Abas: Painel, Governança, Cenários, Eventos,      │
│    Plano de Ação, Peak                                  │
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
- Estrutura HTML das 6 abas
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

**Fatores por Tipo de Licença**:
- **Premium Authorized**: 5 pontos
- **Premium Concurrent**: 15 pontos
- **Base Authorized**: 3 pontos
- **Base Concurrent**: 10 pontos

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
**Definição**: Número máximo de usuários simultâneos em um período

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

**Nota**: Fatores são aplicados apenas quando há dados horários disponíveis.

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

```
CHECKUSER/
├── bat/                          # Scripts batch para Windows
│   ├── extrair_baseline.bat      # Extrai dados do Maximo
│   ├── extrair_logintrack.bat    # Extrai histórico de logins
│   ├── processar_pipeline.bat    # Executa pipeline completo
│   └── gerar_relatorio.bat       # Gera relatórios
│
├── config/                       # Configurações do sistema
│   ├── config.json               # Configurações gerais
│   ├── licensing_rules.json      # Regras de licenciamento
│   └── query_catalog.json        # Consultas SQL
│
├── docs/                         # Documentação
│   ├── SISTEMA_DOCUMENTACAO.md   # Este arquivo
│   ├── ARQUITETURA.md            # Arquitetura detalhada
│   ├── PIPELINE.md               # Guia do pipeline
│   └── GUIA_USO.md               # Manual do usuário
│
├── output/                       # Dados de saída
│   ├── consolidated/             # Dados consolidados (CSV)
│   │   ├── consolidated_user_identity.csv
│   │   ├── consolidated_user_access.csv
│   │   ├── consolidated_email.csv
│   │   ├── consolidated_persongroupview.csv
│   │   ├── consolidated_groupuser.csv
│   │   ├── license_decision_plan.csv
│   │   └── true_capacity_metrics.json
│   │
│   ├── reports/                  # Relatórios gerados
│   │   ├── maximo_unified_dashboard.html
│   │   └── maximo_risk_and_optimization_workbook.xlsx
│   │
│   ├── raw/                      # Dados brutos extraídos
│   └── logs/                     # Logs de execução
│
├── queries/                      # Consultas SQL
│   └── queries.py
│
├── scripts/                      # Código fonte
│   ├── generate_risk_report.py   # Orquestrador principal
│   ├── consolidate_*.py          # Scripts de consolidação
│   ├── extract_*.py              # Scripts de extração
│   │
│   ├── config.py                 # Carregador de configurações
│   ├── domain/                   # Análise de domínios
│   │   ├── user.py               # Perfis de usuário
│   │   └── identity_analyzer.py  # Análise de identidades
│   │
│   ├── services/                 # Serviços de negócio
│   │   ├── analysis.py           # Análise de governança
│   │   └── app_points.py         # Simulação de AppPoints
│   │
│   └── reporting/                # Geração de relatórios
│       ├── html_builder.py       # Construtor HTML
│       ├── html_template.py      # Template HTML
│       ├── html_data_processor.py # Processador de dados
│       └── html_helpers.py       # Funções auxiliares
│
├── src/                          # Módulos core
│   ├── analyze_usage.py          # Análise de uso
│   ├── consolidate_license_footprint.py
│   ├── consolidate_user_access.py
│   ├── cross_env_userid_reuse.py
│   ├── identity_classification.py
│   ├── identity_resolution.py
│   ├── license_optimizer.py
│   ├── login_conflicts.py
│   ├── normalize.py
│   ├── rules_manager.py
│   └── true_capacity_calculator.py
│
├── tests/                        # Testes automatizados
├── run_pipeline.py               # Entry point principal
├── requirements.txt              # Dependências Python
└── README.md                     # Este arquivo
```

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
**Última Atualização**: Junho 2026  
**Versão**: 2.0.0

---

## 12. Changelog

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