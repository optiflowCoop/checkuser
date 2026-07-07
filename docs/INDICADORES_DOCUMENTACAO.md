# Documentacao da Funcionalidade de Indicadores Mensais (Aba 9)

> Status: REMOVIDA do projeto CHECKUSER em 2026-07-07.
> Descontinuada porque o HTML do dashboard ficou complexo demais.
> A feature sera migrada para um projeto separado.

## 1. Visao Geral

Aba 9 exibia metricas operacionais do IBM Maximo agregadas por unidade (SITEID) e mes/ano.

Categorias: work_orders (Work Orders), moc (MOC), ptw (PTWs), loto (LOTO).
Unidades: ODN1, ODN2, N06, N08, N09, HTQ, POL, PGA, PGB, PGC, BASE.

## 2. Arquitetura / Fluxo de Dados

DB2 (MAXIMO)
  queries: workorder_indicadores, moc_indicadores, ptw_indicadores, loto_indicadores
  => output/raw/{ENV}_{tipo}_indicadores.txt  (run_db2cli_queries.py)
  => scripts/extract_indicadores.py
  => output/consolidated/consolidated_{tipo}_indicadores.csv  (SITEID, ANO, MES, TOTAL)
  => scripts/reporting/ab9_indicadores.py  (_load_indicadores_from_csv)
  => scripts/reporting/html_builder.py  (injeta 'indicadores_data')
  => scripts/reporting/html_template.py  (render_tab_indicadores)
  => Dashboard HTML (Aba 9)

## 3. Arquivos Envolvidos (originais)

- scripts/reporting/ab9_indicadores.py (render aba 9 HTML+JS e carga dos CSVs)
- scripts/extract_indicadores.py (extract DB2 -> CSV)
- scripts/generate_indicadores_report.py (orquestrador DB2->extract->risk report)
- verify_indicadores.py (debug dos CSVs)
- queries/queries.py (SQL das queries)
- config/config.json (lista workorder/moc/ptw/loto_indicadores)
- run_pipeline.py (passo 15 do pipeline)
- scripts/reporting/html_builder.py (injeta indicadores_data)
- scripts/reporting/html_template.py (botao da aba + render/scripts)
- scripts/debug_alexeikerkis.py (comentario sobre queries de indicadores)

## 4. Queries SQL (preservadas para migracao)

### workorder_indicadores
SELECT SITEID, COUNT(*) as TOTAL, YEAR(REPORTDATE) as ANO, MONTH(REPORTDATE) as MES
FROM WORKORDER
WHERE HISTORYFLAG = 0 AND ISTASK = 0 AND STATUS IN ('COMP','CLOSE','INPRG')
AND REPORTDATE BETWEEN TIMESTAMP('{data_inicio}') AND TIMESTAMP('{data_fim}')
GROUP BY SITEID, YEAR(REPORTDATE), MONTH(REPORTDATE) ORDER BY SITEID, ANO, MES

### moc_indicadores
SELECT SITEID, COUNT(*) as TOTAL, YEAR(REPORTDATE) as ANO, MONTH(REPORTDATE) as MES
FROM WORKORDER
WHERE WOCLASS = 'MOC' AND HISTORYFLAG = 0 AND STATUS IN ('COMP','CLOSE','INPRG')
AND REPORTDATE BETWEEN TIMESTAMP('{data_inicio}') AND TIMESTAMP('{data_fim}')
GROUP BY SITEID, YEAR(REPORTDATE), MONTH(REPORTDATE) ORDER BY SITEID, ANO, MES

### ptw_indicadores
SELECT SITEID, COUNT(*) as TOTAL, YEAR(CREATEDATE) as ANO, MONTH(CREATEDATE) as MES
FROM PLUSGPERMITWORK
WHERE HISTORYFLAG = 0 AND STATUS IN ('ISSUED','CLOSED','ISOLATION COMP','ISOLATION REMOVED')
AND CREATEDATE BETWEEN TIMESTAMP('{data_inicio}') AND TIMESTAMP('{data_fim}')
GROUP BY SITEID, YEAR(CREATEDATE), MONTH(CREATEDATE) ORDER BY SITEID, ANO, MES

