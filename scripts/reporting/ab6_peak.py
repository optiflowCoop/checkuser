# scripts/reporting/ab6_peak.py
import json
from .html_helpers import fmt_br


def render_tab_peak(analytics):
    """Renders the Peak tab with aligned hourly series."""
    
    def rows_to_map(rows, value_keys):
        if isinstance(rows, dict):
            return {str(k): v for k, v in rows.items() if k}
        mapped = {}
        if isinstance(rows, list):
            for entry in rows:
                if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    mapped[str(entry[0])] = entry[1]
                elif isinstance(entry, dict):
                    hour = entry.get('hour') or entry.get('ts') or entry.get('time')
                    value = None
                    for key in value_keys:
                        if entry.get(key) is not None:
                            value = entry.get(key)
                            break
                    if hour:
                        mapped[str(hour)] = value
        return mapped

    users_by_hour = rows_to_map(
        analytics.get('concurrency_hourly', {}) or analytics.get('concurrency_peak_users_hours', []),
        ('users', 'count', 'value'),
    )
    points_by_hour = rows_to_map(
        analytics.get('concurrency_hourly_app_points', {}) or analytics.get('concurrency_peak_hours', []),
        ('app_points', 'points', 'count', 'value'),
    )
    nem_by_hour = rows_to_map(
        analytics.get('concurrency_hourly_app_points_nem', {}),
        ('app_points_nem', 'app_points', 'points', 'count', 'value'),
    )

    if not nem_by_hour:
        nem_by_hour = points_by_hour.copy()

    all_hours = set(users_by_hour) | set(points_by_hour) | set(nem_by_hour)
    
    if not all_hours:
        return f"""
        <div id="tab-peak" class="container tab-content">
            <div class="card">
                <h2 class="card-header">⛰️ Peak Hours (High-Water Mark) </h2>
                <div class="alert-box">
                    <strong>📊 Dados de Pico Não Disponíveis</strong>
                    <p>O arquivo <code>true_capacity_metrics.json</code> não contém dados horários de pico.</p>
                    <p style="margin-top: 0.5rem;"><strong>Métrica Disponível:</strong> Pico Real (P100) = {analytics.get('concurrency_peak_count', 0)} AppPoints</p>
                    <p style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">Para visualizar o gráfico, execute o <code>true_capacity_calculator.py</code> com dados de logintracking completos.</p>
                </div>
            </div>
        </div>
        """
    
    peak_hours = sorted(
        all_hours,
        key=lambda hour: max(
            float(points_by_hour.get(hour) or 0),
            float(nem_by_hour.get(hour) or 0),
            float(users_by_hour.get(hour) or 0),
        ),
        reverse=True,
    )[:24]
    labels = sorted(peak_hours)

    def series_values(source):
        values = []
        for hour in labels:
            try:
                values.append(round(float(source.get(hour) or 0), 2))
            except (TypeError, ValueError):
                values.append(0)
        return values

    labels_json = json.dumps(labels, ensure_ascii=False)
    users_data_json = json.dumps(series_values(users_by_hour), ensure_ascii=False)
    points_data_json = json.dumps(series_values(points_by_hour), ensure_ascii=False)
    nem_data_json = json.dumps(series_values(nem_by_hour), ensure_ascii=False)

    p100 = analytics.get('concurrency_peak_count', 0)
    p95 = analytics.get('scenario_points', {}).get('p95', 0)
    peak_hours_list = analytics.get('concurrency_peak_hours', [])
    peak_info = peak_hours_list[0] if peak_hours_list else ['N/A', 0]
    peak_time = peak_info[0] if len(peak_info) > 0 else 'N/A'
    peak_value = peak_info[1] if len(peak_info) > 1 else 0

    # Peak Contributors
    peak_contributors = analytics.get('concurrency_peak_contributors', []) or []
    peak_contributors_count = analytics.get('concurrency_peak_contributors_count', 0)
    
    # Gera tabela de contribuidores
    contributors_rows = ""
    if peak_contributors:
        for i, contributor in enumerate(peak_contributors[:20], 1):  # Top 20
            userid = contributor.get('userid', 'N/A')
            app_points = contributor.get('app_points', 0)
            license_type = contributor.get('license_type', 'N/A')
            
            # Cores por tipo de licença
            license_badge = ""
            if 'PREMIUM' in license_type and 'AUTHORIZED' in license_type:
                license_badge = '<span style="background: #1e3a8a; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">PREM AUTH</span>'
            elif 'PREMIUM' in license_type:
                license_badge = '<span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">PREM CONC</span>'
            elif 'AUTHORIZED' in license_type:
                license_badge = '<span style="background: #047857; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">BASE AUTH</span>'
            else:
                license_badge = '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">BASE CONC</span>'
            
            contributors_rows += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{userid}</strong></td>
                <td>{license_badge}</td>
                <td style="text-align: right;"><strong>{app_points}</strong> pts</td>
            </tr>
            """
    else:
        contributors_rows = """
        <tr>
            <td colspan="4" style="text-align: center; color: #64748b; padding: 2rem;">
                Nenhum contribuidor identificado. Execute o true_capacity_calculator.py novamente.
            </td>
        </tr>
        """

    return f"""
    <div id="tab-peak" class="container tab-content">
        <div class="card">
            <h2 class="card-header">⛰️ Peak Hours (High-Water Mark) </h2>
            <p style="color:#475569;">Passe o mouse para ver usuários simultâneos e consumo de AppPoints no mesmo horário.</p>
            
            <div class="stats-grid" style="margin-bottom: 1.5rem;">
                <div class="stat-card border-danger">
                    <div class="stat-value" style="color: var(--danger);">{fmt_br(p100)}</div>
                    <div class="stat-title">Pico Real (P100)</div>
                    <div class="stat-subtitle">Máximo histórico</div>
                </div>
                <div class="stat-card border-warning">
                    <div class="stat-value" style="color: var(--warning);">{fmt_br(p95)}</div>
                    <div class="stat-title">Pico Seguro (P95)</div>
                    <div class="stat-subtitle">Percentil 95</div>
                </div>
                <div class="stat-card border-accent">
                    <div class="stat-value" style="color: var(--accent);">{fmt_br(peak_value)}</div>
                    <div class="stat-title">Maior Pico Registrado</div>
                    <div class="stat-subtitle">{peak_time}</div>
                </div>
                <div class="stat-card border-success">
                    <div class="stat-value" style="color: var(--success);">{peak_contributors_count}</div>
                    <div class="stat-title">Contribuidores no Pico</div>
                    <div class="stat-subtitle">Usuários simultâneos</div>
                </div>
            </div>

            <div class="chart-box" style="height: 380px; align-items: stretch; padding: 1.5rem;">
                <canvas id="peakLineChart"
                        data-labels='{labels_json}'
                        data-users-data='{users_data_json}'
                        data-points-data='{points_data_json}'
                        data-nem-data='{nem_data_json}'></canvas>
            </div>
        </div>

        <!-- Tabela de Peak Contributors -->
        <div class="card">
            <h2 class="card-header">👥 Top Contribuidores do Pico ({peak_time})</h2>
            <p style="color:#475569; margin-bottom: 1rem;">Usuários que mais consumiram AppPoints no horário de pico histórico.</p>
            
            <div class="table-responsive">
                <table class="gov-table">
                    <thead>
                        <tr>
                            <th style="width: 60px;">#</th>
                            <th>USERID</th>
                            <th style="width: 180px;">Tipo de Licença</th>
                            <th style="width: 120px; text-align: right;">Contribuição</th>
                        </tr>
                    </thead>
                    <tbody>
                        {contributors_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """