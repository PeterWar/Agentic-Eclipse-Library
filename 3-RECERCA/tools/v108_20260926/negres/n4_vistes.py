"""n4 (V108 · negres) · Vistes del LLENÇ SENCER (mai retalls): V107 | candidata | diferència, i mapes de zones negres V107 | candidata.
Els composts són els emulats (pila ràster de la V107 sense capes d'ajust); perquè s'assemblin al que veu Pere, s'hi aplica a tots dos la MATEIXA
corba global per canal ajustada del compost emulat de la V107 al compost fusionat del PSB (que porta les capes d'ajust). És una aproximació
declarada: la «Claredat» és local i una corba global no la reprodueix; la comparació V107 | candidata és justa perquè la corba és la mateixa.
Ús: n4_vistes.py <candidata> [<candidata> …]   → 4-RESULTATS/v108_20260926/negres/vistes/"""
import sys, struct, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_negres import *
from n1_mesura_v107 import zones, r as r2, th as th2, ok as ok2, okm as okm2
CAND = OUT / 'candidats'


def esp_de(spec):
    """Com n3_avalua.esp_de: 'V107' o 'CARPETA[+lid=RUTA]'."""
    parts = spec.split('+'); esp = {}
    if parts[0] != 'V107':
        c = Path(parts[0]); c = c if c.is_absolute() else CAND / c
        esp[41] = {'F': str(c / 'P01_NRGF_u16.npy')}; esp[42] = {'F': str(c / 'P01_NRGF_extrap_u16.npy')}
    for p_ in parts[1:]:
        lid, ruta = p_.split('='); esp[int(lid)] = {'F': ruta}
    return esp
V = OUT / 'vistes'; V.mkdir(exist_ok=True); d2 = OUT / 'pas2'; PAS = 2; RED = 2   # pas 2 i reducció ×2 → 1/4 del llenç (2638×1877)
P2 = Pila((0, 0, W, H), PAS)


