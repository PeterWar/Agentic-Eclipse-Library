"""Mesura a la FONT de cada marca de la V32 (embolcall de l'A2 de v32_arcs amb les fonts V32):
perfils radials en ln de la base V32 i de cada tren, passa-alt σ24/σ96, correlació creuada entre
trens dins del tram, fraccions de pes per fotograma (fronteres HDR) i cura 1-D. Sortides amb
prefix R32 a output/revisio_marques_v33_20260907/. Només lectura."""
import os, sys, json
from pathlib import Path
os.environ['V32'] = '1'
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907'))
import a2_diagnosi_marques as a2
OUT = ROOT / 'output/revisio_marques_v33_20260907'
cat = json.loads((OUT / '4-rebuts/review_catalog.json').read_text())
only = os.environ.get('ONLY')
sel = [m for m in cat['marks'] if m['color'] != 'neutre' and (not only or m['id'] in only.split(','))]
a2.marks = lambda colors=None: sel
a2.PFX = 'R32'; a2.VIS = OUT / 'lliurables/vistes'; a2.REB = OUT / '4-rebuts'; a2.OUT32 = OUT
a2.main()
