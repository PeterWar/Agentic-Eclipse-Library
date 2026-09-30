"""V37fc · la V37 amb el FORAT LUNAR CIRCULAR al radi màxim de la unió de posicions de la Lluna (1,046 R☉ des del centre del Sol,
el primer anell sencer del suport V36), per comparar-la amb la V37 (que conserva la franja de la unió temporal). Tot igual que la V37
llevat del suport i la base: dins del cercle no hi ha dada. Pere decideix."""
import os, sys, json, time
from pathlib import Path
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0, str(ROOT / 'research/tools/v37_20260908'))
import comu37
from comu37 import *
from comu37 import CAU37, HERE37, REP_CANVIS as REP_CANVIS_V37
HERE37FC = Path(__file__).resolve().parent
CAU37FC = HERE37FC / 'cau'; OUT37FC = ROOT / 'output/v37fc_20260908'; VIS37FC = OUT37FC / 'lliurables/vistes'; REB37FC = OUT37FC / '4-rebuts'
IAOUT37FC = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v37fc_20260908')
for p in (CAU37FC, VIS37FC, REB37FC, IAOUT37FC):
    p.mkdir(parents=True, exist_ok=True)
RADI_FORAT_PX = 461            # primer anell sencer del suport V36 (1,046 R☉)
REP_CANVIS = {'v37': REP_CANVIS_V37, 'forat_circular': {'radi_px': RADI_FORAT_PX, 'radi_R': RADI_FORAT_PX / RS, 'centre': 'Sol (CX, CY)', 'que_treu': 'la franja de la unió temporal (1,005–1,046 R☉ segons azimut, 18 px a l\'oest)'}}
