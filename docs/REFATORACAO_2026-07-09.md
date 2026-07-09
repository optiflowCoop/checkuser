# 🔧 CORREÇÃO CRÍTICA — MOTOR DE CÁLCULO DE APPPOINTS (ABA 3)

## Data: 2026-07-09
## Cientista de Dados: Auditoria completa a pedido do usuário

---

## 📋 RESUMO EXECUTIVO

O usuário reportou que os campos do Simulador de Cenários de AppPoints (Aba 3) apareciam **em branco em todos os cenários**. A investigação revelou que o problema não era só de interface: havia **4 bugs em cadeia** no motor de cálculo, e um deles — um erro de sintaxe real (`IndentationError`) em `src/true_capacity_calculator.py` — impedia esse script de **executar por completo há algum tempo**, deixando o cálculo estatístico de concorrência (NEM) sem dados válidos.

Depois de corrigidos os 4 bugs e regenerado o pipeline, o pico real de AppPoints (P100) passou a aparecer como **1.861 pontos** — valor mais alto do que o observado antes da correção (~970-990), porque antes o número exibido não incluía a reserva de licenças Authorized (871 pts) nem tinha o motor NEM funcionando de fato. Uma auditoria adicional (também a pedido do usuário) confirmou que a matemática corrigida está correta e não tem duplicidade de contagem — ver seção "Auditoria da Matemática" abaixo.

---

## 🎯 BUGS CORRIGIDOS

### 1️⃣ [CRÍTICO] `continue` mal posicionado exclui usuários BASE dos cenários Saneado/Otimizado

**Arquivo**: `scripts/reporting/html_data_processor.py` (função `process_app_points_analytics`, ~linha 70-84)

**Problema**: o `continue` que deveria pular **somente usuários inativos** estava dentro do `else` (ramo dos usuários BASE), de forma incondicional:

```python
# ANTES
if is_prem:
    scenarios_by_scope[scope_key]['asis']['pA' if is_auth else 'pC'] += 1
else:
    scenarios_by_scope[scope_key]['asis']['bA' if is_auth else 'bC'] += 1

    if rec.startswith('INATIVO'):
        inativos_count += 1
    # Inativo sai do saneado/otimizado, mas continua no As-Is.
    continue          # ← roda para TODO usuário BASE, ativo ou não
```

**Impacto**:
- Todo usuário BASE (ativo ou inativo) era excluído dos cenários Saneado e Otimizado — só entrava no As-Is. Por isso os campos "Base Auth" e "Base Conc" do simulador ficavam sempre zerados nesses dois cenários.
- Usuários PREMIUM inativos, ao contrário, **nunca** eram excluídos de Saneado/Otimizado (o `continue` só existia dentro do ramo BASE) — quando deveriam ser, pela mesma regra de negócio.

**Correção**: mover o `continue` para fora do `else`, condicionado apenas ao status de inatividade (aplica-se a PREMIUM e BASE igualmente):

```python
# DEPOIS
if is_prem:
    scenarios_by_scope[scope_key]['asis']['pA' if is_auth else 'pC'] += 1
else:
    scenarios_by_scope[scope_key]['asis']['bA' if is_auth else 'bC'] += 1

if rec.startswith('INATIVO'):
    inativos_count += 1
    # Inativo sai do saneado/otimizado, mas continua no As-Is.
    continue
```

---

### 2️⃣ [CRÍTICO] `IndentationError` real em `true_capacity_calculator.py` — o motor NEM nunca executava

**Arquivo**: `src/true_capacity_calculator.py`, função `main()`

**Problema A** (linha ~106) — código morto após `return`, dentro do bloco `if`:
```python
# ANTES
if not optimizations or not login_rows:
    print("❌ Dados insuficientes para cálculo de capacidade.")
    return

    golden = {}      # ← indentado como parte do "if", nunca executa
skipped_rows = 0
```
Mesmo que a indentação abaixo (Problema B) fosse corrigida isoladamente, este trecho geraria `NameError: name 'golden' is not defined` na primeira iteração do laço de otimizações.