### loto_indicadores
SELECT SITEID, COUNT(*) as TOTAL, YEAR(LCK07) as ANO, MONTH(LCK07) as MES
FROM LOCKOUT
WHERE LCK07 IS NOT NULL AND LCK07 BETWEEN TIMESTAMP('{data_inicio}') AND TIMESTAMP('{data_fim}')
GROUP BY SITEID, YEAR(LCK07), MONTH(LCK07) ORDER BY SITEID, ANO, MES


### Queries alternativas (variantes *_new / *_doc)
-- moc_doc_indicadores
SELECT COUNT(*) as TOTAL, SITEID FROM PLUSGMOC w
WHERE REPORTDATE >= TIMESTAMP('{data_inicio}') AND REPORTDATE < TIMESTAMP('{data_fim}')
AND PARENT IS NULL AND WONUM LIKE 'MOC-DOC%' GROUP BY SITEID

-- wo_indicadores
SELECT COUNT(*) as TOTAL, SITEID FROM WORKORDER w
WHERE REPORTDATE >= TIMESTAMP('{data_inicio}') AND REPORTDATE < TIMESTAMP('{data_fim}')
AND PARENT IS NULL AND WONUM NOT LIKE 'MOC-%' GROUP BY SITEID

-- ptw_indicadores_new
SELECT COUNT(*) as TOTAL, SITEID FROM PLUSGPERMITWORK p
WHERE CREATEDATE >= TIMESTAMP('{data_inicio}') AND CREATEDATE < TIMESTAMP('{data_fim}') GROUP BY SITEID

-- loto_indicadores_new
SELECT COUNT(*) as TOTAL, SITEID FROM PLUSGISOLATION p
WHERE CREATEDATE >= TIMESTAMP('{data_inicio}') AND CREATEDATE < TIMESTAMP('{data_fim}') GROUP BY SITEID

## 5. Formato dos CSVs Consolidados

Arquivo: output/consolidated/consolidated_{workorder|moc|ptw|loto}_indicadores.csv
Colunas: SITEID (unidade), ANO, MES (1-12), TOTAL (qtd de registros).


## 6. Comportamento da Aba 9 (HTML/JS)

- Seletor de Ano (botoes) e Mes (dropdown) via query params ?ano=&mes=&tab=indicadores.
- Cards de resumo rapido (acumulado Jan->mes) por categoria.
- Para cada categoria: Total Acumulado, Media Mensal, Mes Maior/Menor e tabela por unidade.
- Botoes de exportacao: exportIndicadoresExcel() (CSV) e exportIndicadoresPDF() (declarado, nao implementado).
- Graficos Chart.js estavam DESATIVADOS (apenas tabelas para uso offline).

## 7. Como executar (historico)

Pipeline completo: python run_pipeline.py
Apenas indicadores: python scripts/generate_indicadores_report.py --ano 2026 --mes-inicio 1 --mes-fim 6
Verificacao: python verify_indicadores.py

## 8. Notas de Remocao

1. scripts/reporting/ab9_indicadores.py - removido.
2. scripts/extract_indicadores.py - removido.
3. scripts/generate_indicadores_report.py - removido.
4. verify_indicadores.py - removido.
5. queries/queries.py - removidas queries *_indicadores e branch do resolve_query.
6. config/config.json - removidas 4 queries de indicadores da lista.
7. run_pipeline.py - removido o passo 15.
8. scripts/reporting/html_builder.py - removida injecao de indicadores_data.
9. scripts/reporting/html_template.py - removido import, botao da aba e chamadas de render.
10. scripts/debug_alexeikerkis.py - removido comentario sobre queries de indicadores.
