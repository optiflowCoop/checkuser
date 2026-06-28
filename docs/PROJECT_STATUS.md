# Maximo Consolidation Project

## Identidade, Acessos, Licenciamento e Preparação para MAS 9

**Atualizado em:** 2026-06-25  
**Versão:** 3.1 - Phase 3 + LocationSite Corrections  
**Status Oficial:** Etapa 1-3 Concluídas; Etapa 3 com correções de LocationSite e Consolidação de LoginTracking implementadas.

---

# 1. Estrutura de Fases do Projeto

Após o alinhamento com a arquitetura de negócios para o MAS 9, o roadmap do projeto foi oficialmente estruturado nas seguintes etapas progressivas:

*   **✅ Etapa 1 — Identity Discovery & Ambiguity Detection:** Mapeamento do reuso de logins (USERID), detecção de clones humanos, e separação segura da massa histórica x ativa.
*   **✅ Etapa 2 — Padronização / Baseline:** Identificação de perfis funcionais (PERSONGROUP), grupos discrepantes entre unidades e harmonização de regras.
*   **✅ Etapa 3 — AppPoints & Licenciamento:** Avaliação da bilhetagem MAS 9 focada APENAS em Identidades Únicas ATIVAS com LocationSite correto.
*   **✅ Etapa 3.1 — Correções de Dados:** LocationSite como source-of-truth, consolidação de LoginTracking múltiplas fontes, classificação Onshore/Offshore corrigida.
*   **⏳ Etapa 4 — Validação AD (Active Directory):** Bate-estaca final para importação dos usuários e unificação de SSO, utilizando a Fila de `AWAITING_AD_MATCH`.

---

# 2. Fechamento Formal: Etapa 1 (Identity Discovery)

A **Etapa 1 foi concluída tecnicamente**. O objetivo de descobrir o tamanho real do passivo e bloquear unificações cegas do sistema legado foi atingido.

**Critérios de Aceite Alcançados na Etapa 1:**
- [x] Todo `USERID` repetido entre bases foi classificado em uma hipótese de risco cruzando Dados Humanos (Tabela `PERSON` e `EMAIL`).
- [x] Todos os casos críticos de "Mesmo login, pessoa diferente" ficaram cravados em `DO_NOT_MERGE` ou `MANUAL_REVIEW_REQUIRED`.
- [x] A fila operacional de saneamento (`identity_collisions_enriched.csv`) foi gerada e está pronta para revisão manual.
- [x] A massa ATIVA foi isolada e quantificada separadamente da massa inativa/legada em todo o Dashboard e lógicas de conflito.
- [x] As tabelas `PERSON` e `EMAIL` já estão incorporadas como fonte humana obrigatória para cruzar com `MAXUSER`.

**Declaração de Status para a Gestão:**
> "Já conseguimos levantar os usuários, identificar ambiguidades biológicas e mapear o reuso de logins entre as sondas com segurança técnica estruturada, impedindo merges indevidos de sistema. A Fila de Saneamento está montada. A fase de tratamento humano começa agora, enquanto a engenharia avança para a Padronização (Etapa 2)."

---

# 3. Fechamento Formal: Etapa 2 (Padronização / Baseline)

A **Etapa 2 foi concluída tecnicamente**. O objetivo de identificar e visualizar as discrepâncias de acesso entre unidades para um mesmo perfil funcional foi atingido.

**Critérios de Aceite Alcançados na Etapa 2:**
- [x] A `PERSONGROUPVIEW` foi incorporada para enriquecer os dados de usuário com `TITLE` e `PERSONGROUP`.
- [x] O Dashboard HTML e o Excel agora exibem `TITLE` e `PERSONGROUP` nas tabelas de detalhe.
- [x] A seção "Auditoria de Perfis" no Dashboard HTML e a aba "9_BaselineDivergences" no Excel foram redesenhadas para:
    - Agrupar a análise por `PERSONGROUP` (Grupo de Pessoas), que representa o perfil funcional real.
    - Visualizar claramente o "Padrão Comum" (grupos de segurança presentes em todas as unidades para aquele `PERSONGROUP`).
    - Destacar as "Divergências" (grupos de segurança extras adicionados localmente por unidade).
    - Apresentar a análise de forma intuitiva com "badges" (pílulas visuais) e layout responsivo, eliminando o scroll horizontal.