**Problema B** (linha ~180) — bloco `if` sem corpo indentado, erro de sintaxe fatal:
```python
# ANTES
    max_dt = None
    for rec in login_rows:
        ...
        if dt and (max_dt is None or dt > max_dt):
            max_dt = dt

        if not max_dt:
        print("⚠ Nenhum login válido encontrado.")   # ← mesma indentação do "if", SyntaxError
        ...
        return
```
Isso é um `IndentationError` de verdade — o Python se recusa a interpretar o arquivo. **Qualquer execução deste script (direta ou via `run_pipeline.py`) falhava imediatamente**, e `true_capacity_metrics.json` nunca era (re)gerado. É por isso que esse arquivo aparecia como deletado (`D`) no `git status` no início desta investigação: ele existia numa versão antiga comitada, mas o código atual nunca conseguiu recriá-lo.

**Correção**: desindentar `golden = {}` para o nível da função; mover o `if not max_dt:` para fora do laço `for` (deve rodar uma vez, depois de percorrer todos os logins, não a cada iteração) e indentar corretamente seu corpo:

```python
# DEPOIS
if not optimizations or not login_rows:
    print("❌ Dados insuficientes para cálculo de capacidade.")
    return

golden = {}
skipped_rows = 0
...

    max_dt = None
    for rec in login_rows:
        ...
        if dt and (max_dt is None or dt > max_dt):
            max_dt = dt

    if not max_dt:
        print("⚠ Nenhum login válido encontrado.")
        ...
        return
```

**Correção acessória**: havia também um `print(f"✓ Loaded {len(golden)} ...")` indentado dentro do laço de otimizações (rodava uma vez por linha, poluindo o log com centenas de linhas repetidas). Movido para fora do laço, gerando um único resumo ao final.

---

### 3️⃣ [CRÍTICO] Chave `hourly_app_points_nem_by_scope` descartada ao montar `concurrency_summary`

**Arquivo**: `scripts/generate_risk_report.py` (~linha 824-835)

**Problema**: mesmo com o motor NEM funcionando (bug 2 corrigido), o dicionário `concurrency_summary` — que alimenta o dashboard — **não copiava** a chave `hourly_app_points_nem_by_scope` do JSON gerado por `true_capacity_calculator.py`:

```python
# ANTES
concurrency_summary = {
    'hourly_counts': metrics.get('hourly_counts', {}),
    'hourly_app_points': metrics.get('hourly_app_points', {}),
    'hourly_concurrent_app_points': metrics.get('hourly_concurrent_app_points', {}),
    'hourly_app_points_nem': metrics.get('hourly_app_points_nem', {}),
    # 'hourly_app_points_nem_by_scope' ausente
    ...
}
```

**Impacto**: sem essa chave, `html_data_processor.py` nunca encontrava a série horária por escopo (FORESEA/TERCEIROS/INTEGRAÇÃO/TODOS) e caía num fallback de "soma física simples" — o mesmo número aparecia para P50, P95, P100 e Blackout em cada escopo, perdendo toda a diferenciação estatística que é a razão de existir do cálculo NEM.

**Correção**:
```python
# DEPOIS
concurrency_summary = {
    ...
    'hourly_app_points_nem': metrics.get('hourly_app_points_nem', {}),
    'hourly_app_points_nem_by_scope': metrics.get('hourly_app_points_nem_by_scope', {}),
    ...
}
```

Adicionalmente, `scripts/reporting/html_data_processor.py` foi ajustado para incluir `'todos'` na lista de escopos cobertos pelo fallback defensivo de composição física (antes só `foresea`/`terceiros`/`integracao` estavam cobertos; `todos` podia ficar zerado indevidamente se a série global falhasse mas a por-escopo funcionasse).

---

### 4️⃣ [AMBIENTE] Pipeline aborta silenciosamente por `UnicodeEncodeError` (emoji no console Windows)

**Arquivos afetados**: `scripts/generate_logintrack_from_sources.py`, `scripts/generate_risk_report.py` (`write_license_decision_plan`), e ao menos outros 8 scripts do pipeline que imprimem emojis (🔄, ✅, ✓, ⚠, etc.)

