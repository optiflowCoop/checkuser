# scripts/reporting/ab3_cenarios.py
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


def render_tab_apppoints(analytics, reconciliation_data=None):
    """Renders the 'Cenários de AppPoints' tab content."""
    return f"""
    <div id="tab-apppoints" class="container tab-content">
        {_render_cenario_conciliado(reconciliation_data)}
        <div class="card">
            <div class="card-header">
                <div>
                    <h2 style="margin:0;">Simulador de Cenários</h2>
                    <p class="card-desc" style="margin-top:4px;">Selecione um cenário pré-definido ou ajuste os campos manualmente.</p>
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
            <div style="display: grid; grid-template-columns: 280px 1fr; gap: 1.5rem; align-items: stretch;">
                <div class="preset-btn-group" style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <button class="preset-btn" id="btnAsIs" onclick="loadScenario('asis', this)" style="flex: 1; min-height: 120px;">
                        <strong style="font-size: 1rem;">1. Cenário Atual</strong>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Consumo se todos os usuários atuais fossem migrados sem otimização.</p>
                    </button>
                    <button class="preset-btn" id="btnSaneado" onclick="loadScenario('saneado', this)" style="flex: 1; min-height: 120px;">
                        <strong style="font-size: 1rem;">2. Pós-Saneamento</strong>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Consumo após desativar usuários inativos (&gt; 90 dias).</p>
                    </button>
                    <button class="preset-btn active" id="btnOtimizado" onclick="loadScenario('otimizado_p95', this)" style="flex: 1; min-height: 120px;">
                        <strong style="font-size: 1rem;">3. Otimizado — Pico P95</strong>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Todas as otimizações aplicadas, fator de pico (P95).</p>
                    </button>
                    <button class="preset-btn" id="btnOtimizadoP50" onclick="loadScenario('otimizado_p50', this)" style="flex: 1; min-height: 120px;">
                        <strong style="font-size: 1rem;">4. Otimizado — Mediana P50</strong>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Todas as otimizações aplicadas, fator de uso mediano (P50).</p>
                    </button>
                </div>
                <div class="simulator-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; align-items: start;">
                    <div class="simulator-inputs" style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div class="calc-input-group">
                            <label>
                                <span>Premium Auth</span>
                                <span class="calc-badge-pts">5 pts</span>
                            </label>
                            <input type="number" id="inpPremAuth" oninput="updateCalculator()">
                        </div>
                        <div class="calc-input-group">
                            <label>
                                <span>Premium Conc</span>
                                <span class="calc-badge-pts">15 pts</span>
                            </label>
                            <input type="number" id="inpPremConc" oninput="updateCalculator()">
                        </div>
                        <div class="calc-input-group">
                            <label>
                                <span>Base Auth</span>
                                <span class="calc-badge-pts">3 pts</span>
                            </label>
                            <input type="number" id="inpBaseAuth" oninput="updateCalculator()">
                        </div>
                        <div class="calc-input-group">
                            <label>
                                <span>Base Conc</span>
                                <span class="calc-badge-pts">10 pts</span>
                            </label>
                            <input type="number" id="inpBaseConc" oninput="updateCalculator()">
                        </div>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        <div class="simulator-total">
                            <h3 style="margin: 0 0 0.75rem 0; font-size: 0.85rem; color: var(--text-light); text-transform: uppercase; letter-spacing: 0.5px; font-weight:600;">AppPoints Requeridos (NEM)</h3>
                            <div id="calcTotalDisplay" style="font-size: 3rem; font-weight: 700; color: var(--primary); line-height:1.2; word-break: break-word; margin-bottom: 0.75rem;">0</div>
                            <div style="font-size: 0.85rem; color: var(--text-light); padding-top: 0.75rem; border-top: 1px solid var(--border);">
                                <strong id="currentScopeLabel" style="color: var(--secondary);">Escopo: FORESEA + PARCEIRO</strong><br>
                                <span style="font-size: 0.8rem;">Concorrência real (NEM)</span>
                            </div>
                            <div id="calcAlertBox" class="alert-inline" style="display:none;">Teto excedido</div>
                        </div>
                        <div class="simulator-chart">
                            <canvas id="simChart" style="max-height: 100%;"></canvas>
                        </div>
                    </div>
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
