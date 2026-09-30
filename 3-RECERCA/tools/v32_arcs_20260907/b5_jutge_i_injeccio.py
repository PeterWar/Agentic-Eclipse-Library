"""B5a · Jutge extern fix i injecció cega sobre la base i les vistes pures V32,
amb EL MATEIX CODI de v31_purs (qa_science.external_judge, qa_injection.main).

Jutge: la Vixen ORIGINAL (v29/cau_final/vixen_total, sense cap correcció) a les
quatre finestres de 3,5/4 R☉ on la base és Sony: correlació per bandes de cada
vista pura V32 i de la base V32. Injecció: tres gaussianes (σ 2/8/24 px, 1 % de la
mediana) a una finestra nativa de la base V32; resposta aparellada positiva de
MGN/WOW/WOW bilateral/NAFE. Rebuts a purs/receipts/ (external_judge.json, injection.json).
"""
import os, sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PURS = ROOT / 'research/tools/v31_purs'; MINE = HERE / 'purs'
sys.path = [str(PURS)] + [p for p in sys.path if 'research/tools' not in p]
os.environ['V29_FINAL_GRID'] = '1'
import common as vc
import numpy as np
vc.C = MINE / 'cau'; vc.OUT = ROOT / 'output/v32_arcs_20260907/lliurables/vistes'; vc.D = MINE
CAU32 = HERE / 'cau'
def readbase():
    return np.load(CAU32 / 'base_G_v32.npy', mmap_mode='r'), np.load(CAU32 / 'support_v32.npy')
vc.readbase = readbase
import qa_science, qa_injection
assert qa_science.readbase is readbase and qa_science.OLD == vc.OLD and qa_injection.readbase is readbase and qa_science.D == MINE
if __name__ == '__main__':
    qa_science.external_judge(); vc.log('jutge extern fet')
    qa_injection.main(); vc.log('injecció feta')
    # comparació abans/després del jutge (mateixes finestres, mateixes bandes)
    before = json.loads((PURS / 'receipts/external_judge.json').read_text())['rows']; after = json.loads((MINE / 'receipts/external_judge.json').read_text())['rows']
    rows = []
    for b, a in zip(before, after):
        assert b['tag'] == a['tag'] and b['xy'] == a['xy'] and b['band_sigma_px'] == a['band_sigma_px']
        rows.append({'tag': a['tag'], 'xy': a['xy'], 'band': a['band_sigma_px'], 'V31_corr': b['correlation_fixed_Vixen'], 'V32_corr': a['correlation_fixed_Vixen'], 'V31_base_corr': b['base_correlation_fixed_Vixen'], 'V32_base_corr': a['base_correlation_fixed_Vixen']})
    dz = [r['V32_corr'] - r['V31_corr'] for r in rows]; dzb = [r['V32_base_corr'] - r['V31_base_corr'] for r in rows]
    summary = {'rows': rows, 'delta_corr_layers_mean': float(np.mean(dz)), 'delta_corr_layers_median': float(np.median(dz)), 'n_up': int(np.sum(np.array(dz) > 0)), 'n_down': int(np.sum(np.array(dz) < 0)),
               'delta_corr_base_mean': float(np.mean(dzb)), 'judge': 'original uncorrected Vixen G total (v29/cau_final), fixed'}
    (ROOT / 'output/v32_arcs_20260907/4-rebuts/B5_jutge_abans_despres.json').write_text(json.dumps(summary, indent=1) + '\n')
    vc.log(f"jutge: Δcorr capes mitjana {summary['delta_corr_layers_mean']:+.4f} (puja {summary['n_up']}, baixa {summary['n_down']}) · base {summary['delta_corr_base_mean']:+.4f}")
