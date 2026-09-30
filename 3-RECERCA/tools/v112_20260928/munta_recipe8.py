from pathlib import Path
import json,numpy as np
from psb_munta import ROOT,PSB,q_blocs,sha,assemble
O=ROOT/'4-RESULTATS/v112_20260928';S=O/'sensor_recipe8_raw';source=ROOT/'4-RESULTATS/v110_torre_20260928/V111.psb';p=PSB(str(source));rep=json.loads((O/'sensor01/RHEF_TARGETS.json').read_text());targets=rep['replacement']
for lid,tag in [(41,'P01_NRGF'),(42,'P01_NRGF_extrap')]:
 oldp=O/'nrgf_recipe8_control_raw/G_MAX_T_e30_W_H0'/(tag+'_u16.npy');newp=S/'nrgf/G_MAX_T_e30_W_H0'/(tag+'_u16.npy');old=q_blocs(np.load(oldp));new=q_blocs(np.load(newp));actual=p.channel(lid,1)[0];change=new!=old
 assert np.array_equal(actual[change],old[change]),(lid,'control source differs on changed support')
 target=actual.copy();target[change]=new[change];f=S/f'L{lid}.npy';assert not f.exists();np.save(f,target);targets[str(lid)]=dict(path=str(f),sha256=sha(f));rep['verification'][str(lid)]=dict(changed=int(change.sum()),control_exact_where_changed=True,manual234_changed=int(np.count_nonzero(change&(np.load(O/'L234_mascara.npy')>0))))
inputs=[source,ROOT/'1-PHOTOSHOP/V108_Artefactes.psb',ROOT/'4-RESULTATS/v108_20260926/cadena/v108/lineal/base_G.npy',ROOT/'4-RESULTATS/v108_20260926/cadena/v108/lineal/support.npy',ROOT/'4-RESULTATS/v108_20260926/cadena/v108/franja/A3C_franja_silueta.npz',ROOT/'4-RESULTATS/v108_20260926/cadena/v108/base/base_v108_final_u16.npy']
rep['source_sha256']=sha(source);rep['inputs']={str(f):sha(f) for f in inputs};rep['producers']={str(f):sha(f) for f in [ROOT/'3-RECERCA/tools/v98_20260925/f3_filtres_v98.py',Path(__file__).parent/'rhef_sensor.py',ROOT/'3-RECERCA/tools/v108_20260926/negres_v2/g1_nrgf_genoll.py',Path(__file__)]};rep['science_status']='UNVALIDATED';rep['method']='45/46 full deterministic sensor-boundary operator; legacy exact on its unchanged support; dependent41/42 recomputed from corrected raw-generation45/46 and original54 with frozen recipe8; V111 manual opacity31 retained later by native Photoshop; no new layer.'
(S/'TARGETS.json').write_text(json.dumps(rep,indent=2)+'\n');cfg=dict(source=str(source),sha256=sha(source),destination=str(S/'V112_sensor_recipe8_raw_stage.psb'),hide=[412],replace={lid:{str(c):v['path'] for c in (0,1,2)} for lid,v in targets.items()})
(S/'CONFIG.json').write_text(json.dumps(cfg,indent=2)+'\n');assemble(cfg)
