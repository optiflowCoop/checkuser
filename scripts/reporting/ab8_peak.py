# scripts/reporting/ab8_peak.py
import json
from .html_helpers import fmt_br

SCOPE_LABELS = {'foresea': 'FORESEA + PARCEIRO', 'terceiros': 'TERCEIROS',
                'integracao': 'INTEGRAÇÃO', 'todos': 'TODOS',
                'sem_dominio': 'SEM DOMÍNIO (revisar e-mail)'}
LICENSE_BADGE = {
    'PREMIUM_AUTHORIZED': ('#1e3a8a', 'PREM AUTH'),
    'PREMIUM_CONCURRENT': ('#3b82f6', 'PREM CONC'),
    'BASE_AUTHORIZED': ('#047857', 'BASE AUTH'),
    'BASE_CONCURRENT': ('#10b981', 'BASE CONC'),
}


def _badge_html(license_type):
    color, label = LICENSE_BADGE.get(license_type, ('#64748b', license_type))
    return f'<span style="background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">{label}</span>'


def _breakdown_rows_html(breakdown):
    if not breakdown:
        return ('<tr><td colspan="4" style="text-align: center; color: #64748b; padding: 2rem;">'
                'Nenhum contribuidor identificado nesse escopo.</td></tr>')
    rows = []
    for b in breakdown:
        rows.append(
            f'<tr data-scope="{b["scope"]}">'
            f'<td>{SCOPE_LABELS.get(b["scope"], b["scope"])}</td>'
            f'<td>{_badge_html(b["license_type"])}</td>'
            f'<td style="text-align: right;">{b["qtd"]}</td>'
            f'<td style="text-align: right;"><strong>{b["pts"]}</strong> pts</td></tr>'
        )
    return ''.join(rows)


def render_tab_peak(analytics):
    """Renders the Peak tab. Dados 100% do Cenário Conciliado
    (license_reconciliation.py) — mesmo seletor de escopo da aba Cenários de
    AppPoints, com curva de uso, pico e composição recalculados de verdade
    por escopo (não um filtro visual sobre uma série fixa)."""
    nem_by_scope = analytics.get('nem_by_scope') or {}

    if not nem_by_scope or not nem_by_scope.get('todos', {}).get('hourly_series'):
        p100 = analytics.get('concurrency_peak_count', 0)
        return f"""
        <div id="tab-peak" class="container tab-content">
            <div class="card">
                <h2 class="card-header">Peak Hours (High-Water Mark)</h2>
                <div class="alert-box">
                    <strong>Dados de Pico Não Disponíveis</strong>
                    <p>Execute <code>license_reconciliation.py</code> (via <code>generate_risk_report.py</code>) para gerar a série horária do Cenário Conciliado.</p>
                    <p style="margin-top: 0.5rem;"><strong>Métrica Disponível:</strong> Pico Real (P100) = {fmt_br(p100)} AppPoints</p>
                </div>
            </div>
        </div>
        """

    # Top 24 horas de cada escopo, pelo próprio pico daquele escopo — uma
    # curva de TERCEIROS não deveria ser forçada a mostrar as horas de pico
    # de TODOS, onde ela pode estar zerada.
    chart_by_scope = {}
    for scope, data in nem_by_scope.items():
        series = data.get('hourly_series', [])
        top = sorted(series, key=lambda h: -h['points_nem'])[:24]
        top_sorted = sorted(top, key=lambda h: h['hour'])
        chart_by_scope[scope] = {
            'labels': [h['hour'] for h in top_sorted],
            'users': [h['users'] for h in top_sorted],
            'points_concurrent': [h['points_concurrent'] for h in top_sorted],
            'points_nem': [h['points_nem'] for h in top_sorted],
        }

    # Payload enxuto por escopo p/ os cards + tabela (sem repetir a série
    # horária, que já foi para chart_by_scope).
    stats_by_scope = {
        scope: {
            'p50': data.get('p50', 0), 'p95': data.get('p95', 0), 'p100': data.get('p100', 0),
            'peak_hour': data.get('peak_hour'),
            'contributors_count': len(data.get('peak_contributors', [])),
            'breakdown': data.get('peak_breakdown', []),
        }
        for scope, data in nem_by_scope.items()
    }

    chart_json = json.dumps(chart_by_scope, ensure_ascii=False)
    stats_json = json.dumps(stats_by_scope, ensure_ascii=False)

    default = nem_by_scope.get('foresea') or nem_by_scope['todos']
    default_stats = stats_by_scope.get('foresea') or stats_by_scope['todos']
    default_chart = chart_by_scope.get('foresea') or chart_by_scope['todos']

    return f"""
    <div id="tab-peak" class="container tab-content">
        <div class="card">
            <h2 class="card-header">Peak Hours (High-Water Mark)</h2>
            <p class="card-desc">Usuários simultâneos e consumo de AppPoints por horário. Selecione o escopo — a
            curva, o pico e a composição são recalculados para aquele recorte (não é um filtro visual sobre a série
            de TODOS).</p>

            <div class="filter-bar">
                <span class="filter-bar-label">Escopo</span>
                <label class="radio-label">
                    <input type="radio" name="scopeFilterPeak" value="foresea" checked onchange="updateScopeFilterPeak()">
                    <span>FORESEA + PARCEIRO</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="scopeFilterPeak" value="terceiros" onchange="updateScopeFilterPeak()">
                    <span>TERCEIROS</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="scopeFilterPeak" value="integracao" onchange="updateScopeFilterPeak()">
                    <span>INTEGRAÇÃO</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="scopeFilterPeak" value="todos" onchange="updateScopeFilterPeak()">
                    <span>TODOS</span>
                </label>
            </div>

            <div class="stats-grid" style="margin-bottom: 1.5rem;">
                <div class="stat-card border-neutral">
                    <div class="stat-value" id="peakCardP50">{fmt_br(default_stats['p50'])}</div>
                    <div class="stat-title">Uso Cotidiano (P50)</div>
                    <div class="stat-subtitle">Mediana — dia típico</div>
                </div>
                <div class="stat-card border-warning">
                    <div class="stat-value" style="color: var(--warning);" id="peakCardP95">{fmt_br(default_stats['p95'])}</div>
                    <div class="stat-title">Pico Seguro (P95)</div>
                    <div class="stat-subtitle">Percentil 95</div>
                </div>
                <div class="stat-card border-danger">
                    <div class="stat-value" style="color: var(--danger);" id="peakCardP100">{fmt_br(default_stats['p100'])}</div>
                    <div class="stat-title">Pico Real (P100)</div>
                    <div class="stat-subtitle" id="peakCardScopeLabel1">Escopo: {SCOPE_LABELS.get('foresea')}</div>
                </div>
                <div class="stat-card border-accent">
                    <div class="stat-value" style="color: var(--accent);" id="peakCardTime">{default_stats['peak_hour'] or 'N/A'}</div>
                    <div class="stat-title">Maior Pico Registrado</div>
                    <div class="stat-subtitle">Data/hora do P100</div>
                </div>
                <div class="stat-card border-success">
                    <div class="stat-value" style="color: var(--success);" id="peakCardContributors">{fmt_br(default_stats['contributors_count'])}</div>
                    <div class="stat-title">Contribuidores no Pico</div>
                    <div class="stat-subtitle">Usuários simultâneos</div>
                </div>
            </div>

            <div class="chart-box" style="height: 380px; align-items: stretch; padding: 1.5rem;">
                <canvas id="peakLineChart"
                        data-labels='{json.dumps(default_chart["labels"], ensure_ascii=False)}'
                        data-users-data='{json.dumps(default_chart["users"], ensure_ascii=False)}'
                        data-points-data='{json.dumps(default_chart["points_concurrent"], ensure_ascii=False)}'
                        data-nem-data='{json.dumps(default_chart["points_nem"], ensure_ascii=False)}'></canvas>
            </div>
        </div>

        <div class="card">
            <h2 class="card-header">Composição do Pico por Categoria <span id="peakCardTime2">({default_stats['peak_hour'] or 'N/A'})</span></h2>
            <p class="card-desc">Quem estava logado no horário de pico daquele escopo, por escopo real e tipo de
            licença: <span id="peakContribText">{fmt_br(default_stats['contributors_count'])} pessoas simultâneas</span>.
            Cada tipo de licença consome sempre o mesmo valor em pontos, então a composição importa mais que um
            ranking individual.</p>

            <div class="table-responsive">
                <table class="gov-table" id="table-peak-contributors">
                    <thead>
                        <tr>
                            <th>Escopo</th>
                            <th style="width: 180px;">Tipo de Licença</th>
                            <th style="width: 100px; text-align: right;">Pessoas</th>
                            <th style="width: 120px; text-align: right;">AppPoints</th>
                        </tr>
                    </thead>
                    <tbody id="peakBreakdownBody">
                        {_breakdown_rows_html(default_stats['breakdown'])}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const peakChartByScope = {chart_json};
        const peakStatsByScope = {stats_json};
        const peakScopeLabels = {json.dumps(SCOPE_LABELS, ensure_ascii=False)};
        const peakLicenseBadgeColors = {json.dumps({k: v[0] for k, v in LICENSE_BADGE.items()}, ensure_ascii=False)};
        const peakLicenseBadgeLabels = {json.dumps({k: v[1] for k, v in LICENSE_BADGE.items()}, ensure_ascii=False)};
    </script>
    """
