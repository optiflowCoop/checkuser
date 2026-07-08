import re
p = 'output/reports/maximo_unified_dashboard.html'
s = open(p, encoding='utf-8').read()
parts = s.split('id="tab-')
for part in parts[1:]:
    tabid = part[:part.find('"')]
    cnt = part.count('NORBE')
    if cnt > 0:
        print(tabid, '-> NORBE:', cnt)
print('TOTAL NORBE:', s.count('NORBE'))
print('TOTAL NOR(not BE):', len(re.findall(r'NOR(?!BE)', s)))