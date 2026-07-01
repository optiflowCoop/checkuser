# Checklist de Teste Visual - Filtros de Escopo (Aba 3)

## 🎯 Como Testar os Filtros Implementados

### Pré-requisitos
1. Abrir o arquivo: `output/reports/maximo_unified_dashboard.html`
2. Navegar até **Aba 3: Cenários de AppPoints**

---

## ✅ Testes de Funcionamento

### Teste 1: Filtro de Escopo FORESEA + PARCEIRO (padrão)
**Passo a passo**:
1. Certificar que o radio button **"FORESEA + PARCEIRO"** está selecionado
2. Verificar que o label exibe: **"Escopo: FORESEA + PARCEIRO"**
3. Clicar no botão **"Otimizado (P95)"**
4. Observar os valores nos campos:
   - Premium Auth (pA): **216**
   - Premium Conc (pC): **521**
   - Base Auth (bA): **1**
   - Base Conc (bC): **9**
   - Total AppPoints: **~8.988**

**Resultado Esperado**: ✅ Valores devem bater com os listados acima

---

### Teste 2: Filtro de Escopo TERCEIROS
**Passo a passo**:
1. Clicar no radio button **"TERCEIROS"**
2. Aguardar atualização automática
3. Verificar que o label mudou para: **"Escopo: TERCEIROS"**
4. Observar os valores nos campos:
   - Premium Auth (pA): **0** (terceiros geralmente não têm PREMIUM AUTH)
   - Premium Conc (pC): **10**
   - Base Auth (bA): **0**
   - Base Conc (bC): **371**
   - Total AppPoints: **~3.860**

**Resultado Esperado**: ✅ Valores devem ser **muito menores** que FORESEA (terceiros têm menos licenças Premium)

---

### Teste 3: Filtro de Escopo TODOS
**Passo a passo**:
1. Clicar no radio button **"TODOS"**
2. Aguardar atualização automática
3. Verificar que o label mudou para: **"Escopo: TODOS"**
4. Observar os valores nos campos:
   - Premium Auth (pA): **216** (= FORESEA 216 + TERCEIROS 0)
   - Premium Conc (pC): **531** (= FORESEA 521 + TERCEIROS 10)
   - Base Auth (bA): **1** (= FORESEA 1 + TERCEIROS 0)
   - Base Conc (bC): **380** (= FORESEA 9 + TERCEIROS 371)
   - Total AppPoints: **~12.848**

**Resultado Esperado**: ✅ Valores devem ser a **soma exata** de FORESEA + TERCEIROS

---

### Teste 4: Alternância de Cenários com Escopo Ativo
**Passo a passo**:
1. Selecionar escopo **"FORESEA + PARCEIRO"**
2. Clicar em **"As-Is (Atual)"**
3. Anotar o valor de Premium Conc (pC): **521**
4. Clicar em **"Saneado"**
5. Observar mudança em Premium Conc (pC): **501** (redução de 20 usuários inativos)
6. Trocar escopo para **"TERCEIROS"**
7. Observar que os valores mudam para refletir o novo escopo

**Resultado Esperado**: ✅ Cada mudança de cenário ou escopo deve atualizar os valores imediatamente

---

### Teste 5: Gráfico de Pizza Responsivo
**Passo a passo**:
1. Selecionar escopo **"FORESEA + PARCEIRO"**
2. Observar distribuição no gráfico de pizza (lado direito)
3. Trocar para escopo **"TERCEIROS"**
4. Observar que o gráfico **atualiza automaticamente** refletindo a nova distribuição
5. Verificar que **BASE CONCURRENT** domina o gráfico (terceiros usam mais BASE)

**Resultado Esperado**: ✅ Gráfico deve atualizar instantaneamente ao trocar escopo

---

### Teste 6: Verificação de Campo Obsoleto Removido
**Passo a passo**:
1. Procurar visualmente na Aba 3 por qualquer texto: **"Soma bruta (XLSX)"**
2. Procurar por valor fixo **"9.000"**

**Resultado Esperado**: ❌ **NÃO** deve aparecer nenhum desses textos na Aba 3

---

### Teste 7: Consistência na Aba 4 (Eventos Críticos)
**Passo a passo**:
1. Navegar para **Aba 4: Eventos Críticos**
2. Verificar que os cards de cenário mostram valores dinâmicos
3. Confirmar que **não há** valores hardcoded "9.000"
4. Clicar em cada card (P50, P95, P100, Blackout)
5. Observar que o termômetro atualiza com valores diferentes

**Resultado Esperado**: ✅ Cada cenário deve mostrar valor único e dinâmico

---

## 🔍 Valores de Referência

### Cenários por Escopo (Otimizado)

| Escopo        | pA  | pC  | bA | bC  | Total AppPoints |
|---------------|-----|-----|----|-----|-----------------|
| FORESEA       | 216 | 521 | 1  | 9   | 8.988           |
| TERCEIROS     | 0   | 10  | 0  | 371 | 3.860           |
| TODOS         | 216 | 531 | 1  | 380 | 12.848          |

**Fórmula**: Total = (pA × 5) + (pC × 15) + (bA × 3) + (bC × 10)

---

## ⚠️ Problemas Comuns

### Filtro não muda valores
**Causa**: JavaScript não carregou ou erro no console  
**Solução**: 
1. Abrir **DevTools** (F12)
2. Verificar **Console** por erros
3. Recarregar página (Ctrl+F5)

### Label de escopo não atualiza
**Causa**: Elemento `currentScopeLabel` não encontrado  
**Solução**: Verificar que o HTML foi gerado após as correções

### Valores zerados
**Causa**: `scenariosByScope` não carregou corretamente  
**Solução**: 
1. Reexecutar pipeline: `python scripts/generate_risk_report.py`
2. Verificar que não há erros no processamento

---

## 📊 Comportamento Esperado vs. Antes

| Aspecto                | ANTES                          | DEPOIS                              |
|------------------------|--------------------------------|-------------------------------------|
| Filtro de Escopo       | Sem efeito (decorativo)        | Totalmente funcional                |
| Valor "Soma bruta"     | 9.000 fixo (incorreto)         | Removido (substituído por NEM)      |
| Label de escopo        | Não existia                    | Dinâmico (atualiza com filtro)      |
| Cenários por escopo    | Apenas FORESEA                 | 3 escopos independentes             |
| Gráfico de pizza       | Fixo                           | Atualiza com filtro de escopo       |
| Aba 4 valores          | Hardcoded "9.000"              | Dinâmicos e corretos                |

---

## ✅ Critérios de Aceitação

Considere o teste **APROVADO** se:

- [ ] Todos os 3 filtros de escopo funcionam (FORESEA, TERCEIROS, TODOS)
- [ ] Label de escopo atualiza ao trocar filtro
- [ ] Valores numéricos mudam ao trocar escopo
- [ ] Gráfico de pizza atualiza ao trocar escopo
- [ ] Cenários (As-Is, Saneado, Otimizado) funcionam em todos os escopos
- [ ] Não há texto "Soma bruta (XLSX)" visível na Aba 3
- [ ] Não há valores fixos "9.000" na Aba 4
- [ ] Somatório correto: TODOS = FORESEA + TERCEIROS

---

## 📞 Suporte

Se algum teste falhar:

1. **Capturar screenshot** da tela
2. **Abrir Console** (F12) e copiar mensagens de erro
3. **Reportar** com:
   - Passo que falhou
   - Resultado esperado vs. obtido
   - Logs do console (se houver erros)

---

**Última Atualização**: 2025-01-03  
**Versão do Sistema**: 2.0 (Filtros de Escopo Implementados)
