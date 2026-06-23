# Documentação de Capacity Planning e Inteligência MAS 9.1 (Foresea)

Este documento detalha os pilares de inteligência e regras de negócio aplicados pelo algoritmo na migração e otimização do licenciamento para o IBM Maximo Application Suite (MAS 9.1).

## 1. O Problema da "Migração Cega" (As-Is)
A transposição direta de utilizadores do Maximo 7.6 para o MAS 9.1 sem sanitização gera um passivo inflado (Opex elevado). A abordagem inicial tratava todas as identidades ativas na base de dados como consumidoras de licenças de forma 1:1, ignorando a ociosidade, o turnover e a escala de turnos offshore.

## 2. A Evolução em Três Pilares de Inteligência

A arquitetura de otimização foi estruturada em três camadas consecutivas aplicadas pelo motor em Python.

### Pilar 1: Saneamento Baseado em Dados (Filtro > 90 Dias)
* **Critério:** O sistema analisa a tabela `LOGINTRACKING` consolidada das 7 instâncias.
* **Ação:** Identidades com status `ACTIVE` no banco, mas que não registraram um único evento de login nos últimos 90 dias, recebem a recomendação `INATIVO (>90d)`.
* **Impacto no ROI:** Estas contas são expurgadas do cálculo de faturamento no cenário final, criando uma economia imediata.

### Pilar 2: Otimização de Perfil O&G (Downgrades Inteligentes)
A indústria de Óleo e Gás exige obrigatoriamente licenciamento **Premium** para módulos críticos (HSE, Permissão de Trabalho, Drilling).
* **Critério:** O algoritmo mapeia os grupos de segurança (Security Groups).
* **Ação:** Se o utilizador possui acesso Premium, mas o seu cargo não exige acesso a módulos O&G contextuais, a máquina emite um alerta de `DOWNGRADE_CANDIDATE`.
* **Impacto no ROI:** O custo desse utilizador cai de 15 pontos (Premium Conc) para 10 pontos (Base Conc), ou de 5 pontos (Premium Auth) para 3 pontos (Base Auth).

### Pilar 3: Inteligência Estatística de Escalas (High Watermark Analytics)
O erro mais grave em Capacity Planning é utilizar uma média de mercado plana (ex: assumir que 3 eletricistas contratados consomem exatamente 1 licença simultânea, ou 33%).
* **Critério:** O motor Python cruza o histórico diário de acessos (`LOGINTRACKING`) com o passivo físico (`PERSON`).
* **Ação:** A concorrência é calculada **por cargo**. O sistema extrai a mediana cotidiana (P50), o pico seguro (P95) e o cenário de estresse máximo (P100). Cargos críticos da base (Onshore) e Lideranças são blindados e recebem alocação fixa de 100% (`AUTHORIZED`) para garantia de SLA 24/7.
* **Impacto no ROI:** Permite dimensionar o orçamento exato para acomodar os *handovers* de turno nas Sondas sem exceder o teto contratual de 1.200 AppPoints.

## 3. Evolução das Telas de Dashboard (UX/UI)
O sistema de relatórios (`html_builder.py`) evoluiu de um visualizador de tabelas estáticas para um Cockpit Gerencial interativo:
1. **Painel Operacional:** Consolidou a visão de identidades reais vs passivo contratual (Terceiros/Parceiros).
2. **Filtros de Cenário e Simulador de ROI:** Permite aos gestores alternar entre:
   - *Cenário 1:* Migração Cega (Opex bruto).
   - *Cenário 2:* Pós-Saneamento (Expurgo de Inativos).
   - *Cenário 3:* Otimizado (Inteligência Artificial de Escalas e Downgrades aplicados).
3. **Simulador de Estresse:** Gráficos que provam a saúde da plataforma mesmo durante Picos Seguros (Percentil 95) ou Emergências (Percentil 100).
4. **Exportação Acionável:** Integração nativa JavaScript para exportar planos de ação diretos para Excel (Service Desk/RH).