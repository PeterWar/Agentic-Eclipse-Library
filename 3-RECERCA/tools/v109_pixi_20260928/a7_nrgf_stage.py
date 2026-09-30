from pathlib import Path
import json,numpy as np
from psb_munta import ROOT,PSB,q_blocs,assemble,sha
O=ROOT/'4-RESULTATS/v109_pixi_20260928';src=O/'entrades/V108_Artefactes_base.psb';p=PSB(str(src))
old=O/'nrgf01/CEL_G_MAX_T_e30_W_H0';new=O/'nrgf01/G_MAX_T_e30_W_H0';rep={};replace={}
for lid,tag in [(41,'P01_NRGF'),(42,'P01_NRGF_extrap')]:
 a=q_blocs(np.load(old/(tag+'_u16.npy'),mmap_mode='r'));b=q_blocs(np.load(new/(tag+'_u16.npy'),mmap_mode='r'));actual=p.channel(lid,1)[0]
 d=b.astype(np.int32)-a.astype(np.int32);changed=d!=0
 assert np.array_equal(actual[changed],a[changed]),'control mismatch where change would act'
 target=actual.astype(np.int32)+d;assert target.min()>=0 and target.max()<=65535
 f=O/'nrgf01'/f'L{lid}_nou.npy';np.save(f,target.astype(np.uint16));replace[str(lid)]={str(c):str(f) for c in [0,1,2]}
 rep[str(lid)]={'changed':int(changed.sum()),'control_exact_on_support':True,'difference_DN':[int(d.min()),int(d.max())]}
cfg={'source':str(src),'sha256':sha(src),'destination':str(O/'CEL_retirat_stage.psb'),'hide':[307],'replace':replace}
(O/'NRGF_STAGE_CONFIG.json').write_text(json.dumps(cfg,indent=2));(O/'NRGF_STAGE_CONTROL.json').write_text(json.dumps(rep,indent=2));assemble(cfg)
