# Regras de Negócio: AppPoints e Definição de Licenças

**Última atualização**: 2026-07-09
**Público-alvo**: qualquer pessoa que precise entender ou auditar *por que* um usuário específico recebeu um determinado custo de licença, sem precisar ler o código-fonte.

Este documento é a referência única e definitiva das regras de negócio. Se o código mudar, este documento deve ser atualizado no mesmo commit — ele descreve o comportamento real do sistema em 2026-07-09, não uma aspiração.

---

## 1. O que é um AppPoint

**AppPoint** é a unidade de consumo de licença do IBM Maximo 9.1 usada no contrato da Foresea. Cada usuário custa uma quantidade fixa de AppPoints por licença, definida pela combinação de dois eixos independentes:

| Eixo | O que significa | Valores possíveis |
|---|---|---|
| **Entitlement** | Quais módulos do Maximo o usuário pode acessar | `PREMIUM`, `BASE`, `LIMITED`, `SELF FREE` |
| **Modelo de Licença** | Como a licença é reservada | `AUTHORIZED` (dedicada) ou `CONCURRENT` (compartilhada/pool) |

### Tabela canônica de custo (fonte única: `scripts/config.py::get_app_points_config()`)

| Entitlement | Authorized | Concurrent |
|---|---|---|
| PREMIUM | **5** | **15** |
| BASE | **3** | **10** |
| LIMITED | 2 | 5 |
| SELF FREE | 0 | 0 |

**Regra de governança**: nenhum outro módulo do sistema pode recalcular esses valores localmente. Todo custo exibido em HTML, Excel, CSV e no motor NEM deve vir de `scripts/analysis/entitlement.py::calculate_app_points()`, que apenas consulta esta tabela.

> Nota histórica: o valor de BASE/AUTHORIZED já foi erroneamente configurado como 2 (deveria ser 3) — corrigido em 2026-07-01 (ver `docs/REFATORACAO_2026-07-01.md`). Se esse valor divergir de 3 no futuro, é uma regressão, não uma correção.

---

## 2. Como o Entitlement (PREMIUM/BASE/LIMITED) é determinado

**Módulo**: `scripts/analysis/entitlement.py::determine_user_entitlement(user_groups)`

Regra do **"nível mais alto"**: percorre os grupos de segurança do usuário no Maximo e verifica palavras-chave, na ordem PREMIUM → BASE → LIMITED (do mais caro para o mais barato). O primeiro nível cujo padrão bate em qualquer grupo do usuário é o entitlement final — mesmo que o usuário também tenha grupos de nível mais barato.

| Entitlement | Palavras-chave nos nomes dos grupos |
|---|---|
| **PREMIUM** | `O&G`, `HSE`, `DRILLING`, `OIL` |
| **BASE** | `WOTRACK`, `ASSET`, `SCHEDULER`, `PLANNING`, `JOBPLAN` |
| **LIMITED** | `INVENTORY`, `PO`, `RECEIVING`, `SR`, `REQUEST` |
| **SELF FREE** | (nenhuma palavra-chave bateu) |

Fonte: `scripts/config.py::get_entitlement_keywords()`.

### 2.1 Regra especial: acesso O&G via grupos protege contra downgrade indevido

Além dessas palavras-chave básicas, existe uma lista mais ampla de padrões de grupo que indicam acesso a operações críticas de Oil & Gas (`scripts/config.py::get_og_group_keywords()`): `OG_`, `OOG_`, `OOG_PTW_ISSUER`, `O&G`, `OILGAS`, `PETROLEUM`, `PETRO`, `HSE`, `DRILLING`, `DRILL`, `RIG`, `FPSO`, `PFWORK`, `LOCREC`, `COMPLIANCE`, `WELL`.

Essa lista é usada especificamente para **impedir um downgrade incorreto** de usuários PREMIUM com baixo uso (ver regra 4.3 abaixo) — um usuário com pouquíssimos logins mas que pertence a um grupo O&G **não** é rebaixado para BASE, porque a criticidade operacional do acesso (ex.: emitir permissão de trabalho) importa mais do que a frequência de login.

---

## 3. Como o Modelo de Licença (AUTHORIZED/CONCURRENT) é determinado

**Módulo**: `scripts/services/app_points.py::_assign_license_model(profile, entitlement, login_count, operational_presence, titles)`

Avaliada nesta ordem — a primeira condição que casar decide:

