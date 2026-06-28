# 📖 CHECKUSER - Sistema de Governança e Otimização de Licenças Maximo

## ✨ O que é?

Sistema completo e automatizado para:
- 🔍 **Descoberta de Identidades**: Detecção de colisões, reuso de logins e ambiguidades
- 📍 **Localização Correta**: LocationSite do PersonGroupView como source-of-truth
- 📊 **Análise de Uso Real**: LoginTracking consolidado com classificação Onshore/Offshore
- 💰 **Otimização de AppPoints**: Recomendações de licenciamento baseadas em dados reais
- 🎯 **Baseline Funcional**: Identificação de divergências de acesso por cargo
- 📄 **Relatórios Executivos**: Dashboard HTML + Excel para tomadores de decisão

---

## 🚀 Quick Start

### 1. Primeira Execução (Extração + Processamento)
```bash
python run_pipeline.py
```
**Resultado**: Todos os dados extraídos, processados e relatórios gerados

### 2. Atualização Rápida (sem DB2)
```bash
python run_pipeline.py --skip-extract
```
**Resultado**: Reprocessa dados existentes (mais rápido)

### 3. Apenas LoginTracking Recente
```bash
python src/analyze_usage.py
python integrate_usage_data.py
```
**Resultado**: Atualiza análise de uso com dados corretos

---

## 📚 Documentação

| Documento | Conteúdo |
|-----------|----------|
| **GUIA_USO.md** | Como usar o sistema, interpretação de resultados, troubleshooting |
| **PIPELINE.md** | Arquitetura, fluxo de dados, etapas de processamento |
| **PROJECT_STATUS.md** | Fases do projeto, status atual, roadmap |
| **LOGICA_OFFSHORE_ONSHORE.md** | Regras de negócio para classificação de licenças |
| **CORRECOES_JUNHO_2026.md** | ⭐ NOVO - Correções implementadas (LocationSite, LoginTracking, etc.) |

---

## 📊 Status Atual (v3.1)

| Componente | Status | Notas |
|-----------|--------|-------|
| **Identidades** | ✅ Completo | 13.272 usuários processados |
| **LocationSite** | ✅ Corrigido | Source-of-truth implementado |
| **LoginTracking** | ✅ Consolidado | 373.123 registros de múltiplas fontes |
| **Onshore/Offshore** | ✅ Corrigido | Baseado em dados reais |
| **XLSX** | ✅ Atualizado | 768 registros com dados corretos |
| **Dashboard HTML** | ✅ Pronto | Inclui análise de uso atualizada |

---

## 🔧 Recursos Principais

### Source-of-Truth para Localização
- **PersonGroupView.LocationSite** → LOCATION (N08, ODN1, etc.)
- Classificação automática: ONSHORE vs OFFSHORE
- Exemplo: ALESSANDROCORREA = N08 → OFFSHORE ✅

### Consolidação de LoginTracking
- Múltiplas fontes: `consolidated_logintracking.csv` + `DadosTabelas/`
- Total: 373.123 registros
- Eliminação automática de duplicatas

### Análise de Uso Real (Phase 3)
- Parse correto de data: `YYYY-MM-DD-HH.MM.SS`
- Cálculo preciso de `DAYS_SINCE_LAST`
- Identificação de `POWER_USERS` por módulo O&G

### Otimização de AppPoints
- Segregação FORESEA vs TEMPORARY
- Simulação de pico simultâneo
- Recomendações de downgrade/não-migração

---

## 📁 Estrutura de Diretórios

