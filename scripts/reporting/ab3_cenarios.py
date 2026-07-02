# scripts/reporting/ab3_cenarios.py
from .html_helpers import fmt_br


def render_tab_apppoints(analytics):
    """Renders the 'Cenários de AppPoints' tab content."""
    return f"""
    <div id="tab-apppoints" class="container tab-content">
        <div class="card" style="border-left: 4px solid var(--success); background-image: linear-gradient(to right, #ffffff, #f8fafc);">
            <div class="card-header" style="border:none; margin-bottom:0.5rem;">
                <div>
                    <h2 style="margin:0; color:var(--success);">🧮 Simulador de Cenários de AppPoints</h2>
                    <p style="font-size: 0.9rem; color: #64748b; font-weight: normal; margin-top: 4px;">Selecione um cenário para ver o impacto no consumo de AppPoints ou edite os campos para uma simulação manual.</p>
                </div>
            </div>
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem; padding: 1rem; background: #f8fafc; border-radius: 8px; align-items: center;">
                <span style="font-weight: 600; color: var(--secondary);">🔍 Escopo:</span>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="radio" name="scopeFilter" value="foresea" checked onchange="updateScopeFilter()">
                    <span>🏢 FORESEA + PARCEIRO</span>
                </label>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="radio" name="scopeFilter" value="terceiros" onchange="updateScopeFilter()">
                    <span>🏭 TERCEIROS</span>
                </label>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="radio" name="scopeFilter" value="integracao" onchange="updateScopeFilter()">
                    <span>🔌 INTEGRAÇÃO</span>
                </label>
                <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;">
                    <input type="radio" name="scopeFilter" value="todos" onchange="updateScopeFilter()">
                    <span>🌐 TODOS</span>
                </label>
            </div>
            <div style="display: grid; grid-template-columns: 280px 1fr; gap: 1.5rem; align-items: stretch;">
                <div class="preset-btn-group" style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <button class="preset-btn" id="btnAsIs" onclick="loadScenario('asis', this)" style="flex: 1; min-height: 120px;">
                        <strong style="font-size: 1rem;">1. Cenário Atual (As-Is)</strong>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Simula o consumo se todos os usuários atuais fossem migrados sem nenhuma otimização.</p>
                    </button>
                    <button class="preset-btn" id="btnSaneado" onclick="loadScenario('saneado', this)" style="flex: 1; min-height: 120px;">
                        <strong style="font-size: 1rem;">2. Pós-Saneamento</strong>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Simula o consumo após a desativação de usuários inativos (> 90 dias).</p>
                    </button>
                    <button class="preset-btn active" id="btnOtimizado" onclick="loadScenario('otimizado_p95', this)" style="flex: 1; min-height: 120px;">
                        <strong style="font-size: 1rem;">3. Otimizado (Pico P95)</strong>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Aplica todas as otimizações (inativos, downgrades, concorrência) usando o fator de pico (P95).</p>
                    </button>
                    <button class="preset-btn" id="btnOtimizadoP50" onclick="loadScenario('otimizado_p50', this)" style="flex: 1; min-height: 120px;">
                        <strong style="font-size: 1rem;">4. Otimizado (Mediana P50)</strong>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Aplica todas as otimizações usando o fator de uso mediano (P50) para um dia comum.</p>
                    </button>
                </div>
                <div class="simulator-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; align-items: start;">
                    <div class="simulator-inputs" style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div class="calc-input-group" style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                            <label style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; font-weight: 600; color: var(--secondary);">
                                <span>Premium Auth</span>
                                <span class="calc-badge-pts" style="background: #1e3a8a; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">5 pts</span>
                            </label>
                            <input type="number" id="inpPremAuth" oninput="updateCalculator()" style="width: 100%; padding: 0.5rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 1rem;">
                        </div>
                        <div class="calc-input-group" style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                            <label style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; font-weight: 600; color: var(--secondary);">
                                <span>Premium Conc</span>
                                <span class="calc-badge-pts" style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">15 pts</span>
                            </label>
                            <input type="number" id="inpPremConc" oninput="updateCalculator()" style="width: 100%; padding: 0.5rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 1rem;">
                        </div>
                        <div class="calc-input-group" style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                            <label style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; font-weight: 600; color: var(--secondary);">
                                <span>Base Auth</span>
                                <span class="calc-badge-pts" style="background: #047857; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">3 pts</span>
                            </label>
                            <input type="number" id="inpBaseAuth" oninput="updateCalculator()" style="width: 100%; padding: 0.5rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 1rem;">
                        </div>
                        <div class="calc-input-group" style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                            <label style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; font-weight: 600; color: var(--secondary);">
                                <span>Base Conc</span>
                                <span class="calc-badge-pts" style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">10 pts</span>
                            </label>
                            <input type="number" id="inpBaseConc" oninput="updateCalculator()" style="width: 100%; padding: 0.5rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 1rem;">
                        </div>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        <div class="simulator-total" style="background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); flex: 1;">
                            <h3 style="margin: 0 0 0.75rem 0; font-size: 0.9rem; color: var(--secondary); text-transform: uppercase; letter-spacing: 0.5px;">AppPoints Requeridos (NEM)</h3>
                            <div id="calcTotalDisplay" style="font-size: 3.5rem; font-weight: 800; color: var(--success); line-height:1.2; word-break: break-word; margin-bottom: 0.75rem;">0</div>
                            <div style="font-size: 0.85rem; color: #64748b; padding-top: 0.75rem; border-top: 1px solid #e2e8f0;">
                                <strong id="currentScopeLabel" style="color: var(--secondary);">Escopo: FORESEA + PARCEIRO</strong><br>
                                <span style="font-size: 0.8rem;">Baseado em concorrência real (NEM)</span>
                            </div>
                            <div id="calcAlertBox" style="margin-top: 1rem; padding: 0.75rem; background: var(--danger); color:white; font-weight:bold; border-radius:6px; display:none; font-size:1.1rem; text-align: center;">⚠️ TETO EXCEDIDO</div>
                        </div>
                        <div class="simulator-chart" style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 250px;">
                            <canvas id="simChart" style="max-height: 100%;"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="card" style="border-top: 4px solid var(--primary);">
            <h2 class="card-header" style="border:none; margin-bottom:0.5rem;">🧠 Quadro de Regras de Negócio O&G</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; align-items: start;">
                <div class="legend-grid" style="display: grid; grid-template-columns: 1fr; gap: 1rem;">
                    <div class="legend-box" style="border-left: 3px solid #1e3a8a;">
                        <h3>🔰 Entitlement (Módulos)</h3>
                        <ul class="legend-list">
                            <li><strong>PREMIUM:</strong> Usuários com acesso a módulos críticos O&G (PTW, HSE, Permissões de Trabalho).</li>
                            <li><strong>BASE:</strong> Usuários com acesso a módulos padrão (Compras, PCM, Ordem de Serviço).</li>
                        </ul>
                    </div>
                    <div class="legend-box" style="border-left: 3px solid #f59e0b;">
                        <h3>🔑 Licença (Acesso)</h3>
                        <ul class="legend-list">
                            <li><strong>AUTHORIZED:</strong> Licença dedicada para usuários com acesso crítico (Supervisores, Coordenadores). Garante disponibilidade 100%.</li>
                            <li><strong>CONCURRENT:</strong> Licença compartilhada (pool) para usuários offshore/sonda. Dimensionada pelo pico real de logins.</li>
                        </ul>
                    </div>
                </div>
                <div class="legend-box" style="border-left: 3px solid #10b981; background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);">
                    <h3>📊 Capacidade Real (NEM)</h3>
                    <ul class="legend-list">
                        <li><strong>Pico Real (P100):</strong> Máximo histórico de logins simultâneos registrado no logintracking.</li>
                        <li><strong>Pico Seguro (P95):</strong> Referência estatística para planejamento (95% dos dias).</li>
                        <li><strong>Contratado:</strong> Capacidade total adquirida no contrato de licenciamento.</li>
                        <li><strong>Folga Disponível:</strong> Espaço remanescente antes de atingir o limite contratual.</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """