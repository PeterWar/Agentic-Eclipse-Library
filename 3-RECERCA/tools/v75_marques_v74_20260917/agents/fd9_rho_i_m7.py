"""fd9: (a) el residu ρ = P − f(RAW) de B és un operador de contrast local (hipòtesi 'Claridad de Pere')? correlació de ρ amb el passabanda de P a diverses escales, a tot el disc i a la taca.
(b) m7: contrast sector fosc (az 227–255) − referència (az 205–215) a r 459–470, L* final i lineal Vixen (mesura pròpia)."""
import numpy as np, json
from scipy.ndimage import gaussian_filter
import fd_lib as F
disc=F.RR<430; res={}
rho=np.load(F.S4+'/fb5_residu.npy').astype(np.float64); P=np.load(F.S4+'/fb3_P_rec.npy').astype(np.float64); fR=np.load(F.S4+'/fb5_fRAW.npy').astype(np.float64)
m6=F.mask('m6'); e6=F.mask('ent_m6'); ok=disc&np.isfinite(rho)&np.isfinite(P)&(F.RR>60)
def sm(A,s): mm=ok.astype(float); return gaussian_filter(np.nan_to_num(A)*mm,s)/np.maximum(gaussian_filter(mm,s),1e-9)
res['rho_stats']=dict(mediana=float(np.median(rho[ok])),std=float(rho[ok].std()),mediana_taca=float(np.median(rho[m6&ok])),mediana_entorn=float(np.median(rho[e6&ok])),p_rms_bandpass=None)
corr={}
for s in (10,20,40,80,150):
    hp=fR-sm(fR,s)   # estructura de f(RAW) (el que un operador de contrast local amplificaria)
    r_all=float(np.corrcoef(rho[ok],hp[ok])[0,1]); slope=float(np.sum(rho[ok]*hp[ok])/np.sum(hp[ok]**2))
    r_taca=float(np.corrcoef(rho[(m6|e6)&ok],hp[(m6|e6)&ok])[0,1])
    corr[s]=dict(corr_disc=round(r_all,3),pendent=round(slope,3),corr_taca=round(r_taca,3)); print('σ %3d: corr(ρ, f(RAW)−suau) disc %.3f pendent %.3f | taca %.3f'%(s,r_all,slope,r_taca))
res['rho_vs_passabanda_fRAW']=corr
# ρ suau (σ20) per sectors i anells: és una depressió localitzada a la taca o un camp general?
r20=sm(rho,20); sec=(F.AZ//30).astype(int)
res['rho_s20_per_sector30_r250_330']={int(s):round(float(np.median(r20[(sec==s)&ok&F.anell(250,330)])),0) for s in range(12)}
print('ρ σ20 per sector 30° (r 250–330):',res['rho_s20_per_sector30_r250_330'])
res['rho_s20_taca_menys_entorn_aparellat']=None
vals=[]
for r0 in np.arange(170,412,4):
    ring=F.anell(r0,r0+4); a=m6&ring&ok; b=e6&ring&ok
    if a.sum()>=20 and b.sum()>=20: vals.append(float(np.median(r20[a])-np.median(r20[b])))
res['rho_s20_taca_menys_entorn_aparellat']=round(float(np.median(vals)),0); print('ρ σ20 taca − entorn aparellat: %.0f DN16 (nivell P a la taca %.0f)'%(res['rho_s20_taca_menys_entorn_aparellat'],np.median(P[m6&ok])))
# (b) m7
c74=F.compo74(); C74,_=c74.recompon(exclou=(222,)); L74=F.Lstar(C74)
H=np.load(F.OLD+'/corona_hdr_3000.npy'); V=np.load(F.OLD+'/corona_valid_3000.npy'); Hroi=H[502:2502,501:2501].astype(np.float64); Vroi=V[502:2502,501:2501]&(Hroi>0)
band=F.anell(459,471); sA=band&F.sector(227,255); sB=band&F.sector(205,215); sC=band&F.sector(260,275)
res['m7']=dict(L_sector=float(np.median(L74[sA])),L_ref_205_215=float(np.median(L74[sB])),L_ref_260_275=float(np.median(L74[sC])),lineal_ratio_vs_205_215=float(np.median(Hroi[sA&Vroi])/np.median(Hroi[sB&Vroi])),lineal_ratio_vs_260_275=float(np.median(Hroi[sA&Vroi])/np.median(Hroi[sC&Vroi])))
print('m7:',res['m7'])
F.dump('fd9_rho_i_m7',res); print('fd9 fet')
