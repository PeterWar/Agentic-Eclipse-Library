import json, re, os
h = open('apod.tpl.html', encoding='utf-8').read()
figs = {'__FIG_A__': open('figA.svg', encoding='utf-8').read(),
        '__FIG_B__': open('figB.svg', encoding='utf-8').read()}
for k, v in figs.items():
    assert k in h, k
    h = h.replace(k, v)
# tot el text no-ASCII a entitats numeriques: immune a qualsevol charset
h = ''.join(c if ord(c) < 128 else f'&#{ord(c)};' for c in h)
u = json.load(open('imgs.json'))
for k, v in (('__VIXEN_NET__', u['vixen_net']), ('__VIXEN_MARK__', u['vixen_mark']),
             ('__SONY_NET__', u['sony_net']), ('__SONY_MARK__', u['sony_mark']),
             ('__VIDEO__', u['video']), ('__POSTER__', u['poster'])):
    assert k in h, k
    h = h.replace(k, v)
open('apod.html', 'w', encoding='utf-8').write(h)
print(f'apod.html {os.path.getsize("apod.html")/1024/1024:.2f} MB · '
      f'placeholders: {re.findall(r"__[A-Z_]+__", h)}')
