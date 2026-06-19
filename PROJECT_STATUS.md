# Maximo Consolidation Project

## Identidade, Acessos, Licenciamento e Preparação para MAS 9

**Atualizado em:** 2026-06-18  
**Versão:** MVP 2.0 - Saneamento e Governança de Acessos  
**Status Oficial:** Etapa 1 (Descoberta e Ambiguidade) Concluída Tecnicamente; Etapa 2 (Padronização de Baseline) Iniciada.

---

# 1. Estrutura de Fases do Projeto

Após o alinhamento com a arquitetura de negócios para o MAS 9, o roadmap do projeto foi oficialmente estruturado nas seguintes etapas progressivas:

* **✅ Etapa 1 — Identity Discovery & Ambiguity Detection:** Mapeamento do reuso de logins (USERID), detecção de clones humanos, e separação segura da massa histórica x ativa.
* **🟡 Etapa 2 — Padronização / Baseline:** Identificação de perfis funcionais (TYPE), grupos discrepantes entre unidades e harmonização de regras.
* **⏳ Etapa 3 — AppPoints & Licenciamento:** Avaliação da bilhetagem MAS 9 focada APENAS em Identidades Únicas ATIVAS.
* **⏳ Etapa 4 — Validação AD (Active Directory):** Bate-estaca final para importação dos usuários e unificação de SSO, utilizando a Fila de `AWAITING_AD_MATCH`.

---

# 2. Fechamento Formal: Etapa 1 (Identity Discovery)

A **Etapa 1 foi concluída tecnicamente**. O objetivo de descobrir o tamanho real do passivo e bloquear unificações cegas do sistema legado foi atingido.

**Critérios de Aceite Alcançados na Etapa 1:**
- [x] Todo `USERID` repetido entre bases foi classificado em uma hipótese de risco cruzando Dados Humanos (Tabela `PERSON` e `EMAIL`).
- [x] Todos os casos críticos (Ex: mesmo Login com nomes diferentes) foram "congelados" sob a tag opercional `DO_NOT_MERGE` ou `MANUAL_REVIEW_REQUIRED`.
- [x] A Fila Operacional de Saneamento (`identity_collisions_enriched.csv`) foi gerada e está pronta para revisão manual.
- [x] A massa ATIVA foi isolada e quantificada separadamente da massa inativa/legada em todo o Dashboard e lógicas de conflito.

**Declaração de Status para a Gestão:**
> "Já conseguimos levantar os usuários, identificar ambiguidades biológicas e mapear o reuso de logins entre as sondas com segurança técnica estruturada, impedindo merges indevidos de sistema. A Fila de Saneamento está montada. A fase de tratamento humano começa agora, enquanto a engenharia avança para a Padronização (Etapa 2)."

---

# 3. Escopo Atual: Etapa 2 (Padronização / Baseline)

Com as ambiguidades engavetadas para tratamento, a aplicação entra em sua **Fase 2**, voltada a investigar:
1. **O que deveria ser igual entre as unidades?** (Ex: Todos os apontadores deveriam ter os mesmos grupos de permissão).
2. **O que está fora do padrão?** (Ex: Almoxarife da N08 possuindo acesso a Contratos, e o da N09 não).
3. **Quais contas técnicas estão se misturando com acessos humanos?**

### Artefatos da Fase 2
O projeto já conta com o relatório de `Baseline Divergences` que calcula a Intersecção de Grupos vs Adições Locais.

**Backlog Operacional Fase 2:**
- Refinar/Harmonizar as permissões (Grupos de Segurança) baseadas na função cruzada que a aplicação aponta.
- Gerar export `baseline_standardization_candidates.csv` caso um refinamento mais complexo da trilha funcional (`TYPE`) seja requerido.
- Adequar perfis antes de bater o snapshot final de Capacity (AppPoints).

---

# 4. Estrutura Canônica de Decisão e Hipóteses (Regra de Ouro)

O pipeline foi cristalizado na seguinte premissa:
> **"Qualquer USERID repetido em ambientes diferentes NÃO é automaticamente considerado a mesma pessoa física."**

### Decisões de Saneamento Emitidas pela App (`MERGE_DECISION`)
* **`DO_NOT_MERGE`**: Decisão dura contra a automação MAS 9. (Nomes ou E-mails Diferentes no mesmo Login).
* **`MANUAL_REVIEW_REQUIRED`**: Necessita decisão humana (Inconsistência de status, tipos de conta conflitantes).
* **`AWAITING_AD_MATCH`**: Hipótese perfeita no Maximo, pendente prova final de AD.

---

# 5. O Pipeline de Motor de Dados

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

## 5.1 Relatórios Oficiais de Governança
Toda a auditoria (Saneamento e Baseline) pode ser visualizada pelos stakeholders via:
* `output/reports/maximo_identity_sanity_report.html` (Dashboard Gerencial)
* `output/reports/maximo_identity_sanity_workbook.xlsx` (Worklist do Time Técnico)