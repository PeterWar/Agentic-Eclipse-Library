import numpy as np, json, sys
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
CX,CY,R=998.88,998.41,456.0
Y,X=np.mgrid[0:2000,0:2000]; RR=np.hypot(X-CX,Y-CY); AZ=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360
M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]],np.float32)
WN=np.array([0.9505,1.0,1.089],np.float32)
def lab(C):
    lin=np.clip(C,0,1)**2.2; XYZ=lin@M.T; t=XYZ/WN
    f=np.where(t>(6/29)**3,np.cbrt(t),t/(3*(6/29)**2)+4/29)
    L=116*f[...,1]-16; a=500*(f[...,0]-f[...,1]); b=200*(f[...,1]-f[...,2]); return L,a,b
def Lstar(C): return lab(C)[0]
MARKS=['m2','m3','m4','m5','m7']
_mk=np.load(S4+'/marques74_masks.npz')
def mask(k): return _mk[k]
def bbox(m,pad=0):
    ys,xs=np.nonzero(m); return max(0,ys.min()-pad),min(2000,ys.max()+1+pad),max(0,xs.min()-pad),min(2000,xs.max()+1+pad)
