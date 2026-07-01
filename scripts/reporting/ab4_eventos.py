# scripts/reporting/ab4_eventos.py
from .html_helpers import fmt_br


def render_tab_eventos(analytics):
    """Renders the 'Eventos Críticos' tab content."""
    scenario_points = analytics['scenario_points']
    return f"""
    <div id="tab-eventos" class="container tab-content">
        <div class="alert-box" style="border-left-color: var(--warning); background-color: #fffbeb;">
            <strong style="color: #b45309;">📊 Simulador de Teto de AppPoints (Eventos de Sonda)</strong>
            <p style="color: #92400e;">Teste a resistência da arquitetura de licenciamento. O que acontece com o consumo se houver um evento atípico na Foresea?</p>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem;">
            <div>
                <div class="card">
                    <h3 style="margin-top:0; font-size:1.1rem; color:var(--primary);">🚀 Disparadores de Cenário</h3>
                    <div class="event-card" onclick="triggerEventScenario('p50')">
                        <h4>🟢 Cenário Cotidiano (Mediana - P50)</h4>
                        <p>Simula um dia comum. Consome aprox. {fmt_br(scenario_points['p50'])} AppPoints baseado em concorrência real (NEM).</p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('p95')" style="border-left-color: var(--warning);">
                        <h4>🟡 Pico Seguro (Percentil 95)</h4>
                        <p>O teto projetado pela máquina. Consome aprox. {fmt_br(scenario_points['p95'])} AppPoints. Referência para planejamento de capacidade.</p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('p100')" style="border-left-color: var(--danger);">
                        <h4>🔴 Emergência Operacional (P100)</h4>
                        <p>Pico máximo histórico. Consome aprox. {fmt_br(scenario_points['p100'])} AppPoints. Cenário de stress máximo registrado.</p>
                    </div>
                    <div class="event-card" onclick="triggerEventScenario('blackout')" style="border-left-color: #7c3aed; background: #faf5ff; border-color:#e9d5ff">
                        <h4>⚡ Blackout Total (100% de Acessos)</h4>
                        <p>Cenário extremo: Todos os usuários simultâneos. Consome aprox. {fmt_br(scenario_points['blackout'])} AppPoints. Hipótese para disaster recovery.</p>
                    </div>
                </div>
            </div>
            <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <h3 id="eventCeilingLabel" style="margin-top:0; font-size:1.2rem; color:var(--secondary);">Termômetro de Impacto (Limite)</h3>
                <div style="height: 280px; position: relative;">
                    <canvas id="eventChart"></canvas>
                </div>
                <div id="eventOutputBox" style="padding: 1rem; text-align: center; font-weight: bold; border-radius: 6px; font-size: 1.1rem; margin-top: 1rem; background: #ecfdf5; color:#047857;">
                    Selecione um cenário ao lado...
                </div>
            </div>
        </div>
    </div>
    """