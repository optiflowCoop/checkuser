# Evolução da Aba 3: Filtros de Escopo e Correção de Cálculos

**Data**: 2025-01-03  
**Autor**: Data Scientist CHECKUSER  
**Tipo**: Correção Crítica + Feature Enhancement

---

## 🎯 Problema Identificado

### Sintomas Reportados
1. **Filtros de escopo não funcionando**: Usuário vê três opções de filtro (FORESEA+PARCEIRO, TERCEIROS, TODOS) mas não há efeito prático
2. **Valor incorreto "Soma bruta (XLSX): 9.000"**: Campo confuso exibindo valor que não representa capacidade real
3. **Dados hardcoded na Aba 4**: Valores fixos "9.000" em múltiplos locais

### Diagnóstico Técnico

#### Causa Raiz 1: Ausência de Segregação de Dados por Escopo
**Arquivo**: `scripts/reporting/html_data_processor.py` (linhas 90-124)

O sistema calculava cenários (AS-IS, SANEADO, OTIMIZADO) apenas para o escopo `FORESEA+PARCEIRO` e armazenava em `scenarios_data`. O JavaScript não tinha acesso a cenários segregados por domínio, tornando impossível implementar filtros funcionais.

**Evidência**:
```python
# ANTES: Apenas um conjunto de cenários
scenarios_data = {
    'asis': {'pA': count, 'pC': count, ...},
    'saneado': {...},
    'otimizado': {...}
}
```

#### Causa Raiz 2: Cálculo Incorreto de scenario_points_total
**Arquivo**: `scripts/reporting/html_data_processor.py` (linhas 118-124)

A métrica `scenario_points_total` somava os AppPoints brutos de **TODOS OS USUÁRIOS**, ignorando o conceito de concorrência (NEM). Esse valor não tinha significado operacional e confundia usuários.

**Evidência**:
```python
# ANTES: Soma individual (ERRADO)
foresea_parceiro_total = sum(
    float(u.get('APP_POINTS', 0) or 0) 
    for u in foresea_parceiro_users
)
# Resultado: ~9.000 AppPoints (soma de 300+ usuários)
# Realidade: P95 = ~1.150 AppPoints (concorrência real)
```

**Por que é incorreto:**
- Assumia que todos os usuários acessariam simultaneamente 24/7 (impossível)
- Contradizia o conceito de NEM (Non-Exclusive Maximum)
- O cálculo correto já estava em `scenario_points` (P50/P95/P100)

#### Causa Raiz 3: Stub de Função JavaScript
**Arquivo**: `scripts/reporting/html_template.py` (linha 416-426)

A função `updateScopeFilter()` apenas logava o valor mas não atualizava os dados exibidos.

**Evidência**:
```javascript
// ANTES: Função stub
function updateScopeFilter() {
    var sc = "foresea";
    // ... detecta valor ...
    console.log("Escopo Cenários:", sc);
    loadScenario("otimizado_p95", document.getElementById("btnOtimizado"));
}
// ⚠️ Sempre chamava loadScenario com rawScenarios fixo
```

---

## ✅ Solução Implementada

### Mudança 1: Segregação Completa de Cenários por Escopo

**Arquivo**: `scripts/reporting/html_data_processor.py`

Criada estrutura `scenarios_by_scope` com três camadas:
- `foresea`: FORESEA + PARCEIRO (funcionários internos)
- `terceiros`: TERCEIROS (contractors externos)
- `todos`: Soma de ambos (visão consolidada)

**Código Refatorado**:
```python
scenarios_by_scope = {
    'foresea': {'asis': {...}, 'saneado': {...}, 'otimizado': {...}},
    'terceiros': {'asis': {...}, 'saneado': {...}, 'otimizado': {...}},
    'todos': {'asis': {...}, 'saneado': {...}, 'otimizado': {...}}
}

# Loop de classificação com segregação
for u in self.app_points:
    domain_cat = u.get('DOMAIN_CATEGORY', '')
    is_foresea = domain_cat in ('FORESEA', 'PARCEIRO')
    is_terceiro = domain_cat not in ('FORESEA', 'PARCEIRO', 'SEM DOMINIO')
    
    scope_key = 'foresea' if is_foresea else ('terceiros' if is_terceiro else None)
    if scope_key is None:
        continue  # Ignora usuários sem domínio válido
    
    # Calcula cenários para este escopo específico
    scenarios_by_scope[scope_key][scenario][key] += 1
```

**Benefícios**:
- Cada escopo tem contadores independentes
- JavaScript pode alternar entre escopos sem recalcular
- Transparência para auditoria

### Mudança 2: Remoção de scenario_points_total

**Justificativa**: Métrica redundante e incorreta que causava confusão.

**Antes**:
```python
'scenario_points_total': {  # INCORRETO
    'p50': 9000,
    'p95': 9000,
    'p100': 9000,
    'blackout': 9000
}
```

**Depois**:
```python
# Removido completamente
# Uso correto: scenario_points já contém valores NEM reais
'scenario_points': {
    'p50': 480,    # Mediana da concorrência
    'p95': 1150,   # Percentil 95 (teto seguro)
    'p100': 1780,  # Pico histórico real
    'blackout': 2500  # Cenário extremo (100%)
}
```

### Mudança 3: Interface de Usuário Aprimorada

**Arquivo**: `scripts/reporting/ab3_cenarios.py` (linha 58-65)

Removida referência a "Soma bruta (XLSX)" e substituída por label de escopo dinâmico.

**Antes**:
```html
<div>Soma bruta (XLSX): <strong id="rawSumDisplay">0</strong></div>
```

**Depois**:
```html
<div>
    <strong id="currentScopeLabel">Escopo: FORESEA + PARCEIRO</strong><br>
    <span style="font-size: 0.8rem;">Baseado em concorrência real (NEM)</span>
</div>
```

### Mudança 4: Função JavaScript Funcional

**Arquivo**: `scripts/reporting/html_template.py`

Implementada lógica completa de filtro de escopo.

**Código Novo**:
```javascript
let currentScope = 'foresea';  // Estado global do filtro

function updateScopeFilter() {
    var els = document.getElementsByName('scopeFilter');
    var newScope = 'foresea';
    for (var i = 0; i < els.length; i++) {
        if (els[i].checked) { 
            newScope = els[i].value; 
            break; 
        }
    }
    
    // Atualiza variável global
    currentScope = newScope;
    
    // Atualiza label de escopo
    const scopeLabelEl = document.getElementById('currentScopeLabel');
    if (scopeLabelEl) {
        if (newScope === 'foresea') {
            scopeLabelEl.innerText = 'Escopo: FORESEA + PARCEIRO';
        } else if (newScope === 'terceiros') {
            scopeLabelEl.innerText = 'Escopo: TERCEIROS';
        } else {
            scopeLabelEl.innerText = 'Escopo: TODOS';
        }
    }
    
    // Recarrega o cenário atualmente selecionado com novo escopo
    const activeBtn = document.querySelector('.preset-btn.active');
    if (activeBtn) {
        const scenarioMap = {
            'btnAsIs': 'asis',
            'btnSaneado': 'saneado',
            'btnOtimizado': 'otimizado_p95',
            'btnOtimizadoP50': 'otimizado_p50'
        };
        const scenarioKey = scenarioMap[activeBtn.id] || 'otimizado_p95';
        loadScenario(scenarioKey, activeBtn);
    }
}

// loadScenario também atualizado para usar currentScope
function loadScenario(scenarioKey, btnElement) {
    // ...
    const data = scenariosByScope[currentScope][physicalCountsKey];
    // ...
}
```

**Fluxo de Funcionamento**:
1. Usuário clica no filtro de escopo (FORESEA+PARCEIRO / TERCEIROS / TODOS)
2. `updateScopeFilter()` detecta mudança
3. Atualiza variável global `currentScope`
4. Atualiza label na tela
5. Recarrega cenário atual com dados do novo escopo
6. Atualiza inputs, gráfico e cálculos

### Mudança 5: Limpeza da Aba 4

**Arquivo**: `scripts/reporting/ab4_eventos.py`

Removidas referências a `scenario_points_total` hardcoded.

**Antes**:
```python
<p>... {fmt_br(scenario_points['p95'])} AppPoints. 
   <small>(Soma bruta: {fmt_br(analytics.get('scenario_points_total', {}).get('p95', 0))})</small>
</p>
```

**Depois**:
```python
<p>... {fmt_br(scenario_points['p95'])} AppPoints. 
   Referência para planejamento de capacidade.</p>
```

---

## 📊 Impacto Esperado

### Correção de Dados
- **Antes**: Exibição de "9.000 AppPoints" (soma impossível de 300+ usuários)
- **Depois**: Valores reais de concorrência (P95 = ~1.150 AppPoints)
- **Melhoria**: Redução de 87% no valor exibido (reflete realidade operacional)

### Funcionalidade
- **Antes**: Filtros de escopo eram decorativos (sem efeito)
- **Depois**: Filtros totalmente funcionais com atualização dinâmica
- **Novos Casos de Uso**:
  - Planejamento separado para FORESEA vs. TERCEIROS
  - Análise de impacto por domínio
  - Simulações de consolidação

### Experiência do Usuário
- **Antes**: Confusão entre "Soma bruta" e valores de cenário
- **Depois**: Interface clara com indicador de escopo ativo
- **Redução de Suporte**: Elimina dúvidas sobre "por que 9.000 não bate com contrato"

---

## 🔬 Validação

