"""Seal the read-only review; verify source hashes and referenced outputs."""
from extract import *
from datetime import datetime,timezone
import re,platform
import scipy,PIL,psd_tools
def record(p):
    p=Path(p);return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)}
rep=json.loads(Path(RUN.rebut('marks_inventory.json')).read_text())
original=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_FiltresPurs.psb')
ann=Path(rep['source_original']);a=record(ann);o=record(original);snap=record(D/'input_anotat.psb')
assert a['sha256']==rep['source_sha256']==snap['sha256']
assert o['sha256']=='89d509bcc53982307cf9e3d78b0a84ed7548f4045e8cbb95d9f8594e4e877dfd'
for p in [Path(RUN.lliurable('RESULTAT.md')),ROOT/'research/145_REVISIO_MARQUES_V31_20260907.md']:
    for link in re.findall(r'\]\(<?(/[^\n]*?)>?\)',p.read_text()):assert Path(link).exists(),link
receipts=[p for p in Path(RUN.rebut('')).glob('*.json') if p.name!='manifest.json']
for p in receipts:json.loads(p.read_text())
assert len(rep['layers'])==19 and sum(len(l['marks']) for l in rep['layers'])==137
artifacts=list(Path(RUN.vista('')).glob('*.png'))+list(Path(RUN.lliurable('')).glob('*.md'))+list(Path(RUN.lliurable('')).glob('*.csv'))
artifacts += [ROOT/'research/145_REVISIO_MARQUES_V31_20260907.md']
data=list(D.glob('*_mark_codes.npy'))+list(D.glob('*_original_G8.npy'))
for l in rep['layers']:
    for m in l['marks']:
        data.extend(D/'windows'/(m['id']+suffix) for suffix in ['_marked.npy','_original.npy'])
inputs=[ROOT/'research/tools/v29/cau_final'/f for f in ['vixen_total.npy','sony_corrected_total.npy','vixen_support.npy','sony_support.npy','fusion_support.npy']]
code=list(D.glob('*.py'))+[ROOT/'research/tools/v29/inspect_inputs.py',ROOT/'research/tools/eclipse_determinista/comu.py']
j={'created_utc':datetime.now(timezone.utc).isoformat(),'claim_id':'CODEX_REVISIO_MARQUES_V31_20260907',
    'status':'COMPLETED_LAYER_REVIEW; no correction applied','source_annotation_unchanged':a,'original_V31_unchanged':o,'annotation_snapshot':snap,
    'layer_count':19,'brush_components':137,'Pere_confirmed_components':129,'green_uncertain_components':8,
    'not_a_count_of_independent_defects':True,'runtime':{'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'scipy':scipy.__version__,'opencv':cv2.__version__,'pillow':PIL.__version__,'psd_tools':psd_tools.__version__},
    'inputs':[record(p) for p in inputs],'code':[record(p) for p in code],
    'protocol':record(D/'PLAN.md'),'decoder_QA':record(D/'decoder_QA.json'),
    'receipts':[record(p) for p in receipts],'artifacts':[record(p) for p in artifacts],'diagnostic_data':[record(p) for p in data],
    'visual_QA':'All19 complete annotated canvases; matching unpainted canvases and mark/reference panels reviewed by root and independent read-only reviewers; no new PSB',
    'limitations':['Color components can split one stroke or join crossing strokes; IDs are indexing units',
        'Pere certainty is distinct from a measured causal attribution','All green marks remain uncertain',
        'Cross-train local correlations verify shared texture, not each marked curve',
        'No source intervention or artifact correction tested','Unmarked layers not certified artifact-free',
        '8bit views not photometry; quantitative original float sources retained'],
    'superseded':'provisional_SUPERSEDED directories and inventory_before_color_refinement.json are not final evidence',
    'reviewers':['Halley: ten pure filters and operator provenance','Raman: green-mark neighborhoods and physical source scope']}
write(RUN.rebut('manifest.json'),j)
print(json.dumps({'manifest':RUN.rebut('manifest.json'),'sources_unchanged':True,'artifacts':len(artifacts),'diagnostic_data':len(data),'receipts':len(receipts)},indent=2))
