"""fd5: (1) de qui és la vora de la capa 30: alfa pròpia (c-1) o màscara d'usuari (c-2)? per sectors; V69/V71/V74.
(2) premissa de B: capa74 = capa69·F71 (±1 DN16)? contra V71 (NEW) i V69 (OLD). (3) taca al RAW absolut (fb5) amb el meu aparellament per anells."""
import numpy as np, json
from scipy.ndimage import gaussian_filter
import fd_lib as F
res={}
d74=np.load(F.S4+'/roi74p_L30.npz'); d71=np.load(F.NEW+'/roi71_L30.npz'); d69=np.load(F.OLD+'/roi_L30.npz')
for nom,d in (('V74',d74),('V71',d71),('V69',d69)):
    a=d['c-1'].astype(np.float32)/65535; m=d['c-2'].astype(np.float32)/65535 if 'c-2' in d else None
    q=dict(claus=d.files,alfa_min_max=[float(a.min()),float(a.max())],alfa_frac_1=float((a>=0.999).mean()),alfa_frac_0=float((a<=0.001).mean()))
    if m is not None: q.update(masc_min_max=[float(m.min()),float(m.max())],masc_frac_1=float((m>=0.999).mean()),masc_frac_0=float((m<=0.001).mean()),masc_valors_unics=int(len(np.unique(d['c-2'][::7,::7]))))
    rb=np.arange(436,476); vor={}
    for A0 in list(range(0,132,8))+list(range(160,212,4))+list(range(296,360,8)):
        s=F.sector(A0,A0+4)
        def r50(arr):
            p=np.array([float(arr[s&F.anell(r,r+1)].mean()) for r in rb])
            for i in range(len(p)-1):
                if p[i]>=0.5>p[i+1]: return round(float(rb[i]+(p[i]-0.5)/(p[i]-p[i+1])),1)
            return None
        vor[A0]=dict(r50_alfa_propia=r50(a),r50_masc=r50(m) if m is not None else None,alfa_propia_r457_462=round(float(a[s&F.anell(457,462)].mean()),3),masc_r457_462=round(float(m[s&F.anell(457,462)].mean()),3) if m is not None else None,
                     alfa_propia_r448_452=round(float(a[s&F.anell(448,452)].mean()),3),masc_r448_452=round(float(m[s&F.anell(448,452)].mean()),3) if m is not None else None)
    q['vores']=vor; res[nom]=q
    print('==',nom,{k:v for k,v in q.items() if k!='vores'})
    print('az | r50 alfa pròpia | r50 màscara | alfa pròpia 457-462 | màscara 457-462 | alfa pròpia 448-452 | màscara 448-452')
    for A0,v in vor.items(): print('%3d | %6s | %6s | %.3f | %s | %.3f | %s'%(A0,v['r50_alfa_propia'],v['r50_masc'],v['alfa_propia_r457_462'],v['masc_r457_462'],v['alfa_propia_r448_452'],v['masc_r448_452']))
# la màscara c-2 de V74 és igual a la de V71 i V69?
res['masc_V74_eq_V71']=bool((d74['c-2']==d71['c-2']).all()); res['masc_V74_eq_V69']=bool((d74['c-2']==d69['c-2']).all()) if 'c-2' in d69 else None
res['alfa_V74_eq_V71']=bool((d74['c-1']==d71['c-1']).all()); res['alfa_V74_eq_V69']=bool((d74['c-1']==d69['c-1']).all())
print('masc V74==V71',res['masc_V74_eq_V71'],'V74==V69',res['masc_V74_eq_V69'],'| alfa V74==V71',res['alfa_V74_eq_V71'],'V74==V69',res['alfa_V74_eq_V69'])
# (2) premissa de B
disc=F.RR<430; F71=np.load(F.OLD+'/vel_corr_final.npy').astype(np.float64)
G74=d74['c1'].astype(np.float64); G71=d71['c1'].astype(np.float64); G69=d69['c1'].astype(np.float64)
for nom,a,b in (('G74-G71',G74,G71),('G71-G69xF71',G71,np.rint(G69*F71)),('G74-G69xF71',G74,np.rint(G69*F71)),('G74-G69',G74,G69)):
    dd=(a-b)[disc&(G69>0)]; res[nom]=dict(mediana=float(np.median(dd)),p99abs=float(np.percentile(np.abs(dd),99)),max=float(np.abs(dd).max()))
    print(nom,res[nom])
# el quocient G74/G69 és suau? (=un factor) o té gra
q=G74/np.maximum(G69,1); mk=disc&(G69>500)
res['quocient_G74_G69']=dict(p1=float(np.percentile(q[mk],1)),p50=float(np.percentile(q[mk],50)),p99=float(np.percentile(q[mk],99)),std_residu_s6=float((q-gaussian_filter(q,6))[mk].std()))
print('G74/G69:',res['quocient_G74_G69'])
# (3) taca al RAW absolut
RAW=np.load(F.S4+'/fb5_raw10s_abs_roi.npy').astype(np.float64); v=np.isfinite(RAW)&(RAW>0)
m6=F.mask('m6'); e6=F.mask('ent_m6')
def s6(A,msk):
    mm=msk.astype(float); return gaussian_filter(np.nan_to_num(A)*mm,6)/np.maximum(gaussian_filter(mm,6),1e-9)
a=s6(np.where(v,RAW,0),v&disc); vals=[]
for r0 in np.arange(170,412,4):
    ring=F.anell(r0,r0+4); md=m6&ring&v; ed=e6&ring&v
    if md.sum()>=20 and ed.sum()>=20: vals.append(np.log(np.median(a[md])/np.median(a[ed])))
vals=np.array(vals); n=len(vals)
res['raw_abs_taca']=dict(anells=round(float(np.median(vals)),4),tercos=[round(float(np.median(vals[:n//3])),4),round(float(np.median(vals[n//3:2*n//3])),4),round(float(np.median(vals[2*n//3:])),4)],masc=round(float(np.log(np.median(a[m6&v])/np.median(a[e6&v]))),4),nivell=float(np.median(RAW[m6&v])))
print('RAW abs taca:',res['raw_abs_taca'])
F.dump('fd5_capa30_alfa',res); print('fd5 fet')
