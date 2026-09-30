"""12 — Contrast §5.3: el compost V4 contra l'autoritat fotomètrica `hdr_vixen_countss.npy`
(22 estrelles, B/B☉ = 2,772×10⁻¹¹ ×ADU/s). El compost (Display P3 codificat) es decodifica a
lineal i es TRANSPORTA ENRERE a l'espai de càmera (la transformació FM2→Bradford→P3 és lineal i
invertible, i commuta amb la barreja de capes perquè totes hi han passat): G de càmera sense guany
WB × (13995−512) × 15 = ADU/s de fotometria directa, comparable amb el màster (que és ADU/s de
càmera). Sense aquesta inversió, el canal G de P3 arrossega ~25 % de R amb guany WB 1,94 i la raó
surt inflada i amb pendent radial (mesurat: 1,31→1,13). Alineació per correlació de fase.
Porta: mediana de la raó per anell a 1,3–5 R☉ dins del ±10 % (0,90–1,10)."""
import json, sys
from pathlib import Path
import numpy as np
from v4_lib import *

MASTER = Path.home() / 'Desktop/Eclipse 2026/Derivats/Vixen/Corona_HDR_Vixen/hdr_vixen_countss.npy'
B_PER_ADUS = 2.772e-11
W07 = 13995 - 512
T_REF = 1 / 15
sys.path.insert(0, str(HERE.parent / 'revelat_normalitzat'))
import render_lineal as RL

def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def main(state_npy):
    st = np.load(state_npy, mmap_mode='r')          # (CH, CW, 3) u16 codificat
    P3 = np.asarray(st[463:463 + FH, 457:457 + FW, :3], np.float32) / 65535.0
    lin = srgb_to_linear(P3)                         # Display P3 lineal
    FM2 = RL.forward_matrix_2(RL.dng_font('07'))
    M_INV = np.linalg.inv(RL.M_XYZ_TO_P3 @ RL.M_BRAD @ FM2)
    wb = np.array([1.9433588981628418, 1.0, 1.6591808795928955])   # As Shot, idèntic als 12
    cam = lin @ M_INV.T                              # espai de càmera amb WB
    comptes = cam / wb                               # fracció de blanc a t_ref per pla
    comp_adus = comptes * W07 / T_REF                # ADU/s per pla (G = índex 1)
    m = np.load(MASTER, mmap_mode='r')
    mg = np.asarray(m[..., 1], np.float32)           # ADU/s
    MH, MW = mg.shape                                # 4638x6958: la geometria comuna menys 1 px de vora
    a = np.log1p(np.clip(np.asarray(comp_adus[:MH, :MW, 1], np.float32), 0, None))
    a = a - a.mean()
    b = np.log1p(np.clip(mg, 0, None))
    b = b - b.mean()
    corr = np.fft.irfft2(np.fft.rfft2(a) * np.conj(np.fft.rfft2(b)), s=a.shape)
    py, px = np.unravel_index(np.argmax(np.abs(corr)), corr.shape)
    dy = py if py < a.shape[0] // 2 else py - a.shape[0]
    dx = px if px < a.shape[1] // 2 else px - a.shape[1]
    print(f'desplaçament màster→V4: dx={dx} dy={dy}')
    mg_al = np.roll(np.roll(mg, dy, axis=0), dx, axis=1)
    comp_c = np.asarray(comp_adus[:MH, :MW, 1], np.float32)
    sx, sy = SUN[0] - 457 - 1, SUN[1] - 463 - 1
    yy, xx = np.mgrid[0:MH, 0:MW].astype(np.float32)
    rs = np.hypot(xx - sx, yy - sy) / R_SUN
    rows = []
    for r0, r1 in [(1.3, 1.6), (1.6, 2.0), (2.0, 2.6), (2.6, 3.3), (3.3, 4.2), (4.2, 5.0)]:
        s = (rs >= r0) & (rs < r1) & np.isfinite(mg_al) & (mg_al > 0)
        rao = float(np.median(comp_c[s] / mg_al[s]))
        rows.append(dict(r=[r0, r1], rao_v4_mestre=round(rao, 4),
                         v4_ADUs=round(float(np.median(comp_c[s])), 1),
                         mestre_ADUs=round(float(np.median(mg_al[s])), 1),
                         mestre_B_Bsol=round(float(np.median(mg_al[s])) * B_PER_ADUS, 13)))
        print(f'  {r0}-{r1} R☉: raó V4/mestre = {rao:.4f}  (V4 {np.median(comp_c[s]):.0f} vs mestre {np.median(mg_al[s]):.0f} ADU/s)', flush=True)
    ok = all(0.90 <= r['rao_v4_mestre'] <= 1.10 for r in rows)
    rep = dict(state=str(state_npy), dx=int(dx), dy=int(dy), anells=rows, porta='±10 % a 1,3–5 R☉',
               nota='comparació a l\'espai de càmera (matrius invertides); el cel de la V4 NO està restat, el del màster sí',
               veredicte='DINS' if ok else 'FORA')
    out = V4W / 'QA/contrast_5.3_master.json'
    jdump(rep, out)
    print('VEREDICTE §5.3:', rep['veredicte'], '->', out)
    return rep

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else V4W / 'states/S17.npy')
