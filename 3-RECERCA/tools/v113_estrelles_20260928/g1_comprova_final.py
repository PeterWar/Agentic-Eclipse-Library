"""g1 · V113 (Claude, 28-09-2026): comprovació final SOBRE LA IMATGE (render natiu del Photoshop, llenç sencer, sense retalls) de la V113 d'abans
(estrelles de la Vixen desplaçades) contra la V113 nova. Per a cada posició: excés = màxim de la luminància a r < 3 px menys la mediana de l'anell
8–12 px, en sigmes robustos de l'anell. Tres famílies:
  · les 60 del S22 (han de quedar iguals: quocient d'excés ≈ 1);
  · les còpies desplaçades de la Vixen (EXTRA_ESTRELLES.json, vixen_copy) — les estrelles fantasma: l'excés ha de baixar al soroll;
  · les 4 estrelles de Tycho que faltaven (noves.json): l'excés ha de pujar.
Sortida: 4-RESULTATS/v113_estrelles_20260928/G1_COMPROVACIO_FINAL.json"""
import json
from pathlib import Path
import numpy as np, tifffile
R = Path(__file__).resolve().parents[3]
O = R / '4-RESULTATS/v113_estrelles_20260928'
ABANS = R / '4-RESULTATS/v112_claude_20260928/V113_natiu/visible_complet.tif'
ARA = O / 'V113e_natiu/visible_complet.tif'
S22 = json.loads((R / '4-RESULTATS/v65_pere_estrelles_20260914/S22_final_catalog.json').read_text())['stars']
EXTRA = json.loads((O / 'fantasmes/EXTRA_ESTRELLES.json').read_text())
NOVES = json.loads((O / 'estrelles/noves.json').read_text())
def lum(p):
    a = tifffile.imread(p).astype(np.float32); return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
LA, LN = lum(ABANS), lum(ARA)
H, W = LA.shape
yy, xx = np.mgrid[-12:13, -12:13]; rr = np.hypot(xx, yy); nucli = rr < 3; anell = (rr >= 8) & (rr < 12)
def exces(L, x, y):
    ix, iy = int(round(x)), int(round(y))
    if not (12 <= ix < W - 12 and 12 <= iy < H - 12): return None
    w = L[iy - 12:iy + 13, ix - 12:ix + 13]; bg = float(np.median(w[anell])); s = 1.4826 * float(np.median(np.abs(w[anell] - bg)))
    return dict(exces=float(w[nucli].max() - bg), sigma=max(s, 1.0), snr=float((w[nucli].max() - bg) / max(s, 1.0)))
out = dict(abans=str(ABANS.relative_to(R)), ara=str(ARA.relative_to(R)), s22=[], fantasmes=[], noves=[])
for s in S22:
    a, n = exces(LA, s['x'], s['y']), exces(LN, s['x'], s['y'])
    if a and n: out['s22'].append(dict(id=s['id'], abans=round(a['exces'], 1), ara=round(n['exces'], 1), quocient=round(n['exces'] / max(a['exces'], 1), 4)))
for e in EXTRA:
    if not e.get('vixen_copy'): continue
    a, n = exces(LA, e['xf'], e['yf']), exces(LN, e['xf'], e['yf'])
    if a and n: out['fantasmes'].append(dict(copia_de=e['copia_de'], x=e['x'], y=e['y'], snr_abans=round(a['snr'], 1), snr_ara=round(n['snr'], 1),
                                             exces_abans=round(a['exces'], 1), exces_ara=round(n['exces'], 1)))
for s in NOVES:
    a, n = exces(LA, s['x'], s['y']), exces(LN, s['x'], s['y'])
    out['noves'].append(dict(id=s['id'], snr_abans=round(a['snr'], 1), snr_ara=round(n['snr'], 1), exces_abans=round(a['exces'], 1), exces_ara=round(n['exces'], 1)))
q = np.array([t['quocient'] for t in out['s22']])
out['resum'] = dict(s22_n=len(q), s22_quocient_mediana=float(np.median(q)), s22_quocient_min=float(q.min()), s22_quocient_max=float(q.max()),
                    s22_fora_5pct=[t['id'] for t in out['s22'] if abs(t['quocient'] - 1) > 0.05],
                    fantasmes_n=len(out['fantasmes']), fantasmes_snr_abans_mediana=float(np.median([t['snr_abans'] for t in out['fantasmes']])),
                    fantasmes_snr_ara_mediana=float(np.median([t['snr_ara'] for t in out['fantasmes']])),
                    fantasmes_ara_snr_sobre_5=[(t['copia_de'], t['snr_ara']) for t in out['fantasmes'] if t['snr_ara'] > 5])
(O / 'G1_COMPROVACIO_FINAL.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps(out['resum'], ensure_ascii=False, indent=1))
for t in sorted(out['fantasmes'], key=lambda t: -t['snr_abans']): print('fantasma', t['copia_de'], t['x'], t['y'], 'S/N', t['snr_abans'], '→', t['snr_ara'])
for t in out['noves']: print('nova', t['id'], 'S/N', t['snr_abans'], '→', t['snr_ara'], ' excés', t['exces_abans'], '→', t['exces_ara'])
