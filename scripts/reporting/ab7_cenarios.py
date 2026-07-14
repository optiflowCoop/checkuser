# scripts/reporting/ab7_cenarios.py
from .html_helpers import fmt_br


def _render_cenario_conciliado(reconciliation_data):
    """Dimensionamento oficial de AppPoints para o MAS 9: população
    conciliada AD × Maximo, licença por presença real ajustada por rotação
    offshore. Reage ao mesmo seletor de escopo do simulador abaixo."""
    if not reconciliation_data:
        return ''
    nem0 = reconciliation_data['stats']['nem_by_scope'].get('foresea', {'p50': 0, 'p95': 0, 'p100': 0})
    return f"""
        <div class="card">
            <h2 class="card-header">Cenário Conciliado — Dimensionamento MAS 9</h2>
            <p class="card-desc">População = usuários ativos no Maximo conciliados com conta ativa no AD (e-mail,
            prefixo de e-mail ou nome completo). Presença medida sobre a janela de embarque de cada pessoa (blocos de
            rotação detectados no próprio histórico de login), não o calendário corrido — Authorized só compensa
            economicamente acima de 30–33% de presença ajustada; cargos de aprovação mantêm Authorized por garantia de
            acesso. Terceiros ativos não conciliados permanecem como Concurrent.</p>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="cardScopedConciliados">{fmt_br(nem0.get('conciliados', 0))}</div>
                    <div class="stat-title">Conciliados AD × Maximo</div>
                    <div class="stat-subtitle" id="cardScopedTerceiros">+{fmt_br(nem0.get('terceiros_ativos', 0))} terceiros ativos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="cardScopedAuthConc">{fmt_br(nem0.get('authorized', 0))} / {fmt_br(nem0.get('concurrent', 0))}</div>
                    <div class="stat-title">Authorized / Concurrent</div>
                    <div class="stat-subtitle">Reserva fixa <span id="cardScopedReserva">{fmt_br(nem0['reserva_authorized'])}</span> pts</div>
                </div>
                <div class="stat-card stat-card-warning">
                    <div class="stat-value" id="cardScopedP95">{fmt_br(nem0['p95'])}</div>
                    <div class="stat-title" id="cardScopedP95Label">P95 — FORESEA + PARCEIRO</div>
                    <div class="stat-subtitle">P100 <span id="cardScopedP100">{fmt_br(nem0['p100'])}</span> · teto 1.200</div>
                </div>
            </div>
            <p class="card-footnote">Acompanha o seletor de escopo do simulador abaixo. Detalhamento por usuário: Excel
            aba 24_Cenario_Conciliado_Usuarios (resumo na aba 17) e <code>cenario_conciliado_licencas.csv</code>.</p>
        </div>
    """


def _render_critical_title_checkboxes(critical_titles):
    items = []
    for t in critical_titles:
        t_upper = str(t).strip().upper()
        items.append(f"""
            <label class="sim-title-chip">
                <input type="checkbox" class="sim-title-toggle" value="{t_upper}" checked onchange="runSimulator()">
                <span>{t_upper}</span>
            </label>""")
    return ''.join(items)


