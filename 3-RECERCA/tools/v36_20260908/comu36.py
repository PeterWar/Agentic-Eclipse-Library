"""V36 · les marques de la V35 (research/153): (1) la LUT de linealitat de la Sony APLICADA de debò (errata V34/V35, vegeu avall); la vora dels 8 s de la Sony (quadrat arrodonit pel vinyetatge, a 3,3–3,8 R☉) queda com a RESIDU DECLARAT després de dues cures provades i refusades (finestra quadràtica; esvaïment espacial); (2) operadors isotròpics amb condició de contorn SEPARABLE (perfil radial amb pendent
que decau, L 100 px, × modulació azimutal de les primeres corones senceres) i variància/potència NOMÉS sobre el suport real;
(3) NRGF/RHEF: anells interiors incomplets estimats com els de la vora del llenç, i rang de la RHEF en radi CONTINU (interpolació
entre les CDF de dos anells veïns) contra les bandes de fase prop dels eixos. La resta és la V35.
⛔ ERRATA V34/V35 (trobada el 08-09 a la tarda): `plans_v34` només aplicava la LUT de linealitat Sony si `run.tren == 'sony'`, però el run es diu
'SONYTOT' → la LUT NO es va aplicar mai a la V34 ni a la V35 (els seus rebuts ho declaren en fals). Aquí s'aplica de debò (i la finestra dels 8 s)."""
import os, sys, json, time
from pathlib import Path
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0, str(ROOT / 'research/tools/v35_20260908'))
import comu35
from comu35 import *          # comu34/comu32/v29 common: H, W, CX, CY, RS, coords, smooth, gauss, normgauss, CAUF, f2, comu, sha, log, savejson, GHOST_XY…
from comu35 import CAU35, HERE35, TAPER_VIXEN_PX, TAPER_A_PX, RELLEU_R, DELTA_SIGMA_PX, DELTA_RAMP_R, REP_CANVIS as REP_CANVIS_V35
from comu34 import CAU34, HERE34, lin_corr_sony, finestra_v34
HERE36 = Path(__file__).resolve().parent
CAU36 = HERE36 / 'cau'; OUT36 = ROOT / 'output/v36_20260908'; VIS36 = OUT36 / 'lliurables/vistes'; REB36 = OUT36 / '4-rebuts'
IAOUT36 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v36_20260908')
for p in (CAU36, VIS36, REB36, IAOUT36):
    p.mkdir(parents=True, exist_ok=True)
# ---- (1) finestra pròpia dels fotogrames de 8 s de la Sony: (1 − smoothstep(f, 0,10·alt, alt))², terra igual
FOTOGRAMES_8S = ('DSC06987.ARW', 'DSC06993.ARW'); INICI_8S = 0.10 / 0.85; POTENCIA_8S = 2.0
def finestra_8s(f, t, sat, ped):
    alt = f2.SOSTRE * (sat - ped)
    w = np.clip((f - f2.TERRA_DN) / (3.0 * f2.TERRA_DN), 0.0, 1.0)
    w *= (1.0 - smooth(f, INICI_8S * alt, alt)) ** POTENCIA_8S
    return (w * t).astype(np.float32)
def plans_v36(s, nom, e):
    """Com plans_v34 (LUT de linealitat Sony abans del flat), amb la finestra dels 8 s als dos fotogrames de 8 s de la Sony."""
    import rawpy
    with rawpy.imread(s.ruta[nom]) as r:
        raw = r.raw_image.astype(np.float32)
    dk = s.dark(e); out = {}; ped = s.cfg['pedestal_dn']; sat = s.cfg['saturacio_dn']
    es_sony = s.run.tren.upper().startswith('SONY')          # ⛔ el run es diu 'SONYTOT': la V34/V35 comparaven amb 'sony' i la LUT no entrava mai
    fin = finestra_v34            # V36b: la finestra pròpia dels 8 s (quadràtica 0,10→0,85) es va provar i REFUSAR: +14 % de gra a tot el camp on els 8 s són al 10–50 % de saturació (C3 15:31); l'entrada gradual dels 8 s es fa en ESPAI (taper_8s)
    for i in range(4):
        oy, ox = s.orig[i]; rs = raw[oy::2, ox::2]; ds = dk[oy::2, ox::2]
        if es_sony:
            rs = ds + (rs - ds) * lin_corr_sony(rs, ped, sat)
        pl = comu.calibra_pla(rs, ds, s.flat[oy::2, ox::2], e, s.wb, s.mc, i)
        w = fin(raw[oy::2, ox::2] - ped, e, sat, ped) * s.valid[oy::2, ox::2]
        out[i] = (pl, w)
    return out
