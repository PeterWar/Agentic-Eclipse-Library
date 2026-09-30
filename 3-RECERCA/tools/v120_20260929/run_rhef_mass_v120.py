"""run_rhef_mass_v120 (V120): còpia de v114/run_rhef_mass_v114.py amb el claim de la V120. run_rhef_mass_v113 · el RHEF local «mass» del Codex (V112, 3-RECERCA/tools/v112_20260928/rhef_mass.py, sense canvis) dins de
f3_filtres_v98.py, com run_rhef_mass.py del Codex però amb el claim de la V112-V113. Ús: V97_SORT=… V97_FONTS=… V98_FRANJA=… run_rhef_mass_v113.py E6"""
from pathlib import Path
import sys, runpy, importlib.util, json
R = Path(__file__).resolve().parents[3]; TX = R / '3-RECERCA/tools/v112_20260928'
# 30-09-2026: regla de l'escriptor únic retirada per Pere: assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V120_DISTORSIO_20260929'
spec = importlib.util.spec_from_file_location('rhef_local_sim', TX / 'rhef_mass.py'); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
sys.modules['rhef_local_sim'] = module
sys.argv[0] = str(R / '3-RECERCA/tools/v98_20260925/f3_filtres_v98.py')
runpy.run_path(sys.argv[0], run_name='__main__')
