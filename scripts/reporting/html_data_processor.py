import numpy as np
from datetime import datetime

from .html_helpers import get_recommendation_badge, get_identity_hypothesis_badge, get_login_conflict_badge


def _parse_dt(s):
    if not s:
        return None
    text = str(s).strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d-%H.%M.%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


class DataProcessor:
    def __init__(self, summary, governance, app_points, domains, identity_analytics, reconciliation_data=None):
        self.summary = summary
        self.governance = governance
        self.app_points = app_points
        self.domains = domains
        self.identity_analytics = identity_analytics
        self.reconciliation_data = reconciliation_data

    def process_app_points_analytics(self):
        inativos_count = 0
        downgrade_count = 0
        concurrent_count = 0

        scenario_points = {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0}
        scenario_points_by_scope = {
            'foresea': {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0},
            'terceiros': {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0},
            'integracao': {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0},
            'todos': {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0},
        }
        scenarios_by_scope = {
            'foresea': {'asis': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}, 'saneado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}, 'otimizado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}},
            'terceiros': {'asis': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}, 'saneado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}, 'otimizado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}},
            'integracao': {'asis': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}, 'saneado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}, 'otimizado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}},
            'todos': {'asis': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}, 'saneado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}, 'otimizado': {'pA': 0, 'pC': 0, 'bA': 0, 'bC': 0}},
        }

        for u in self.app_points:
            domain_cat = str(u.get('DOMAIN_CATEGORY', '')).strip().upper()
            if domain_cat in ('FORESEA', 'PARCEIRO'):
                scope_key = 'foresea'
            elif domain_cat == 'INTEGRACAO':
                scope_key = 'integracao'
            elif domain_cat and domain_cat != 'SEM DOMINIO':
                scope_key = 'terceiros'
            else:
                continue

            lic = str(u.get('LICENSE_MODEL', 'CONCURRENT') or '').strip().upper()
            ent = str(u.get('ENTITLEMENT', 'BASE') or '').strip().upper()
            rec = str(u.get('OPTIMIZATION_REC', 'OK') or '').strip().upper()
            is_prem = (ent == 'PREMIUM')
            is_auth = (lic == 'AUTHORIZED')

            if is_prem:
                scenarios_by_scope[scope_key]['asis']['pA' if is_auth else 'pC'] += 1
            else:
                scenarios_by_scope[scope_key]['asis']['bA' if is_auth else 'bC'] += 1

            if rec.startswith('INATIVO'):
                inativos_count += 1
                # Inativo sai do saneado/otimizado, mas continua no As-Is.
                continue

            if rec == 'DOWNGRADE_CANDIDATE':
                downgrade_count += 1
            if rec == 'MOVE_TO_CONCURRENT':
                concurrent_count += 1

            if is_prem:
                scenarios_by_scope[scope_key]['saneado']['pA' if is_auth else 'pC'] += 1
            else:
                scenarios_by_scope[scope_key]['saneado']['bA' if is_auth else 'bC'] += 1

            final_ent = 'BASE' if (rec == 'DOWNGRADE_CANDIDATE' and ent == 'PREMIUM') else ent
            final_lic = 'CONCURRENT' if rec == 'MOVE_TO_CONCURRENT' else lic
            f_is_prem = (final_ent == 'PREMIUM')
            f_is_auth = (final_lic == 'AUTHORIZED')

            if f_is_prem:
                scenarios_by_scope[scope_key]['otimizado']['pA' if f_is_auth else 'pC'] += 1
            else:
                scenarios_by_scope[scope_key]['otimizado']['bA' if f_is_auth else 'bC'] += 1

        for scenario in ('asis', 'saneado', 'otimizado'):
            for key in ('pA', 'pC', 'bA', 'bC'):
                scenarios_by_scope['todos'][scenario][key] = (
                    scenarios_by_scope['foresea'][scenario][key]
                    + scenarios_by_scope['terceiros'][scenario][key]
                    + scenarios_by_scope['integracao'][scenario][key]
                )

        # FONTE ÚNICA de P50/P95/P100 (unificação 2026-07-11): antes esta
        # série vinha de `true_capacity_metrics.json` — uma população e
        # lógica de licença DIFERENTES das usadas no Cenário Conciliado —
        # e cada aba (Cenários de AppPoints, Eventos Críticos, Peak
        # Contributors) acabava mostrando um número diferente para "P95".
        # Agora todas as três leem `reconciliation_data['stats']['nem_by_scope']`
        # (população conciliada AD×Maximo + licença estatística com presença
        # ajustada por rotação offshore — ver license_reconciliation.py).
        reconciliation_stats = (self.reconciliation_data or {}).get('stats', {})
        nem_by_scope = reconciliation_stats.get('nem_by_scope', {})
        for scope_key in ('foresea', 'terceiros', 'integracao', 'todos'):
            v = nem_by_scope.get(scope_key)
            if v:
                scenario_points_by_scope[scope_key] = {
                    'p50': v['p50'], 'p95': v['p95'], 'p100': v['p100'], 'blackout': v['p100'],
                    'conciliados': v.get('conciliados', 0), 'terceiros_ativos': v.get('terceiros_ativos', 0),
                    'authorized': v.get('authorized', 0), 'concurrent': v.get('concurrent', 0),
                    'reserva_authorized': v.get('reserva_authorized', 0),
                }
        if nem_by_scope.get('todos'):
            scenario_points = dict(scenario_points_by_scope['todos'])

        # Fallback defensivo: se o Cenário Conciliado ainda não rodou para um
        # escopo, usa a composição física do simulador de otimização.
        for scope_key in ('foresea', 'terceiros', 'integracao', 'todos'):
            if scenario_points_by_scope[scope_key] == {'p50': 0, 'p95': 0, 'p100': 0, 'blackout': 0}:
                otimizado = scenarios_by_scope[scope_key]['otimizado']
                total_fisico_otimizado = (
                    (otimizado['pA'] * 5)
                    + (otimizado['pC'] * 15)
                    + (otimizado['bA'] * 3)
                    + (otimizado['bC'] * 10)
                )
                scenario_points_by_scope[scope_key] = {
                    'p50': total_fisico_otimizado,
                    'p95': total_fisico_otimizado,
                    'p100': total_fisico_otimizado,
                    'blackout': total_fisico_otimizado,
                }

        scenarios_data = scenarios_by_scope['todos']


        app_points_summary = self.summary.get('app_points_summary', {}) or {}
        contracted = self.summary.get('ceiling_limit', 1200)
        # P100/P95 do Painel também vêm do Cenário Conciliado (fonte única).
        true_peak = scenario_points['p100']
        p95 = scenario_points['p95']

        authorized = len(app_points_summary.get('auth_users', []))
        concurrent_lic = len(app_points_summary.get('conc_users', []))
        premium = len(app_points_summary.get('premium_users', []))

        domain_counts = self.identity_analytics.get('domain_counts', {}) or {}
        if not domain_counts or not any(k in domain_counts for k in ('foresea', 'foresea_partner', 'other', 'no_domain')):
            domain_counts = {'foresea': 0, 'foresea_partner': 0, 'other': 0, 'no_domain': 0}
            identities = self.summary.get('identities', []) or []
            for ident in identities:
                email = str(ident.get('PRIMARYEMAIL', '')).lower()
                if '@foresea.com' in email:
                    domain_counts['foresea'] += 1
                elif '@foresea-partner.com' in email:
                    domain_counts['foresea_partner'] += 1
                elif '@' in email:
                    domain_counts['other'] += 1
                else:
                    domain_counts['no_domain'] += 1

        painel_data = {
            'usuarios_ativos': self.summary.get('active_profiles_count', 0),
            'usuarios_plano': len(self.app_points),
            'authorized': authorized,
            'concurrent': concurrent_lic,
            'premium': premium,
            'true_peak': true_peak,
            'p95': p95,
            'contratado': contracted,
            'folga': contracted - p95,
            'percentual_uso': round((p95 / contracted) * 100, 1) if contracted else 0,
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
            'scenarios_by_scope': scenarios_by_scope,
            'scenario_points': scenario_points,
            'scenario_points_by_scope': scenario_points_by_scope,
            'concurrency_peak_count': true_peak,
            # Todos os 4 escopos (com série horária, pico e composição
            # próprios) — permite a aba Peak ter o MESMO seletor de escopo
            # da aba Cenários de AppPoints, com a curva de uso recalculada
            # de verdade por escopo (não só um filtro visual de tabela).
            'nem_by_scope': nem_by_scope,
            'painel_data': painel_data,
            'identity_status': self.identity_analytics.get('status_counts', {}),
            'identity_domains': self.identity_analytics.get('domain_counts', {}),
            'ceiling_limit': contracted,
        }

    def prepare_governance_tables(self):
        # cross_env_userid_reuse.csv não tem sua própria conclusão de risco (só um
        # REUSE_FLAG constante) — a classificação real (HYPOTHESIS) é calculada por
        # USERID em identity_classification.py e vive em identity_collisions_enriched.csv.
        # Usamos essa mesma classificação aqui para a coluna "Conclusão".
        worklist_hypothesis_by_userid = {
            w.get('USERID'): w.get('HYPOTHESIS')
            for w in self.governance.get('worklist', [])
            if w.get('USERID')
        }

        cross_env_rows = [
            [
                f" <strong>{c.get('USERID')} </strong>",
                c.get('ENV_LIST'),
                c.get('DISPLAYNAME_LIST'),
                get_identity_hypothesis_badge(worklist_hypothesis_by_userid.get(c.get('USERID')))
            ]
            for c in self.governance.get('cross_env', [])[:200]
        ]

        login_conflicts_rows = [
            [
                f"<strong>{l.get('LOGINID')}</strong>",
                l.get('USERID_LIST'),
                l.get('DISPLAYNAME_LIST'),
                get_login_conflict_badge(l.get('CONFLICT_HINT', ''))
            ]
            for l in self.governance.get('login_conflicts', [])[:200]
        ]

        worklist_rows = [
            [
                w.get('RAW_ID'),
                w.get('DISPLAYNAME'),
                get_identity_hypothesis_badge(w.get('HYPOTHESIS')),
                w.get('MERGE_DECISION')
            ]
            for w in self.governance.get('worklist', [])[:200]
        ]

        title_divergence_html = []
        for div in self.governance.get('detailed_divergences', [])[:30]:
            title = div.get('title')
            data = div.get('data', {})
            alerts = []

            all_types = {t for types in data.get('types', {}).values() for t in types if t}
            if len(all_types) > 1:
                alerts.append('<span class="badge badge-critical">TYPE DIVERGENTE</span>')

            base_groups = next(iter(data.get('groups', {}).values()), set())
            if any(s != base_groups for s in data.get('groups', {}).values()):
                alerts.append('<span class="badge badge-high">GRUPOS DIVERGENTES</span>')

            title_divergence_html.append(f'<div class="type-card"><h4>{title} {" ".join(alerts)}</h4>')

            if len(all_types) > 1:
                title_divergence_html.append('<div class="env-divergence"><div class="env-header">Inconsistência de TYPE</div>')
                for env, types in sorted(data.get('types', {}).items()):
                    title_divergence_html.append(f'<div>{env}: {", ".join(sorted(t for t in types if t))}</div>')
                title_divergence_html.append('</div>')

            title_divergence_html.append('</div>')

        return {
            'cross_env_rows': cross_env_rows,
            'cross_env_total': len(self.governance.get('cross_env', [])),
            'login_conflicts_rows': login_conflicts_rows,
            'login_conflicts_total': len(self.governance.get('login_conflicts', [])),
            'worklist_rows': worklist_rows,
            'worklist_total': len(self.governance.get('worklist', [])),
            'title_divergence_html': ''.join(title_divergence_html)
        }

    def prepare_app_points_rows(self):
        app_points_rows = []

        for s in sorted(self.app_points, key=lambda x: x.get('APP_POINTS', 0), reverse=True):
            points = s.get('APP_POINTS', 0)
            rec_code = s.get('OPTIMIZATION_REC')
            current_license = s.get('LICENSE_MODEL', 'CONCURRENT')
            current_entitlement = s.get('ENTITLEMENT', 'BASE')

            if rec_code == 'MOVE_TO_CONCURRENT':
                license_to_be = 'CONCURRENT'
                recommendation_text = 'Migrar para Concurrent (baixo uso).'
            elif rec_code == 'CONFIRMED_AUTHORIZED':
                license_to_be = 'AUTHORIZED'
                recommendation_text = 'Manter Authorized (uso crítico).'
            elif rec_code == 'DOWNGRADE_CANDIDATE':
                license_to_be = 'CONCURRENT'
                recommendation_text = 'Downgrade de Premium para Base.'
            elif rec_code == 'INATIVO (>90d)':
                license_to_be = 'CONCURRENT'
                recommendation_text = 'Usuário inativo. Considerar remoção.'
            elif rec_code == 'REQUER_REVISAO':
                license_to_be = 'CONCURRENT'
                recommendation_text = 'Requer revisão manual.'
            else:
                license_to_be = current_license
                recommendation_text = 'Licença atual adequada ao perfil de uso.'

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
                license_to_be,
                f"{points:,.0f}",
                f"{points:,.0f}",
                s.get('LOGIN_COUNT_90D', 0),
                s.get('LOCATION_SITE', 'N/A'),
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