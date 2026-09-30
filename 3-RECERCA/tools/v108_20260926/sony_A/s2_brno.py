"""s2 · Brno com a JUTGE (cap píxel seu al producte): les composicions de Brno alineades al llenç (capes 230–232 de l'estat E) tenen T1 o T2
a la mateixa geometria fixa? Brno és un altre instrument en un altre lloc: si hi ha la línia, és corona (o cel comú); si no, no ho prova
(Brno està processat i pot no resoldre-la), però si la té és un indici fort de realitat. Mateixa mesura que s1 (residu relatiu σ 40, nul
de paral·leles i girades). També el cas «sense normalitzar» (diferència de logaritmes), perquè el ràster de Brno és ja no lineal.
Sortida: S2_BRNO.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); from jutge_comu import Estat
ES = Estat(ARREL / '4-RESULTATS/v103_banda_20260926/E/estat_v103'); res = {}
for lid in (230, 231, 232):
    for k, tr in TRACOS.items():
        box = caixa_tr(tr, 700); rgb = ES.rgb(lid, box); al = ES.dada(lid, box) if hasattr(ES, 'dada') else None
        Y = (0.25 * rgb[..., 0] + 0.5 * rgb[..., 1] + 0.25 * rgb[..., 2]).astype(np.float32)
        if al is not None: Y = np.where(np.asarray(al, np.float32) > 0.5, Y, 0)
        Y = np.where(Y > 0.002, Y, 0)
        cob = float((Y > 0).mean())
        if cob < 0.2: res[f'L{lid}_T{k}'] = dict(cobertura=cob); print(f'L{lid} T{k}: sense cobertura ({cob:.2f})', flush=True); continue
        r = rel_map(Y); m, t, pr = mesura_amb_nul(r, box[:2], tr['centre'], tr['d'], tr['llarg'])
        m['cobertura_caixa'] = cob; res[f'L{lid}_T{k}'] = m
        print(f"Brno L{lid} T{k}: D {m['D']*1e4:+.1f}‱ · nul {m.get('nul_med', np.nan)*1e4:+.1f}±{m.get('nul_mad', np.nan)*1e4:.1f}‱ · z {m.get('z', np.nan):+.1f} · p {m.get('p', np.nan):.3f} · cob {m.get('cobertura', np.nan):.2f}", flush=True)
desa(OUT / 'S2_BRNO.json', res)
