"""Recompute causal channels at source position. Never a composite compensation."""
from pathlib import Path
import sys,json,numpy as np
from psb_munta import ROOT,PSB,q_blocs,sha
O=ROOT/'4-RESULTATS/v112_20260928';v=sys.argv[1];stage=O/v;stage.mkdir(exist_ok=False);fstd=stage/'filtres_std';fstd.mkdir()
source=ROOT/'4-RESULTATS/v110_torre_20260928/V111.psb';p=PSB(str(source));r={};targets={}
for lid,tag in [(45,'P02c_RHEF_local60_native'),(46,'P02d_RHEF_local30_native')]:
 old=q_blocs(np.load(O/'rhef_control/filtres'/(tag+'_u16.npy')));new=q_blocs(np.load(O/'rhef_sensor/filtres'/(tag+'_u16.npy')));actual=p.channel(lid,1)[0];changed=new!=old
 assert np.array_equal(actual[changed],old[changed]),f'Unreproduced source on changed support {lid}'
 target=actual.copy();target[changed]=new[changed];f=stage/f'L{lid}.npy';np.save(f,target);targets[str(lid)]=dict(path=str(f),sha256=sha(f));r[str(lid)]=dict(changed=int(changed.sum()),control_exact_where_changed=True,manual234_changed=int(np.count_nonzero(changed&(np.load(O/'L234_mascara.npy')>0))))
 (fstd/(tag+'_u16.npy')).symlink_to(f)
for lid,tag in [(54,'P03_MGN'),(45,'P02c_RHEF_local60_native'),(46,'P02d_RHEF_local30_native')]:
 if lid==54:np.save(fstd/(tag+'_u16.npy'),p.channel(lid,1)[0])
 np.save(fstd/(tag+'_alfa_u16.npy'),p.channel(lid,-1)[0])
(stage/'RHEF_TARGETS.json').write_text(json.dumps(dict(replacement=targets,verification=r),indent=2)+'\n');print(r)