- [x] O relatório agora responde à pergunta de negócio: "Por que um Almoxarife na N08 tem 10 grupos de acesso e na N09 tem apenas 4?", fornecendo a base para a otimização de acessos e AppPoints.
- [x] A tabela de "Auditoria de Perfis" no HTML não é mais afetada pelos filtros globais, garantindo que a análise de baseline seja sempre completa.

**Declaração de Status para a Gestão:**
> "A fase de Padronização de Perfis foi concluída tecnicamente. Agora temos uma visão clara das divergências de acesso entre as unidades para um mesmo perfil funcional (PERSONGROUP), permitindo identificar e otimizar os grupos de segurança. A ferramenta está pronta para suportar a harmonização de acessos e a preparação para a otimização de AppPoints."

---

# 4. Conclusão: Etapa 3 (AppPoints / Licenciamento) + Correções 3.1

Com as identidades limpas, confiáveis e cravadas como "Logins Únicos", e o baseline de acessos mapeado, a aplicação **concluiu a Etapa 3 com sucesso** e implementou as **Correções 3.1**.

### Objetivo alcançado
Medir o *footprint* de licenciamento e direcionar a precificação / *capacity plan* do MAS 9, focando APENAS em Identidades Únicas ATIVAS.

### Correções Implementadas (Etapa 3.1):

#### 1. LocationSite como Source-of-Truth
- [x] PersonGroupView.LocationSite é agora a fonte oficial para LOCATION
- [x] Coluna LOCATION preenchida corretamente (N08, ODN1, etc.)
- [x] 768 registros atualizados no XLSX com dados corretos

#### 2. Consolidação de LoginTracking
- [x] Consolidação automática de múltiplas fontes:
  - consolidated_logintracking.csv (356.705 registros)
  - DadosTabelas/LOGINTRACKING_*.csv (16.414 registros)
- [x] Total: 373.123 registros de LoginTracking

#### 3. Classificação Onshore/Offshore
- [x] Baseada em LocationSite (não mais palavras-chave genéricas)
- [x] ONSHORE: base-unp, og-base, macae
- [x] OFFSHORE: N06, N08, N09, ODN1, ODN2

#### 4. Parse de Data Corrigido
- [x] Suporte para formato: YYYY-MM-DD-HH.MM.SS
- [x] Cálculo correto de DAYS_SINCE_LAST
- [x] ALESSANDRO: 15 dias (antes 999)

### Backlog Operacional Fase 4:
- [ ] Validação AD (Active Directory)
- [ ] Importação de usuários no MAS 9
- [ ] Unificação de SSO baseada em `AWAITING_AD_MATCH`

---

# 5. Estrutura Canônica de Decisão e Hipóteses (Regra de Ouro)

O pipeline foi cristalizado na seguinte premissa:
> **"Qualquer USERID repetido em ambientes diferentes NÃO é automaticamente considerado a mesma pessoa física."**

### Decisões de Saneamento Emitidas pela App (`MERGE_DECISION`)
*   **`DO_NOT_MERGE`**: Decisão dura contra a automação MAS 9. (Nomes ou E-mails Diferentes no mesmo Login).
*   **`MANUAL_REVIEW_REQUIRED`**: Necessita decisão humana (Inconsistência de status, tipos de conta conflitantes).
*   **`AWAITING_AD_MATCH`**: Hipótese perfeita no Maximo, pendente prova final de AD.

---

# 6. O Pipeline de Motor de Dados

O motor opera por linha de comando em ambiente restrito, orquestrado pelo `run_pipeline.py`.

```text
1. scripts/run_db2cli_queries.py
2. scripts/consolidate_outputs.py
3. src/consolidate_user_access.py
4. src/normalize.py
5. src/cross_env_userid_reuse.py
6. src/login_conflicts.py
7. src/identity_classification.py
8. src/consolidate_license_footprint.py
9. scripts/generate_risk_report.py
```

## 6.1 Relatórios Oficiais de Governança
Toda a auditoria (Saneamento e Baseline) pode ser visualizada pelos stakeholders via:
*   `output/reports/maximo_identity_sanity_report.html` (Dashboard Gerencial)
*   `output/reports/maximo_identity_sanity_workbook.xlsx` (Worklist do Time Técnico)