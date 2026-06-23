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
