import re
s = open('_bb.xml', encoding='utf-8').read()
pages = re.findall(r'<page width="([0-9.]+)" height="([0-9.]+)">(.*?)</page>', s, re.S)
print('pages:', len(pages))
for pi, (w, h, body) in enumerate(pages, 1):
    ws = []
    for m in re.finditer(
            r'<word xMin="([0-9.]+)" yMin="([0-9.]+)" xMax="([0-9.]+)" yMax="([0-9.]+)">([^<]+)</word>',
            body):
        xMax = float(m.group(3))
        if xMax > 515:
            ws.append((round(xMax, 1), m.group(5), round(float(m.group(2)))))
    if ws:
        print('page %d: %d words >515pt' % (pi, len(ws)))
        for x in ws[:8]:
            print('   xMax=%.1f y=%.0f word=%s' % (x[0], x[1], x[2]))
        print('   page w=%s h=%s' % (w, h))
