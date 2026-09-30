from pathlib import Path
import json,os,subprocess,sys,numpy as np
from psb_munta import ROOT,PSB,q_blocs,sha,assemble
T=Path(__file__).parent;O=ROOT/'4-RESULTATS/v112_20260928';S=O/'sensor_mass_raw';S.mkdir(exist_ok=False);fstd=S/'filtres_generation';fstd.mkdir()
source=ROOT/'4-RESULTATS/v110_torre_20260928/V111.psb';p=PSB(str(source));rep=dict(replacement={},verification={});targets=rep['replacement']
for lid,tag in [(45,'P02c_RHEF_local60_native'),(46,'P02d_RHEF_local30_native')]:
 old=q_blocs(np.load(O/'rhef_control/filtres'/(tag+'_u16.npy')));new=q_blocs(np.load(O/'rhef_mass/filtres'/(tag+'_u16.npy')));actual=p.channel(lid,1)[0];change=new!=old
 assert np.array_equal(actual[change],old[change]),(lid,'unreproduced source where changed')
 target=actual.copy();target[change]=new[change];f=S/f'L{lid}.npy';np.save(f,target);targets[str(lid)]=dict(path=str(f),sha256=sha(f));rep['verification'][str(lid)]=dict(changed=int(change.sum()),manual234_changed=int(np.count_nonzero(change&(np.load(O/'L234_mascara.npy')>0))))
 for suffix in ['_u16.npy','_alfa_u16.npy']:(fstd/(tag+suffix)).symlink_to(O/'rhef_mass/filtres'/(tag+suffix))
for suffix in ['_u16.npy','_alfa_u16.npy']:(fstd/('P03_MGN'+suffix)).symlink_to(ROOT/'4-RESULTATS/v108_20260926/cadena/v108/filtres_std/filtres'/('P03_MGN'+suffix))
env={k:v for k,v in os.environ.items() if not k.startswith(('V97_','V98_','V108_'))}
base=ROOT/'4-RESULTATS/v108_20260926/cadena/v108'
env.update(V97_FONTS=str(base/'lineal'),V98_FRANJA=str(base/'franja/A3C_franja_silueta.npz'),V108_BASE=str(base/'base/base_v108_final_u16.npy'),V108_R=str(base),V97_SORT=str(S/'nrgf'),PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='4')
args=[sys.executable,str(T/'trace_producer.py'),str(S/'TRACE_G1.json'),str(ROOT/'3-RECERCA/tools/v108_20260926/negres_v2/g1_nrgf_genoll.py'),'G_MAX_T_e30_W_H0','--psb',str(ROOT/'1-PHOTOSHOP/V108_Artefactes.psb'),'--filtres-std',str(fstd)]
with (S/'g1.log').open('w') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
for lid,tag in [(41,'P01_NRGF'),(42,'P01_NRGF_extrap')]:
 oldp=O/'nrgf_recipe8_control_raw/G_MAX_T_e30_W_H0'/(tag+'_u16.npy');newp=S/'nrgf/G_MAX_T_e30_W_H0'/(tag+'_u16.npy');old=q_blocs(np.load(oldp));new=q_blocs(np.load(newp));actual=p.channel(lid,1)[0];change=new!=old
 assert np.array_equal(actual[change],old[change]),(lid,'control source differs on changed support')
 target=actual.copy();target[change]=new[change];f=S/f'L{lid}.npy';np.save(f,target);targets[str(lid)]=dict(path=str(f),sha256=sha(f));rep['verification'][str(lid)]=dict(changed=int(change.sum()),manual234_changed=int(np.count_nonzero(change&(np.load(O/'L234_mascara.npy')>0))))
rep['source_sha256']=sha(source);rep['science_status']='UNVALIDATED';rep['method']='Nominal paired comparison mass at FOV boundary; raw generation recipe8 propagated; native manual31 preserved; no new layer.'
(S/'TARGETS.json').write_text(json.dumps(rep,indent=2)+'\n');cfg=dict(source=str(source),sha256=sha(source),destination=str(S/'V112_sensor_mass_stage.psb'),hide=[412],replace={lid:{str(c):v['path'] for c in (0,1,2)} for lid,v in targets.items()});(S/'CONFIG.json').write_text(json.dumps(cfg,indent=2)+'\n');assemble(cfg)
