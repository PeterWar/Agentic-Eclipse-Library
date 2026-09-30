"""Constants i geometria comunes dels filtres Druckmüller (18-08-2026, vespre).

LLENÇ: el de Pere del 18-08 al vespre, 7648×5353 (l'«ESTESA»: la reixa crua de la R6 6960×4640
a (457,463); `CapesExteriors.psb`, `CapesInteriors.psb` i `2-Filtres/Aplicant_Filtres.tif`).
El Sol s'ha mesurat directament sobre `Aplicant_Filtres.tif` per correlació de fase de la corona
amb el compost HDR (tres bandes, dos anells): (4021,3–4021,5, 2737,9) — 0,5 px a la dreta del que
donava la convenció TIFF (4020,89, 2737,66). Es pren (4021,35, 2737,90).

Compost Vixen (Corona_HDR_Vixen/hdr_vixen_countss.npy): 6958×4638, Sol a (3479, 2319), 2,1495 ″/px,
R☉ = 446,15 px, RETALL = files 85..4595, columnes 40..6830. HDR → llenç: +542,35 columnes, +418,90 files.

Sony (apilat ≥ 1 s a la reixa de DSC06993, 5320×7968): Sol de la placa a (3894,7, 2768,7); similitud al
llenç: escala 3,2020/2,1495 = 1,4896 (7 estrelles: 1,48860), gir 33,088°; translació REFINADA per
correlació de la corona (vegeu prepara_lluminancia.py).
"""
import os
import numpy as np

W_LLENC, H_LLENC = 7648, 5353
SOL_LLENC = (4021.35, 2737.90)          # (x, y) al llenç
ESCALA = 2.1495                          # ″/px (Vixen i llenç)
R_SOL_PX = 959.0 / ESCALA                # 446,15 px
PA_NORD = 57.19                          # ° al sensor Vixen (= llenç)

# compost Vixen
HDR_DIR = os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/Corona_HDR_Vixen')
HDR_SOL = (3479.0, 2319.0)
HDR_RETALL = (85, 4595, 40, 6830)        # files 85..4595, cols 40..6830 (inclusius)
HDR_A_LLENC = (SOL_LLENC[0] - HDR_SOL[0], SOL_LLENC[1] - HDR_SOL[1])   # (+542,35, +418,90)
K_VERMELL = 1.2545355558395386           # luminància = (G + k·R)/2, vis_params.json

# Sony
SONY_SOL_PLACA = (3894.7, 2768.7)        # reixa 5320×7968 (raw_image_visible de DSC06993)
SONY_ESCALA = 3.2020 / 2.1495            # px del llenç per px Sony (astrometria)
SONY_GIR_DEG = 33.088                    # research/80 §7 (7 estrelles); astrometria 33,08
SONY_SOL_LLENC_INICIAL = (4027.0, 2735.2)   # 7 estrelles vs capa Vixen de Pere; es refina

SCR = os.environ.get('FD_SCR') or os.path.join(
    '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad', 'treball')


def malla_llenc():
    yy, xx = np.mgrid[0:H_LLENC, 0:W_LLENC].astype(np.float32)
    r = np.hypot(xx - SOL_LLENC[0], yy - SOL_LLENC[1]) / R_SOL_PX
    th = np.arctan2(yy - SOL_LLENC[1], xx - SOL_LLENC[0])
    return r, th
