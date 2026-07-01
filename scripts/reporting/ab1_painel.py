# scripts/reporting/ab1_painel.py
from .html_helpers import fmt_br


def render_tab_painel(analytics, identity_analytics):
    """Renders the 'Painel Operacional' tab content."""
    painel = analytics.get('painel_data', {})
    folga = painel.get('folga', 0)
    folga_color = 'var(--success)' if folga >= 0 else 'var(--danger)'

    return f"""
<div id="tab-painel" class="container tab-content active">

<div class="card">
<h2 class="card-header">📊 Visão Executiva - Resumo de Identidades</h2>
<div class="stats-grid">

<div class="stat-card border-success">
<div class="stat-value" style="color: var(--success);">{fmt_br(painel.get('usuarios_ativos', 0))}</div>
<div class="stat-title">Usuários Ativos Analisados</div>
<div class="stat-subtitle">Total de usuários ACTIVE em todos os ambientes</div>
</div>

<div class="stat-card border-primary">
<div class="stat-value">{fmt_br(painel.get('usuarios_plano', 0))}</div>
<div class="stat-title">Usuários no Plano de Licença</div>
<div class="stat-subtitle">FORESEA + PARCEIRO + TERCEIRO (com domínio válido)</div>
</div>

<div class="stat-card border-warning">
<div class="stat-value">{fmt_br(painel.get('authorized', 0))}</div>
<div class="stat-title">Authorized</div>
<div class="stat-subtitle">Licença dedicada (acesso garantido)</div>
</div>

<div class="stat-card border-accent">
<div class="stat-value">{fmt_br(painel.get('concurrent', 0))}</div>
<div class="stat-title">Concurrent</div>
<div class="stat-subtitle">Pool compartilhado (modelo offshore)</div>
</div>

<div class="stat-card border-secondary">
<div class="stat-value">{fmt_br(painel.get('premium', 0))}</div>
<div class="stat-title">Premium</div>
<div class="stat-subtitle">Entitlement O&G (módulos críticos)</div>
</div>

</div>
</div>

<div class="card">
<h2 class="card-header">🏢 Distribuição por Domínio</h2>
<div class="stats-grid">

<div class="stat-card" style="border-bottom: 4px solid #2563eb;">
<div class="stat-value" style="color: #2563eb;">{fmt_br(painel.get('dominio_foresea', 0))}</div>
<div class="stat-title">@foresea.com</div>
<div class="stat-subtitle">Colaboradores Foresea (permanentes)</div>
</div>

<div class="stat-card" style="border-bottom: 4px solid #10b981;">
<div class="stat-value" style="color: #10b981;">{fmt_br(painel.get('dominio_parceiro', 0))}</div>
<div class="stat-title">@foresea-partner.com</div>
<div class="stat-subtitle">Parceiros e contratados</div>
</div>

<div class="stat-card" style="border-bottom: 4px solid #f59e0b;">
<div class="stat-value" style="color: #f59e0b;">{fmt_br(painel.get('dominio_terceiro', 0))}</div>
<div class="stat-title">Outros Domínios</div>
<div class="stat-subtitle">Terceiros e prestadores</div>
</div>

<div class="stat-card" style="border-bottom: 4px solid #ef4444;">
<div class="stat-value" style="color: #ef4444;">{fmt_br(painel.get('dominio_sem_dominio', 0))}</div>
<div class="stat-title">Sem Domínio</div>
<div class="stat-subtitle">Requer revisão de email</div>
</div>

</div>
</div>

<div class="card" style="border-left: 4px solid var(--danger);">
<h2 class="card-header">⚡ Capacidade NEM vs Contrato</h2>
<div class="stats-grid">

<div class="stat-card">
<div class="stat-value" style="color: var(--danger);">{fmt_br(painel.get('true_peak', 0))}</div>
<div class="stat-title">Pico Real (P100)</div>
<div class="stat-subtitle">Máximo histórico de AppPoints simultâneos</div>
</div>

<div class="stat-card">
<div class="stat-value" style="color: var(--warning);">{fmt_br(painel.get('p95', 0))}</div>
<div class="stat-title">Pico Seguro (P95)</div>
<div class="stat-subtitle">Percentil 95 - referência de planejamento</div>
</div>

<div class="stat-card">
<div class="stat-value">{fmt_br(painel.get('contratado', 0))}</div>
<div class="stat-title">Capacidade Contratada</div>
<div class="stat-subtitle">Limite do contrato de licenciamento</div>
</div>

<div class="stat-card">
<div class="stat-value" style="color: {folga_color};">{fmt_br(folga)}</div>
<div class="stat-title">Folga / Déficit</div>
<div class="stat-subtitle">Diferença entre contrato e P95</div>
</div>

<div class="stat-card">
<div class="stat-value">{painel.get('percentual_uso', 0)}%</div>
<div class="stat-title">% Uso do Contrato (P95)</div>
<div class="stat-subtitle">Percentual de ocupação do contrato</div>
</div>

</div>
</div>

</div>
"""