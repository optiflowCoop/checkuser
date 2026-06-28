import re 
p = r"scripts/reporting/html_template.py" 
with open(p, "r", encoding="utf-8") as f: t = f.read() 
t = t.replace( 
    "chart_labels = [r[0] for r in peak_rows if r and len(r) >= 2]", 
