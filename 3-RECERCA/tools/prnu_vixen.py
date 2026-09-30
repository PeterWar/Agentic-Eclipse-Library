#!/usr/bin/env python3
"""Mapa de PRNU del sensor de la R6 III, mesurat a les pròpies dades.

El **walking noise** que es veu al fons del compost —traços diagonals curts— no
són píxels calents: és el patró de guany píxel a píxel del sensor (PRNU) que el
master de fosc no toca, escombrat en línies perquè la muntura deriva
0,269 px/s **en línia recta i monòtona**, sense cap ditherat aleatori.

Proves que és PRNU i no altra cosa:

* l'angle dels traços és **46,7° ± 1,5°** i la deriva mesurada va a 46,5-47,6°;
* la llargada mediana és **7,22 px** i el desplaçament entre el primer i
  l'últim fotograma de 10,3 s és **7,10 px** (error 1,7 %);
* la correlació amb el mapa de píxels calents del master és **+0,008** i la
  curtosi del patró és **3,14**: és gaussià, o sigui de TOTS els píxels;
* el patró **escala amb el senyal** — és multiplicatiu, no additiu;
* i el que ho tanca: un mapa fet amb la **fotosfera filtrada** de les parcials
  correlaciona **r = 0,21** amb un mapa fet amb la **corona** (n = 139.000 px),
  que són escenes, instants i exposicions totalment diferents. El PRNU real que
  se'n deriva és **~1,2 %**.

⚠️ `research/75` §4 estimava «PRNU ≲ 0,2 %». La mesura directa diu sis vegades
més. Aquell número venia de fitxes i no d'una mesura sobre aquest sensor.

⛔ **Encongiment de Wiener, i no és opcional.** El mapa mesurat és
`veritat + soroll`. Dividir-hi directament deixa el soroll del mapa com a patró
fix nou, que torna a caminar igual. Es mesura quina fracció del mapa és real
—correlació entre dues meitats disjuntes— i s'encongeix per aquella fracció:
és l'estimador òptim i garanteix que mai no s'injecta més del que es treu.

⛔ **v2 (17-08, research/78 §8): el mapa v1 portava LES ESTRELLES.** Era una
mitjana ponderada pel senyal sobre 24 fotogrames, sense cap rebuig: cada
estrella dels fotogrames llargs deixava, al llarg de la seva traça de deriva
pel sensor, una filera de bonys positius de +0,04 a +0,135 (3–10 σ del mapa),
i en dividir-hi cada fotograma sortien **clots foscos en diagonal al costat de
cada estrella** i l'estrella mateixa perdia fins a un 10 % del pic. Ara:

1. **les estrelles i qualsevol transitori compacte s'emmascaren a cada
   fotograma abans de res** —píxels més de 6 σ per damunt de la mediana 7×7,
   dilatats 3 px de pla— i la mitjana local es calcula sense ells (convolució
   normalitzada), perquè un veí d'estrella tampoc no surti negatiu;
2. la mitjana ponderada es fa dues vegades, i a la segona es rebutja tota
   mostra que s'aparti més de 3,5 σ (fotons + lectura) del mapa de la primera:
   raigs còsmics i restes.

⚠️ La primera versió d'aquest rebuig (sense la màscara d'estrelles, cinc
passades amb dilatació) **convergia al mode equivocat** allà on la primera
passada ja era esbiaixada: rebutjava els fotogrames profunds i es quedava amb
el soroll dels curts, i en algun píxel deixava un bony de +0,12. La màscara
independent del mapa és el que ho arregla. El v1 es conserva com a
`prnu_v1_amb_estrelles.npz`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import uniform_filter, binary_dilation, median_filter

# ⛔ El mapa es mesura sobre els fotogrames SENSE cap correcció de PRNU: si
# calibra() apliqués el mapa que ja existeix, el nou es mesuraria sobre dades
# ja corregides i sortiria buit.
os.environ["SENSE_PRNU"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hdr_corona_vixen as H  # noqa: E402

DESTI = H.SRC / "Masters_v2" / "prnu.npz"
FINESTRA = 9          # px de pla; petita perquè no s'empassi el vinyetatge
SENYAL_MIN = 40.0     # ADU: per sota, el soroll de fotons domina del tot
RETALL = 0.15
K_REBUIG = 3.5        # σ (fotons + lectura) per damunt del mapa de la 1a passada
K_ESTRELLA = 6.0      # σ per damunt de la mediana 7×7: estrella o transitori
DILATA_ESTRELLA = 3   # px de pla al voltant de cada píxel d'estrella


def mapa(fotogrames, ref: dict | None = None) -> tuple[dict, dict, dict]:
    """Mapa multiplicatiu per pla, amb les estrelles emmascarades a cada
    fotograma i, si es passa `ref` (mapa d'una primera passada), rebuig de les
    mostres discordants."""
    acc: dict = {}
    pes: dict = {}
    n_reb: dict = {}
    for f in fotogrames:
        mos, _ = H.calibra(f)
        rn = H.RN_CURT if f.exp_s < H.LLINDAR_MODE_S else H.RN_LLARG
        for k in ((0, 0), (0, 1), (1, 0), (1, 1)):
            pla = mos[k[0]::2, k[1]::2].astype(np.float32)
            # estrelles i transitoris: molt per damunt de la mediana local
            med = median_filter(pla, size=7)
            sig_px = np.sqrt(np.maximum(med, 1.0) / H.GUANY["G"] + rn * rn)
            estrella = (pla - med) > K_ESTRELLA * sig_px
            estrella = binary_dilation(estrella, iterations=DILATA_ESTRELLA)
            ok = (~estrella) & (pla < H.SOSTRE)
            okf = ok.astype(np.float32)
            # mitjana local SENSE els píxels emmascarats (convolució normalitzada)
            cob = uniform_filter(okf, FINESTRA)
            loc = uniform_filter(pla * okf, FINESTRA) / np.maximum(cob, 1e-3)
            bo = ok & (loc > SENYAL_MIN) & (cob > 0.5)
            rel = np.where(bo, (pla - loc) / np.maximum(loc, 1e-3), 0.0)
            if ref is not None:
                sig = np.sqrt(np.maximum(loc, 1.0) / H.GUANY["G"] + rn * rn) / np.maximum(loc, 1e-3)
                fora = bo & (np.abs(rel - ref[k]) > K_REBUIG * sig)
                n_reb[k] = n_reb.get(k, 0) + int(fora.sum())
                bo = bo & ~fora
                rel = np.where(bo, rel, 0.0)
            # pes = electrons: és el que fixa el senyal/soroll de cada mostra
            w = np.where(bo, np.maximum(loc, 0.0) * H.GUANY["G"], 0.0)
            acc[k] = acc.get(k, 0.0) + rel * w
            pes[k] = pes.get(k, 0.0) + w
    return ({k: np.clip(acc[k] / np.maximum(pes[k], 1e-9), -RETALL, RETALL)
             for k in acc}, pes, n_reb)


def mapa_robust(fotogrames) -> tuple[dict, dict, dict]:
    m1, _, _ = mapa(fotogrames)
    return mapa(fotogrames, ref=m1)


def main() -> int:
    fg = [f for f in H.llegeix_manifest() if f.usat]
    # només els que tenen senyal de sobres: els curts no aporten res al mapa
    bons = [f for f in fg if f.exp_s >= 0.03]
    print(f"{len(bons)} fotogrames amb senyal suficient "
          f"({min(f.exp_s for f in bons):.4g} a {max(f.exp_s for f in bons):.4g} s)")

    A, _, _ = mapa_robust(bons[0::2])
    B, _, _ = mapa_robust(bons[1::2])
    fraccio = {}
    print("\nquina part del mapa és PRNU de veritat (meitats disjuntes):")
    for k in A:
        a, b = A[k].ravel(), B[k].ravel()
        m = (np.abs(a) > 1e-9) & (np.abs(b) > 1e-9)
        r = float(np.corrcoef(a[m], b[m])[0, 1])
        # variància comuna contra la del mapa sencer (mitjana de les meitats)
        sg_real = np.sqrt(max(r, 0.0) * a[m].std() * b[m].std())
        fraccio[k] = r
        print(f"  pla {k}: sigma_A={a[m].std():.4f} sigma_B={b[m].std():.4f} "
              f"r={r:.4f}  → PRNU real ≈ {100*sg_real:.2f} %")

    M, pes, n_reb = mapa_robust(bons)
    sortida = {}
    print("\nmapa final i encongiment de Wiener:")
    for k in M:
        m = M[k]
        cob = pes[k] > 0
        # amb el doble de fotogrames el soroll del mapa cau a la meitat en
        # variància: la fracció real puja en conseqüència
        r2 = fraccio[k]
        w_shrink = min(1.0, 2 * r2 / (1 + r2)) if r2 > 0 else 0.0
        sortida[f"{k[0]}{k[1]}"] = np.where(cob, m * w_shrink, 0.0).astype(np.float32)
        print(f"  pla {k}: sigma del mapa {m[cob].std():.4f}, "
              f"encongiment ×{w_shrink:.3f} → s'aplica {m[cob].std()*w_shrink:.4f} "
              f"({100*cob.mean():.1f} % de cobertura); mostres rebutjades a la "
              f"2a passada: {n_reb[k]} ({100*n_reb[k]/(len(bons)*m.size):.3f} %)")

    np.savez_compressed(DESTI, **sortida)
    DESTI.with_suffix(".json").write_text(json.dumps({
        "versio": 2,
        "n_fotogrames": len(bons),
        "finestra_px": FINESTRA,
        "senyal_min_ADU": SENYAL_MIN,
        "rebuig_sigma": K_REBUIG,
        "estrella_sigma": K_ESTRELLA,
        "dilatacio_estrella_px_pla": DILATA_ESTRELLA,
        "mostres_rebutjades": {str(k): v for k, v in n_reb.items()},
        "correlacio_meitats": {str(k): v for k, v in fraccio.items()},
        "nota": "mapa multiplicatiu: el fotograma s'ha de DIVIDIR per (1 + mapa); "
                "v2 amb rebuig robust (les estrelles ja no hi són)",
    }, indent=1, ensure_ascii=False))
    print(f"\n→ {DESTI}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
