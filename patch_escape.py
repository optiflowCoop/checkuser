import sys
p = 'scripts/reporting/html_template.py'
with open(p, 'r', encoding='utf-8') as f:
    t = f.read()

# O tooltip foi inserido com chaves simples, mas o retorno é f-string.
# Precisamos escapar { -> {{ e } -> }} SOMENTE dentro do bloco do tooltip,
# exceto os marcadores do template como {labels_json}, {data_json} etc.
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
if old_tooltip not in t:
    print('tooltip not found')
    sys.exit(1)
t = t.replace(old_tooltip, new_tooltip)
print('escaped')

with open(p, 'w', encoding='utf-8') as f:
    f.write(t)