f2.Ctx.plans = plans_v36

# ---- (1b) esvaïment ESPACIAL dels dos fotogrames de 8 s: τ(x) = smoothstep(d, 0, TAPER_8S_PX)^3 amb d la distància cap enfora del contorn
#      de mig pes dels 8 s (pesos V34 a 1/4, pujats a resolució completa). El cub fa que la variància del compost (que canvia sobretot
#      mentre el pes dels 8 s és petit) es reparteixi al llarg dels 900 px en lloc d'acumular-se als primers 100.
TAPER_8S_PX = 900.0; TAPER_8S_POT = 3.0
_TAPER = {}
def taper_8s(coarse=False):
    key = 'c' if coarse else 'f'
    if key not in _TAPER:
        w = np.load(CAU34 / 'sony_w.npy', mmap_mode='r'); meta = json.loads((CAU34 / 'sony_meta.json').read_text())['frames']
        idx = [i for i, fr in enumerate(meta) if fr['name'] in FOTOGRAMES_8S]; w8 = sum(np.asarray(w[i]) for i in idx); plateau = float(np.percentile(w8[w8 > 0], 90))
        inside_c = (w8 < 0.5 * plateau).astype(np.uint8)
        if coarse:
            d = cv2.distanceTransform(1 - inside_c, cv2.DIST_L2, 5) * 4.0          # distància en px del llenç (cel·les de 4 px)
        else:
            inside = cv2.resize(inside_c, (W, H), interpolation=cv2.INTER_NEAREST); d = cv2.distanceTransform(1 - inside, cv2.DIST_L2, 5)
        _TAPER[key] = (smooth(d, 0.0, TAPER_8S_PX) ** TAPER_8S_POT).astype(np.float32)
    return _TAPER[key]

FARCIT_L_PX = 100.0; FARCIT_ANELLS_AZ = (1.05, 1.15); FARCIT_SIGMA_AZ_DEG = 3.0
REP_CANVIS = {'v35': REP_CANVIS_V35, 'vora_8s_sony': {'fotogrames': FOTOGRAMES_8S, 'estat': 'RESIDU DECLARAT: dues cures provades i refusades (finestra quadràtica 0,10→0,85: +14 % de gra a tot el camp on els 8 s són al 10–50 % de saturació; esvaïment espacial smoothstep(d,0,900)^3 des del contorn de mig pes: bony de gra fins a +30 % en una banda de 1200 px). Pesos dels 8 s com la V35 (finestra V34).', 'motiu': 'vora dels 8 s = quadrat arrodonit (vinyetatge del 300 mm sobre el cel) a 3,3–3,8 R☉; graó de gra del 14 % (base) en ~200 px; origen de captura (salt ×4 d\'exposició)'},
              'condicio_contorn_purs': {'radial': f'ln B continuat cap endins amb pendent que decau exp(−d/L), L {FARCIT_L_PX:.0f} px', 'azimutal': f'modulació ln B − ⟨ln B⟩ mesurada a {FARCIT_ANELLS_AZ} R☉, suavitzada {FARCIT_SIGMA_AZ_DEG}°', 'normalitzacio': 'variància (MGN) i potència (WOW) només sobre el suport real'},
              'radials': {'anells_interiors_incomplets': 'estimació de l\'anell sencer per la forma azimutal de les primeres corones senceres (com a la vora del llenç)', 'rhef': 'rang en radi continu: interpolació entre les CDF dels dos anells veïns'}}
