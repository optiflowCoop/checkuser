# scripts/reporting/html_data_processor.py

import numpy as np
from .html_helpers import get_recommendation_badge


class DataProcessor:

    def __init__(self, summary, governance, app_points, domains, identity_analytics):
        self.summary = summary
        self.governance = governance
        self.app_points = app_points
        self.domains = domains
        self.identity_analytics = identity_analytics

    # ==========================================================
    # CORE ANALYTICS
    # ==========================================================
    def process_app_points_analytics(self):

        inativos_count = 0
        downgrade_count = 0
        concurrent_count = 0

        scenarios_data = {
            'asis': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0},
            'saneado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0},
            'otimizado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}
        }

        opt_total_points = 0

        for u in self.app_points:

            lic = u.get('LICENSE_MODEL', 'CONCURRENT')
            ent = u.get('ENTITLEMENT', 'BASE')
            rec = u.get('OPTIMIZATION_REC', 'OK')
            app_pts = float(u.get('APP_POINTS', 0) or 0)

            is_prem = (ent == 'PREMIUM')
            is_auth = (lic == 'AUTHORIZED')

            # AS-IS (inclui todos)
            if is_prem:
                scenarios_data['asis']['pA' if is_auth else 'pC'] += 1
            else:
                scenarios_data['asis']['bA' if is_auth else 'bC'] += 1

            opt_total_points += app_pts

            if rec == 'INATIVO (>90d)':
                inativos_count += 1
                continue

            if rec == 'DOWNGRADE_CANDIDATE':
                downgrade_count += 1

            if rec == 'MOVE_TO_CONCURRENT':
                concurrent_count += 1

            # SANEADO
            if is_prem:
                scenarios_data['saneado']['pA' if is_auth else 'pC'] += 1
            else:
                scenarios_data['saneado']['bA' if is_auth else 'bC'] += 1

            # OTIMIZADO físico
            final_ent = 'BASE' if (rec == 'DOWNGRADE_CANDIDATE' and ent == 'PREMIUM') else ent
            final_lic = 'CONCURRENT' if rec == 'MOVE_TO_CONCURRENT' else lic

            f_is_prem = (final_ent == 'PREMIUM')
            f_is_auth = (final_lic == 'AUTHORIZED')

            if f_is_prem:
                scenarios_data['otimizado']['pA' if f_is_auth else 'pC'] += 1
            else:
                scenarios_data['otimizado']['bA' if f_is_auth else 'bC'] += 1

        # ======================================================
        # NEM REAL (única fonte oficial)
        # ======================================================

        concurrency_summary = (
            self.summary.get('concurrency', {})
            if isinstance(self.summary, dict)
            else {}
        )

        scenario_points = {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0}

        hourly_nem = concurrency_summary.get('hourly_app_points_nem', {})

        if hourly_nem:
            values = list(hourly_nem.values())
            if values:
                scenario_points['p50'] = int(np.percentile(values, 50))
                scenario_points['p95'] = int(np.percentile(values, 95))
                scenario_points['p100'] = int(max(values))
                scenario_points['blackout'] = int(max(values))

        scenario_points_total = {
            'p50': int(opt_total_points),
            'p95': int(opt_total_points),
            'p100': int(opt_total_points),
            'blackout': int(opt_total_points)
        }

        # ======================================================
        # ABA 1 – AGORA USA summary_data (MESMO DO EXCEL)
        # ======================================================

        app_points_summary = self.summary.get('app_points_summary', {})

        painel_data = {
            'usuarios_ativos': self.summary.get('active_profiles_count', 0),
            'authorized': len(app_points_summary.get('auth_users', [])),
            'concurrent': len(app_points_summary.get('conc_users', [])),
            'premium': len(app_points_summary.get('premium_users', [])),
        }

        return {
            'inativos_count': inativos_count,
            'downgrade_count': downgrade_count,
            'concurrent_count': concurrent_count,
            'scenarios_data': scenarios_data,
            'scenario_points': scenario_points,
            'scenario_points_total': scenario_points_total,

            # NEM REAL
            'concurrency_peak_count': concurrency_summary.get('true_total_app_points'),
            'concurrency_peak_hours': concurrency_summary.get('peak_hours', []),
            'concurrency_peak_users_hours': concurrency_summary.get('peak_hours_users', []),
            'concurrency_hourly': concurrency_summary.get('hourly_counts', {}),
            'concurrency_hourly_app_points': concurrency_summary.get('hourly_app_points', {}),
            'concurrency_hourly_concurrent_app_points': concurrency_summary.get('hourly_concurrent_app_points', {}),
            'concurrency_hourly_app_points_nem': concurrency_summary.get('hourly_app_points_nem', {}),

            # ABA 1 alinhada ao Excel
            'painel_data': painel_data,

            # Mantém identidade apenas para seção Governança
            'identity_status': self.identity_analytics.get('status_counts', {}),
            'identity_domains': self.identity_analytics.get('domain_counts', {}),

            'ceiling_limit': self.summary.get('ceiling_limit', 1200)
            if isinstance(self.summary, dict)
            else 1200,
        }

    # ==========================================================
    # RESTANTE DO ARQUIVO INALTERADO
    # ==========================================================
    def prepare_governance_tables(self):
        cross_env_rows = [
            [f"<strong>{c.get('USERID')}</strong>",
             c.get('ENV_LIST'),
             c.get('DISPLAYNAME_LIST'),
             get_recommendation_badge(c.get('HYPOTHESIS', ''))]
            for c in self.governance['cross_env'][:200]
        ]

        login_conflicts_rows = [
            [f"<strong>{l.get('LOGINID')}</strong>",
             l.get('USERID_LIST'),
             l.get('DISPLAYNAME_LIST'),
             get_recommendation_badge(l.get('MERGE_DECISION', ''))]
            for l in self.governance['login_conflicts'][:200]
        ]

        worklist_rows = [
            [w.get('RAW_ID'),
             w.get('DISPLAYNAME'),
             w.get('HYPOTHESIS'),
             w.get('MERGE_DECISION')]
            for w in self.governance['worklist'][:200]
        ]

        return {
            'cross_env_rows': cross_env_rows,
            'login_conflicts_rows': login_conflicts_rows,
            'worklist_rows': worklist_rows,
            'title_divergence_html': ''
        }

    def prepare_app_points_rows(self):
        app_points_rows = []
        for s in sorted(self.app_points, key=lambda x: x.get('APP_POINTS', 0), reverse=True):

            points = s.get('APP_POINTS', 0)
            rec_code = s.get('OPTIMIZATION_REC')

            recommendation_badge_html = get_recommendation_badge(rec_code)
            recommendation_text = "Licença atual adequada ao perfil de uso."

            full_recommendation_html = f"{recommendation_badge_html}<br><small>{recommendation_text}</small>"

            app_points_rows.append([
                f"<strong>{s.get('USERID')}</strong>",
                s.get('DISPLAYNAME', 'N/A')[:30],
                full_recommendation_html,
                s.get('ENTITLEMENT'),
                s.get('LICENSE_MODEL'),
                f"{points:,.0f}",
                s.get('LOGIN_COUNT_90D', 0),
                s.get('TITLES', '')
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
            'domains': self.domains,
            'identity_analytics': self.identity_analytics
        }