1. **`login_count == 0` (sem login em 90 dias)**:
   - Se o usuário tem acesso administrativo crítico (grupo `MAXADMIN`) ou cargo crítico → `AUTHORIZED` (preserva disponibilidade mesmo sem uso recente — evita zerar indevidamente usuários críticos por uma janela de dados incompleta).
   - Caso contrário → `CONCURRENT`.
2. **`entitlement == 'LIMITED'`** → sempre `CONCURRENT` (nunca justifica licença dedicada).
3. **Acesso administrativo crítico** (grupo `MAXADMIN`) → sempre `AUTHORIZED`.
4. **Presença operacional OFFSHORE** (ver seção 3.1) → `AUTHORIZED` se o cargo for crítico (ver seção 3.2), senão `CONCURRENT`.
5. **Caso geral (ONSHORE)** → `AUTHORIZED` se `login_count > 60` (em 90 dias, ~2 a cada 3 dias úteis) OU cargo crítico; senão `CONCURRENT`.

### 3.1 Como a presença operacional (OFFSHORE/ONSHORE) é classificada

**Módulo**: `scripts/services/app_points.py::_classify_operational_presence(profile)`

- Se o usuário está no grupo `MAXADMIN` → `ONSHORE` (força).
- Se os únicos ambientes Maximo do usuário estão em `ONSHORE_ENVS = {'BASE'}` → `ONSHORE`.
- Se título, grupo pessoal (PERSONGROUPS) ou algum ambiente do usuário bate com uma palavra-chave offshore (`OFFSHORE`, `PLATAFORMA`, `PLATFORM`, `EMBARCADO`, `FPSO`, `RIG`, `SONDA`, `VESSEL`, `NAVIO`, `MOB_`, `TURNO`, ou o nome de qualquer ambiente offshore: `ODN1`, `ODN2`, `N06`, `N08`, `N09`, `HTQ`) → `OFFSHORE`.
- Se o usuário tem QUALQUER ambiente diferente de `BASE` → `OFFSHORE` (fallback).
- Caso contrário → `ONSHORE`.

**Limitação conhecida**: não há calendário de escala/rotação (ex.: 14x14) — a classificação é estática (a pessoa "é" offshore ou não), não dinâmica por data. A rotação real de turmas (quem está embarcado numa data específica) é capturada de forma diferente, no cálculo de concorrência do NEM (seção 6), que usa login real hora a hora — não neste ponto de classificação de licença.

### 3.2 O que é um "cargo crítico"

**Módulo**: `scripts/services/app_points.py::_is_critical_title(titles)` — usa `scripts/config.py::get_critical_titles()`:

```
ALMOXARIFE, SUPERVISOR, COORDENADOR, GERENTE, LIDER, ENCARREGADO
```

Basta o título do usuário conter uma dessas palavras (case-insensitive) para ser considerado crítico.

### 3.3 O que é "acesso administrativo crítico"

**Módulo**: `scripts/services/app_points.py::_is_critical_access(profile)` — verdadeiro se o usuário pertence ao grupo `MAXADMIN`.

---

## 4. Como a Recomendação de Otimização (`OPTIMIZATION_REC`) é determinada

**Módulo**: `scripts/services/app_points.py::_recommend(profile, entitlement, license_model, login_count, operational_presence)`

Avaliada nesta ordem:

### 4.1 `INATIVO (>90d)`
**Critério**: `login_count == 0` (nenhum login no extrato consolidado dos últimos 90 dias).
**Efeito**: usuário permanece no cenário "As-Is" do simulador de AppPoints, mas é **excluído** dos cenários "Saneado" e "Otimizado" — a lógica assume que uma conta inativa há 90+ dias deveria ser desativada.

### 4.2 `CONFIRMED_AUTHORIZED` (acesso administrativo)
**Critério**: usuário tem acesso administrativo crítico (`MAXADMIN`).
**Ação**: manter Authorized — acesso confirmado por grupo administrativo, não precisa de mais validação.

### 4.3 `DOWNGRADE_CANDIDATE`
**Critério**: `entitlement == PREMIUM` E presença `ONSHORE` E `login_count < 5` E **sem** acesso O&G detectado via grupos (ver seção 2.1).
**Ação sugerida**: rebaixar de PREMIUM para BASE — uso extremamente baixo não justifica módulos críticos, e não há evidência de necessidade operacional O&G.
**Exceção**: se o mesmo usuário TEM acesso O&G via grupos, a recomendação passa a ser `OK` com o motivo "Premium mantido: acesso O&G detectado via grupos" — a regra de criticidade operacional tem prioridade sobre a regra de baixo uso.

