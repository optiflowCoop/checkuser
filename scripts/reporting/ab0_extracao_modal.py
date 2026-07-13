# scripts/reporting/ab0_extracao_modal.py
"""Ícone de engrenagem + popup de 'Extração de Dados' no cabeçalho do
dashboard. Os botões chamam scripts .bat locais (pasta bat/) através do
servidor local (scripts/local_dashboard_server.py) — o navegador não pode
executar arquivos por conta própria, então isso só funciona quando o
dashboard é acessado via http://127.0.0.1:8765/ (iniciado por
bat/iniciar_dashboard_server.bat). Ao abrir o HTML direto do disco
(file://), o popup avisa isso e não trava.
"""


def render_gear_icon():
    """Botão de engrenagem para colocar no cabeçalho (topbar)."""
    return """
    <button class="gear-icon-btn" onclick="openBatModal()" title="Extração de Dados">⚙️</button>
    """


def render_bat_modal():
    """Markup do popup (overlay + painel), oculto por padrão."""
    return """
    <style>
        .gear-icon-btn {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.2);
            color: #e2e8f0;
            font-size: 1.3rem;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            cursor: pointer;
            transition: background 0.15s, transform 0.15s;
        }
        .gear-icon-btn:hover { background: rgba(255,255,255,0.18); transform: rotate(25deg); }

        .bat-modal-overlay {
            display: none;
            position: fixed; inset: 0;
            background: rgba(15, 23, 42, 0.6);
            z-index: 1000;
            align-items: center; justify-content: center;
        }
        .bat-modal-overlay.open { display: flex; }
        .bat-modal-panel {
            background: #ffffff;
            border-radius: 12px;
            width: min(680px, 92vw);
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 20px 50px rgba(0,0,0,0.35);
        }
        .bat-modal-header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid #e2e8f0;
        }
        .bat-modal-header h3 { margin: 0; color: #0f172a; }
        .bat-modal-close {
            background: none; border: none; font-size: 1.4rem; cursor: pointer; color: #64748b;
        }
        .bat-modal-body { padding: 1.5rem; }
        .bat-group-title {
            font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;
            color: #64748b; font-weight: 700; margin: 1.25rem 0 0.6rem;
        }
        .bat-group-title:first-child { margin-top: 0; }
        .bat-btn-row {
            display: flex; align-items: center; gap: 0.75rem;
            padding: 0.75rem 0.9rem;
            border: 1px solid #e2e8f0; border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .bat-btn-row .bat-info { flex: 1; }
        .bat-btn-row .bat-label { font-weight: 600; color: #0f172a; font-size: 0.92rem; }
        .bat-btn-row .bat-desc { font-size: 0.8rem; color: #64748b; margin-top: 0.15rem; }
        .bat-run-btn {
            background: #2563eb; color: white; border: none;
            padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem;
            white-space: nowrap;
        }
        .bat-run-btn:hover { background: #1d4ed8; }
        .bat-run-btn:disabled { background: #94a3b8; cursor: wait; }
        .bat-status-msg {
            font-size: 0.85rem; margin-top: 0.75rem; padding: 0.6rem 0.8rem;
            border-radius: 6px; display: none;
        }
        .bat-status-msg.ok { display: block; background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
        .bat-status-msg.err { display: block; background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
        .bat-offline-hint {
            background: #fffbeb; border: 1px solid #fde68a; color: #92400e;
            padding: 0.9rem 1rem; border-radius: 8px; font-size: 0.88rem; line-height: 1.5;
        }
        .bat-offline-hint code {
            background: #fef3c7; padding: 0.1rem 0.35rem; border-radius: 4px;
        }
    </style>

    <div class="bat-modal-overlay" id="batModalOverlay" onclick="if(event.target===this) closeBatModal()">
        <div class="bat-modal-panel">
            <div class="bat-modal-header">
                <h3>⚙️ Extração de Dados</h3>
                <button class="bat-modal-close" onclick="closeBatModal()">✕</button>
            </div>
            <div class="bat-modal-body" id="batModalBody">
                <p style="color:#64748b;">Carregando scripts disponíveis...</p>
            </div>
        </div>
    </div>
    """


def render_bat_modal_scripts():
    """JS do popup: abrir/fechar, carregar lista de .bat, disparar execução."""
    return """
    <script>
        function openBatModal() {
            document.getElementById('batModalOverlay').classList.add('open');
            loadBatList();
        }
        function closeBatModal() {
            document.getElementById('batModalOverlay').classList.remove('open');
        }

        function loadBatList() {
            const body = document.getElementById('batModalBody');
            fetch('/api/list-bats')
                .then(r => { if (!r.ok) throw new Error('offline'); return r.json(); })
                .then(data => renderBatButtons(data.bats || []))
                .catch(() => {
                    body.innerHTML = `
                        <div class="bat-offline-hint">
                            <strong>Servidor local não está rodando.</strong><br>
                            Estes botões só funcionam quando o dashboard é aberto pelo servidor local
                            (ele é quem tem permissão de executar os .bat no seu computador).<br><br>
                            1. Dê duplo clique em <code>bat\\iniciar_dashboard_server.bat</code><br>
                            2. Deixe a janela do terminal aberta<br>
                            3. Use o dashboard que abrir em <code>http://127.0.0.1:8765/</code>
                        </div>`;
                });
        }

        function renderBatButtons(bats) {
            const body = document.getElementById('batModalBody');
            if (!bats.length) {
                body.innerHTML = '<p style="color:#64748b;">Nenhum script .bat encontrado na pasta bat/.</p>';
                return;
            }
            const groups = {};
            bats.forEach(b => { (groups[b.group] = groups[b.group] || []).push(b); });

            let html = '';
            Object.keys(groups).forEach(group => {
                html += `<div class="bat-group-title">${group}</div>`;
                groups[group].forEach(b => {
                    html += `
                        <div class="bat-btn-row">
                            <div class="bat-info">
                                <div class="bat-label">${b.label}</div>
                                <div class="bat-desc">${b.description}</div>
                            </div>
                            <button class="bat-run-btn" onclick="runBat('${b.name}', this)">Executar</button>
                        </div>`;
                });
            });
            html += '<div class="bat-status-msg" id="batStatusMsg"></div>';
            body.innerHTML = html;
        }

        function runBat(name, btnEl) {
            const status = document.getElementById('batStatusMsg');
            btnEl.disabled = true;
            const originalText = btnEl.textContent;
            btnEl.textContent = 'Iniciando...';
            fetch('/api/run-bat?name=' + encodeURIComponent(name))
                .then(r => r.json())
                .then(data => {
                    status.className = 'bat-status-msg ' + (data.ok ? 'ok' : 'err');
                    status.textContent = data.ok ? data.message : data.error;
                })
                .catch(() => {
                    status.className = 'bat-status-msg err';
                    status.textContent = 'Não foi possível conectar ao servidor local.';
                })
                .finally(() => {
                    btnEl.disabled = false;
                    btnEl.textContent = originalText;
                });
        }
    </script>
    """
