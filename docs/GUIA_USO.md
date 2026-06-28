# Sistema de Governança Maximo EAM - Guia de Uso

## 📋 Visão Geral

Sistema completo para governança de identidades, baseline funcional e otimização de licenciamento MAS 9.

**Funcionalidades:**
- ✅ Detecção de colisões de identidades e reuso de logins
- ✅ Baseline funcional por TITLE (cargo) com análise de divergências de TYPE e grupos
- ✅ Otimização de licenciamento AppPoints com análise de uso real (LOGINTRACKING)
- ✅ **LocationSite correto do PersonGroupView** como source-of-truth
- ✅ **Classificação Onshore/Offshore** baseada em dados reais
- ✅ Dashboard HTML profissional para apresentações executivas

---

## 🚀 Fluxo de Uso Rápido

### 1️⃣ Extração de Dados (Primeira vez ou atualização completa)
```
Clique em: extrair_tudo.bat
```
Extrai TODAS as consultas do DB2 (maxuser, persongroupview, logintracking, etc.)

### 2️⃣ Processamento do Pipeline
```
Clique em: processar_pipeline.bat
```
Executa todas as 11 etapas:
- Normalização de identidades
- Detecção de colisões
- Enriquecimento de conflitos
- Análise de baseline funcional
- **Análise de uso (Phase 3)** ← Agora com LocationSite correto
- Geração de recomendações

### 3️⃣ Geração do Relatório
```
Clique em: gerar_relatorio.bat
```
Gera o HTML e abre automaticamente no navegador.

---

## 📊 Extrações Pontuais (Atualizações Parciais)

### Extrair apenas LOGINTRACKING
```
Clique em: extrair_logintrack.bat
```
Útil para atualizar análise de uso sem recarregar identidades.
**Novo**: Consolida LoginTracking de múltiplas fontes (consolidated + DadosTabelas/)

### Extrair apenas Baseline Funcional
```
Clique em: extrair_baseline.bat
```
Atualiza dados de TITLE, PERSONGROUP e PERSONGROUPTEAM.

---

## 📁 Estrutura de Arquivos

### Entrada (input/)
- `maxuser_*.csv` - Dados de identidades por ambiente
- `persongroupview_*.csv` - Cargos, departamentos e **LocationSite** ⭐
- `logintracking_*.csv` - Histórico de login (90 dias)

### Entrada Adicional (DadosTabelas/)
- `LOGINTRACKING_*.csv` - Arquivos de LoginTracking baixados manualmente
  - Consolida automaticamente com dados consolidados
  - Detecta e elimina duplicatas

### Saída (output/)
- `consolidated/` - Dados consolidados do pipeline
  - `usage_analysis_phase3.csv` - Análise de uso com **LOCATION** do PersonGroupView
  - `consolidated_persongroupview.csv` - Dados de localização
- `reports/` - Dashboard HTML + Excel com dados corrigidos

### Scripts
- `run_pipeline.py` - Orquestrador principal (11 steps)
- `generate_risk_report.py` - Gerador do dashboard HTML
- `src/analyze_usage.py` - Analisador de uso (Phase 3) ← **ATUALIZADO**
- `integrate_usage_data.py` - Integra dados de análise no XLSX final ← **NOVO**
- `src/license_optimizer.py` - Otimizador de licenças

---

## 🎯 Interpretação dos Resultados

### Dashboard - Seção 1: Resumo Executivo
- **Pessoas Únicas (Ativas)**: Base real para licenciamento
- **Registros Ativos**: Total de contas logáveis (pode ter duplicatas)
- **Riscos de Reuso**: Logins repetidos entre unidades
- **Colisões Críticas**: Mesmo login, pessoas diferentes (CRÍTICO!)

### Dashboard - Seção 2: Otimização de AppPoints ⭐ NOVO
**Segregação Estratégica:**
- **AppPoints FORESEA**: Usuários permanentes (@foresea.com, @foresea-partner.com) - SERÃO MIGRADOS
- **AppPoints Temporários**: Contratados externos - NÃO SERÃO MIGRADOS PARA MAS 9
- **Margem Disponível**: Quanto ainda pode usar (baseado apenas em usuários FORESEA)
- **Power Users O&G**: Usuários que realmente acessam módulos Petroleum/OilGas e precisam Premium

**Top 20 Usuários FORESEA:**
- 🏢 = Usuário permanente Foresea
- 👷 = Usuário temporário/contratado
- Ordenados por custo de AppPoints

**Recomendações:**
- 🔵 NÃO MIGRAR - Usuário temporário (não incluir no MAS 9)
- 🔴 DESATIVAR - Sem uso há 90 dias (mesmo sendo FORESEA)
- 🟡 DOWNGRADE - Premium alocado mas não usa módulos O&G
- 🟢 OK - Licença correta para o uso

### Dashboard - Seção 6: Baseline Funcional
Análise por TITLE (cargo):
- **TYPE DIVERGENTE**: Mesmo cargo tem TYPEs diferentes entre unidades
- **GRUPOS DIVERGENTES**: Mesmo cargo participa de grupos diferentes

**Exemplo de interpretação:**
```
CHEFE DE MECANICA - TYPE DIVERGENTE GRUPOS DIVERGENTES
⚠️ Inconsistência de TYPE (2 diferentes):
📍 NORBE06: TYPE 4 (1 usuário)
📍 NORBE08: TYPE 4, TYPE 5 (2 usuários - sendo que 1 é TYPE 4 e outro é TYPE 5)
```
Significa: O cargo "Chefe de Mecânica" está como TYPE 4 na NORBE06, mas na NORBE08 tem DOIS usuários desse cargo - um é TYPE 4 e outro é TYPE 5. Isso indica despadronização.

---

## 📍 Classificação de Localização (NOVO)

### Coluna LOCATION (source-of-truth: PersonGroupView.LocationSite)
```
LOCATION: Identificação da unidade/base onde o usuário está alocado
Exemplos: N06, N08, N09, ODN1, ODN2, BASE-UNP, OG-BASE
```

### OPERATIONAL_PRESENCE (classificação automática)
- **ONSHORE**: base-unp, og-base, macae, base
- **OFFSHORE**: N06, N08, N09, ODN1, ODN2, e similares
- **UNKNOWN**: Não classificado (sem LocationSite no PersonGroupView)

**Exemplo:**
```
USERID: ALESSANDROCORREA
LOCATION: N08 (vindo de PersonGroupView)
OPERATIONAL_PRESENCE: OFFSHORE (classificação)
```

---

## 🔧 Configurações Importantes

### Regras de Licenciamento (src/analyze_usage.py)

**Módulos O&G que exigem Premium:**
- WOTRACK com contexto "Petroleum"
- PFWORKTRACK (Planning & Forecasting)
- DRILLING, HSE, LOCREC, COMPLIANCE

**Custos AppPoints (config):**
- Premium Concurrent: 15 pts
- Premium Authorized: 5 pts
- Base Concurrent: 10 pts
- Base Authorized: 2 pts
- Limited: 5 pts

**Classificação de Tier:**
- **POWER_OG**: Acessa módulos O&G + >60 logins/90d
- **MEDIUM_OG**: Acessa módulos O&G + <60 logins/90d
- **IDLE**: 0 logins nos últimos 90 dias
- **VERY_LIGHT**: 1-5 logins/90d

### Contrato
- **Total contratado**: 1.200 AppPoints
- **Fonte**: Configurado em `src/license_optimizer.py` linha 14

---

## 🐛 Troubleshooting

### Erro ao extrair dados
**Problema**: db2cli.exe não encontrado
**Solução**: Verificar PATH do DB2 CLI no `config.yaml`

### Pipeline falha na etapa 9 (analyze_usage)
**Problema**: Falta arquivo `logintracking_*.csv`
**Solução**: Executar `extrair_logintrack.bat` primeiro

### Dashboard mostra "⚠️ Análise de uso pendente"
**Problema**: Phase 3 não foi executada
**Solução**: 
1. Executar `extrair_logintrack.bat`
2. Executar `processar_pipeline.bat`
3. Executar `gerar_relatorio.bat`

### Cards não atualizam ao filtrar
**Problema**: JavaScript desabilitado
**Solução**: Habilitar JavaScript no navegador

### LOCATION aparece como UNKNOWN
**Problema**: PersonGroupView não tem LocationSite para o usuário
**Solução**: Verificar se o usuário existe em consolidated_persongroupview.csv

---

## 📞 Suporte Técnico

Para dúvidas específicas sobre:
- **Identidades/Colisões**: Ver `identity_collisions_enriched.csv` campo `CONFLICT_REASON`
- **Baseline Funcional**: Ver seção 6 do dashboard HTML
- **Otimização Licenças**: Ver `license_optimization_recommendations.csv`
- **LocationSite**: Ver `consolidated_persongroupview.csv` coluna `locationsite`

**Documentação IBM Maximo**: 
- [MAS 9 Licensing Guide](https://www.ibm.com/docs/en/mas-cd/continuous-delivery?topic=administering-application-licenses)
- [AppPoints Calculator](https://www.ibm.com/docs/en/mas-cd/continuous-delivery?topic=licenses-apppoints)

---

## 🎨 Painel Operacional no HTML

O dashboard possui um painel superior com botões para download dos scripts .bat. Basta clicar com botão direito e "Salvar link como..." para baixar os scripts.

**Status exibido:**
- ✓ Pipeline configurado
- ✓ X identidades carregadas
- ✓ X análises de uso (ou ⚠️ se não executou Phase 3)

---

## ✨ Atualizações Recentes (Junho 2026)

### Correções Implementadas
1. **Parse de Data**: Suporte para formato `YYYY-MM-DD-HH.MM.SS` (LoginTracking)
2. **LocationSite**: Agora é source-of-truth para coluna LOCATION
3. **Consolidação LoginTracking**: Mescla automática de múltiplas fontes
4. **Classificação Onshore/Offshore**: Baseada em LocationSite
5. **Integração XLSX**: Script novo para atualizar dados no workbook

### Exemplo de Resultado
```
USERID: ALESSANDROCORREA
DISPLAYNAME: ALESSANDRO DE CARVALHO CORREA
LOCATION: N08 ✅ (do PersonGroupView)
OPERATIONAL_PRESENCE: OFFSHORE ✅
LOGIN_COUNT_90D: 1623
DAYS_SINCE_LAST: 15
USER_TIER: OFFSHORE_STD
```

---

**Última atualização**: Junho 2026  
**Versão**: 3.1 (Phase 3 + LocationSite Corrections)