def fusionat():
    psb = R0 / '1-PHOTOSHOP/V107.psb'
    with open(psb, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
        pos = f.tell(); assert struct.unpack('>H', f.read(2))[0] == 0
    mm = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
    return np.stack([np.asarray(mm[c, ::PAS, ::PAS], np.float32) / 65535 for c in range(3)], -1)


def corba(emu, fus, ok):
    """Corba monòtona per canal emulat → fusionat (medianes per quantils), com a taula."""
    T = []
    for c in range(3):
        x = emu[..., c][ok]; y = fus[..., c][ok]; q = np.quantile(x, np.linspace(0, 1, 513)); q = np.unique(q)
        idx = np.clip(np.searchsorted(q, x) - 1, 0, len(q) - 2); med = np.array([np.median(y[idx == i]) if (idx == i).sum() > 20 else np.nan for i in range(len(q) - 1)])
        xc = 0.5 * (q[:-1] + q[1:]); g = np.isfinite(med); xc, med = xc[g], np.maximum.accumulate(med[g]); T.append((xc, med))
    return T


def aplica(C, T): return np.stack([np.interp(C[..., c], T[c][0], T[c][1]) for c in range(3)], -1)


def a8(C): return (np.clip(C, 0, 1) ** 1.0 * 255 + 0.5).astype(np.uint8)


def reduir(a): return cv2.resize(a, (a.shape[1] // RED, a.shape[0] // RED), interpolation=cv2.INTER_AREA)


def etiqueta(img, text):
    out = img.copy(); cv2.rectangle(out, (0, 0), (out.shape[1], 54), (0, 0, 0), -1)
    cv2.putText(out, text, (18, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.15, (255, 255, 255), 2, cv2.LINE_AA); return out


def mapa_negres(L, base_gris):
    z, sky, skys, Ls = zones(L); neg = okm2 & (r2 >= 1.3) & (r2 < 4.5) & (Ls < skys)
    g = np.repeat(base_gris[..., None], 3, 2).astype(np.float32) * 0.8; g[neg] = [235, 40, 40]
    for rs in (1.3, 2.0, 3.0, 4.5):
        cv2.circle(g, (int(SOL[0] / PAS), int(SOL[1] / PAS)), int(rs * RSOL / PAS), (80, 200, 255), 2)
    return g.astype(np.uint8), z['1.3-4.5']['local_suau']


if __name__ == '__main__':
    L7, C7 = P2.compon({}, rgb=True); C7 = C7.astype(np.float32); F = fusionat(); okc = ok2 & (r2 > 1.05)
    T = corba(C7, F, okc); np.save(V / 'corba_emulat_a_fusionat.npy', np.array([np.interp(np.linspace(0, 1, 1025), *T[c]) for c in range(3)]))
    ajust = float(np.median(np.abs(aplica(C7, T) - F)[okc])); print('corba: mediana |emulat corbat − fusionat|', round(ajust, 4), flush=True)
    V7 = a8(aplica(C7, T)); gris7 = cv2.cvtColor(V7, cv2.COLOR_RGB2GRAY)
    m7, f7 = mapa_negres(L7, gris7)
    rep = dict(corba_mediana_abs=ajust)
    for spec in sys.argv[1:]:
        nom = spec.split('=')[0] if '=' in spec.split('+')[0] else spec; sp = spec.split('=', 1)[1] if '=' in spec.split('+')[0] else spec
        Lc, Cc = P2.compon(esp_de(sp), rgb=True); Cc = Cc.astype(np.float32); Vc = a8(aplica(Cc, T))
        dl = np.log(np.maximum(Lc, 1e-3)) - np.log(np.maximum(L7, 1e-3)); lim = 0.15
        t = np.clip(dl / lim, -1, 1); dif = np.zeros(dl.shape + (3,), np.float32)
        dif[..., 0] = np.where(t > 0, 255, 255 * (1 + t)); dif[..., 2] = np.where(t < 0, 255, 255 * (1 - t)); dif[..., 1] = 255 * (1 - np.abs(t))
        dif[~(E.alfa_efectiva(3, (0, 0, W, H), PAS) > 0.5)] = 40
        mc, fc = mapa_negres(Lc, cv2.cvtColor(Vc, cv2.COLOR_RGB2GRAY))
        fila1 = np.concatenate([etiqueta(reduir(V7), 'V107 (emulada, corba global)'), etiqueta(reduir(Vc), f'{nom} (emulada, mateixa corba)'),
                                etiqueta(reduir(dif.astype(np.uint8)), f'ln({nom}/V107): vermell = mes clar, blau = mes fosc, +-{lim}')], 1)
        fila2 = np.concatenate([etiqueta(reduir(m7), f'V107: zones negres (suau) {100 * f7:.1f} %'), etiqueta(reduir(mc), f'{nom}: zones negres (suau) {100 * fc:.1f} %'),
                                etiqueta(reduir(Vc), f'{nom} (sense marques)')], 1)
        img = np.concatenate([fila1, fila2], 0)
        cv2.imwrite(str(V / f'V107_{nom}_diferencia_i_negres.jpg'), cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        cv2.imwrite(str(V / f'{nom}_llenc_sencer.png'), cv2.cvtColor(reduir(Vc), cv2.COLOR_RGB2BGR))
        rep[nom] = dict(negres_suau_V107=f7, negres_suau=fc, dl_p1=float(np.percentile(dl[okm2], 1)), dl_p99=float(np.percentile(dl[okm2], 99)))
        print(nom, rep[nom], flush=True); del Lc, Cc, Vc, dl, dif, mc
    cv2.imwrite(str(V / 'V107_llenc_sencer_emulada.png'), cv2.cvtColor(reduir(V7), cv2.COLOR_RGB2BGR))
    desa(V / 'N4_VISTES.json', rep)
