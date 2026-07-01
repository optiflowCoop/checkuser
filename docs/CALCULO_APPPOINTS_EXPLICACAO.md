# Explicação: Cálculo de AppPoints por Cenário

**Data**: 2025-01-03  
**Versão**: 2.1  
**Autor**: Data Scientist CHECKUSER

---

## 🎯 Por que os Números Variam Entre Cenários?

Os valores de **AppPoints** exibidos na **Aba 3: Cenários de AppPoints** variam conforme o tipo de análise:

### 📊 Tipos de Cálculo

| Cenário | Tipo de Cálculo | Fórmula | Exemplo (FORESEA) |
|---------|----------------|---------|-------------------|
| **AS-IS (Atual)** | Inventário Físico | Soma de todas as licenças contratadas | **9.098 AppPoints** |
| **SANEADO** | Inventário Otimizado | Soma após remover inativos (>90 dias) | **8.788 AppPoints** |
| **OTIMIZADO P95** | **NEM Real** (Concorrência) | Pico de sessões simultâneas (95% confiança) | **~705 AppPoints** |
| **OTIMIZADO P50** | **NEM Mediana** | Mediana de sessões simultâneas | **~480 AppPoints** |

---

## 🔍 Diferença Fundamental

### ❌ **INVENTÁRIO** (AS-IS / SANEADO)
Responde: **"Quantas licenças temos contratadas?"**

**Cálculo:**
```
AppPoints = (Premium Auth × 5) + (Premium Conc × 15) + (Base Auth × 3) + (Base Conc × 10)
```

**Exemplo FORESEA (AS-IS):**
- 236 Premium Auth × 5 = **1.180**
- 521 Premium Conc × 15 = **7.815**
- 1 Base Auth × 3 = **3**
- 10 Base Conc × 10 = **100**
- **Total = 9.098 AppPoints**

**Interpretação:** Esse é o custo **potencial máximo** se todos os usuários acessassem simultaneamente 24/7 (cenário impossível).

---

### ✅ **NEM (Non-Exclusive Maximum)** - OTIMIZADO P95/P50
Responde: **"Quantas pessoas realmente acessam ao mesmo tempo?"**

**Cálculo:**
1. Analisa histórico de 90 dias de logins (`logintracking`)
2. Agrupa sessões ativas por janela de 1 hora
3. Calcula AppPoints de cada sessão (considerando tipo de licença do usuário)
4. Extrai percentis da distribuição:
   - **P50**: Mediana (dia comum) → ~480 AppPoints
   - **P95**: Teto seguro (pico esperado 95% do tempo) → ~705 AppPoints
   - **P100**: Pico histórico absoluto → ~1.150 AppPoints

**Exemplo:**
```python
# Sessão em 2024-12-15 às 14:00
Usuários ativos simultâneos:
- MAXMORAES (Premium Auth) → 5 AppPoints
- WLADMIRSILVA (Premium Conc) → 15 AppPoints
- PIETROMACHADO (Base Auth) → 3 AppPoints
... (mais 45 usuários)
Total da sessão: 705 AppPoints
```

**Interpretação:** Esse é o consumo **real medido** em picos operacionais. É a base correta para **dimensionar capacidade**.

---

## 📈 Gráfico Comparativo

```
AS-IS:          [████████████████████████████████████████] 9.098 AppPoints (100%)
SANEADO:        [███████████████████████████████████████ ] 8.788 AppPoints (97%)
OTIMIZADO P95:  [███                                     ] 705 AppPoints (8%)
OTIMIZADO P50:  [██                                      ] 480 AppPoints (5%)
```

**Redução AS-IS → P95:** **92% de economia** (de 9.098 para 705 AppPoints)

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

**Exemplo de Decisão:**
```
Contrato Atual: 1.200 AppPoints (R$ 500k/ano)
NEM P95 Real: 705 AppPoints

Redimensionamento Seguro:
- Renovar com 800 AppPoints (P95 + 13% margem)
- Economia: R$ 167k/ano (33%)
- Risco: Baixo (cobre 95% dos picos históricos)
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
- `true_capacity_metrics.json`:
  ```json
  {
    "scenario_points": {
      "p50": 480,
      "p95": 705,
      "p100": 1150,
      "blackout": 2500
    }
  }
  ```

---

## 📊 Exemplo Real de Sessão (Aba 6)

A **Aba 6: Peak Contributors** mostra os usuários que contribuem para o pico de concorrência:

| Usuário | Tipo Licença | AppPoints | Contribuição |
|---------|--------------|-----------|--------------|
| MAXMORAES | Premium Auth | 5 | 0.7% |
| WLADMIRSILVA | Premium Conc | 15 | 2.1% |
| PIETROMACHADO | Base Auth | 3 | 0.4% |
| ... | ... | ... | ... |
| **TOTAL** | - | **705** | **100%** |

Esses usuários estavam **logados simultaneamente** no momento do pico P95.

---

## 🚨 Alertas e Validações

### Teto de Contrato

Se o NEM P95 exceder o contrato:
```
Contrato: 1.200 AppPoints
NEM P95: 1.350 AppPoints  ❌ EXCEDIDO

⚠️ Risco de throttling ou licenças negadas
✅ Recomendação: Aumentar para 1.500 AppPoints
```

### Cenários de Estresse

**Blackout (P100 × 2):** Simula cenário extremo onde TODOS os usuários do pico histórico acessam simultaneamente. Usado para plano de contingência.

---

## 📝 Resumo Executivo

| Métrica | Valor | Significado |
|---------|-------|-------------|
| **AS-IS** | 9.098 AppPoints | Inventário total contratado |
| **NEM P95** | 705 AppPoints | Capacidade real necessária |
| **Economia** | 92% | Diferença entre inventário e uso real |
| **Status** | ✅ DENTRO DO TETO | P95 < 1.200 (contrato) |

**Conclusão:** O sistema está **superdimensionado**. Oportunidade de otimização mantendo margem de segurança adequada.

---

**Validado por:** Motor de cálculo `true_capacity_calculator.py` (Fase 4)  
**Base de dados:** 90 dias de histórico de logins consolidados  
**Última atualização:** 2025-01-03
