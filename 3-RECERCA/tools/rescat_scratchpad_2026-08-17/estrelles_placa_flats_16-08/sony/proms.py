import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from common import planes, SCALE
from esf import limb_circle, OFF
nm=sys.argv[1] if len(sys.argv)>1 else "DSC06975.ARW"
P=planes(nm)
cx,cy,R,rms,n=limb_circle(P['G1'],'G1',None if False else (1775.9/1,1660.1/1),80,320)
print(nm,"center %.2f %.2f R %.3f"%(cx,cy,R))
from scipy.ndimage import map_coordinates
ang=np.linspace(0,2*np.pi,720,endpoint=False)
r=np.arange(R+0.5,R+8,0.25)
out={}
for ch in ['R','G1','B']:
    dx,dy=OFF[ch]; img=P[ch]
    px=cx+np.outer(np.cos(ang),r)-dx; py=cy+np.outer(np.sin(ang),r)-dy
    out[ch]=map_coordinates(img,[py,px],order=1,mode='constant',cval=np.nan).mean(axis=1)
ratio=out['R']/np.maximum(out['G1'],1)
sm=np.convolve(np.r_[ratio[-10:],ratio,ratio[:10]],np.ones(9)/9,'same')[10:-10]
print("median R/G ratio %.3f"%np.median(sm))
idx=np.argsort(sm)[::-1][:60]
print("top azimuths by R/G (deg, ratio, R-flux):")
sel=sorted(set((np.degrees(ang[i])//5*5) for i in idx))
for a in sel:
    i=int(a/360*720)
    print("  az %4.0f  R/G=%.2f  R=%9.1f G=%9.1f"%(a,sm[i],out['R'][i],out['G1'][i]))