### 4.4 `MOVE_TO_CONCURRENT`
**Critério**: `license_model == AUTHORIZED` E `login_count < 30` (em 90 dias, menos de 1 a cada 3 dias).
**Ação sugerida**: mover de Authorized (licença dedicada, sempre reservada) para Concurrent (pool compartilhado) — a frequência de uso não justifica mais uma reserva fixa.
**Regra canônica de negócio**: o corte é `< 30`, unificado em 2026-07-01 entre `app_points.py` e `usage_analyzer.py` (antes havia dois limiares divergentes, `< 20` em um módulo e `< 30` documentado — ver `docs/REFATORACAO_2026-07-01.md`).

### 4.5 `CONFIRMED_AUTHORIZED` (uso justifica)
**Critério**: `license_model == AUTHORIZED` e não caiu em nenhuma das regras acima (ou seja, uso ≥ 30 logins/90d).
**Ação**: manter Authorized — uso ou cargo justifica disponibilidade fixa.

### 4.6 `OK` (caso geral)
Qualquer usuário Concurrent que não seja candidato a downgrade — está corretamente dimensionado para o pool compartilhado.

---

## 5. Como as licenças são traduzidas em custo final

Depois da recomendação, o `license_decision_plan.csv` aplica o efeito da recomendação ao entitlement/licença **originais** para chegar no estado **"Otimizado"**:

```
final_entitlement = 'BASE' se (rec == 'DOWNGRADE_CANDIDATE' e entitlement == 'PREMIUM') senão entitlement
final_license     = 'CONCURRENT' se rec == 'MOVE_TO_CONCURRENT' senão license_model

AppPoints (Otimizado) = calculate_app_points(final_entitlement, final_license)
```

Os quatro cenários exibidos na Aba 6 (Cenários de AppPoints) usam essa mesma tabela de custo, mas cortes diferentes de população:

| Cenário | Quem entra | Fórmula |
|---|---|---|
| **As-Is** | Todos os usuários, incluindo inativos | Soma de `entitlement`/`license_model` originais |
| **Saneado** | Remove os `INATIVO (>90d)` | Soma de `entitlement`/`license_model` originais, só ativos |
| **Otimizado (composição física)** | Remove inativos + aplica downgrade/move-to-concurrent | Soma de `final_entitlement`/`final_license` |
| **Otimizado P50 / P95 / P100** | Concorrência real medida (NEM) | Ver seção 6 — **não** é uma soma de inventário, é uma medição estatística |

---

## 6. O motor NEM (Non-Exclusive Maximum) — de onde vêm P50/P95/P100

**Módulo**: `src/true_capacity_calculator.py`

A diferença fundamental entre "quantas licenças estão provisionadas" (As-Is/Saneado/Otimizado físico) e "quantas realmente precisamos simultaneamente" (NEM) é o motivo de existir desta segunda camada de cálculo.

### 6.1 Fórmula

Para cada hora dos últimos 90 dias:

```
AppPoints da hora = (reserva fixa de todos os usuários AUTHORIZED, sempre — estejam
                      logados ou não naquela hora específica)
                   + (soma do custo dos usuários CONCURRENT que estavam logados
                      naquela hora específica, usando uma janela de sessão de 60 min
                      após cada evento de login)
```

- **P50** = mediana da série horária de 90 dias (dia comum).
- **P95** = percentil 95 (pico esperado, cobre 95% dos casos históricos).
- **P100** = máximo histórico absoluto.
- **Blackout**: no código atual, **é idêntico ao P100** — não é um multiplicador (`P100 × 2`) como versões antigas da documentação chegaram a descrever. Se a intenção de negócio for simular algo pior que o pico já observado, isso precisa ser implementado — hoje não está.

### 6.2 Por que a reserva Authorized é sempre somada, mesmo fora do horário de login

Por definição de negócio: uma licença **Authorized** é "dedicada, com disponibilidade garantida 100%" — o contrato reserva aquele AppPoint para aquela pessoa em qualquer hora do dia, esteja ela logada ou não. Reclassificar alguém de Concurrent para Authorized tem impacto permanente e constante no NEM, independentemente do padrão real de uso dessa pessoa depois da reclassificação.

### 6.3 Limitações conhecidas (não são bugs — são o limite do que os dados permitem)

