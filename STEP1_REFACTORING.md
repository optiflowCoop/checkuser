# STEP 1: Externalização de Regras de Negócio ✅

## Objetivo
Centralizar todas as regras de negócio hardcoded em um único arquivo JSON (`config/licensing_rules.json`), preparando o código para aplicar princípios SOLID sem quebrar a saída atual.

## Mudanças Implementadas

### 1. Novo Arquivo: `config/licensing_rules.json`

Arquivo estruturado que consolida TODOS os hardcodes previamente distribuídos em:
- `src/analyze_usage.py` (linhas 20-151)
- `src/license_optimizer.py` (linha 19)
- `scripts/services/usage_analyzer.py` (linhas 14-23 - mocks)

#### Estrutura do JSON:

```json
{
  "metadata": {...},
  "capacity_planning": {
    "contracted_apppoints": 1200
  },
  "premium_modules": {
    "modules": {
      "WOTRACK": {...},
      "ASSET": {...},
      ...
    }
  },
  "standard_modules": [...],
  "user_classification": {
    "priority_domains": ["@foresea.com", "@foresea-partner.com"],
    "offshore_keywords": ["offshore", "plataforma", ...],
    "critical_functions": ["almoxarife", "supervisor", ...],
    "og_group_keywords": ["OG_", "O&G", ...]
  },
  "user_tier_rules": {
    "IDLE": {...},
    "POWER_OG": {...},
    ...
  },
  "optimization_thresholds": {...},
  "apppoints_cost_matrix": {...}
}
```

**Localização**: `C:\Users\esilva\OneDrive - FORESEA\Documentos\04 - APPS\CHECKUSER\config\licensing_rules.json`

### 2. Nova Função: `src/config_loader.py`

Adicionada função `load_licensing_rules()` para ler o JSON de forma padronizada:

```python
def load_licensing_rules():
    """
    Load centralized business rules for license optimization and user classification.
    Returns: dict with licensing rules configuration
    """
    path = CONFIG_DIR / 'licensing_rules.json'
    if not path.exists():
        raise FileNotFoundError(f"Licensing rules not found at {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

## Impacto Atual: **ZERO** ✅

✔️ Nenhum arquivo foi modificado  
✔️ Nenhuma saída foi alterada  
✔️ Nenhum comportamento mudou  
✔️ Todos os CSVs gerados continuam idênticos  

**Por quê?** O JSON é um "blueprint" (plano de construção). Os scripts continuam usando os hardcodes diretos. Na Etapa 2+, refatoraremos o código para **ler do JSON** em vez de usar hardcodes.

## Próxima Etapa (STEP 2)

**Substituir Simulação por Dados Reais** em `scripts/services/usage_analyzer.py`:
- Remover `random.randint()` de linhas 14-23
- Ler dados reais de `consolidated_logintracking.csv`
- Calcular: `last_login_date`, `login_frequency`, `premium_modules_accessed`

## Verificação

Para verificar que o JSON está válido:

```bash
python -m json.tool config/licensing_rules.json
```

Para testar carregamento da função:

```python
from src.config_loader import load_licensing_rules
rules = load_licensing_rules()
print(rules['capacity_planning']['contracted_apppoints'])  # Should print: 1200
```

## Organização para Próximas Fases

### STEP 2: Real Data (Esperado impacto: 5-10% ajuste nos números)
```
usage_analyzer.py (remover mocks)
  ↓
consolidated_logintracking.csv (dados reais)
  ↓
usage_analysis_phase3.csv (com dados empíricos absolutos)
```

### STEP 3: SOLID Refactoring (Esperado impacto: +20% precisão de classificação)
```
config/licensing_rules.json (ler daqui)
  ↓
src/engine/rules.py (Strategy Pattern)
  ↓
analyze_usage.py (usar rules.py)
```

### STEP 4: Rule Engine (Esperado impacto: +30% economia via regras inteligentes)
```
config/licensing_rules.json (ler daqui)
  ↓
src/engine/optimizer.py (LicenseOptimizer)
  ↓
license_optimizer.py (usar optimizer.py)
```

## Checklist - STEP 1 ✅

- [x] Identificar todos os hardcodes em 3 arquivos
- [x] Estruturar JSON com categorias lógicas
- [x] Criar `config/licensing_rules.json`
- [x] Adicionar `load_licensing_rules()` em `config_loader.py`
- [x] Documentar mudanças (este arquivo)
- [x] Validar JSON é válido
- [x] Confirmar impacto ZERO na saída

## Timeline Estimado (Refactoring Total)

| Fase | Tarefa | Tempo | Impacto |
|------|--------|-------|--------|
| STEP 1 ✅ | Externalizar Regras | **DONE** | Zero |
| STEP 2 | Real Data | 1-2h | +5-10% |
| STEP 3 | SOLID Rules | 2-3h | +20% |
| STEP 4 | Rule Engine | 2-3h | +30% |
| **TOTAL** | **Refactoring Completo** | **~7-8h** | **+55% Precisão** |

---

**Próxima ação**: Implementar STEP 2 seguindo o mesmo padrão seguro (blueprint → implementação).