### Checklist de Testes
- [ ] Executar pipeline completo (`scripts/generate_risk_report.py`)
- [ ] Validar estrutura de `scenarios_by_scope` no JSON
- [ ] Abrir dashboard HTML e testar filtros de escopo na Aba 3
- [ ] Verificar que label de escopo atualiza ao trocar filtro
- [ ] Confirmar que valores de AppPoints mudam ao trocar escopo
- [ ] Verificar que cenários AS-IS/SANEADO/OTIMIZADO respondem ao filtro
- [ ] Confirmar que Aba 4 não exibe mais valores hardcoded
- [ ] Validar que gráfico Chart.js atualiza ao trocar escopo

### Métricas de Qualidade
```python
# Exemplo de dados esperados em scenarios_by_scope
{
    'foresea': {
        'asis': {'pA': 150, 'pC': 50, 'bA': 80, 'bC': 20},
        'saneado': {'pA': 140, 'pC': 45, 'bA': 75, 'bC': 18},
        'otimizado': {'pA': 120, 'pC': 60, 'bA': 70, 'bC': 25}
    },
    'terceiros': {
        'asis': {'pA': 20, 'pC': 5, 'bA': 15, 'bC': 3},
        'saneado': {'pA': 18, 'pC': 4, 'bA': 14, 'bC': 2},
        'otimizado': {'pA': 15, 'pC': 6, 'bA': 13, 'bC': 4}
    },
    'todos': {
        'asis': {'pA': 170, 'pC': 55, 'bA': 95, 'bC': 23},
        'saneado': {'pA': 158, 'pC': 49, 'bA': 89, 'bC': 20},
        'otimizado': {'pA': 135, 'pC': 66, 'bA': 83, 'bC': 29}
    }
}
```

---

## 📁 Arquivos Modificados

1. **scripts/reporting/html_data_processor.py**
   - Linhas 90-170: Implementação de `scenarios_by_scope`
   - Linha 185: Remoção de `scenario_points_total`

2. **scripts/reporting/ab3_cenarios.py**
   - Linhas 58-65: Substituição de "Soma bruta" por label de escopo

3. **scripts/reporting/ab4_eventos.py**
   - Linhas 17-32: Remoção de referências a `scenario_points_total`

4. **scripts/reporting/html_template.py**
   - Linha 142: Mudança de `rawScenarios` para `scenariosByScope`
   - Linha 145: Adição de variável global `currentScope`
   - Linhas 156-180: Refatoração de `loadScenario()` para usar escopo dinâmico
   - Linhas 416-458: Implementação completa de `updateScopeFilter()`

---

## 🔄 Retrocompatibilidade

### Campos Mantidos
- `scenarios_data`: Mantido para compatibilidade com código legado (aponta para `scenarios_by_scope['foresea']`)
- `scenario_points`: Continua com cálculos NEM originais (sem mudanças)

### Campos Removidos
- `scenario_points_total`: Removido (era incorreto e confuso)

### Migração para Código Existente
Módulos que dependem de `scenarios_data` continuam funcionando sem mudanças. Para adotar filtros de escopo, usar:
```python
# Novo padrão
analytics['scenarios_by_scope'][escopo_desejado][cenario]

# Compatibilidade legada
analytics['scenarios_data']  # Equivalente a scenarios_by_scope['foresea']
```

---

## 🎓 Lições Aprendidas

1. **Clareza Semântica**: Termos como "Soma bruta" sem contexto geram confusão. Preferir "Concorrência Real (NEM)" ou "Capacidade Simultânea"

2. **Separation of Concerns**: Dados de backend (Python) devem vir segregados. Filtros no frontend (JavaScript) devem apenas alternar entre datasets prontos, não recalcular.

3. **Validação Stateless**: Funções JavaScript não devem manter estado implícito. Usar variável global explícita (`currentScope`) para rastreamento.

4. **Progressive Enhancement**: Filtros de escopo adicionados sem quebrar funcionalidade existente. Código legado continua funcionando com escopo padrão.

---

## 📌 Próximos Passos

### Melhorias Futuras (Opcionais)
1. **Persistência de Filtro**: Salvar preferência de escopo no `localStorage`
2. **Aba 6 (Peak Contributors)**: Aplicar mesmo padrão de filtro de escopo
3. **Exportação Filtrada**: CSV exports respeitarem escopo selecionado
4. **Comparação Side-by-Side**: Visualização simultânea de FORESEA vs. TERCEIROS

### Documentação Técnica
- Atualizar `docs/SISTEMA_DOCUMENTACAO.md` com novo fluxo de filtros
- Adicionar exemplos de uso de `scenarios_by_scope` para desenvolvedores futuros

---

**Status**: ✅ Implementação Completa  
**Pronto para Testes**: Sim  
**Breaking Changes**: Não (retrocompatível)  
**Requer Revalidação**: Sim (testes funcionais no dashboard)
