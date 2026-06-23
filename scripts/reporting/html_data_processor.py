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

        sum_p50 = 0
        sum_p95 = 0
        sum_p100 = 0
        count_conc = 0

        for u in self.app_points:
            lic = u['LICENSE_MODEL']
            ent = u['ENTITLEMENT']
            rec = u['OPTIMIZATION_REC']

            f_p50 = u.get('FACTOR_P50', 0.33)
            f_p95 = u.get('FACTOR_P95', 0.50)
            f_p100 = u.get('FACTOR_P100', 0.85)

            is_prem = (ent == 'PREMIUM')
            is_auth = (lic == 'AUTHORIZED')

            # 1. As-Is
            if is_prem:
                if is_auth:
                    scenarios_data['asis']['pA'] += 1
                else:
                    scenarios_data['asis']['pC'] += 1
            else:
                if is_auth:
                    scenarios_data['asis']['bA'] += 1
                else:
                    scenarios_data['asis']['bC'] += 1

            if rec == 'INATIVO (>90d)':
                inativos_count += 1
                continue

            if rec == 'DOWNGRADE_CANDIDATE': downgrade_count += 1
            if rec == 'MOVE_TO_CONCURRENT': concurrent_count += 1

            # 2. Saneado
            if is_prem:
                if is_auth:
                    scenarios_data['saneado']['pA'] += 1
                else:
                    scenarios_data['saneado']['pC'] += 1
            else:
                if is_auth:
                    scenarios_data['saneado']['bA'] += 1
                else:
                    scenarios_data['saneado']['bC'] += 1

            # 3. Otimizado
            final_ent = 'BASE' if (rec == 'DOWNGRADE_CANDIDATE' and ent == 'PREMIUM') else ent
            final_lic = 'CONCURRENT' if rec == 'MOVE_TO_CONCURRENT' else lic

            f_is_prem = (final_ent == 'PREMIUM')
            f_is_auth = (final_lic == 'AUTHORIZED')

            if f_is_prem:
                if f_is_auth:
                    scenarios_data['otimizado']['pA'] += 1
                else:
                    scenarios_data['otimizado']['pC'] += f_p95
            else:
                if f_is_auth:
                    scenarios_data['otimizado']['bA'] += 1
                else:
                    scenarios_data['otimizado']['bC'] += f_p95

            if not f_is_auth:
                sum_p50 += f_p50
                sum_p95 += f_p95
                sum_p100 += f_p100
                count_conc += 1

        avg_f_p50 = (sum_p50 / count_conc) if count_conc > 0 else 0.25
        avg_f_p95 = (sum_p95 / count_conc) if count_conc > 0 else 0.45
        avg_f_p100 = (sum_p100 / count_conc) if count_conc > 0 else 0.75

        return {
            'inativos_count': inativos_count,
            'downgrade_count': downgrade_count,
            'concurrent_count': concurrent_count,
            'scenarios_data': scenarios_data,
            'avg_f_p50': avg_f_p50,
            'avg_f_p95': avg_f_p95,
            'avg_f_p100': avg_f_p100
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
        for s in sorted(self.app_points, key=lambda x: x['APP_POINTS'], reverse=True)[:1000]:
            fator_display = f"Med: {s.get('FACTOR_P50', 0) * 100:.0f}% | Pico: {s.get('FACTOR_P95', 0) * 100:.0f}%" if s[
                                                                                                                           'LICENSE_MODEL'] == 'CONCURRENT' else "100% Fixo"
            app_points_rows.append([
                f"<strong>{s['USERID']}</strong>",
                s['DISPLAYNAME'][:30],
                get_recommendation_badge(s['OPTIMIZATION_REC']),
                f"<span class='badge' style='background:#f1f5f9; color:var(--primary);'>{s['ENTITLEMENT']}</span>",
                f"<strong>{s['LICENSE_MODEL']}</strong>",
                f"<strong>{s['APP_POINTS']}</strong>",
                f"<span style='color:var(--accent); font-weight:600; font-size:0.85rem;'>{fator_display}</span>",
                s['LOGIN_COUNT_90D'],
                s['TITLES'][:40]
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