**Problema**: o console padrão do Windows usa a codepage `cp1252`, que não sabe representar a maioria dos emojis usados nos `print()` do pipeline. Quando um desses `print()` executa, o processo é abortado com `UnicodeEncodeError` — e como `run_pipeline.py` usa `subprocess.run(..., check=True)`, esse erro interrompe a etapa e, dependendo de quando ocorre, deixa arquivos consolidados **parcialmente escritos ou desatualizados** sem aviso claro ao usuário.

**Evidência concreta encontrada nesta investigação**: `consolidated_logintracking_from_sources.csv` estava com **100% dos usuários sem USERID e ambiente preenchidos** (arquivo corrompido/vazio), fazendo com que **todo usuário fosse classificado como INATIVO** (`login_count == 0` para todos) — o que, combinado com o bug 1, zerava os cenários Saneado/Otimizado por completo, mesmo antes de qualquer problema de concorrência.

**Correção aplicada nesta sessão**: regeneração manual dos artefatos executando os scripts com `PYTHONIOENCODING=utf-8` (contorna o crash sem alterar código). **Não foi implementada uma correção definitiva no código** — recomenda-se, como próximo passo, uma das opções:
- Definir `env['PYTHONUTF8'] = '1'` ao spawnar subprocessos em `run_pipeline.py`, ou
- Adicionar `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` no topo de cada script de entrada do pipeline.

---

## 🔬 AUDITORIA DA MATEMÁTICA (a pedido do usuário)

Depois de corrigir os 4 bugs, o usuário questionou diretamente se os novos números (pico subindo de ~990 para 1.861) estavam corretos, e se a simulação considera login, tempo de login, quantidade de login, criticidade de cargo e rotação de turma em plataformas offshore. Verificação feita com dados reais:

| Item verificado | Resultado |
|---|---|
| Duplicidade de pessoa (mesmo humano, USERIDs diferentes) | Não encontrada em escala relevante — `license_decision_plan.csv` tem 1.368 linhas para 1.244 nomes distintos + 125 sem nome + 1 coincidência, consistente com 1 linha por pessoa. |
| Contas de serviço/integração (WSORACLE: 275.444 logins/90d; ITEAM: 2.728; MAXADMIN: 969) | Classificadas corretamente como AUTHORIZED, isoladas no escopo INTEGRAÇÃO (WSORACLE) ou FORESEA (ITEAM/MAXADMIN); impacto total de 15 pts em 1.861 (~0,8%) — não é a causa do aumento do pico. |
| Duplicidade AUTHORIZED × CONCURRENT no cálculo horário | Confirmado no código que usuários AUTHORIZED nunca somam no pool concorrente (já estão na reserva fixa `authorized_reserved`) — sem contagem dupla. |
| Quantidade/frequência de login | Usada nos limiares de classificação (`>60 logins/90d` → Authorized; `<30` → candidato a Concurrent; `==0` → Inativo) em `scripts/services/app_points.py`. |
| Criticidade de cargo | Usada via lista de títulos críticos (`SUPERVISOR`, `COORDENADOR`, `GERENTE`, `LIDER`, `ENCARREGADO`, `ALMOXARIFE`) e grupo `MAXADMIN`. |
| Rotação de turma offshore (plataformas com turma em casa/trabalhando) | **Não modelada por calendário de escala explícito**, mas capturada implicitamente: o pico é calculado a partir de logins reais hora a hora, então quem está de folga simplesmente não aparece logado. Ponto forte do modelo (mede uso real, não headcount teórico). |
| Duração/tempo de login ("tempo de login") | **Limitação real, não corrigível com os dados disponíveis**: o log só tem evento de "LOGIN", sem "LOGOUT". O código assume sessão fixa de `SESSION_MINUTES = 60`. Teste com os dados reais mostrou que 75% dos intervalos entre logins consecutivos do mesmo usuário são ≤60min, mas ~20% passam de 2h — nesses casos a pessoa pode "desaparecer" da contagem de concorrência mesmo se ainda estiver trabalhando. |

