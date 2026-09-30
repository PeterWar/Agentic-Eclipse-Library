"""fd4: injeccions pròpies sobre el pipeline candidat del lector B (A_add, W pel punt fix): posicions, mides i amplituds diferents de les seves;
i dues proves que ell no fa: bombolla NOMÉS al revelat P (defecte tipus ρ) i bombolla NOMÉS al RAW (el model injecta estructura del RAW?)."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad')
from fb6_candidata import *          # RAWs, P(G69+Wdq), G69, F71, ajusta_f, vel_lineal, kappa, rr, X, Y, d ...
from scipy.ndimage import gaussian_filter
Wst=np.load(S4+'/fb14_W_s8_puntfix.npy').astype(np.float64); Pst=G69+Wst; kap=kappa(); disc=rr<430
m=np.isfinite(np.load(S4+'/fb5_raw10s_abs_roi.npy'))
def suau(A,s): mm=m.astype(float); return gaussian_filter(np.nan_to_num(A)*mm,s)/np.maximum(gaussian_filter(mm,s),1e-9)
def pipeline_A(RAWs_,P_,W_):
    f,finv,xc,yi=ajusta_f(RAWs_,P_); Vdev,ringmed,Vl=vel_lineal(RAWs_); L0=suau(RAWs_,15); D=f(L0)-f(L0-Vdev)
    return (P_-W_+kap*(W_-D)), f, D
cand0,f0,D0=pipeline_A(RAWs,Pst,Wst)
chk=np.load(S4+'/fb14_candidata.npz'); print('reproducció de la candidata de B (cand69): |dif| màx %.2f DN16'%np.abs(cand0-chk['cand69'])[disc].max())
out={'reproduccio_cand69_maxdif':float(np.abs(cand0-chk['cand69'])[disc].max())}
pos={'taca az255 r289':(828,1157),'centre':(999,998),'limbe az200 r400':(623,1135),'est az0 r300':(1299,998),'nord az90 r350':(999,648),'sud az270 r200':(999,1198)}
inj=[]
for nom,(cx,cy) in pos.items():
    for sig in (25,50,80):
        for amp in (-0.03,0.02):
            e=np.exp(-((X-cx)**2+(Y-cy)**2)/(2*sig**2)); use=(e>0.05)&(rr<430); g=amp*e
            Pi=Pst+(f0(RAWs*(1+g))-f0(RAWs)); ci,_,_=pipeline_A(RAWs*(1+g),Pi,Wst); resp=ci-cand0; esp=Pi-Pst
            gain=float(np.sum(resp[use]*esp[use])/np.sum(esp[use]**2)); fora=(e<0.01)&(rr<430)
            row=dict(posicio=nom,sigma=sig,amplitud=amp,gain=round(gain,3),passa=bool(0.9<=gain<=1.1),fuita_fora_p99_DN16=round(float(np.percentile(np.abs(resp[fora]),99)),1),esp_amplitud_DN16=round(float(np.abs(esp[use]).max()),0))
            inj.append(row); print(row,flush=True)
out['injeccions_RAW_i_P']=inj; out['n_passen']=sum(r['passa'] for r in inj); out['n_total']=len(inj)
# bombolla NOMÉS a P (defecte del revelat): el pipeline la deixa (gain 1) → no cura ρ
sol=[]
for nom,(cx,cy) in (('taca az255 r289',(828,1157)),('est az0 r300',(1299,998))):
    e=np.exp(-((X-cx)**2+(Y-cy)**2)/(2*50.0**2)); use=(e>0.05)&(rr<430)
    for amp in (-0.03,):
        Pi=Pst*(1+amp*e); ci,_,_=pipeline_A(RAWs,Pi,Wst); resp=ci-cand0; esp=Pi-Pst
        gain=float(np.sum(resp[use]*esp[use])/np.sum(esp[use]**2)); sol.append(dict(prova='nomes_P',posicio=nom,amplitud=amp,sigma=50,gain=round(gain,3)))
    # bombolla NOMÉS al RAW (cap canvi a P): quant en posa el model a la capa?
    for amp in (-0.03,0.03):
        g=amp*e; ci,_,Di=pipeline_A(RAWs*(1+g),Pst,Wst); resp=ci-cand0
        # el que hauria canviat P si la bombolla fos real: f0(RAWs(1+g))−f0(RAWs)
        esp=f0(RAWs*(1+g))-f0(RAWs); gain=float(np.sum(resp[use]*esp[use])/np.sum(esp[use]**2))
        sol.append(dict(prova='nomes_RAW',posicio=nom,amplitud=amp,sigma=50,resposta_mediana_DN16=round(float(np.median(resp[use])),1),resposta_max_abs_DN16=round(float(np.abs(resp[use]).max()),1),gain_respecte_f_RAW=round(gain,3),nivell_P=round(float(np.median(Pst[use])),0)))
print(sol); out['proves_nomes_P_nomes_RAW']=sol
# de què és fet D (la correcció)? estructura per escales i correlació amb el RAW σ15 i amb la LROC
def band(a,lo,hi,msk):
    mm_=msk.astype(float); return (gaussian_filter(a*mm_,lo)/np.maximum(gaussian_filter(mm_,lo),1e-9))-(gaussian_filter(a*mm_,hi)/np.maximum(gaussian_filter(mm_,hi),1e-9))
mk=disc&(rr<400)&(rr>60); L0=suau(RAWs,15)
esc={}
for lo,hi in ((3,8),(8,32),(32,120)):
    bD=band(D0,lo,hi,disc); bP=band(Pst,lo,hi,disc); bR=band(L0,lo,hi,disc)
    esc[f'{lo}-{hi}']=dict(std_D_DN16=round(float(bD[mk].std()),1),std_P_DN16=round(float(bP[mk].std()),1),corr_D_amb_RAWs15=round(float(np.corrcoef(bD[mk],bR[mk])[0,1]),3),corr_D_amb_P=round(float(np.corrcoef(bD[mk],bP[mk])[0,1]),3))
out['D_per_escales']=esc; print(esc)
json.dump(out,open(S4+'/fd4_injeccions.json','w'),indent=1,ensure_ascii=False); print('fd4 fet')