def render_tab_apppoints(analytics, reconciliation_data=None):
    """Renders the 'Cenários de AppPoints' tab content."""
    sim_defaults = analytics.get('simulator_defaults', {}) or {}
    onshore_floor = sim_defaults.get('onshoreFloor', 120)
    offshore_floor = sim_defaults.get('offshoreFloor', 60)
    critical_titles = sim_defaults.get('criticalTitles', [])

    return f"""
    <div id="tab-apppoints" class="container tab-content">
        {_render_cenario_conciliado(reconciliation_data)}
        <div class="card">
            <div class="card-header">
                <div>
                    <h2 style="margin:0;">Simulador de Cenários</h2>
                    <p class="card-desc" style="margin-top:4px;">Parte da população real (por escopo) e reclassifica
                    Authorized/Concurrent com os parâmetros abaixo. Ajuste os pisos de login e os cargos críticos até
                    o total de AppPoints bater a meta que você quer testar contra o teto contratado.</p>
                </div>
            </div>
            <div class="filter-bar">
                <span class="filter-bar-label">Escopo</span>
                <label class="radio-label">
                    <input type="radio" name="scopeFilter" value="foresea" checked onchange="updateScopeFilter()">
                    <span>FORESEA + PARCEIRO</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="scopeFilter" value="terceiros" onchange="updateScopeFilter()">
                    <span>TERCEIROS</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="scopeFilter" value="integracao" onchange="updateScopeFilter()">
                    <span>INTEGRAÇÃO</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="scopeFilter" value="todos" onchange="updateScopeFilter()">
                    <span>TODOS</span>
                </label>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; align-items: start;">
                <div class="simulator-inputs" style="display: flex; flex-direction: column; gap: 1rem;">
                    <div>
                        <label style="font-size:0.8rem; font-weight:600; color: var(--text-light); text-transform:uppercase; letter-spacing:0.5px;">
                            Cenário de pico (dimensiona o pool Concurrent)
                        </label>
                        <div style="display:flex; flex-wrap:wrap; gap:0.5rem; margin-top:0.5rem;">
                            <label class="radio-label">
                                <input type="radio" name="simPeakScenario" value="p50" onchange="setSimPeakScenario('p50')">
                                <span>P50 — uso típico</span>
                            </label>
                            <label class="radio-label">
                                <input type="radio" name="simPeakScenario" value="p95" checked onchange="setSimPeakScenario('p95')">
                                <span>P95 — planejamento (padrão)</span>
                            </label>
                            <label class="radio-label">
                                <input type="radio" name="simPeakScenario" value="p100" onchange="setSimPeakScenario('p100')">
                                <span>P100 — pico histórico</span>
                            </label>
                        </div>
                        <p class="card-footnote" style="margin:0.4rem 0 0;">Concurrent não usa o total de elegíveis: parte da população nunca
                        está logada ao mesmo tempo. O simulador ancora no P50/P95/P100 REAL medido no Cenário Conciliado (mesma fonte da Aba 8 —
                        Peak Contributors) e escala pelo número de elegíveis simulado — não é um cálculo de pico paralelo. Authorized é reserva
                        fixa (100% do custo, sempre) e não usa esse ajuste.</p>
                    </div>
                    <div class="calc-input-group">
                        <label>
                            <span>Piso Onshore (Authorized) — logins/60d</span>
                        </label>
                        <input type="number" id="simOnshoreFloor" value="{onshore_floor}" oninput="runSimulator()">
                    </div>
                    <div class="calc-input-group">
                        <label>
                            <span>Piso Offshore (Authorized) — logins/60d</span>
                        </label>
                        <input type="number" id="simOffshoreFloor" value="{offshore_floor}" oninput="runSimulator()">
                    </div>
                    <div>
                        <label style="font-size:0.8rem; font-weight:600; color: var(--text-light); text-transform:uppercase; letter-spacing:0.5px;">
                            Cargos críticos (Authorized garantido acima do piso)
                        </label>
                        <div id="simTitleChips" style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-top:0.5rem;">
                            {_render_critical_title_checkboxes(critical_titles)}
                        </div>
                        <div style="display:flex; gap:0.5rem; margin-top:0.6rem;">
                            <input type="text" id="simNewTitle" placeholder="Adicionar cargo (ex.: TORRISTA)" style="flex:1; padding:0.4rem 0.6rem; border:1px solid var(--border); border-radius:6px;">
                            <button class="btn-export" onclick="addSimCriticalTitle()" style="white-space:nowrap;">+ Adicionar</button>
                        </div>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:0.5rem; padding-top:0.5rem; border-top:1px solid var(--border);">
                        <button class="btn-export" onclick="setSimOverride('all_concurrent')">Forçar tudo Concurrent</button>
                        <button class="btn-export" onclick="setSimOverride('all_authorized')">Forçar tudo Authorized</button>
                        <button class="btn-export" onclick="setSimOverride(null)">Restaurar regra atual</button>
                    </div>
                    <p class="card-footnote" style="margin:0;">Terceirizados sem acesso administrativo (MAXADMIN) continuam Concurrent mesmo em "Forçar tudo Authorized" — regra de negócio fixa, não editável aqui.</p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div class="simulator-total">
                        <h3 style="margin: 0 0 0.75rem 0; font-size: 0.85rem; color: var(--text-light); text-transform: uppercase; letter-spacing: 0.5px; font-weight:600;" id="simTotalLabel">AppPoints Requeridos (cenário simulado — pico P95)</h3>
                        <div id="calcTotalDisplay" style="font-size: 3rem; font-weight: 700; color: var(--primary); line-height:1.2; word-break: break-word; margin-bottom: 0.75rem;">0</div>
                        <div style="font-size: 0.85rem; color: var(--text-light); padding-top: 0.75rem; border-top: 1px solid var(--border);">
                            <strong id="currentScopeLabel" style="color: var(--secondary);">Escopo: FORESEA + PARCEIRO</strong><br>
                            <span id="simDeltaText">vs. regra atual: 0 pts · 0 usuários migrando</span>
                        </div>
                        <div id="calcAlertBox" class="alert-inline" style="display:none;">Teto excedido</div>
                    </div>
                    <div class="simulator-chart">
                        <canvas id="simChart" style="max-height: 100%;"></canvas>
                    </div>
                    <p class="card-footnote" id="simPeakRefText" style="margin:0;">carregando...</p>
                </div>
            </div>
        </div>
        <div class="card">
            <h2 class="card-header">Regras de Negócio</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; align-items: start;">
                <div class="legend-grid" style="display: grid; grid-template-columns: 1fr; gap: 1rem;">
                    <div class="legend-box">
                        <h3>Entitlement (módulos)</h3>
                        <ul class="legend-list">
                            <li><strong>PREMIUM:</strong> acesso a módulos críticos O&G (PTW, HSE, permissões de trabalho).</li>
                            <li><strong>BASE:</strong> acesso a módulos padrão (Compras, PCM, Ordem de Serviço).</li>
                        </ul>
                    </div>
                    <div class="legend-box">
                        <h3>Licença (acesso)</h3>
                        <ul class="legend-list">
                            <li><strong>AUTHORIZED:</strong> licença dedicada, disponibilidade garantida 100%.</li>
                            <li><strong>CONCURRENT:</strong> licença compartilhada (pool), dimensionada pelo pico real de logins.</li>
                        </ul>
                    </div>
                </div>
                <div class="legend-box">
                    <h3>Capacidade Real (NEM)</h3>
                    <ul class="legend-list">
                        <li><strong>P100:</strong> máximo histórico de logins simultâneos.</li>
                        <li><strong>P95:</strong> referência estatística de planejamento (95% dos dias).</li>
                        <li><strong>Contratado:</strong> capacidade adquirida no contrato.</li>
                        <li><strong>Folga:</strong> espaço remanescente antes do limite contratual.</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """
