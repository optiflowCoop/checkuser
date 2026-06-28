import sys
p = 'scripts/reporting/html_template.py'
with open(p, 'r', encoding='utf-8') as f: t = f.read()

# Patch 4: JS - ler attributes
old4 = "                    const labelsJson = canvasEl.getAttribute('data-labels') || '[]';\n                    const dataJson = canvasEl.getAttribute('data-data') || '[]';"
new4 = "                    const labelsJson = canvasEl.getAttribute('data-labels') || '[]';\n                    const dataJson = canvasEl.getAttribute('data-data') || '[]';\n                    const pointsLabelsJson = canvasEl.getAttribute('data-points-labels') || '[]';\n                    const pointsDataJson = canvasEl.getAttribute('data-points-data') || '[]';"
if old4 not in t: print('FAIL 4'); sys.exit(1)
t = t.replace(old4, new4); print('Patch 4 ok')

# Patch 5: JS - parse
old5 = "                    const peakLabels = JSON.parse(labelsJson);\n                    const peakData = JSON.parse(dataJson);"
new5 = "                    const peakLabels = JSON.parse(labelsJson);\n                    const peakData = JSON.parse(dataJson);\n                    const peakPointsLabels = JSON.parse(pointsLabelsJson);\n                    const peakPointsData = JSON.parse(pointsDataJson);"
if old5 not in t: print('FAIL 5'); sys.exit(1)
t = t.replace(old5, new5); print('Patch 5 ok')

# Patch 6: tooltip
old6 = "                                        label: (ctx) => ` ${'{'}ctx.parsed.y{'}'} users simultâneos`"
new6 = "                                        label: function(ctx) {\n                                            const ts = ctx.label;\n                                            const users = ctx.parsed.y;\n                                            const pointsByTs = {};\n                                            (peakPointsLabels || []).forEach((h, i) => { pointsByTs[h] = peakPointsData[i]; });\n                                            const appPoints = pointsByTs[ts] ?? null;\n                                            return [\n                                                ts + ' | Usuários simultâneos: ' + users,\n                                                'Consumo AppPoints: ' + (appPoints !== null ? appPoints : 'N/D')\n                                            ];\n                                        }"
if old6 not in t: print('FAIL 6'); sys.exit(1)
t = t.replace(old6, new6); print('Patch 6 ok')

with open(p, 'w', encoding='utf-8') as f: f.write(t)
print('ALL JS DONE')