# Explicação: Cálculo de AppPoints por Cenário

**Data**: 2025-01-03 (última correção de dados: 2026-07-09)
**Versão**: 2.2
**Autor**: Data Scientist CHECKUSER

> ⚠️ **Aviso de correção (2026-07-09)**: os exemplos numéricos originais deste documento (P95 ≈ 705, P100 ≈ 1.150, AS-IS ≈ 9.098) foram calculados quando o motor `src/true_capacity_calculator.py` **não conseguia executar** (havia um `IndentationError` real no código — não uma questão de dados). Os números abaixo foram atualizados para os valores reais pós-correção. Ver `docs/REFATORACAO_2026-07-09.md` para o detalhamento técnico da correção.

---

## 🎯 Por que os Números Variam Entre Cenários?

Os valores de **AppPoints** exibidos na **Aba 3: Cenários de AppPoints** variam conforme o tipo de análise:

### 📊 Tipos de Cálculo

| Cenário | Tipo de Cálculo | Fórmula | Exemplo (FORESEA + PARCEIRO, escopo do simulador) |
|---------|----------------|---------|-------------------|
| **AS-IS (Atual)** | Inventário Físico | Soma de todas as licenças contratadas | **6.478 AppPoints** |
| **SANEADO** | Inventário Otimizado | Soma após remover inativos (>90 dias) | **6.213 AppPoints** |
| **OTIMIZADO P95** | **NEM Real** (Concorrência) | Pico de sessões simultâneas (95% confiança) | **1.478 AppPoints** |
| **OTIMIZADO P50** | **NEM Mediana** | Mediana de sessões simultâneas | **1.195 AppPoints** |

Valores para o escopo **TODOS** (consolidado FORESEA+PARCEIRO+TERCEIROS+INTEGRAÇÃO): AS-IS = 9.676, SANEADO = 8.816, OTIMIZADO P95 = 1.586, OTIMIZADO P50 = 1.231, P100 (pico histórico) = 1.861.

---

## 🔍 Diferença Fundamental

### ❌ **INVENTÁRIO** (AS-IS / SANEADO)
Responde: **"Quantas licenças temos contratadas?"**

**Cálculo:**
```
AppPoints = (Premium Auth × 5) + (Premium Conc × 15) + (Base Auth × 3) + (Base Conc × 10)
```

**Exemplo FORESEA+PARCEIRO (AS-IS, dados 2026-07-09):**
- 199 Premium Auth × 5 = **995**
- 360 Premium Conc × 15 = **5.400**
- 1 Base Auth × 3 = **3**
- 8 Base Conc × 10 = **80**
- **Total = 6.478 AppPoints**

**Interpretação:** Esse é o custo **potencial máximo** se todos os usuários acessassem simultaneamente 24/7 (cenário impossível).

---

### ✅ **NEM (Non-Exclusive Maximum)** - OTIMIZADO P95/P50
Responde: **"Quantas pessoas realmente acessam ao mesmo tempo?"**

**Cálculo:**
1. Analisa histórico de 90 dias de logins (`logintracking`)
2. Agrupa sessões ativas por janela de 1 hora
3. Calcula AppPoints de cada sessão (considerando tipo de licença do usuário)
4. Extrai percentis da distribuição:
   - **P50**: Mediana (dia comum) → 1.195 AppPoints (escopo FORESEA+PARCEIRO) / 1.231 (TODOS)
   - **P95**: Teto seguro (pico esperado 95% do tempo) → 1.478 AppPoints (FORESEA+PARCEIRO) / 1.586 (TODOS)
   - **P100**: Pico histórico absoluto → 1.673 AppPoints (FORESEA+PARCEIRO) / 1.861 (TODOS)

O cálculo soma dois componentes por hora: a **reserva fixa** dos usuários AUTHORIZED (871 AppPoints, contam em toda hora, estejam logados ou não — é o significado de "licença dedicada") + o **custo variável** do pool CONCURRENT logado naquela hora específica.

**Exemplo real (pico histórico, escopo TODOS):**
```
Hora de pico: 2026-05-27 07:00
217 usuários simultâneos ativos (janela de sessão de 60 min)

Reserva AUTHORIZED (fixa, todas as horas):     871 AppPoints
Pool CONCURRENT ativo nesta hora específica:   990 AppPoints
Total da hora: 1.861 AppPoints (= P100, o pico histórico)
```
Contribuidores de exemplo no pico (todos Premium Concurrent, 15 pts cada): LUISPARAGUASSU, JEANANEY, LUCASRIBEIRO, GUSTAVOSERRONI, VALDEMIRJESUS, JAMILESILVA, JOSEALVIM, PAULOLOPES — lista completa (top 50) em `peak_contributors` dentro de `true_capacity_metrics.json`.

