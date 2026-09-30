"""⛔ HISTORIC des del 27-08-2026: el mode MEMORIA esta DEPRECAT i el projecte
segueix amb CIENCIA. Aquest script no alimenta cap run; es conserva perque
el numero que va mesurar SI que es una mesura, i viu a
`comu.MODES_DEPRECATS`.

El guany que fa que el Vixen es renderitzi com el DSC06991 de Pere.

Sortida: un vector (g_R, 1, g_B) que s'aplica DESPRES de la matriu de color.
Es mesura sobre la banda 2,0-5,5 R_sol, que es on els dos fotogrames tenen
anell sencer, res saturat i prou senyal.
"""
import json, subprocess, sys
import numpy as np

# taules del dos_cossos2.py (matriu amb convencio dcraw, pedestal mesurat)
SONY = {2.18:(1.817,0.431), 2.49:(1.654,0.503), 2.84:(1.514,0.565), 3.24:(1.398,0.615),
        3.70:(1.305,0.655), 4.23:(1.230,0.687), 4.82:(1.171,0.711), 5.51:(1.124,0.731)}
CANON = {1.89:(1.702,0.300), 2.10:(1.591,0.372), 2.34:(1.478,0.444), 2.60:(1.376,0.506),
         2.89:(1.289,0.557), 3.22:(1.216,0.599), 3.58:(1.157,0.632), 3.98:(1.105,0.659),
         4.43:(1.066,0.681), 4.92:(1.032,0.697)}
cr = np.array(sorted(CANON)); crg = np.array([CANON[k][0] for k in cr]); cbg = np.array([CANON[k][1] for k in cr])
sr = np.array(sorted(SONY))
ok = (sr >= cr.min()) & (sr <= cr.max())
gr = np.array([SONY[k][0] for k in sr])[ok] / np.interp(sr[ok], cr, crg)
gb = np.array([SONY[k][1] for k in sr])[ok] / np.interp(sr[ok], cr, cbg)
print(f"radis usats: {sr[ok].round(2).tolist()}")
print(f"  g_R  per radi: {gr.round(4).tolist()}")
print(f"  g_B  per radi: {gb.round(4).tolist()}")
G = (float(np.median(gr)), 1.0, float(np.median(gb)))
print(f"\nGUANY_MEMORIA = ({G[0]:.4f}, 1.0000, {G[2]:.4f})")
print(f"  dispersio: g_R {gr.std()/gr.mean()*100:.1f} %   g_B {gb.std()/gb.mean()*100:.1f} %")
print(f"\nCorona del compost Vixen (R/G 1.928 B/G 0.194) amb aquest guany:")
print(f"  -> R/G {1.928*G[0]:.3f}   B/G {0.194*G[2]:.3f}")
json.dump({"guany": G, "banda_Rsol": [float(sr[ok].min()), float(sr[ok].max())],
           "dispersio_pct": [float(gr.std()/gr.mean()*100), float(gb.std()/gb.mean()*100)],
           "font": "DSC06991.ARW contra 572A2996.CR3, cadena de color sencera"},
          open("guany_memoria.json","w"), indent=1)
