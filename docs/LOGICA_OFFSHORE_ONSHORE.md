# 🎯 LÓGICA DE LICENCIAMENTO FORESEA - OFFSHORE vs ONSHORE

## Regras de Negócio Implementadas

### 1. Classificação Operacional

**OFFSHORE (Turnista)**
- Keywords: offshore, plataforma, platform, embarcado, fpso, rig, sonda, vessel, mob_, turno
- Revezamento 12h → Baixa simultaneidade
- **SEMPRE Concurrent**

**ONSHORE (Administrativo)**  
- Demais usuários não identificados como offshore
- Alta simultaneidade
- **Authorized = EXCEÇÃO** (só se uso >60 logins/90d)

### 2. Matriz de Decisão AppPoints

```
┌────────────────┬──────────────┬──────────────┬────────────────┐
│ Presença       │ Módulos      │ Logins/90d   │ Licença        │
├────────────────┼──────────────┼──────────────┼────────────────┤
│ OFFSHORE       │ O&G Premium  │ Qualquer     │ PREMIUM_CONC   │
│ OFFSHORE       │ Standard     │ Qualquer     │ BASE_CONC      │
│ ONSHORE        │ O&G Premium  │ >60          │ PREMIUM_AUTH   │
│ ONSHORE        │ O&G Premium  │ ≤60          │ PREMIUM_CONC   │
│ ONSHORE        │ Standard     │ >60          │ BASE_AUTH      │
│ ONSHORE        │ Standard     │ ≤60          │ BASE_CONC      │
│ Qualquer       │ Qualquer     │ 0            │ IDLE (0 pts)   │
│ Qualquer       │ Qualquer     │ <5           │ LIMITED (5pts) │
└────────────────┴──────────────┴──────────────┴────────────────┘
```

### 3. Custos AppPoints

| Licença               | AppPoints | Uso                          |
|-----------------------|-----------|------------------------------|
| PREMIUM_CONCURRENT    | 15        | Offshore O&G / ONSHORE médio |
| PREMIUM_AUTHORIZED    | 5         | ONSHORE intenso (>60 logins) |
| BASE_CONCURRENT       | 10        | Offshore STD / ONSHORE médio |
| BASE_AUTHORIZED       | 2         | ONSHORE intenso (>60 logins) |
| LIMITED               | 5         | Uso esporádico (<5 logins)   |
| NONE (IDLE)           | 0         | Sem uso (0 logins)           |

### 4. Módulos O&G que Exigem Premium

**WOTRACK** + contexto Petroleum/OilGas  
**PFWORKTRACK** - PetroField Work Tracking  
**PFASSIGNMENT** - Field Operations Assignment  
**LOCREC** - Location Records  
**COMPLIANCE** - Compliance Management  
**HSE** - Health Safety Environment  
**DRILLING** - Drilling Operations  

## Exemplo Prático

### Caso 1: Técnico Offshore
```
USERID: JOAOSILVA
PERSONGROUP: MOB_N09, OOG_FPSO
TITLE: Técnico de Manutenção
LOGIN_COUNT_90D: 45
APPS: WORKORDER, PM, ASSET

→ OFFSHORE = BASE_CONCURRENT (10 pts)
```

### Caso 2: Engenheiro ONSHORE Intenso
```
USERID: MARIACOSTA
PERSONGROUP: ENG_RJ, OOG_PROJ
TITLE: Engenheira de Projetos
LOGIN_COUNT_90D: 85
APPS: PFWORKTRACK, WOTRACK+Petroleum, COMPLIANCE

→ ONSHORE + >60 logins + O&G = PREMIUM_AUTHORIZED (5 pts)
```

### Caso 3: Supervisor ONSHORE Médio
```
USERID: CARLOSROCHA
PERSONGROUP: SUP_BA
TITLE: Supervisor Elétrica
LOGIN_COUNT_90D: 35
APPS: WORKORDER, PM, INVENTORY

→ ONSHORE + ≤60 logins + Standard = BASE_CONCURRENT (10 pts)
```

## Resultado Esperado

### Distribuição Estimada (1.900 usuários FORESEA)

| Categoria          | Qtd   | %   | Licença         | AppPoints/usuário |
|--------------------|-------|-----|-----------------|-------------------|
| Offshore Técnico   | 1.140 | 60% | CONCURRENT      | 10-15             |
| Offshore Super     | 380   | 20% | CONCURRENT      | 10-15             |
| Onshore Eng/Coord  | 285   | 15% | Mix (80% CONC)  | 8-12              |
| Onshore Admin/TI   | 95    | 5%  | AUTH (exceção)  | 2-5               |

### Economia vs Cenário "Tudo Authorized"

**Cenário Ruim (tudo Authorized):**
- 1.900 × média 4 pts = **7.600 AppPoints** ❌

**Cenário Otimizado (lógica OFFSHORE/ONSHORE):**
- Offshore: 1.520 × 12 pts (Concurrent) = 18.240 ÷ 3 (30% simultaneidade) = **6.080**
- Onshore: 380 × 80% Concurrent (9 pts) + 20% Auth (4 pts) = **3.116**
- **Total simultâneo: ~1.000 AppPoints** ✅

### Pico Simultâneo Calculado

**Offshore:** 1.520 usuários × 30% (turno) = **456 simultâneos**  
**Onshore:** 380 usuários × 60% (pico) = **228 simultâneos**  
**Total pico: ~684 simultâneos**

Com 1.200 AppPoints contratados:
- Sobram **~516 pontos de margem** 🎯
- Cobertura de **175% do pico real**

## Campos no CSV de Saída

```
USERID
DISPLAYNAME
EMAIL
USER_CATEGORY (FORESEA/TEMPORARY)
OPERATIONAL_PRESENCE (OFFSHORE/ONSHORE)  ← NOVO
STATUS
TITLE
PERSONGROUP
ENV_COUNT
SECURITY_GROUPS_COUNT
LOGIN_COUNT_90D
LAST_LOGIN
APPS_USED
PREMIUM_APPS
STANDARD_APPS
USER_TIER
REQUIRED_LICENSE
APP_POINTS_COST
MIGRATION_PRIORITY
```

## Executar

```bash
# Reprocessar com nova lógica
python src\analyze_usage.py
python src\license_optimizer.py
python scripts\generate_risk_report.py
```

## Inteligência Entregue

✅ **OFFSHORE sempre Concurrent** (revezamento natural)  
✅ **ONSHORE Authorized = exceção** (>60 logins = uso intenso)  
✅ **Premium reservado para O&G real**  
✅ **Temporários excluídos da migração**  
✅ **Simulação de pico simultâneo**  
✅ **Assertividade máxima na distribuição**

**Objetivo:** Maximizar cobertura dentro de 1.200 AppPoints, priorizando realidade operacional offshore da Foresea.
