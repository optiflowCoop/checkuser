import numpy as np
from .html_helpers import get_recommendation_badge
from datetime import datetime

def _parse_dt(s):
    if not s:
        return None
    text = str(s).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d-%H.%M.%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None

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

        # Cenários físicos (As-Is e Saneado) + otimizado físico (apenas contagem para UI)
        # Filtra apenas usuários FORESEA + PARCEIRO (escopo de licenciamento)
        foresea_parceiro_users = [
            u for u in self.app_points 
            if u.get('DOMAIN_CATEGORY', '') in ('FORESEA', 'PARCEIRO')
        ]
        
        for u in foresea_parceiro_users:
            lic = u.get('LICENSE_MODEL', 'CONCURRENT')
            ent = u.get('ENTITLEMENT', 'BASE')
            rec = u.get('OPTIMIZATION_REC', 'OK')
            app_pts = float(u.get('APP_POINTS', 0) or 0)

            is_prem = (ent == 'PREMIUM')
            is_auth = (lic == 'AUTHORIZED')

            # AS-IS (inclui todos do escopo)
            if is_prem:
                scenarios_data['asis']['pA' if is_auth else 'pC'] += 1
            else:
                scenarios_data['asis']['bA' if is_auth else 'bC'] += 1

            opt_total_points += app_pts

            # Inativos não entram nas próximas camadas
            if rec == 'INATIVO (>90d)':
                inativos_count += 1
                continue

            if rec == 'DOWNGRADE_CANDIDATE':
                downgrade_count += 1
            if rec == 'MOVE_TO_CONCURRENT':
                concurrent_count += 1

            # Saneado (sem inativos)
            if is_prem:
                scenarios_data['saneado']['pA' if is_auth else 'pC'] += 1
            else:
                scenarios_data['saneado']['bA' if is_auth else 'bC'] += 1

            # Otimizado físico (após recomendações)
            final_ent = 'BASE' if (rec == 'DOWNGRADE_CANDIDATE' and ent == 'PREMIUM') else ent
            final_lic = 'CONCURRENT' if rec == 'MOVE_TO_CONCURRENT' else lic

            f_is_prem = (final_ent == 'PREMIUM')
            f_is_auth = (final_lic == 'AUTHORIZED')

            if f_is_prem:
                scenarios_data['otimizado']['pA' if f_is_auth else 'pC'] += 1
            else:
                scenarios_data['otimizado']['bA' if f_is_auth else 'bC'] += 1

        # ------------------------------------------------------
        # NEM REAL (única fonte oficial para cenários fatorados)
        # ------------------------------------------------------
        concurrency_summary = self.summary.get('concurrency', {}) or {}
        scenario_points = {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0}

        hourly_nem_raw = concurrency_summary.get('hourly_app_points_nem', {}) or {}
        hourly_nem = {}
        if hourly_nem_raw:
            for date_str, value in hourly_nem_raw.items():
                dt = _parse_dt(date_str)
                if dt:
                    hourly_nem[dt.strftime("%Y-%m-%d %H:00")] = value

        if hourly_nem:
            values = list(hourly_nem.values())
            if values:
                scenario_points['p50'] = int(np.percentile(values, 50))
                scenario_points['p95'] = int(np.percentile(values, 95))
                scenario_points['p100'] = int(max(values))
                scenario_points['blackout'] = int(max(values))

        # Somatório bruto (per-user) apenas para referência (XLSX)
        # Usa apenas usuários FORESEA + PARCEIRO (mesmo escopo dos cenários)
        foresea_parceiro_total = sum(
            float(u.get('APP_POINTS', 0) or 0) 
            for u in foresea_parceiro_users
        )
        scenario_points_total = {
            'p50': int(foresea_parceiro_total),
            'p95': int(foresea_parceiro_total),
            'p100': int(foresea_parceiro_total),
            'blackout': int(foresea_parceiro_total)
        }

        # ------------------------------------------------------
        # Aba 1 alinhada ao Excel (summary_data)
        # ------------------------------------------------------
        app_points_summary = self.summary.get('app_points_summary', {}) or {}
        contracted = self.summary.get('ceiling_limit', 1200)
        true_peak = concurrency_summary.get('true_total_app_points', 0)
        p95 = scenario_points['p95']

        # Domain counts from identity_analytics
        domain_counts = self.identity_analytics.get('domain_counts', {})
        
        painel_data = {
            'usuarios_ativos': self.summary.get('active_profiles_count', 0),
            'usuarios_plano': len(self.app_points),
            'authorized': len(app_points_summary.get('auth_users', [])),
            'concurrent': len(app_points_summary.get('conc_users', [])),
            'premium': len(app_points_summary.get('premium_users', [])),
            'true_peak': true_peak,
            'p95': p95,
            'contratado': contracted,
            'folga': contracted - p95,
            'percentual_uso': round((p95 / contracted) * 100, 1) if contracted else 0,
            # Domain breakdown
            'dominio_foresea': domain_counts.get('foresea', 0),
            'dominio_parceiro': domain_counts.get('foresea_partner', 0),
            'dominio_terceiro': domain_counts.get('other', 0),
            'dominio_sem_dominio': domain_counts.get('no_domain', 0),
        }

        return {
            'inativos_count': inativos_count,
            'downgrade_count': downgrade_count,
            'concurrent_count': concurrent_count,
            'scenarios_data': scenarios_data,
            'scenario_points': scenario_points,
            'scenario_points_total': scenario_points_total,

            # NEM real / picos
            'concurrency_peak_count': true_peak,
            'concurrency_peak_hours': concurrency_summary.get('peak_hours', []),
            'concurrency_peak_users_hours': concurrency_summary.get('peak_hours_users', []),
            'concurrency_hourly': concurrency_summary.get('hourly_counts', {}),
            'concurrency_hourly_app_points': concurrency_summary.get('hourly_app_points', {}),
            'concurrency_hourly_concurrent_app_points': concurrency_summary.get('hourly_concurrent_app_points', {}),
            'concurrency_hourly_app_points_nem': hourly_nem,

            # Aba 1 executiva
            'painel_data': painel_data,

            # Governança (mantém apenas agregados para gráficos/listas)
            'identity_status': self.identity_analytics.get('status_counts', {}),
            'identity_domains': self.identity_analytics.get('domain_counts', {}),

            'ceiling_limit': contracted,
        }

    # ==========================================================
    # GOVERNANÇA (Top Divergências, Cross-Env, LoginID, Worklist)
    # ==========================================================
    def prepare_governance_tables(self):
        cross_env_rows = [
            [
                f" <strong>{c.get('USERID')} </strong>",
                c.get('ENV_LIST'),
                c.get('DISPLAYNAME_LIST'),
                get_recommendation_badge(c.get('HYPOTHESIS', ''))
            ]
            for c in self.governance.get('cross_env', [])[:200]
        ]

        login_conflicts_rows = [
            [
                f"<strong>{l.get('LOGINID')}</strong>",
                l.get('USERID_LIST'),
                l.get('DISPLAYNAME_LIST'),
                get_recommendation_badge(l.get('MERGE_DECISION', ''))
            ]
            for l in self.governance.get('login_conflicts', [])[:200]
        ]

        worklist_rows = [
            [
                w.get('RAW_ID'),
                w.get('DISPLAYNAME'),
                w.get('HYPOTHESIS'),
                w.get('MERGE_DECISION')
            ]
            for w in self.governance.get('worklist', [])[:200]
        ]

        # Matriz de divergências (restaurada)
        title_divergence_html = []
        for div in self.governance.get('detailed_divergences', [])[:30]:
            title = div.get('title')
            data = div.get('data', {})
            alerts = []

            # Divergência de TYPE
            all_types = {t for types in data.get('types', {}).values() for t in types if t}
            if len(all_types) > 1:
                alerts.append('<span class="badge badge-critical">TYPE DIVERGENTE</span>')

            # Divergência de GRUPOS
            base_groups = next(iter(data.get('groups', {}).values()), set())
            if any(s != base_groups for s in data.get('groups', {}).values()):
                alerts.append('<span class="badge badge-high">GRUPOS DIVERGENTES</span>')

            title_divergence_html.append(
                f'<div class="type-card"><h4>{title} {" ".join(alerts)}</h4>'
            )

            # Detalhamento dos ambientes para TYPE
            if len(all_types) > 1:
                title_divergence_html.append(
                    '<div class="env-divergence"><div class="env-header">⚠️ Inconsistência de TYPE</div>'
                )
                for env, types in sorted(data.get('types', {}).items()):
                    title_divergence_html.append(
                        f'<div>📍 {env}: {", ".join(sorted(t for t in types if t))}</div>'
                    )
                title_divergence_html.append('</div>')

            title_divergence_html.append('</div>')

        return {
            'cross_env_rows': cross_env_rows,
            'login_conflicts_rows': login_conflicts_rows,
            'worklist_rows': worklist_rows,
            'title_divergence_html': "".join(title_divergence_html)
        }

    # ==========================================================
    # TABELA DE AÇÕES (Plano de Ação)
    # ==========================================================
    def prepare_app_points_rows(self):
        app_points_rows = []

        for s in sorted(self.app_points, key=lambda x: x.get('APP_POINTS', 0), reverse=True):
            points = s.get('APP_POINTS', 0)
            rec_code = s.get('OPTIMIZATION_REC')
            current_license = s.get('LICENSE_MODEL', 'CONCURRENT')
            current_entitlement = s.get('ENTITLEMENT', 'BASE')

            # Determina a licença To-Be baseada na recomendação
            if rec_code == 'MOVE_TO_CONCURRENT':
                license_to_be = 'CONCURRENT'
                recommendation_text = "Migrar para Concurrent (baixo uso)."
            elif rec_code == 'CONFIRMED_AUTHORIZED':
                license_to_be = 'AUTHORIZED'
                recommendation_text = "Manter Authorized (uso crítico)."
            elif rec_code == 'DOWNGRADE_CANDIDATE':
                license_to_be = 'CONCURRENT'
                recommendation_text = "Downgrade de Premium para Base."
            elif rec_code == 'INATIVO (>90d)':
                license_to_be = 'CONCURRENT'
                recommendation_text = "Usuário inativo. Considerar remoção."
            elif rec_code == 'REQUER_REVISAO':
                license_to_be = 'CONCURRENT'
                recommendation_text = "Requer revisão manual."
            else:  # OK
                license_to_be = current_license
                recommendation_text = "Licença atual adequada ao perfil de uso."

            # Badge + descrição
            recommendation_badge_html = get_recommendation_badge(rec_code)
            full_recommendation_html = f"{recommendation_badge_html}<br><small>{recommendation_text}</small>"

            displayname = s.get('DISPLAYNAME', 'N/A')
            if isinstance(displayname, set):
                displayname = '; '.join(sorted(str(x) for x in displayname if x)) or 'N/A'
            app_points_rows.append([
                f"<strong>{s.get('USERID')}</strong>",
                str(displayname)[:30],
                full_recommendation_html,
                current_entitlement,
                license_to_be,  # Licença To-Be (corrigida)
                f"{points:,.0f}",
                f"{points:,.0f}",  # Fator Analytics
                s.get('LOGIN_COUNT_90D', 0),
                s.get('LOCATION_SITE', 'N/A'),
                s.get('TITLES', '')
            ])

        return app_points_rows

    # ==========================================================
    # ORQUESTRADOR
    # ==========================================================
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