```
CHECKUSER/
├── docs/                          # 📖 Documentação
│   ├── README.md                  # Este arquivo
│   ├── GUIA_USO.md               # Como usar
│   ├── PIPELINE.md               # Arquitetura
│   ├── PROJECT_STATUS.md         # Status do projeto
│   ├── LOGICA_OFFSHORE_ONSHORE.md # Regras de negócio
│   └── CORRECOES_JUNHO_2026.md   # Correções recentes
│
├── src/                           # 🐍 Scripts principais
│   ├── analyze_usage.py          # Phase 3: Análise de uso (ATUALIZADO v3.1)
│   ├── consolidate_user_access.py
│   ├── normalize.py
│   ├── cross_env_userid_reuse.py
│   ├── login_conflicts.py
│   ├── identity_classification.py
│   └── license_optimizer.py
│
├── scripts/                       # 🔧 Utilitários
│   ├── generate_risk_report.py   # Gera HTML/Excel
│   └── services/
│       └── app_points.py
│
├── config/                        # ⚙️ Configurações
│   ├── licensing_rules.json       # Regras de negócio externalizadas
│   └── config.yaml
│
├── output/                        # 📊 Saída de dados
│   ├── consolidated/              # Dados processados
│   │   ├── usage_analysis_phase3.csv (com LOCATION)
│   │   └── consolidated_persongroupview.csv
│   └── reports/                   # Relatórios finais
│       └── maximo_risk_and_optimization_workbook.xlsx
│
├── DadosTabelas/                  # 📥 Entrada: LoginTracking recente
│   ├── LOGINTRACKING_202606251431.csv
│   ├── LOGINTRACKING_202606251433.csv
│   └── LOGINTRACKING_202606251454.csv
│
├── run_pipeline.py               # 🎯 Orquestrador principal
├── integrate_usage_data.py       # ⭐ NOVO: Integra dados no XLSX
├── processar_pipeline.bat         # Atalho Windows
└── gerar_relatorio.bat            # Atalho Windows
```

---

## 🎯 Exemplo Real: ALESSANDROCORREA

### Antes (v3.0)
```
USERID: ALESSANDROCORREA
LOCATION: [VAZIO] ❌
OPERATIONAL_PRESENCE: [INDEFINIDO] ❌
DAYS_SINCE_LAST: 999 ❌
```

### Depois (v3.1)
```
USERID: ALESSANDROCORREA
DISPLAYNAME: ALESSANDRO DE CARVALHO CORREA
LOCATION: N08 ✅ (do PersonGroupView.LocationSite)
OPERATIONAL_PRESENCE: OFFSHORE ✅ (classificação automática)
LOGIN_COUNT_90D: 1623 (analisados 373k+ registros)
DAYS_SINCE_LAST: 15 ✅ (parse correto de data)
USER_TIER: OFFSHORE_STD
```

---

## 📈 Resultados

| Métrica | Valor |
|---------|-------|
| Usuários processados | 13.272 |
| Usuários com LocationSite corrigido | 768 |
| Registros de LoginTracking consolidados | 373.123 |
| Formato de data suportado | YYYY-MM-DD-HH.MM.SS |
| Etapas do pipeline | 11 |
| Tempo de execução (completo) | ~5-10 min |
| Tempo de execução (sem DB2) | ~2-3 min |

---

## 🐛 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| LOCATION vazio | Verificar `consolidated_persongroupview.csv` |
| Dashboard mostra ⚠️ | Executar `python analyze_usage.py` |
| DAYS_SINCE_LAST = 999 | Verificar se LoginTracking foi extraído |
| Erro de parse de data | Confirmar formato: `YYYY-MM-DD-HH.MM.SS` |

---

## 📞 Próximos Passos

1. **Validar dados**: Comparar resultados com análises manuais
2. **Revisar recomendações**: Analisar sugestões de downgrade/não-migração
3. **Preparar AD**: Validação com Active Directory (Etapa 4)
4. **Migração MAS 9**: Importação dos usuários com dados corretos

---

## 📝 Changelog Recente

### v3.1 (Junho 2026) - LocationSite Corrections
- ✅ PersonGroupView.LocationSite como source-of-truth
- ✅ Consolidação de LoginTracking de múltiplas fontes
- ✅ Parse correto de data: YYYY-MM-DD-HH.MM.SS
- ✅ Classificação Onshore/Offshore refinada
- ✅ Script novo: integrate_usage_data.py
- ✅ 768 registros XLSX atualizados com dados corretos

### v3.0 (Junho 2026) - Phase 3 Launch
- Phase 3: Análise de uso e otimização de AppPoints
- Segregação FORESEA vs TEMPORARY
- Simulação de pico simultâneo

### v2.1 (Junho 2026) - Baseline Standardization
- Baseline funcional por PERSONGROUP
- Análise de divergências entre unidades
- Dashboard HTML redesenhado

---

## 📄 Licença

Sistema interno da FORESEA para otimização de licenças Maximo e preparação para MAS 9.

---

## 👥 Suporte

Para dúvidas, consulte:
- **GUIA_USO.md** - Interpretação de resultados
- **CORRECOES_JUNHO_2026.md** - Detalhes das correções recentes
- **PROJECT_STATUS.md** - Status do projeto e roadmap

---

**Versão**: 3.1  
**Última atualização**: Junho 2026  
**Status**: ✅ Production Ready
