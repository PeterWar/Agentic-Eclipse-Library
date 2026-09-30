"""Fixed native-display seam metric, declared before any correction."""
from pathlib import Path
import sys,json,numpy as np,tifffile
from scipy.ndimage import gaussian_filter1d
R=Path(__file__).resolve().parents[3];O=R/'4-RESULTATS/v112_20260928'
CENTRES=[(4200,10067),(4600,9626),(5800,8712)]
def measure(path):
 a=tifffile.memmap(path,mode='r');rows=[]
 for y,x in CENTRES:
  rgb=a[y-15:y+16,x-140:x+141].astype(np.float64);L=(rgb[...,0]+2*rgb[...,1]+rgb[...,2])/4
  v=gaussian_filter1d(np.median(np.log(np.maximum(L,1)),axis=0),sigma=6);d=(v[40:]-v[:-40])[20:-20];i=np.argmax(abs(d))
  rows.append(dict(x=x,y=y,max_step40=float(abs(d[i])),peak_x=int(x-100+i),signed_step=float(d[i])))
 return rows
if __name__=='__main__':
 base=measure(O/'control_natiu/visible_complet.tif');cand=measure(Path(sys.argv[1]));rows=[]
 for a,b in zip(base,cand):rows.append(dict(control=a,candidate=b,reduction=1-b['max_step40']/a['max_step40'],pass_gate=b['max_step40']<=.5*a['max_step40']))
 r=dict(candidate=sys.argv[1],metric='RGB16 native code values L=(R+2G+B)/4; log; median31rows; Gaussian1d sigma6 reflect truncate4; max40px difference over201 fixed positions',status='PASS' if all(x['pass_gate'] for x in rows) else 'FAIL',rows=rows);Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
