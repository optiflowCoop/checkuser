import sys
p = 'scripts/reporting/html_template.py'
with open(p, 'r', encoding='utf-8') as f: t = f.read()

# Corrigir legend
t = t.replace('legend: { display: true },', 'legend: {{ display: true }},')

# Corrigir tooltip com chaves escapadas no f-string
old_tooltip = """                                        label: function(ctx) {
                                            const ts = ctx.label;
                                            const users = ctx.parsed.y;
                                            const pointsByTs = {};
                                            (peakPointsLabels || []).forEach((h, i) => { pointsByTs[h] = peakPointsData[i]; });
                                            const appPoints = pointsByTs[ts] ?? null;
                                            return [
                                                ts + ' | Usuários simultâneos: ' + users,
                                                'Consumo AppPoints: ' + (appPoints !== null ? appPoints : 'N/D')
                                            ];
                                        }"""
new_tooltip = """                                        label: function(ctx) {{
                                            const ts = ctx.label;
                                            const users = ctx.parsed.y;
                                            const pointsByTs = {{}};
                                            (peakPointsLabels || []).forEach((h, i) => {{ pointsByTs[h] = peakPointsData[i]; }});
                                            const appPoints = pointsByTs[ts] ?? null;
                                            return [
                                                ts + ' | Usuários simultâneos: ' + users,
                                                'Consumo AppPoints: ' + (appPoints !== null ? appPoints : 'N/D')
                                            ];
                                        }}"""
if old_tooltip in t:
    t = t.replace(old_tooltip, new_tooltip)
    print('tooltip fixed')
else:
    print('old_tooltip not found')

with open(p, 'w', encoding='utf-8') as f: f.write(t)