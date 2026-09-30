"""fd6: quin és el factor real V69→V71/V74 de la capa 30? contra els quatre vel_corr_*.npy de l'OLD; i quant del canvi per sectors de la candidata
és només el desajust de F71. També: on difereix la màscara (c-2) de la capa 30 entre V69 i V74."""
import numpy as np, json
from scipy.ndimage import gaussian_filter
import fd_lib as F
disc=F.RR<430
d74=np.load(F.S4+'/roi74p_L30.npz'); d69=np.load(F.OLD+'/roi_L30.npz'); G74=d74['c1'].astype(np.float64); G69=d69['c1'].astype(np.float64)
mk=disc&(G69>500); q=np.where(mk,G74/np.maximum(G69,1),1.0); qs=gaussian_filter(q*mk,6)/np.maximum(gaussian_filter(mk.astype(float),6),1e-9)
res={}
for nom in ('vel_corr_final','vel_corr_final_hdr','vel_corr_base','vel_corr_hdr'):
    Fx=np.load(F.OLD+f'/{nom}.npy').astype(np.float64)
    dd=(G74-np.rint(G69*Fx))[mk]; res[nom]=dict(mediana=float(np.median(dd)),p99abs=float(np.percentile(np.abs(dd),99)),max=float(np.abs(dd).max()),ln_ratio_p1_p99=[float(np.percentile(np.log(qs[mk]/Fx[mk]),1)),float(np.percentile(np.log(qs[mk]/Fx[mk]),99))])
    print(nom,res[nom])
# el factor real (quocient suau) vs F71 usat per B, per sectors de 10°
F71=np.load(F.OLD+'/vel_corr_final.npy').astype(np.float64); sec=(F.AZ//10).astype(int)
ps={int(s):round(float(np.median(np.log(qs/np.maximum(F71,1e-6))[(sec==s)&mk&(F.RR>100)])),4) for s in range(36)}
res['ln_Freal_sobre_F71_per_sector']=ps; print('ln(F_real/F71) per sector 10°:',ps)
# candidata: Δln per sector (mesurat a fd2) vs el desajust: quina part és el desajust?
cd=np.load(F.S4+'/roi75_L30_candidata.npz'); Gc=cd['c1'].astype(np.float64); dl=np.log(np.maximum(Gc,1))-np.log(np.maximum(G74,1))
pc={int(s):round(float(np.median(dl[(sec==s)&mk&(F.RR>100)])),4) for s in range(36)}
res['dln_candidata_per_sector']=pc
# si la candidata s'hagués fet amb el factor real: cand69·Freal en comptes de cand69·F71 → Δln corregit = dl − ln(F71/Freal) = dl + ln(Freal/F71)
pcc={s:round(pc[s]+ps[s],4) for s in pc}; res['dln_candidata_amb_factor_real_per_sector']=pcc
print('Δln candidata per sector:',pc); print('Δln candidata si F fos el real:',pcc)
print('max |Δln| sector: candidata %.3f, amb factor real %.3f'%(max(abs(v) for v in pc.values()),max(abs(v) for v in pcc.values())))
# gran escala σ60 del desajust sol
lnq=np.log(np.maximum(qs,1e-6))-np.log(np.maximum(F71,1e-6)); d60=gaussian_filter(lnq*disc,60)/np.maximum(gaussian_filter(disc.astype(float),60),1e-9)
res['s60_desajust_F71']=dict(max=float(np.abs(d60[disc&(F.RR>60)]).max()),rms=float(np.sqrt(np.mean(d60[disc&(F.RR>60)]**2))))
print('σ60 del desajust F71:',res['s60_desajust_F71'])
# màscara c-2 V69 vs V74
m69=d69['c-2'].astype(np.int64); m74=d74['c-2'].astype(np.int64); dm=m74-m69; dif=dm!=0
res['masc_dif']=dict(n_pixels=int(dif.sum()),max_abs=int(np.abs(dm).max()),n_gt_655=int((np.abs(dm)>655).sum()))
if dif.any():
    res['masc_dif']['r_min_max']=[float(F.RR[dif].min()),float(F.RR[dif].max())]; res['masc_dif']['az_hist_30']={int(a):int((dif&F.sector(a,a+30)).sum()) for a in range(0,360,30)}
    big=np.abs(dm)>655
    if big.any(): res['masc_dif']['gran_r_min_max']=[float(F.RR[big].min()),float(F.RR[big].max())]; res['masc_dif']['gran_az_hist_30']={int(a):int((big&F.sector(a,a+30)).sum()) for a in range(0,360,30)}
print('màscara 30 V74−V69:',res['masc_dif'])
F.dump('fd6_factor71',res); print('fd6 fet')
