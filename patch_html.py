import re 
path = r" \c:/Users/esilva/OneDrive - FORESEA/Documentos/04 - "APPS/CHECKUSER/scripts/reporting/html_template.py\' 
with open(path, " "\r\', encoding=\utf-8\') as f: content = f.read() 
 
# Patch 1: _render_tab_peak 
old1 = """    chart_labels = [r[0] for r in chart_rows if r and len(r) >= 2]""" 
