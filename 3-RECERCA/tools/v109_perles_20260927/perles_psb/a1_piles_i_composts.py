"""a1 (V109 · perles_psb) · Llegeix la pila visible de la V107 i de la V108 a la caixa del limbe (ràsters, alfes, màscares, opacitats i modes
reals) i les recompon sense les capes d'ajust. Desa els composts recompostos i els ràsters de les capes a cache/ per als passos següents,
i compara capa a capa V107/V108 (quines capes canvien a la caixa, i on).
Sortida: cache/PILA_V107.npz, cache/PILA_V108.npz, REC_V107.npy, REC_V108.npy, A1_CAPES.json"""
import time
import numpy as np
from comu_perles import PSB, V107, V108, CAIXA, OUT, pila, compon, geom, lum, desa, fusionat
t0 = time.time(); (OUT / 'cache').mkdir(exist_ok=True)
d, th = geom(CAIXA)
P7, P8 = PSB(str(V107)), PSB(str(V108)); S7, S8 = pila(P7, CAIXA), pila(P8, CAIXA)
assert [c['id'] for c in S7] == [c['id'] for c in S8]
for tag, S in (('V107', S7), ('V108', S8)):
    np.savez(OUT / f'cache/PILA_{tag}.npz', **{f"L{c['id']}_{k}": (np.round(c[k] * 65535).astype(np.uint16)) for c in S for k in ('rgb', 'alfa', 'masc')},
             meta=np.array([f"{c['id']}|{c['mode']}|{c['op']}|{c['nom']}" for c in S]))
R7, R8 = compon(S7), compon(S8); np.save(OUT / 'REC_V107.npy', R7); np.save(OUT / 'REC_V108.npy', R8)
rep = dict(caixa=CAIXA, ordre=[f"{c['id']} {c['mode']} {round(c['op']*255)} {c['nom']}" for c in S7], capes={})
bandes = [(-60, -2), (-2, 0), (0, 2), (2, 4), (4, 8), (8, 15), (15, 25), (25, 40), (40, 60), (60, 100)]
for c7, c8 in zip(S7, S8):
    o = {}
    for k in ('rgb', 'alfa', 'masc'):
        dd = np.abs(c8[k] - c7[k]); dd = dd.max(-1) if dd.ndim == 3 else dd
        o[k + '_max'] = round(float(dd.max()), 6)
    if o['rgb_max'] > 0 or o['alfa_max'] > 0:
        g7, g8 = c7['rgb'][..., 1], c8['rgb'][..., 1]; ae = c7['alfa'] * c7['masc'] * c7['op']
        o['G_dif_per_banda'] = {f'{a}..{b}': dict(mitj=round(float((g8 - g7)[(d >= a) & (d < b)].mean()), 6), rms=round(float(np.sqrt(((g8 - g7)[(d >= a) & (d < b)] ** 2).mean())), 6),
                                                   alfa_efectiva_mitj=round(float(ae[(d >= a) & (d < b)].mean()), 4)) for a, b in bandes}
        o['G_dif_perles_150_200'] = {f'{a}..{b}': dict(mitj=round(float((g8 - g7)[(d >= a) & (d < b) & (th >= 150) & (th < 200)].mean()), 6),
                                                        rms=round(float(np.sqrt(((g8 - g7)[(d >= a) & (d < b) & (th >= 150) & (th < 200)] ** 2).mean())), 6),
                                                        alfa_efectiva_mitj=round(float(ae[(d >= a) & (d < b) & (th >= 150) & (th < 200)].mean()), 4)) for a, b in bandes}
    rep['capes'][c7['id']] = dict(nom=c7['nom'], mode=c7['mode'], op=round(c7['op'] * 255), **o)
# recompost contra fusionat
F7, F8 = fusionat(V107, CAIXA), fusionat(V108, CAIXA)
l7, l8, f7, f8 = lum(R7), lum(R8), lum(F7), lum(F8)
rep['recompost_contra_fusionat'] = {}
for a, b in bandes:
    for sec, (s0, s1) in (('tot', (0, 360)), ('perles_150_200', (150, 200))):
        m = (d >= a) & (d < b) & (th >= s0) & (th < s1)
        rep['recompost_contra_fusionat'][f'{sec} {a}..{b}'] = dict(dRec_mitj=round(float((l8 - l7)[m].mean()), 6), dRec_rms=round(float(np.sqrt(((l8 - l7)[m] ** 2).mean())), 6),
                                                                   dFus_mitj=round(float((f8 - f7)[m].mean()), 6), dFus_rms=round(float(np.sqrt(((f8 - f7)[m] ** 2).mean())), 6),
                                                                   rec7_mitj=round(float(l7[m].mean()), 4), fus7_mitj=round(float(f7[m].mean()), 4))
rep['temps_s'] = round(time.time() - t0, 1); desa(OUT / 'A1_CAPES.json', rep); print(open(OUT / 'A1_CAPES.json').read()[:6000])
