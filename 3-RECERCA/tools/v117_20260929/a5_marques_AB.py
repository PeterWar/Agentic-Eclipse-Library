"""a5 (V117: còpia de v116/a5 sobre el b1 CORREGIT) · a5 (V116, 29-09-2026) · Les marques de Pere jutjades amb la NOSTRA dada: els dos apuntaments de la Sony (A i B, ~750 px de desplaçament al sensor).
Un buit real del cel surt al mateix lloc i amb la mateixa fondària a A i a B. Un artefacte del sensor o de l'òptica (flat, pols, patró fix, arcs) no hi coincideix.
Per a cada marca (etiquetes de la V115 de Pere), sobre el detall azimutal de b1 (ln, 0,15°–1,5°): mitjana de D_A, D_B i del detall coherent D dins la marca
menys la de l'anell de 60–300 px, la coherència mitjana w, la fracció de la marca dins el camp comú, i el veredicte:
  REAL si D_A i D_B tenen el mateix signe i |D_A − D_B| < ½·max(|D_A|, |D_B|); D'UN SOL APUNTAMENT si un és ≥ 2× l'altre o de signe contrari; SENSE DADA si < 30 % al camp comú.
Ús: a5_marques_AB.py  → 4-RESULTATS/v117_20260929/AB/A5_MARQUES_AB.json"""
import json, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'; B1 = R / '4-RESULTATS/v117_20260929/AB/b1'
lab = np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r'); M = json.load(open(O / 'MARQUES_V115.json'))['marques']
DA = np.load(B1 / 'DA_f16.npy', mmap_mode='r'); DB = np.load(B1 / 'DB_f16.npy', mmap_mode='r'); D = np.load(B1 / 'D_coherent_f32.npy', mmap_mode='r'); Wc = np.load(B1 / 'W_coherencia_f16.npy', mmap_mode='r')
out = {}
labs = np.asarray(lab); ids = [int(v) for v in np.unique(labs) if v > 0]
for k in ids:
    mk = labs == k; ys, xs = np.nonzero(mk); y0, y1, x0, x1 = max(ys.min() - 320, 0), ys.max() + 320, max(xs.min() - 320, 0), xs.max() + 320
    sub = mk[y0:y1, x0:x1]; dist = ndi.distance_transform_edt(~sub); ring = (dist > 60) & (dist <= 300)
    a = np.asarray(DA[y0:y1, x0:x1], np.float32); b = np.asarray(DB[y0:y1, x0:x1], np.float32); c = np.asarray(D[y0:y1, x0:x1], np.float32); w = np.asarray(Wc[y0:y1, x0:x1], np.float32)
    val = (a != 0) & (b != 0); fin = float((val & sub).sum() / sub.sum())
    if fin < 0.3: out[k] = dict(dins_camp_comu=round(fin, 3), veredicte='SENSE DADA (fora del camp comú de A i B)'); continue
    f = lambda x: float(x[sub & val].mean() - x[ring & val].mean()) * 100
    dA, dB, dC = f(a), f(b), f(c)
    if dA * dB > 0 and abs(dA - dB) < 0.5 * max(abs(dA), abs(dB)): v = 'REAL: A i B el veuen igual'
    elif dA * dB <= 0 or max(abs(dA), abs(dB)) >= 2 * min(abs(dA), abs(dB)): v = "D'UN SOL APUNTAMENT o molt desigual"
    else: v = 'REAL però amb amplada desigual'
    out[k] = dict(dins_camp_comu=round(fin, 3), detall_A_pct=round(dA, 3), detall_B_pct=round(dB, 3), detall_coherent_pct=round(dC, 3), w_marca=round(float(w[sub & val].mean()), 3), w_anell=round(float(w[ring & val].mean()), 3), veredicte=v)
    print(k, out[k], flush=True)
(R / '4-RESULTATS/v117_20260929/AB/A5_MARQUES_AB.json').write_text(json.dumps(dict(nota=__doc__.split('\n')[0], marques=out), ensure_ascii=False, indent=1))