**Explicação do salto numérico**: no pico histórico (2026-05-27, 07:00, 217 usuários simultâneos), o total de 1.861 se divide em **871 pts de reserva Authorized** (fixa, toda hora) + **990 pts do pool Concurrent** só naquela hora. O número antigo (~970-990) citado pelo usuário coincide quase exatamente com a parte do pool Concurrent — indício forte de que o cálculo anterior (quando ainda funcionava, antes do bug do `IndentationError` aparecer) já vinha sem somar a reserva Authorized, ou vinha de uma versão de dados diferente. Não é uma inflação artificial introduzida pela correção — é a conta completa aparecendo pela primeira vez.

---

## 📊 IMPACTO NOS NÚMEROS EXIBIDOS (escopo TODOS)

| Métrica | Antes da correção (dados quebrados) | Depois da correção |
|---|---|---|
| Base Auth / Base Conc nos cenários Saneado/Otimizado | 0 (sempre) | Populados corretamente (ex.: FORESEA otimizado: bA=1, bC=7) |
| `true_capacity_metrics.json` | Ausente/deletado (motor não executava) | Gerado com sucesso |
| P50 / P95 / P100 por escopo | Idênticos entre si (fallback de soma física) | Diferenciados estatisticamente (ex. FORESEA: 1.195 / 1.478 / 1.673) |
| P100 global | Indefinido / ~970-990 (parcial, sem reserva Authorized) | **1.861** (completo) |
| Status vs. teto de 1.200 | Aparentava estar dentro do teto | **Excede o teto em 55% (P100) / 32% (P95)** |

---

## 🚀 PRÓXIMOS PASSOS RECOMENDADOS

### Prioridade ALTA
1. ⏳ Corrigir de forma definitiva o crash de encoding no pipeline (ver bug 4) — hoje qualquer execução via `run_pipeline.py` no Windows sem `PYTHONIOENCODING=utf-8` corre o risco de voltar a corromper os dados de login silenciosamente.
2. ⏳ Validar com a área de negócio se o teto contratual de 1.200 AppPoints precisa ser renegociado, dado que o uso real (P95/P100) agora mede acima do teto.
3. ⏳ Adicionar teste automatizado que rode `python -m py_compile src/true_capacity_calculator.py` (ou equivalente) no CI, para nunca mais deixar um `IndentationError` chegar sem ser notado em um script crítico do pipeline.

### Prioridade MÉDIA
4. ⏳ Avaliar se `SESSION_MINUTES = 60` é a melhor aproximação para duração de sessão, ou se vale a pena investigar se existe algum evento de "LOGOUT"/timeout de sessão real em algum outro extrato do Maximo.
5. ⏳ Decidir formalmente a definição de "Blackout" (hoje idêntico a P100 no código, mas descrito como "P100 × 2" na documentação anterior) — implementar o multiplicador se essa for a intenção de negócio.

---

## 📁 ARQUIVOS MODIFICADOS NESTA SESSÃO

| Arquivo | Mudança |
|---|---|
| `scripts/reporting/html_data_processor.py` | Bug 1 (continue mal posicionado) + inclusão de `'todos'` no fallback defensivo |
| `src/true_capacity_calculator.py` | Bug 2 (IndentationError + código morto + print dentro do laço) |
| `scripts/generate_risk_report.py` | Bug 3 (chave `hourly_app_points_nem_by_scope` ausente) |
| `docs/SUMARIO_EXECUTIVO_ABA3.md` | Registro da investigação e valores atualizados |
| `docs/CALCULO_APPPOINTS_EXPLICACAO.md` | Exemplos numéricos e conclusões atualizados |
| `docs/SISTEMA_DOCUMENTACAO.md` | Changelog e seção de limitações conhecidas |
| `docs/REFATORACAO_2026-07-09.md` | **Este documento** (novo) |

---

## 👥 AUTORIA

**Investigação e correção**: Sessão de auditoria a pedido do usuário (Eduardo Bosco, Foresea), disparada pelo sintoma "os campos continuam em branco em todos os cenários".
**Data**: 2026-07-09