1. **Duração de sessão assumida em 60 minutos fixos** (`SESSION_MINUTES` em `true_capacity_calculator.py`): os dados de login não têm evento de logout, só de login. Não há como medir a duração real de uma sessão. Validação empírica (2026-07-09): 75% dos intervalos entre logins consecutivos do mesmo usuário ficam dentro de 60 minutos; ~20% passam de 2 horas — nesses casos, alguém que continua trabalhando sem gerar novo evento de login pode "desaparecer" momentaneamente da contagem de concorrência.
2. **Sem calendário de escala/rotação offshore explícito**: o sistema não sabe, a priori, quem está embarcado ou de folga numa data específica. Isso é compensado porque o cálculo usa login **real** hora a hora, não um headcount teórico — quem está de folga simplesmente não aparece nos dados. Funciona bem para medir o passado; teria menos precisão para *prever* picos futuros sem essa informação.
3. **Contas de serviço/integração** (ex.: `WSORACLE`, com ~275 mil logins em 90 dias — uma integração, não humano) entram no cálculo como qualquer outro USERID. Hoje isso é inofensivo porque essas contas são poucas e ficam isoladas no escopo `INTEGRACAO` (ou contribuem uma fração desprezível do total), mas não há um filtro explícito que as exclua estruturalmente — se o número de contas de serviço crescer, vale revisitar.

---

## 7. Escopos (FORESEA+PARCEIRO / TERCEIROS / INTEGRAÇÃO / TODOS)

**Módulo**: `scripts/reporting/html_data_processor.py`, campo `DOMAIN_CATEGORY` do perfil do usuário.

| Escopo | Critério |
|---|---|
| `foresea` | `DOMAIN_CATEGORY` é `FORESEA` ou `PARCEIRO` (email `@foresea.com` ou `@foresea-partner.com`) |
| `integracao` | `DOMAIN_CATEGORY == 'INTEGRACAO'` (contas de serviço/sistema) |
| `terceiros` | Qualquer outro domínio válido, diferente de `SEM DOMINIO` |
| `todos` | Soma dos três acima |

Usuários com `DOMAIN_CATEGORY == 'SEM DOMINIO'` (sem email válido cadastrado) **não entram em nenhum escopo** dos cenários AppPoints — mas ainda contam no total geral de "Usuários no Plano de Licença" do Painel (Aba 1), marcados para revisão manual (`OPTIMIZATION_REC = 'REQUER_REVISAO'`).

---

## 8. Onde validar cada regra no código (referência rápida)

| Regra | Arquivo |
|---|---|
| Tabela de custo AppPoints | `scripts/config.py::get_app_points_config()` |
| Cálculo de custo | `scripts/analysis/entitlement.py::calculate_app_points()` |
| Entitlement (Premium/Base/Limited) | `scripts/analysis/entitlement.py::determine_user_entitlement()` |
| Modelo de licença (Authorized/Concurrent) | `scripts/services/app_points.py::_assign_license_model()` |
| Presença operacional (Offshore/Onshore) | `scripts/services/app_points.py::_classify_operational_presence()` |
| Cargo crítico | `scripts/services/app_points.py::_is_critical_title()` + `scripts/config.py::get_critical_titles()` |
| Recomendação de otimização | `scripts/services/app_points.py::_recommend()` |
| Cenários As-Is/Saneado/Otimizado (composição física) | `scripts/reporting/html_data_processor.py::process_app_points_analytics()` |
| Motor NEM (P50/P95/P100) | `src/true_capacity_calculator.py` |
| Escopos (Foresea/Terceiros/Integração/Todos) | `scripts/reporting/html_data_processor.py` (campo `DOMAIN_CATEGORY`) |
| Cruzamento AD × Maximo (Aba 3) | `scripts/domain/sanity_analyzer.py` |

---

## 9. Histórico de correções relevantes a estas regras

- **2026-07-01**: corrigido valor de BASE/AUTHORIZED (2→3 pts); unificado limiar de MOVE_TO_CONCURRENT (<30); consolidado `calculate_app_points`/`assign_license_model`/`determine_user_entitlement` em módulos canônicos únicos. Ver `docs/REFATORACAO_2026-07-01.md`.
- **2026-07-09**: corrigido bug que excluía todos os usuários BASE (ativos ou não) dos cenários Saneado/Otimizado; corrigido `IndentationError` que impedia o motor NEM de executar; corrigida chave de dados descartada que fazia P50/P95/P100 por escopo caírem num fallback sem diferenciação estatística. Ver `docs/REFATORACAO_2026-07-09.md` e `docs/CALCULO_APPPOINTS_EXPLICACAO.md`.
