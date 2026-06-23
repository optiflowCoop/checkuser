# scripts/reporting/html_data_processor.py
import json
from .html_helpers import get_recommendation_badge

class DataProcessor:
    def __init__(self, summary, governance, app_points, domains):
        self.summary = summary
        self.governance = governance
        self.app_points = app_points
        self.domains = domains

    def process_app_points_analytics(self):
        inativos_count = 0
        downgrade_count = 0
        concurrent_count = 0

        scenarios_data = {
            'asis': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0},
            'saneado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0},
            'otimizado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}
        }
        
        scenario_points = {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0}

        opt_auth_points = 0
        opt_conc_users = []

        for u in self.app_points:
            lic = u['LICENSE_MODEL']
            ent = u['ENTITLEMENT']
            rec = u['OPTIMIZATION_REC']
            
            is_prem = (ent == 'PREMIUM')
            is_auth = (lic == 'AUTHORIZED')

            # 1. As-Is Scenario (Physical counts)
            if is_prem:
                scenarios_data['asis']['pA' if is_auth else 'pC'] += 1
            else:
                scenarios_data['asis']['bA' if is_auth else 'bC'] += 1

            if rec == 'INATIVO (>90d)':
                inativos_count += 1
                continue

            if rec == 'DOWNGRADE_CANDIDATE': downgrade_count += 1
            if rec == 'MOVE_TO_CONCURRENT': concurrent_count += 1

            # 2. Saneado Scenario (Physical counts)
            if is_prem:
                scenarios_data['saneado']['pA' if is_auth else 'pC'] += 1
            else:
                scenarios_data['saneado']['bA' if is_auth else 'bC'] += 1

            # 3. Otimizado Scenario (Logic for final calculation)
            final_ent = 'BASE' if (rec == 'DOWNGRADE_CANDIDATE' and ent == 'PREMIUM') else ent
            final_lic = 'CONCURRENT' if rec == 'MOVE_TO_CONCURRENT' else lic
            
            f_is_prem = (final_ent == 'PREMIUM')
            f_is_auth = (final_lic == 'AUTHORIZED')
            
            # **FIX**: Populate 'otimizado' with PHYSICAL user counts for the UI
            if f_is_prem:
                scenarios_data['otimizado']['pA' if f_is_auth else 'pC'] += 1
            else:
                scenarios_data['otimizado']['bA' if f_is_auth else 'bC'] += 1

            # Accumulate data for the precise backend calculation
            if f_is_auth:
                points = 5 if f_is_prem else 3
                opt_auth_points += points
            else:
                opt_conc_users.append({
                    'points': 15 if f_is_prem else 10,
                    'f_p50': u.get('FACTOR_P50', 0.33),
                    'f_p95': u.get('FACTOR_P95', 0.50),
                    'f_p100': u.get('FACTOR_P100', 0.85)
                })

        # Calculate the definitive, factored totals for each stress scenario
        scenario_points['p50'] = opt_auth_points + sum(user['points'] * user['f_p50'] for user in opt_conc_users)
        scenario_points['p95'] = opt_auth_points + sum(user['points'] * user['f_p95'] for user in opt_conc_users)
        scenario_points['p100'] = opt_auth_points + sum(user['points'] * user['f_p100'] for user in opt_conc_users)
        scenario_points['blackout'] = opt_auth_points + sum(user['points'] for user in opt_conc_users)
        
        return {
            'inativos_count': inativos_count,
            'downgrade_count': downgrade_count,
            'concurrent_count': concurrent_count,
            'scenarios_data': scenarios_data, # Contains physical counts for UI
            'scenario_points': scenario_points # Contains precise factored totals for display
        }

    def prepare_governance_tables(self):
        cross_env_rows = [[f"<strong>{c.get('USERID')}</strong>", c.get('ENV_LIST'), c.get('DISPLAYNAME_LIST'),
                           get_recommendation_badge(c.get('HYPOTHESIS', ''))] for c in self.governance['cross_env'][:200]]
        
        login_conflicts_rows = [[f"<strong>{l.get('LOGINID')}</strong>", l.get('USERID_LIST'), l.get('DISPLAYNAME_LIST'),
                                 get_recommendation_badge(l.get('MERGE_DECISION', ''))] for l in
                                self.governance['login_conflicts'][:200]]
        
        worklist_rows = [[w.get('RAW_ID'), w.get('DISPLAYNAME'), w.get('HYPOTHESIS'), w.get('MERGE_DECISION')] for w in
                         self.governance['worklist'][:200]]

        title_divergence_html = []
        for div in self.governance['detailed_divergences'][:30]:
            title = div['title']
            data = div['data']
            alerts = []
            all_types = {t for types in data['types'].values() for t in types if t}
            if len(all_types) > 1: alerts.append('<span class="badge badge-critical">TYPE DIVERGENTE</span>')
            base_groups = next(iter(data['groups'].values()), set())
            if any(s != base_groups for s in data['groups'].values()): alerts.append(
                '<span class="badge badge-high">GRUPOS DIVERGENTES</span>')

            title_divergence_html.append(f'<div class="type-card"><h4>{title} {" ".join(alerts)}</h4>')
            if len(all_types) > 1:
                title_divergence_html.append(
                    '<div class="env-divergence"><div class="env-header">⚠️ Inconsistência de TYPE</div>')
                for env, types in sorted(data['types'].items()):
                    title_divergence_html.append(f'<div>📍 {env}: {", ".join(sorted(t for t in types if t))}</div>')
                title_divergence_html.append('</div>')
            title_divergence_html.append('</div>')

        return {
            'cross_env_rows': cross_env_rows,
            'login_conflicts_rows': login_conflicts_rows,
            'worklist_rows': worklist_rows,
            'title_divergence_html': "".join(title_divergence_html)
        }

    def prepare_app_points_rows(self):
        app_points_rows = []
        for s in sorted(self.app_points, key=lambda x: x.get('APP_POINTS', 0), reverse=True)[:1000]:
            points = s.get('APP_POINTS', 0)
            fator_display = f"Med: {s.get('FACTOR_P50', 0) * 100:.0f}% | Pico: {s.get('FACTOR_P95', 0) * 100:.0f}%" if s.get('LICENSE_MODEL') == 'CONCURRENT' else "100% Fixo"
            
            app_points_rows.append([
                f"<strong>{s.get('USERID')}</strong>",
                s.get('DISPLAYNAME', 'N/A')[:30],
                get_recommendation_badge(s.get('OPTIMIZATION_REC')),
                f"<span class='badge' style='background:#f1f5f9; color:var(--primary);'>{s.get('ENTITLEMENT')}</span>",
                f"<strong>{s.get('LICENSE_MODEL')}</strong>",
                f"<strong>{points}</strong>",
                f"<span style='color:var(--accent); font-weight:600; font-size:0.85rem;'>{fator_display}</span>",
                s.get('LOGIN_COUNT_90D', 0),
                s.get('TITLES', 'N/A')[:40]
            ])
        return app_points_rows

    def get_all_data(self):
        analytics = self.process_app_points_analytics()
        gov_tables = self.prepare_governance_tables()
        app_points_rows = self.prepare_app_points_rows()

        return {
            'analytics': analytics,
            'gov_tables': gov_tables,
            'app_points_rows': app_points_rows,
            'summary': self.summary,
            'domains': self.domains
        }