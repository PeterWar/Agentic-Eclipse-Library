from pathlib import Path
import sys,runpy,importlib.util,json
R=Path(__file__).resolve().parents[3];T=Path(__file__).parent
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V112_ESTRELLES_I_ARTEFACTES_20260928'
mode=sys.argv.pop(1)
if mode in ('soft','sensor','mass'):
 spec=importlib.util.spec_from_file_location('rhef_local_sim',T/('rhef_'+mode+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);sys.modules['rhef_local_sim']=module
elif mode!='legacy':raise ValueError(mode)
sys.argv[0]=str(R/'3-RECERCA/tools/v98_20260925/f3_filtres_v98.py')
runpy.run_path(sys.argv[0],run_name='__main__')
