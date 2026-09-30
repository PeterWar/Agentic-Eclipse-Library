"""Independent, presentation-only branch. No scientific filter is changed."""
from pathlib import Path
import json
from psb_munta import ROOT, sha, assemble
O=ROOT/'4-RESULTATS/v112_20260928'
S=O/'corner_only'; S.mkdir(exist_ok=False)
source=O.parent/'v110_torre_20260928/V111.psb'
corner=O/'control_301'
contract={
 'schema':'V112-presentation-maintenance-1',
 'scope':'Regenerate only the existing derived301 from the unchanged V111 lower stack. All scientific filters and manual operations remain exact.',
 'source_sha256':'8a607e75967b4ef0d8a52eedabbedd986742781ecf3622b12c6e2630faba0da3',
 'changed_rgb':[301], 'annotation_hidden':412,
 'no_scientific_recovery':'Same original presentation-only continuation and alpha; never treat filled pixels as observed corona.',
 'no_global_approval':'This independent branch does not approve mass301 or reclassify its failed seams1/2. Those two seams remain unresolved and must be reported.',
 'quality':{'seam3_reduction_min':0.5,'seams1_2':'exact unchanged native profiles required, still unresolved',
 'outside_301_native':'exact unchanged RGB wherever original301 alpha is zero',
 'manual234':'exact native equality required; source234/308 exact channels and operations',
 'external':'Same frozen Brno windows and thresholds; report limited reference coverage'},
 'method_gates':['source hash exact','all metadata and all channels except301RGB and412visibility exact',
 'original a5 recipe independently reproduced','original301alpha exact','full native TIFF and native saved merged exact','p6','Photoshop open'],
 'status':'PREREGISTERED_BEFORE_BRANCH_ASSEMBLY'
}
(S/'CONTRACT.json').write_text(json.dumps(contract,indent=2)+'\n')
cfg=dict(source=str(source),sha256=contract['source_sha256'],destination=str(S/'V112_corner_only_stage.psb'),
 corner_receipt=str(corner/'RECEIPT.json'),hide=[412],replace={'301':{str(c):str(corner/f'L301_c{c}.npy') for c in (0,1,2)}})
target=dict(source_sha256=contract['source_sha256'],replacement={'301':dict(channels={str(c):dict(path=str(corner/f'L301_c{c}.npy'),sha256=sha(corner/f'L301_c{c}.npy')) for c in (0,1,2)},receipt=str(corner/'RECEIPT.json'),receipt_sha256=sha(corner/'RECEIPT.json'))},science_status='PRESENTATION_ONLY_UNVALIDATED')
(S/'CONFIG.json').write_text(json.dumps(cfg,indent=2)+'\n')
(S/'TARGETS.json').write_text(json.dumps(target,indent=2)+'\n')
assemble(cfg)
