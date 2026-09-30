from pathlib import Path
import json
from psb_munta import ROOT,assemble
O=ROOT/'4-RESULTATS/v109_pixi_20260928'
cfg={'source':str(ROOT/'1-PHOTOSHOP/V108.psb'),'sha256':json.loads((O/'FONTS.json').read_text())['sources']['base']['sha256'],
 'destination':str(O/'V109_retocs_stage.psb'),'new':[{'id':400,'name':'Retocs de Pere · V109','rgb':str(O/'entrades/PIXI_net.npy'),'mask':str(O/'entrades/delta_mask.npy')}]}
(O/'MUNTATGE_RETOCS_CONFIG.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
assemble(cfg)
