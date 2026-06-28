import sys
p = 'scripts/reporting/html_template.py'
with open(p, 'r', encoding='utf-8') as f: t = f.read()

# Remover as 2 repeticoes extras de pointsLabelsJson/pointsDataJson (linhas 637-640)
# O bloco correto deve ter 1 ocorrencia, depois peakLabels, depois peakPointsLabels
old = "                    const pointsLabelsJson = canvasEl.getAttribute('data-points-labels') || '[]';\n                    const pointsDataJson = canvasEl.getAttribute('data-points-data') || '[]';\n                    const pointsLabelsJson = canvasEl.getAttribute('data-points-labels') || '[]';\n                    const pointsDataJson = canvasEl.getAttribute('data-points-data') || '[]';\n                    const pointsLabelsJson = canvasEl.getAttribute('data-points-labels') || '[]';\n                    const pointsDataJson = canvasEl.getAttribute('data-points-data') || '[]';"
new = "                    const pointsLabelsJson = canvasEl.getAttribute('data-points-labels') || '[]';\n                    const pointsDataJson = canvasEl.getAttribute('data-points-data') || '[]';"
if old in t:
    t = t.replace(old, new)
    print('dedup ok')
else:
    print('old not found')

with open(p, 'w', encoding='utf-8') as f: f.write(t)