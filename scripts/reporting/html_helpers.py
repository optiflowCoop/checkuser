# scripts/reporting/html_helpers.py

def fmt_br(num):
    return f"{num:,.0f}".replace(",", ".")


def render_table(headers, rows, table_id="", extra_class=""):
    html = f'<div class="table-responsive"><table id="{table_id}" class="{extra_class}">\n'
    html += '  <thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead>\n'
    html += '  <tbody>\n'
    for row in rows:
        html += '    <tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>\n'
    html += '  </tbody>\n</table></div>\n'
    return html


def get_recommendation_badge(rec):
    if rec == "INATIVO (>90d)": return '<span class="badge badge-neutral">INATIVO (>90d)</span>'
    if rec == "DOWNGRADE_CANDIDATE": return '<span class="badge badge-warning">DOWNGRADE</span>'
    if rec == "MOVE_TO_CONCURRENT": return '<span class="badge badge-accent">P/ CONCURRENT</span>'
    if rec == "CONFIRMED_AUTHORIZED": return '<span class="badge badge-success">CONFIRMADO</span>'
    return '<span>OK</span>'


# Vocabulário de HYPOTHESIS/MERGE_DECISION real, produzido por src/identity_classification.py
# (ver identity_collisions_enriched.csv). O filtro por decisão da Aba 2 (Governança)
# depende deste texto batendo com as opções do <select id="selGovDec">.
def get_identity_hypothesis_badge(hypothesis):
    if hypothesis == 'CONFIRMED_DIFFERENT_PERSON':
        return '<span class="badge badge-critical">🔴 ALTO - PESSOAS DIFERENTES</span>'
    if hypothesis == 'REQUIRES_REVIEW':
        return '<span class="badge badge-warning">🟡 MÉDIO - REQUER REVISÃO</span>'
    if hypothesis == 'POTENTIAL_SAME_PERSON':
        return '<span class="badge badge-success">🟢 BAIXO - POSSÍVEL MESMA PESSOA</span>'
    return '<span class="badge badge-neutral">⚖️ NÃO CLASSIFICADO</span>'


# Vocabulário de CONFLICT_HINT real, produzido por src/login_conflicts.py
# (ver login_conflicts.csv).
def get_login_conflict_badge(conflict_hint):
    if conflict_hint == 'MULTIPLE_PERSONS_SAME_LOGIN':
        return '<span class="badge badge-critical">🔴 ALTO - PESSOAS DIFERENTES</span>'
    if conflict_hint == 'MULTIPLE_USERS_SAME_LOGIN':
        return '<span class="badge badge-warning">🟡 MÉDIO - REQUER REVISÃO</span>'
    return '<span class="badge badge-neutral">⚖️ NÃO CLASSIFICADO</span>'
