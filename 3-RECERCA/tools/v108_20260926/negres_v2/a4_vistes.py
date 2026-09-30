"""a4 (V108 · negres_v2) · Vistes del LLENÇ SENCER (mai retalls), a 1/4 (2638 × 1877), dels composts emulats (pila de la V107 sense capes d'ajust)
amb la MATEIXA corba global per canal que la ronda 1 va ajustar del compost emulat de la V107 al fusionat del PSB (negres/vistes/corba_emulat_a_fusionat.npy):
la Claredat (local) no s'hi reprodueix; la comparació és justa perquè la corba és la mateixa per a tots.
Per a cada candidata, una làmina 2 × 3:
  dalt : V107 | candidata | ln(candidata/V107) (vermell = més clar, blau = més fosc, ±0,15);
  baix : zones negres de la V107 | de la candidata (vermell = negra amb les dues referències de cel, taronja = només amb A (6,5–8,5 R☉),
         groc = només amb B (5–5,6 R☉ dins del marc); cercles a 1,3 / 2 / 3 / 4,5 R☉; marc final en blanc) | ln(candidata/V107) amb ±0,03.
I una làmina de conjunt (V107 i les candidates, netes, 2 × 2 o 2 × 3).
Ús: a4_vistes.py <nom>=<carpeta> …   → 4-RESULTATS/v108_20260926/negres_v2/vistes/"""
import sys, json
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.argv, ARGS = sys.argv[:1], sys.argv[1:]
import a1_avalua as A                                                                                  # (només lectura; geometria, pila i zones)
OUT = A.OUT / 'vistes'; OUT.mkdir(exist_ok=True)
T = np.load(R0 / '4-RESULTATS/v108_20260926/negres/vistes/corba_emulat_a_fusionat.npy'); XT = np.linspace(0, 1, T.shape[1])
def corba(C): return np.stack([np.interp(C[..., c], XT, T[c]) for c in range(3)], -1)
def a8(C): return (np.clip(C, 0, 1) * 255 + 0.5).astype(np.uint8)
def red(a): return cv2.resize(a, (a.shape[1] // 2, a.shape[0] // 2), interpolation=cv2.INTER_AREA)
def etiqueta(img, text):
    out = img.copy(); cv2.rectangle(out, (0, 0), (out.shape[1], 50), (0, 0, 0), -1)
    cv2.putText(out, text, (14, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA); return out
def dif(dl, lim):
    t = np.clip(dl / lim, -1, 1); d = np.zeros(dl.shape + (3,), np.float32)
    d[..., 0] = np.where(t > 0, 255, 255 * (1 + t)); d[..., 2] = np.where(t < 0, 255, 255 * (1 - t)); d[..., 1] = 255 * (1 - np.abs(t))
    d[~A.ok2] = 40; return d.astype(np.uint8)
def mapa(L, gris):
    Ls = cv2.GaussianBlur(L, (0, 0), 3.0); _, skyA = A.cel_local(Ls, A.r2, A.th2, A.ok2); _, skyB = A.cel_sector_B(Ls, A.marc2 & ~A.lluna2)
    zA = A.okm2 & (A.r2 >= 1.3) & (A.r2 < 4.5); zB = A.ZONA_B & (L > 1e-4); nA = zA & (Ls < skyA); nB = zB & (Ls < skyB)
    g = np.repeat(gris[..., None], 3, 2).astype(np.float32) * 0.8
    g[nA & nB] = [235, 30, 30]; g[nA & ~nB] = [255, 150, 0]; g[nB & ~nA] = [250, 230, 0]
    for rs in (1.3, 2.0, 3.0, 4.5): cv2.circle(g, (int(A.SOL[0] / 2), int(A.SOL[1] / 2)), int(rs * A.RSOL / 2), (80, 200, 255), 2)
    x0, y0, x1, y1 = [v // 2 for v in A.MARC]; cv2.rectangle(g, (x0, y0), (x1, y1), (255, 255, 255), 2)
    return g.astype(np.uint8), 100 * float(nA[zA].mean()), 100 * float(nB[zB].mean())
if __name__ == '__main__':
    P2 = A.Pila((0, 0, A.W, A.H), 2)
    L7, C7 = P2.compon({}, rgb=True); V7 = a8(corba(C7.astype(np.float32))); m7, a7, b7 = mapa(L7, cv2.cvtColor(V7, cv2.COLOR_RGB2GRAY))
    netes = [etiqueta(red(V7), 'V107 (emulada, corba global)')]; rep = {}
    for arg in ARGS:
        nom, sp = arg.split('=', 1); c = Path(sp); c = c if c.is_absolute() else A.CAND / c
        _, f41 = A.combinat(c, 41); _, f42 = A.combinat(c, 42)
        Lc, Cc = P2.compon({41: {'F': 'm', '_F': f41[::2, ::2]}, 42: {'F': 'm', '_F': f42[::2, ::2]}}, rgb=True); del f41, f42
        Vc = a8(corba(Cc.astype(np.float32))); dl = np.log(np.maximum(Lc, 1e-3)) - np.log(np.maximum(L7, 1e-3))
        mc, ac, bc = mapa(Lc, cv2.cvtColor(Vc, cv2.COLOR_RGB2GRAY)); rep[nom] = dict(negres_A=ac, negres_B=bc)
        f1 = np.concatenate([etiqueta(red(V7), 'V107 (emulada, corba global)'), etiqueta(red(Vc), f'{nom} (mateixa corba)'), etiqueta(red(dif(dl, 0.15)), f'ln({nom}/V107)  vermell = mes clar, blau = mes fosc, +-0,15')], 1)
        f2 = np.concatenate([etiqueta(red(m7), f'V107 zones negres: A {a7:.1f} %  B {b7:.1f} %'), etiqueta(red(mc), f'{nom}: A {ac:.1f} %  B {bc:.1f} %'), etiqueta(red(dif(dl, 0.03)), 'el mateix, +-0,03')], 1)
        cv2.imwrite(str(OUT / f'V107_{nom}_lamina.jpg'), cv2.cvtColor(np.concatenate([f1, f2], 0), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
        cv2.imwrite(str(OUT / f'{nom}_llenc_sencer.png'), cv2.cvtColor(Vc, cv2.COLOR_RGB2BGR))
        netes.append(etiqueta(red(Vc), nom)); print(nom, rep[nom], flush=True)
    cv2.imwrite(str(OUT / 'V107_llenc_sencer_emulada.png'), cv2.cvtColor(V7, cv2.COLOR_RGB2BGR))
    while len(netes) % 2: netes.append(np.zeros_like(netes[0]))
    files = [np.concatenate(netes[i:i + 2], 1) for i in range(0, len(netes), 2)]
    cv2.imwrite(str(OUT / 'CONJUNT_netes.jpg'), cv2.cvtColor(np.concatenate(files, 0), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    (OUT / 'A4_VISTES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET')
