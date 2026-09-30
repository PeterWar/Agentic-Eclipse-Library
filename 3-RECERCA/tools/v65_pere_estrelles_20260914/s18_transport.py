from pathlib import Path
import numpy as np,json
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';grid=json.loads((R/'research/tools/v29/cau_final/direct_grid_receipt.json').read_text());C=np.array(grid['common_to_final']);corr=json.loads((R/'research/tools/v42_20260910/cau/correccions_B.json').read_text());ctx={}
for tag in ['sony','vixen']:
 p=Path(grid['runs'][tag]['path']);ll=json.loads((p/'4-rebuts/F1.2_sol_llenc.json').read_text())['llenc'];pos=json.loads((p/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];th=np.deg2rad(-ll['pa_north_deg']);rot=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]]);ctx[tag]=(ll,pos,rot)
def final(xy,tag,name):
 ll,pos,rot=ctx[tag];key=name+('.ARW' if tag=='sony' else '.CR3');s=pos[key];xy=np.array(xy,float)
 if tag=='vixen':xy+=np.array([172,108])
 d=rot@(xy-np.array([s['sol_x'],s['sol_y']])-np.array(corr.get(key,[0,0])))
 if tag=='sony' and int(name[-2:])>=91:
  th=np.deg2rad(-8.1/60);d=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])@d
 k=ll['escala_arcsec_px']/ll['escala_sensor_arcsec_px'];q=d/k+[ll['W']/2,ll['H']/2];return C[:,:2]@q+C[:,2]
if __name__=='__main__':
 old=json.loads((R/'output/v58_correccions_20260913/D4_sources.json').read_text())['selected'];old={r['star']['TYC']:r['star'] for r in old if r['star'].get('TYC')};out=[]
 for tag,m,pre,frames in [('sony','S9_native_manifest','S9',['DSC06987','DSC06993']),('vixen','S11_vixen_manifest','S11',['572A2982'])]:
  meta=json.loads((O/(m+'.json')).read_text());fs={n:np.load(O/f'{pre}_{n}.npz') for n in frames}
  for i,r in enumerate(meta['rows']):
   if r['kind']!='catalog' or r['TYC'] not in old:continue
   rec=dict(tag=tag,TYC=r['TYC'],V=r['V'],old_xy=[old[r['TYC']]['x'],old[r['TYC']]['y']],predicted=[r['x_final'],r['y_final']],native={n:final(f['expected'][i],tag,n).tolist() for n,f in fs.items()});out.append(rec)
 (O/'S18_transport_check.json').write_text(json.dumps(out,indent=2))
 for tag in ['sony','vixen']:
  rr=[r for r in out if r['tag']==tag and r['V']<8.5]
  for n in rr[0]['native']:
   delta=np.array([np.array(r['native'][n])-r['old_xy'] for r in rr]);print(tag,n,'median',np.median(delta,0),'norm median/max',np.median(np.linalg.norm(delta,axis=1)),np.max(np.linalg.norm(delta,axis=1)))
 print(out[:3])
