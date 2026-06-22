# 📋 DIRETRIZ: HTML UNIFICADO

## ⚠️ REGRA CRÍTICA

**SEMPRE gerar UM ÚNICO arquivo HTML consolidado:**  
`output/reports/maximo_identity_sanity_report.html`

## ❌ NÃO FAZER

- ❌ Criar múltiplos HTMLs separados (identity_risk_report.html, sanity_report.html, usage_report.html)
- ❌ Gerar dashboards separados por fase
- ❌ Criar arquivos HTML temporários ou de teste no diretório reports/

## ✅ FAZER

- ✅ **UM ÚNICO HTML** com todas as seções consolidadas
- ✅ Usar **abas/accordions** para organizar conteúdo extenso
- ✅ Painel Operacional em aba separada
- ✅ Todas as fases (1, 2, 3) integradas no mesmo arquivo

## 📁 Estrutura do HTML Unificado

```
maximo_identity_sanity_report.html
├── Header (Topbar com título e data)
├── Aba 1: Dashboard Executivo
│   ├── Seção 1: Resumo Executivo Operacional
│   │   ├── Cards: Pessoas Únicas, Registros, Riscos, Colisões
│   │   ├── Cards: Segregação FORESEA vs TEMPORÁRIOS
│   │   └── Cards: Fase 2 Baseline Funcional
│   ├── Seção 2: Otimização AppPoints (Fase 3)
│   │   ├── Alert: Meta de 1.200 AppPoints
│   │   ├── Cards: OFFSHORE, ONSHORE, AUTHORIZED, CONCURRENT
│   │   ├── Cards: PREMIUM, BASE, LIMITED, IDLE
│   │   └── Top 15 Usuários FORESEA
│   └── Filtro Global
├── Aba 2: Amostras de Conflitos
│   ├── Amostra 1: Logins Reaproveitados
│   ├── Amostra 2: Conflitos de LOGINID
│   └── Amostra 3: Worklist de Identidades
├── Aba 3: Baseline Funcional
│   ├── Seção 5: Análise por TITLE (Cargo Real)
│   └── Seção 6: Visão Legada (Modo Comparativo)
└── Aba 4: Painel Operacional
    ├── Botões de Extração
    │   ├── [Extrair Tudo] → extrair_tudo.bat
    │   ├── [Extrair LoginTrack] → extrair_logintrack.bat
    │   └── [Extrair Baseline] → extrair_baseline.bat
    ├── Botões de Processamento
    │   ├── [Processar Pipeline] → processar_pipeline.bat
    │   └── [Gerar Relatório] → gerar_relatorio.bat
    └── Log/Status de execução
```

## 🔧 Implementação Técnica

### Script Principal
**Arquivo:** `scripts/generate_risk_report.py`  
**Função:** `build_html()` → retorna HTML completo como string

### Output
```python
html_path = OUT_DIR / 'maximo_identity_sanity_report.html'
html_path.write_text(html_content, encoding='utf-8')
```

### Encoding
**SEMPRE UTF-8:**
```python
with path.open('w', encoding='utf-8') as f:
    f.write(html_content)
```

## 🎨 Design Guidelines

### Estilo Grafana
- **Cards consolidados** (não listas longas)
- **Gráficos Chart.js** para visualização
- **Métricas visuais** com números grandes
- **Filtros interativos** (status, unidade, decisão)
- Listas detalhadas → Excel (não HTML)

### Responsividade
- Grid adaptativo (stats-grid)
- Mobile-friendly
- Colapso de seções (accordions)

## 📊 Dados Integrados

### Fontes de Dados
1. **consolidated_user_identity.csv** - Identidades base
2. **consolidated_user_access_normalized.csv** - Grupos e perfis
3. **consolidated_logintracking.csv** - Histórico de uso (386K registros)
4. **usage_analysis_phase3.csv** - Análise de uso e licenciamento
5. **license_optimization_recommendations.csv** - Recomendações de otimização
6. **identity_collisions_enriched.csv** - Worklist de conflitos
7. **cross_env_userid_reuse.csv** - Reuso de logins
8. **login_conflicts.csv** - Conflitos de LOGINID

### Consolidação Multi-Unidade
**CRÍTICO:** AppPoints considera **TODAS** as unidades consolidadas:
- ✅ LOGINTRACKING de todas as unidades (norbe06, norbe08, base, etc)
- ✅ Grupos O&G de todas as unidades
- ✅ Usuários únicos consolidados (não repetir mesmo usuário de unidades diferentes)

## 🚀 Fluxo de Geração

```bash
# Sempre executar em sequência
python src\analyze_usage.py        # Gera usage_analysis_phase3.csv
python src\license_optimizer.py    # Gera license_optimization_recommendations.csv
python scripts\generate_risk_report.py  # Gera HTML ÚNICO
```

## ✅ Checklist de Validação

Antes de commitar alterações em `generate_risk_report.py`:

- [ ] Gera apenas 1 arquivo HTML?
- [ ] HTML tem encoding UTF-8?
- [ ] Todas as seções presentes?
- [ ] Painel Operacional incluído?
- [ ] Dados Phase 3 integrados?
- [ ] Cards de segregação FORESEA/TEMPORÁRIOS?
- [ ] Detecção de Premium O&G funcionando?
- [ ] Gráficos Chart.js renderizando?
- [ ] Filtros funcionando (status, unidade)?
- [ ] Accordions expand/collapse OK?

## 🐛 Troubleshooting Comum

### Problema: Caracteres corrompidos (├│├º├ú)
**Causa:** Encoding incorreto  
**Solução:**
```python
html_path.write_text(html_content, encoding='utf-8')  # ✅
html_path.write_text(html_content)  # ❌ Usa default do sistema
```

### Problema: 0 usuários Premium detectados
**Causa:** LOGINTRACKING tem IDs numéricos, não nomes de apps  
**Solução:** Detectar Premium via GROUPS (não apps):
```python
has_premium = detect_premium_from_groups(groups)  # ✅
has_premium = any(is_premium_app(app) for app in app_list)  # ❌
```

### Problema: Duplicação de usuários na contagem AppPoints
**Causa:** Mesmo usuário aparece em múltiplas unidades  
**Solução:** Consolidar por USERID único:
```python
unique_users = {}
for user in all_units_data:
    userid = user['USERID'].upper()
    if userid not in unique_users:
        unique_users[userid] = user
```

## 📝 Notas de Implementação

### Painel Operacional
Adicionar na seção após Baseline Funcional:
```html
<div class="card">
    <h2 class="card-header">🛠️ Painel Operacional</h2>
    <div class="operational-panel">
        <button onclick="window.location.href='../../extrair_tudo.bat'">
            Extrair Tudo
        </button>
        <!-- mais botões -->
    </div>
</div>
```

### Detecção O&G via Grupos
Keywords para grupos Premium:
- OG_, O&G, OILGAS, PETROLEUM, PETRO
- HSE, DRILLING, DRILL, RIG, FPSO
- PFWORK, LOCREC, COMPLIANCE, WELL

## 🎯 Objetivo Final

Dashboard web **único, consolidado e completo** que:
- ✅ Substitui múltiplos relatórios
- ✅ Visualização tipo Grafana (cards + gráficos)
- ✅ Dados de todas as unidades integrados
- ✅ Detalhes no Excel, síntese visual no HTML
- ✅ Fácil navegação por abas/accordions
- ✅ Painel operacional para execução de scripts

---

**Data de criação:** 2026-06-22  
**Mantido por:** GitHub Copilot CLI  
**Versão:** 1.0
