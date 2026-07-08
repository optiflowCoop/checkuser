# Evolução Aba 2 (Governança) + Aba 8 (Migração) — Saneamento de Alocação (Maximo 9)

## Data: 2026-07-07

## Objetivo

Evoluir o dashboard e o relatório Excel para incluir **histórico de logins dos últimos 90 dias por ambiente** e **sugestão de onde criar a conta do usuário** no Maximo 9, considerando:

- Usuários **ativos e inativos** (todos os registros do `consolidated_user_identity.csv`)
- Alocação real (locationsite do persongroupview > DEFSITE > ENV_DB)
- Ambiente principal de uso (maior volume de logins nos últimos 90d)
- Ambientes secundários (>= 5 acessos nos últimos 90d)
- Sugestão de contas a criar (alocação + secundários)

## O que foi alterado

### 1. Novo módulo: `scripts/domain/allocation_analyzer.py`

Analisa para cada USERID único:
- `allocation_primary`: local de alocação (locationsite > DEFSITE > ENV_DB)
- `env_counts`: dicionário {ambiente: total_logins_90d}
- `primary_env`: ambiente com maior volume de logins
- `secondary_envs`: ambientes com >= 5 acessos (diferentes da alocação)
- `suggested_accounts`: lista de ambientes onde criar a conta
- `reason`: texto explicativo da sugestão

**Regra de negócio**: ambiente secundário exige **>= 5 acessos** nos últimos 90 dias.

### 2. Orquestrador: `scripts/generate_risk_report.py`

- Importa `analyze_allocation` do novo módulo
- Executa a análise na etapa 7c (após sanity e migration)
- Passa `allocation_data` para o HTML builder e Excel writer
- Adiciona abas 21 (Resumo) e 22 (Detalhamento) no Excel

### 3. HTML Builder: `scripts/reporting/html_builder.py`

- Parâmetro `allocation_data` adicionado à função `build_html_structure`
- Dados injetados no `processed_data` para renderização

### 4. Template HTML: `scripts/reporting/html_template.py`

- Importa `render_allocation_summary` de `ab2_governanca`
- Importa `render_allocation_detail` de `ab8_migracao`
- Renderiza o resumo na Aba 2 (Governança) e o detalhamento na Aba 8 (Migração)

### 5. Aba 2 (Governança): `scripts/reporting/ab2_governanca.py`

- Nova função `render_allocation_summary()`: cards com estatísticas (total usuários, com login, inativos, multi-ambiente, contas sugeridas, min. acessos)

### 6. Aba 8 (Migração): `scripts/reporting/ab8_migracao.py`

- Assinatura de `render_tab_migracao` atualizada para aceitar `allocation_data`
- Nova função `render_allocation_detail()`: tabela completa com USERID, Nome, Status, Logins 90d, Alocação, Uso Principal, Secundários, Sugestão, Contas Sugeridas, Motivo
- Filtro por texto e exportação CSV

### 7. Excel: `scripts/generate_risk_report.py`

- `add_allocation_sheets()`: cria abas 21 (Resumo) e 22 (Detalhamento)
- Aba 21: métricas agregadas
- Aba 22: 9839 linhas com USERID, NOME, STATUS, EMAIL, ALOCACAO_PRINCIPAL, AMBIENTE_PRINCIPAL_USO, LOGINS_90D, ULTIMO_LOGIN, AMBIENTES_SECUNDARIOS, CONTAS_SUGERIDAS, HISTORICO_90D, MOTIVO

## Impacto no cálculo de AppPoints

**NENHUM.** A análise de alocação é puramente informativa e não altera:
- O cálculo de AppPoints (fatores, cenários)
- A classificação de licenças (Authorized/Concurrent)
- As recomendações de otimização
- O license_decision_plan.csv

## Resultados (dados atuais)

| Métrica | Valor |
|---------|-------|
| Usuários analisados | 9.839 |
| Com login nos últimos 90d | 1.901 |
| Inativos (no Maximo) | 5.660 |
| Multi-ambiente (conta em >1 unidade) | 108 |
| Total de contas sugeridas | 10.002 |
| Limite mín. p/ ambiente secundário | 5 acessos |
| Janela de análise | 2026-03-27 a 2026-06-25 |

## Exemplo de sugestão

**ITEAM** (alocado em POL): acessou N09 (321), N08 (320), N06 (312), ODN1 (293), HTQ (283), ODN2 (274) nos últimos 90d. Sugestão: criar conta em POL + N09 + N08 + N06 + ODN1 + HTQ + ODN2.

**SILVERIOMAIA** (alocado em N08): acessou apenas N08 (601). Sugestão: criar conta apenas em N08.

## Arquivos modificados

| Arquivo | Tipo |
|---------|------|
| `scripts/domain/allocation_analyzer.py` | **NOVO** |
| `scripts/generate_risk_report.py` | Modificado |
| `scripts/reporting/html_builder.py` | Modificado |
| `scripts/reporting/html_template.py` | Modificado |
| `scripts/reporting/ab2_governanca.py` | Modificado |
| `scripts/reporting/ab8_migracao.py` | Modificado |
</write_to_file>