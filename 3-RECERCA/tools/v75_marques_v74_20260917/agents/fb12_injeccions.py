"""fb12: (1) autoconsistència: S8 re-executat sobre P reconstruït ha de reproduir W; (2) injeccions cegues ±3 % σ50 (RAW i P coherents) sobre el pipeline A_add."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad')
sys.path.insert(0,'/Users/USUARI/Desktop/Eclipse 2026/3-RECERCA/tools/earthshine_broad_lroc_20260914')
from fb6_candidata import *
from s8_operator import s8_eval
from scipy.ndimage import gaussian_filter
out={}
# (1) S8 sobre P (retall 1400² = marc S8) contra Wdq
P14=P[300:1700,300:1700].copy(); edge=np.load(R+'/3-RECERCA/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
Ln,Ws8=s8_eval(P14,edge); Wref=Wdq[300:1700,300:1700]; d14=d[300:1700,300:1700]; z=(d14<-70)&(d14>-262)
dif=Ws8-Wref; out['autoconsistencia_S8']=dict(mediana=float(np.median(dif[z])),p99_abs=float(np.percentile(np.abs(dif[z]),99)),max_abs=float(np.abs(dif[z]).max()),rms=float(np.sqrt(np.mean(dif[z]**2))))
print('S8(P reconstruït) − W_dq (d −262…−70): mediana %.0f, rms %.0f, p99 |dif| %.0f, màx %.0f DN16'%(out['autoconsistencia_S8']['mediana'],out['autoconsistencia_S8']['rms'],out['autoconsistencia_S8']['p99_abs'],out['autoconsistencia_S8']['max_abs']))
# (2) injeccions
kap=kappa(); F71=np.load(OLD+'/vel_corr_final.npy').astype(np.float64)
def pipeline_A(RAWs_,P_):
    f,finv,xc,yi=ajusta_f(RAWs_,P_); Vdev,ringmed,Vl=vel_lineal(RAWs_); D=gaussian_filter(f(RAWs_)-f(RAWs_-Vdev),6); return (P_-Wdq+kap*(Wdq-D)), f
cand0,f0=pipeline_A(RAWs,P)
inj=[]
for (cx,cy,nom) in ((828,1157,'taca az255 r289'),(1250,1050,'est az~350 r~255'),(900,700,'nord-oest az~110 r~315')):
    e=np.exp(-((X-cx)**2+(Y-cy)**2)/(2*50.0**2)); use=(e>0.05)&(rr<430)
    for amp in (-0.03,0.03):
        g=amp*e; RAWi=RAWs*(1+g); Pi=P+(f0(RAWs*(1+g))-f0(RAWs))   # la mateixa taca lunar al RAW i al revelat (a través de la corba)
        ci,_=pipeline_A(RAWi,Pi); resp=ci-cand0; esperat=Pi-P
        gain=float(np.sum(resp[use]*esperat[use])/np.sum(esperat[use]**2))
        # també l'S8 històric sobre la mateixa injecció (referència: què feia el vel antic)
        Ls,Wi=s8_eval(Pi[300:1700,300:1700].copy(),edge); s8resp=(Pi[300:1700,300:1700]-Wi)-(P14-Ws8); u14=use[300:1700,300:1700]; e14=esperat[300:1700,300:1700]
        gain_s8=float(np.sum(s8resp[u14]*e14[u14])/np.sum(e14[u14]**2))
        row=dict(posicio=nom,centre_roi=[cx,cy],amplitud=amp,sigma=50,gain_A_add=round(gain,3),passa_090_110=bool(0.9<=gain<=1.1),gain_S8_historic=round(gain_s8,3)); inj.append(row); print(row,flush=True)
out['injeccions']=inj; out['totes_passen_A_add']=all(r['passa_090_110'] for r in inj)
json.dump(out,open(S4+'/fb12_injeccions.json','w'),indent=1,ensure_ascii=False); print('fet')
