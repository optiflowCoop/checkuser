# Maximo Consolidation Project

## Identidade, Acessos, Licenciamento e Preparação para MAS 9

**Atualizado em:** 2026-06-18  
**Versão:** MVP 2.0 - Saneamento e Governança de Acessos  
**Status Oficial:** Etapa 1 (Descoberta e Ambiguidade) Concluída Tecnicamente; Etapa 2 (Padronização de Baseline) Iniciada.

---

# 1. Fase Atual do Projeto: Etapa 2 - Padronização e Baseline

O projeto virou a página da Descoberta Básica e agora foca na governança profunda dos acessos, pavimentando o terreno final antes de contar licenciamento (AppPoints) ou acionar integrações de domínio (Active Directory).

O roadmap atualizado em andamento segue a estrutura:
* **✅ Etapa 1 — Identity Discovery & Ambiguity Detection:** Concluída. A fila de saneamento foi gerada, logins repetidos mapeados e regras severas anti-merge foram implementadas (exigindo dados como Nome e Email cruzados com a tabela `PERSON`).
* **🟡 Etapa 2 — Padronização / Baseline:** EM ANDAMENTO. Foco nas divergências funcionais de acesso. Respondendo à pergunta: *Quais perfis/grupos fogem do padrão corporativo em uma unidade específica?*
* **⏳ Etapa 3 — AppPoints & Licenciamento:** (Futuro) Avaliação financeira das identidades úteis.
* **⏳ Etapa 4 — Validação AD (Active Directory):** (Futuro) O crivo final do SSO para unificação no MAS 9.

---

# 2. Princípio Central de Identidade (A Regra de Ouro)

O sistema de motor de dados foi travado para obedecer, via código, à premissa:

> **O mesmo login (`USERID`) encontrado em bases diferentes NÃO prova tratar-se da mesma pessoa física.**

A chave técnica imutável continua sendo: `RAW_ID = ENV_DB + "|" + USERID`

Qualquer reuso de identidade cross-env requer **Dados Humanos** extraídos da tabela `PERSON` para validar uma correlação (atribuindo a classificação `AWAITING_AD_MATCH`), ou barrar o merge definitivamente (classificando a conta como `DO_NOT_MERGE` quando nomes/emails divergirem).

---

# 3. O Que A Aplicação Já Faz

* O pipeline cruza tabelas vitais para rastreio biológico de sistema: `MAXUSER`, `PERSON`, `EMAIL` e `GROUPUSER`.
* Gera uma **Sanitation Worklist (Fila de Saneamento)** contendo a matriz exata do que deve ser revisado por um humano e o que aguarda integração externa.
* Avalia e exibe um **Diff de Baseline de Perfis**, calculando intersecções matemáticas dos grupos de segurança atribuídos por "Função" (`TYPE`) e expondo os excessos/desvios de cada Unidade (Ex: O Almoxarife que tem permissões a mais na unidade B).
* Classifica tipos de contas com regras nativas via regex (`HUMAN`, `TECHNICAL`, `MOBILE`, `TEST`, etc).
* Foca 100% dos alertas de Colisão de Nomes, Reuso de Login e Capacidade de AppPoints nas **Contas Ativas**, separando o passivo morto histórico.

---

# 4. Pipeline e Comandos

O motor opera de forma blindada com 9 etapas autônomas. Para processar do começo ao fim (gerando Dashboard Dinâmico em HTML e Planilhas Gerenciais):

```powershell
python run_pipeline.py
```

*Nota para testes ágeis de visualização (Pular lentidão do DB2)*: `python run_pipeline.py --skip-extract`

## 4.1 Arquivos e Relatórios Gerados
Toda a auditoria visualiza-se na pasta `output/reports/`:
* `maximo_identity_sanity_report.html` (Dashboard Visual)
* `maximo_identity_sanity_workbook.xlsx` (Para Time Técnico e Resolução da Worklist de `DO_NOT_MERGE`)