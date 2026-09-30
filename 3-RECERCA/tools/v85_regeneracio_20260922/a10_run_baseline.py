from pathlib import Path
import sys,subprocess,json,time,os,datetime
T=Path(__file__).resolve().parent;R=T.parents[2];O=R/'4-RESULTATS/v85_regeneracio_20260922'
steps=[('grid','a4_sources.py',['grid'],'sources_v29'),('v36','a4_sources.py',['v36'],'sources_v36'),('sony_A','a5_recompose.py',['sony_A'],'b2_sony_A'),('vixen','a5_recompose.py',['vixen'],'b2_vixen'),('sony_B','a5_recompose.py',['sony_B'],'b2_sony_B'),('b3','a5_recompose.py',['b3'],'b3_baseline'),('s4','a8_starless_baseline.py',['s4'],'s4_baseline'),('d4','a8_starless_baseline.py',['d4'],'d4_baseline'),('limb_frames','a9_limb_frames.py',[],'limb_frames')]
rows=[]
for name,file,args,folder in steps:
 p=O/folder/'COMPLETE.json'
 if p.exists():
  j=json.loads(p.read_text());assert j['PASS'];print('PREVIOUSLY_COMPLETE',name,flush=True);continue
 log=O/(name+'.log');assert not log.exists(),str(log)+' exists; inspect previous attempt first'
 print('STAGE_START',name,datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True);start=time.monotonic()
 with log.open('x') as f:r=subprocess.run([sys.executable,'-B','-u',str(T/file),*args],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 row={'stage':name,'exit':r.returncode,'seconds':time.monotonic()-start,'log':str(log.relative_to(R))};rows.append(row);(O/'BASELINE_PROGRESS.json').write_text(json.dumps(rows,indent=2));print('STAGE_END',json.dumps(row),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
 assert json.loads(p.read_text())['PASS']
(O/'BASELINE_COMPLETE.json').write_text(json.dumps({'PASS':True,'steps':rows},indent=2));print('BASELINE_COMPLETE',flush=True)
