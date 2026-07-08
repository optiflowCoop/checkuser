import re
p = 'output/reports/maximo_unified_dashboard.html'
s = open(p, encoding='utf-8').read()
# Extract gov tab content
start = s.find('id="tab-gov"')
end = s.find('id="tab-apppoints"', start)
gov = s[start:end]
# Find NORBE contexts
for m in re.finditer(r'NORBE', gov):
    ctx = gov[max(0,m.start()-60):m.start()+40]
    print(repr(ctx))
    print('---')