**Interpretação:** Esse é o consumo **real medido** em picos operacionais. É a base correta para **dimensionar capacidade**.

---

## 📈 Gráfico Comparativo (escopo TODOS, dados 2026-07-09)

```
AS-IS:          [████████████████████████████████████████] 9.676 AppPoints (100%)
SANEADO:        [████████████████████████████████████    ] 8.816 AppPoints (91%)
OTIMIZADO P95:  [██████                                   ] 1.586 AppPoints (16%)
OTIMIZADO P50:  [█████                                    ] 1.231 AppPoints (13%)
```

**Redução AS-IS → P95:** **~84% de economia** (de 9.676 para 1.586 AppPoints) — mas o P95 real **já excede o teto contratual de 1.200** (+32%). Ver alerta na seção "Alertas e Validações" abaixo.

---

## 🎓 Por Que Há Essa Diferença Enorme?

### Motivos Práticos

1. **Uso Assíncrono**: Usuários não acessam todos ao mesmo tempo
   - Turnos de trabalho (manhã/tarde/noite)
   - Dias úteis vs. finais de semana
   - Licenças concorrentes compartilhadas

2. **Sazonalidade**: Picos em períodos específicos
   - Fechamento de período
   - Auditorias
   - Campanhas operacionais

3. **Usuários Inativos**: Licenças provisionadas mas não usadas
   - Conta criada mas nunca acessou
   - Usuário saiu da empresa
   - Mudança de função

4. **Licenças Concurrent**: Múltiplos usuários compartilham mesma licença
   - Apenas **1 usuário ativo** por vez consome AppPoints
   - Exemplo: 521 licenças Concurrent ≠ 521 usuários simultâneos

---

## ✅ Qual Usar para Planejamento?

| Cenário | Quando Usar |
|---------|-------------|
| **AS-IS** | Baseline de contrato atual (auditoria contábil) |
| **SANEADO** | Redução rápida removendo inativos |
| **OTIMIZADO P95** | **RECOMENDADO** - Dimensionamento seguro com margem de segurança |
| **OTIMIZADO P50** | Dimensionamento mínimo (apenas dias comuns) |

### 🎯 Recomendação Oficial

**Use OTIMIZADO P95** para planejamento de capacidade:
- Cobre **95% dos cenários reais** históricos
- Margem de segurança para picos operacionais
- Balanceamento custo-benefício ideal

**Situação atual (dados 2026-07-09, escopo TODOS):**
```
Contrato Atual: 1.200 AppPoints
NEM P95 Real:   1.586 AppPoints  ⚠️ EXCEDE O TETO EM 386 pts (+32%)
NEM P100 Real:  1.861 AppPoints  ⚠️ EXCEDE O TETO EM 661 pts (+55%)

Isto é diferente da conclusão de versões anteriores deste documento (que indicavam
folga/superdimensionamento). A mudança se deve à correção de um bug que impedia o
motor de cálculo NEM de rodar (ver aviso no topo do documento) — o número antigo
(~705-990) contava só o pool concorrente, sem a reserva de licenças Authorized (871 pts).

Ação recomendada: revisar com a área de negócio se o contrato de 1.200 AppPoints
precisa ser renegociado para cima, ou se há oportunidade real de downgrade/saneamento
adicional nos usuários Authorized (que são o maior componente fixo do custo).
```

---

## 🔧 Detalhes Técnicos

### Fórmula de NEM (Pseudocódigo)

```python
# Passo 1: Agrupa sessões por janela de 1 hora
for hour_window in last_90_days:
    active_sessions = get_logins_in_window(hour_window, SESSION_MINUTES=60)
    
    # Passo 2: Calcula AppPoints da janela
    hour_app_points = 0
    for user in active_sessions:
        license_type = get_user_license(user)
        app_points_weight = {
            'PREMIUM_AUTH': 5,
            'PREMIUM_CONC': 15,
            'BASE_AUTH': 3,
            'BASE_CONC': 10
        }
        hour_app_points += app_points_weight[license_type]
    
    hourly_distribution.append(hour_app_points)

# Passo 3: Extrai percentis
p50 = np.percentile(hourly_distribution, 50)   # Mediana
p95 = np.percentile(hourly_distribution, 95)   # Teto seguro
p100 = max(hourly_distribution)                # Pico absoluto
```

### Arquivo de Cálculo

**Módulo**: `src/true_capacity_calculator.py`

**Inputs:**
- `consolidated_logintracking_from_sources.csv`: Histórico de logins
- `license_optimization_recommendations.csv`: Perfil de licença de cada usuário

**Outputs:**
- `true_capacity_metrics.json` (valores reais em 2026-07-09, escopo TODOS):
  ```json
  {
    "scenario_points": {
      "p50": 1231,
      "p95": 1586,
      "p100": 1861,
      "blackout": 1861
    }
  }
  ```
  ⚠️ Nota de implementação: no código atual (`html_data_processor.py`), `blackout` é sempre igual a `p100` (`max(values)`) — **não** é `P100 × 2`. A descrição de "Blackout (P100 × 2)" mais abaixo neste documento é aspiracional/histórica e não reflete o comportamento real do código; se o cenário de blackout deve de fato representar um estresse acima do pico histórico, é necessário implementar esse multiplicador (não implementado nesta correção, que focou apenas nos 4 bugs que zeravam a Aba 3).

---

## 📊 Exemplo Real de Sessão (Aba 6)

A **Aba 6: Peak Contributors** mostra os usuários que contribuem para o pico de concorrência:

| Usuário | Tipo Licença | AppPoints | Contribuição |
|---------|--------------|-----------|--------------|
| LUISPARAGUASSU | Premium Conc | 15 | 0.8% |
| JEANANEY | Premium Conc | 15 | 0.8% |
| LUCASRIBEIRO | Premium Conc | 15 | 0.8% |
| GUSTAVOSERRONI | Premium Conc | 15 | 0.8% |
| ... | ... | ... | ... |
| **TOTAL (217 usuários)** | - | **1.861** | **100%** |

Esses usuários estavam **logados simultaneamente** em 2026-05-27 07:00, o pico histórico (P100) medido nos 90 dias de dados. A lista completa (top 50) fica em `peak_contributors` dentro de `true_capacity_metrics.json`.

---

## 🚨 Alertas e Validações

### Teto de Contrato

Situação real medida em 2026-07-09 (escopo TODOS):
```
Contrato: 1.200 AppPoints
NEM P95: 1.586 AppPoints  ❌ EXCEDIDO (+386 pts / +32%)
NEM P100: 1.861 AppPoints ❌ EXCEDIDO (+661 pts / +55%)

⚠️ Risco de throttling ou licenças negadas em dias de pico
✅ Recomendação: revisar contrato ou aprofundar saneamento de usuários Authorized
```

### Cenários de Estresse

**Blackout:** no código atual, o valor de "Blackout" exibido na Aba 3/4 é **idêntico ao P100** (pico histórico), não um múltiplo dele — ver nota técnica na seção anterior. Se a intenção de negócio é simular algo além do pico já observado (ex.: P100 × 2), isso precisa ser implementado; hoje o rótulo "Blackout Total (100%)" está descrevendo, na prática, o mesmo número do pico histórico.

---

## 📝 Resumo Executivo (atualizado 2026-07-09)

| Métrica | Valor | Significado |
|---------|-------|-------------|
| **AS-IS (TODOS)** | 9.676 AppPoints | Inventário total contratado |
| **NEM P95 (TODOS)** | 1.586 AppPoints | Capacidade real necessária |
| **NEM P100 (TODOS)** | 1.861 AppPoints | Pico histórico real medido |
| **Economia (AS-IS → P95)** | ~84% | Diferença entre inventário e uso real |
| **Status** | ❌ **TETO EXCEDIDO** | P95 (1.586) e P100 (1.861) > 1.200 (contrato) |

**Conclusão:** o inventário físico (AS-IS) continua muito superdimensionado frente ao uso real — mas, diferente do que versões anteriores deste documento concluíam, o **consumo real (NEM) já ultrapassa o teto contratual**. A conclusão anterior de "sistema superdimensionado, dentro do teto" estava baseada em um cálculo que nunca chegou a executar corretamente (ver aviso no topo do documento); não é uma regressão introduzida agora, é a primeira vez que o número real aparece.

---

**Validado por:** Motor de cálculo `true_capacity_calculator.py` (Fase 4)  
**Base de dados:** 90 dias de histórico de logins consolidados  
**Última atualização:** 2026-07-09 — ver `docs/REFATORACAO_2026-07-09.md` para o detalhamento da correção dos 4 bugs que impediam este cálculo de rodar corretamente.
