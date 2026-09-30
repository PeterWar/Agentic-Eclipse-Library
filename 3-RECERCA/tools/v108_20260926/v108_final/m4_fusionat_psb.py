"""m4 (V108 · final) · Zones negres, cel i flamarada sobre el COMPOST FUSIONAT que desa el Photoshop (el que Pere veu, amb les capes d'ajust 239–244),
V107 contra V108. Mateixes definicions que negres/n1 (local_suau: L i cel suavitzats σ 3 px a pas 2; cel A = sector de 10° a 6,5–8,5 R☉; cel B = 5–5,6 R☉;
vara fixa = el cel de la V107). Flamarada = p90 − p10 de ln L per anell de 0,1 R☉ dins del marc. Només lectura.
Ús: m4_fusionat_psb.py → 4-RESULTATS/v108_20260926/v108_final/M4_FUSIONAT_PSB.json"""
import sys, json, struct
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R0 / '3-RECERCA/tools/v108_20260926/negres'))
from comu_negres import mascares, cel_local, W, H
PAS = 2; G = mascares((0, 0, W, H), PAS); r, th, ok, marc = G['r'], G['th'], G['ok'], G['marc']; okm = ok & marc
def fusionat(p):
    with open(p, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]; h, w = struct.unpack('>II', hdr[14:22])
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
        pos = f.tell(); assert struct.unpack('>H', f.read(2))[0] == 0
    mm = np.memmap(p, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, h, w))
    C = np.stack([np.asarray(mm[c, ::PAS, ::PAS], np.float32) / 65535 for c in range(3)], -1)
    return (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4
def cel_ref(L, a, b):
    Ls = cv2.GaussianBlur(L, (0, 0), 3.0); out = np.full(L.shape, np.nan, np.float32); secs = []
    for k in range(36):
        s = ok & (th >= k * 10) & (th < k * 10 + 10); m = s & (r >= a) & (r < b)
        v = float(np.median(Ls[m])) if m.sum() > 50 else np.nan; secs.append(v); out[s] = v
    return Ls, out, secs
L7 = fusionat(R0 / '1-PHOTOSHOP/V107.psb'); L8 = fusionat(R0 / '1-PHOTOSHOP/V108.psb')
rep = {}
for nom, (a, b) in {'A_6.5-8.5': (6.5, 8.5), 'B_5-5.6': (5.0, 5.6)}.items():
    Ls7, S7, s7 = cel_ref(L7, a, b); Ls8, S8, s8 = cel_ref(L8, a, b); d = {}
    for bn, (lo, hi) in {'1.3-4.5': (1.3, 4.5), '2-3': (2, 3), '3-4.5': (3, 4.5)}.items():
        m = okm & (r >= lo) & (r < hi) & np.isfinite(S7) & np.isfinite(S8)
        d[bn] = dict(V107=round(float((Ls7[m] < S7[m]).mean() * 100), 2), V108=round(float((Ls8[m] < S8[m]).mean() * 100), 2), V108_vara_V107=round(float((Ls8[m] < S7[m]).mean() * 100), 2))
    sect = {}
    for q in range(8):
        m = okm & (r >= 1.3) & (r < 4.5) & (th >= q * 45) & (th < q * 45 + 45) & np.isfinite(S7) & np.isfinite(S8)
        if m.sum() > 100: sect[f'{q*45}-{q*45+45}'] = [round(float((Ls7[m] < S7[m]).mean() * 100), 1), round(float((Ls8[m] < S8[m]).mean() * 100), 1)]
    d['sectors_45_V107_V108'] = sect
    dalt = [i for i in range(36) if 45 <= i * 10 < 135]; baix = [i for i in range(36) if 225 <= i * 10 < 315]
    d['cel_dalt_V108_sobre_V107'] = round(float(np.nanmedian([s8[i] / s7[i] for i in dalt])), 3); d['cel_baix_V108_sobre_V107'] = round(float(np.nanmedian([s8[i] / s7[i] for i in baix])), 3)
    rep['zones_negres_' + nom] = d
fl = {}
for rr in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.5):
    m = okm & (np.abs(r - rr) < 0.05)
    q = lambda L: float(np.diff(np.percentile(np.log(np.maximum(L[m], 1e-4)), [10, 90]))[0])
    fl[str(rr)] = round(q(L8) / q(L7), 3)
rep['flamarada_V108_sobre_V107'] = fl
O = R0 / '4-RESULTATS/v108_20260926/v108_final/M4_FUSIONAT_PSB.json'; O.write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False, indent=1))
