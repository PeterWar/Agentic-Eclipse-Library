"""V35 · les cures a l'ORIGEN de les marques de la V34 (research/151). Sobre la composició per grup de la V34
(finestra gradual + linealitat Sony + camps B1: `vixen_total_v34`, `sony_A/B_total_v34`, sense canvis), canvia:
  1. la FUSIÓ (b3): distàncies a la vora sobre suports PLENS (la V34 hi tenia el forat lunar: la Sony entrava a
     1,0–1,36 R☉); la Vixen conformada en baixa freqüència (σ256) a la Sony·ρ de 2,65 R☉ enfora (la seva vora
     anava −2,9 % més fosca); pes Vixen esvaït en 720 px a la vora del seu suport i pes A esvaït en 480 px a la
     vora del seu suport (els contorns dels dos camps eren graons de nivell i de gra); relleu entre trens
     1,9→3,5 R☉ (abans 2,0→2,65: el gra queia a la meitat en 130 px);
  2. els operadors ISOTRÒPICS purs (P03 MGN, P04/P05 WOW): condició de contorn = perfil azimutal mitjà de la
     pròpia imatge (forat lunar i fora del suport), NOMÉS com a entrada de l'operador; el producte conserva el
     suport físic. Sense això la mitjana local d'un sol costat contra el forat feia anells clars al limbe
     (4–5 σ) i l'à trous dispers hi dibuixava rectangles a 2^s px.
La resta (registre, flats, k, offsets, camps B1, ρ 2D, receptes dels filtres, mapa de resolució V29) és la de la V32/V34."""
import os, sys, json, time
from pathlib import Path
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0, str(ROOT / 'research/tools/v34_20260907'))
import comu34
from comu34 import *          # inclou comu32: H, W, CX, CY, RS, coords, smooth, gauss, normgauss, CAUF, sha, log, savejson, GHOST_XY, f2, comu…
from comu34 import CAU34, HERE34, REP_CANVIS as REP_CANVIS_V34
HERE35 = Path(__file__).resolve().parent
CAU35 = HERE35 / 'cau'; OUT35 = ROOT / 'output/v35_20260908_replica'; VIS35 = OUT35 / 'lliurables/vistes'; REB35 = OUT35 / '4-rebuts'
IAOUT35 = ROOT / 'output/v35_20260908_replica/IA_dummy'
for p in (CAU35, VIS35, REB35, IAOUT35):
    p.mkdir(parents=True, exist_ok=True)
TAPER_VIXEN_PX = 720.0      # esvaïment del pes Vixen a la vora del seu suport (ple)
TAPER_A_PX = 480.0          # esvaïment del pes de l'apuntament A a la vora del seu suport (ple)
RELLEU_R = (1.9, 3.5)       # relleu Vixen→Sony (smoothstep en r); la variància només AFEGEIX Vixen
DELTA_SIGMA_PX = 256.0      # conformació de la Vixen a la Sony·ρ en baixa freqüència
DELTA_RAMP_R = (2.0, 2.65)  # la conformació entra amb el relleu
REP_CANVIS = {'composicio_per_grup': 'V34 (finestra gradual 0,35→0,85 sat; linealitat Sony; camps B1)', 'v34': REP_CANVIS_V34,
              'fusio': {'distancies': 'suports plens (forat lunar tapat per a la distància)', 'taper_vixen_px': TAPER_VIXEN_PX, 'taper_A_px': TAPER_A_PX, 'relleu_R': RELLEU_R,
                        'conformacio_vixen': f'V·exp(−δ), δ = ⟨ln(V/(S·ρ))⟩ σ{DELTA_SIGMA_PX:.0f} al solapament, entrada smoothstep {DELTA_RAMP_R}'},
              'filtres_purs': 'P03/P04/P05: entrada = base amb forat lunar i fora del suport omplerts pel perfil azimutal mitjà (ln) de la pròpia imatge; sortida al suport físic; LUT de pantalla de la V34'}
