"""CORONA (tasca B), pas 2: projecta l'HDR del sensor al marc del llenç (escala 456/R, gir +11°), tria l'escala per correlació amb el compost,
desa corona_hdr_3000.npy / corona_valid_3000.npy / corona_hdr_log.png i calcula els perfils radial i azimutal."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
from scipy.ndimage import map_coordinates, gaussian_filter, zoom, rotate
from PIL import Image
D=np.load(SP+'/corona_hdr_sensor_half.npz'); HDR=D['hdr'].astype(np.float32); VAL=D['valid']; NVAL=D['nval']; cx,cy,R2972=float(D['cx']),float(D['cy']),float(D['R'])
J=json.load(open(SP+'/corona_1_sensor.json')); ANG=11.0
# residu per caixa després de l'alineació (comprovació de la linealitat un cop alineat)
for f,aj in J['ajust_lineal'].items():
    if 'caixes_curt_llarg_n' in aj:
        a,b=aj['a_DN16_s'],aj['b']; print('després d\'alinear %s/%s, quocient per caixa (nivell curt DN16/s → q):'%(f[4:8],aj['respecte'][4:8]),[(int(X),round(((Y-a)/b)/X,4)) for X,Y,n in aj['caixes_curt_llarg_n']])
def projecta(img,esc,ang,cxo,cyo,H,W,order=1,cval=0.0):
    """Sortida (H,W) amb el centre lunar a (cxo,cyo); equival a zoom(esc) + rotate(ang, reshape=False) (antihorari a pantalla) al voltant del centre lunar."""
    yy,xx=np.mgrid[0:H,0:W].astype(np.float64); X=xx-cxo; Y=yy-cyo; t=np.deg2rad(ang)
    x=X*np.cos(t)-Y*np.sin(t); y=X*np.sin(t)+Y*np.cos(t)
    return map_coordinates(img,[cy+y/esc,cx+x/esc],order=order,mode='constant',cval=cval)
# 1) verificació del conveni contra zoom+rotate d'a15 (patró sintètic: dues taques)
S=400; im=np.zeros((S,S),np.float32); c=S//2; im[c-2:c+3,c+100-2:c+100+3]=1; im[c-100-2:c-100+3,c-2:c+3]=1
z=zoom(im,2.04,order=1); r=rotate(z,ANG,reshape=False,order=1); cz=(np.array(r.shape)-1)/2
_cx,_cy=cx,cy; cx,cy=float(c),float(c); p=projecta(im,2.04,ANG,cz[1],cz[0],r.shape[0],r.shape[1]); cx,cy=_cx,_cy
from scipy.ndimage import center_of_mass, label
def taques(a):
    lab,n=label(a>0.3); return sorted([tuple(round(v,1) for v in center_of_mass(a,lab,k)) for k in range(1,n+1)])
print('verificació conveni: zoom+rotate →',taques(r),' projecta →',taques(p),' corr %.4f'%np.corrcoef(r.ravel(),p.ravel())[0,1])
# 2) ESCALA: 456/R mesurat al 2972 (mateix fotograma que dona el centre). El 223,5 del 2983 (a10) és la silueta menjada pel glow dels 10 s:
#    els curts (1/30, 1/8, 0,5 s) donen 225,6–225,7 al 50 % (corona_3_escala.json), com la silueta 456,0 del compost (50 % de la capa de perles).
#    La correlació per bandes amb el compost (600–950 px) prefereix 2,005–2,01 amb desplaçaments ≤2 px (dins del registre intern del compost); a 2,04 deriva 3 px.
Rc=np.load(SP+'/roi_recomp.npz'); Lc=Rc['C'].astype(np.float32).mean(-1)/65535; CXp,CYp=998.88,998.41
yy,xx=np.mgrid[0:2000,0:2000]; rp=np.hypot(xx-CXp,yy-CYp); anell=(rp>480)&(rp<950)
hp=lambda a,s1,s2: gaussian_filter(a,s1)-gaussian_filter(a,s2)
Hc=hp(Lc,3,25); ESC=456.0/R2972; tria='2972'; res_esc=json.load(open(SP+'/corona_3_escala.json'))['xcorr']; cc={}; cands={'2972':ESC,'2983':456.0/J['centres']['572A2983.CR3']['R']}
print('ESCALA: 456/R2972 = %.4f (R2972 = %.2f half)'%(ESC,R2972))
# 3) projecció final 3000×3000 centrada al centre lunar del 2972 (píxel 1500,1500), finestra font 1600×1600 half (±800 px del centre)
H=W=3000; C0=1500.0
Wn=np.zeros_like(HDR,bool); y0,y1=int(round(cy))-800,int(round(cy))+800; x0,x1=int(round(cx))-800,int(round(cx))+800; Wn[max(y0,0):y1,max(x0,0):x1]=True
hdr3=projecta(HDR,ESC,ANG,C0,C0,H,W).astype(np.float32)
val3=(projecta((VAL&Wn).astype(np.float32),ESC,ANG,C0,C0,H,W)>0.999)
nv3=projecta(NVAL.astype(np.float32),ESC,ANG,C0,C0,H,W,order=0).astype(np.int8)
yy,xx=np.mgrid[0:H,0:W]; rr=np.hypot(xx-C0,yy-C0); az=np.rad2deg(np.arctan2(-(yy-C0),xx-C0))%360
hdr3[rr<456]=0; val3&=np.isfinite(hdr3); hdr3[~val3]=0
np.save(SP+'/corona_hdr_3000.npy',hdr3); np.save(SP+'/corona_valid_3000.npy',val3)
# PNG en log (llenç sencer 3000×3000): log10 entre p0,5 dels vàlids fora del disc i el màxim
v=hdr3[val3&(rr>=456)]; lo,hi=np.log10(max(np.percentile(v,0.5),1)),np.log10(v.max()); L8=np.clip((np.log10(np.maximum(hdr3,1))-lo)/(hi-lo),0,1); L8[~val3]=0
Image.fromarray(np.uint8(L8*255)).save(SP+'/corona_hdr_log.png')
# vista de comprovació (ROI 2000×2000): passa-alt HDR (vermell) vs passa-alt compost (verd) a l'escala triada
P=projecta(HDR,ESC,ANG,CXp,CYp,2000,2000); Hh=hp(np.log10(np.maximum(P,1)),3,25)
def n8(a,m): s=np.std(a[m]); return np.uint8(np.clip(a/(4*s)+0.5,0,1)*255)
chk=np.dstack([n8(Hh,anell),n8(Hc,anell),np.zeros((2000,2000),np.uint8)]); Image.fromarray(chk).save(SP+'/corona_check_compost.png')
# 4) perfils
perfil_radial=[]
for r0 in range(460,1400,20):
    m=val3&(rr>=r0)&(rr<r0+20); perfil_radial.append([r0+10,float(np.median(hdr3[m])) if m.sum()>50 else None])
m_az=val3&(rr>=470)&(rr<520); sec=(az//10).astype(int); paz=np.array([np.median(hdr3[m_az&(sec==k)]) for k in range(36)]); paz_n=paz/np.median(paz)
contrib=[]
for r0 in range(456,1500,40):
    m=(rr>=r0)&(rr<r0+40); contrib.append([r0,r0+40,round(float(val3[m].mean()),3),round(float(nv3[m&val3].mean()),2) if (m&val3).any() else None])
out=dict(escala=ESC,escala_tria='456/R'+tria,R_half={k:v['R'] for k,v in J['centres'].items()},angle=ANG,centre_half_2972=[cx,cy],centre_sortida=[C0,C0],
         escombratge=res_esc,escales_candidates=cands,perfil_radial=perfil_radial,perfil_azimutal_36=[round(float(x),4) for x in paz_n],
         perfil_azimutal_36_abs=[float(x) for x in paz],contribucio_llenc=contrib,
         nivell_p50_fora_disc=float(np.median(v)),max=float(v.max()),fraccio_valida_fora_disc=float(val3[rr>=456].mean()),
         sat_dins_llenc={'r<1500':float((~val3)[(rr>=456)&(rr<1500)].mean())})
json.dump(out,open(SP+'/corona_2_projecta.json','w'),indent=1)
print('perfil radial (r, mediana DN16/s):',[(r,round(v,1) if v else None) for r,v in perfil_radial])
print('perfil azimutal 36 (470–520, normalitzat):',[round(float(x),3) for x in paz_n])
print('contribució per anell llenç [r0,r1,fracció vàlida,nre. fotogrames mitjà]:',contrib)
print('p50 fora disc %.1f · max %.0f · fracció vàlida fora disc %.4f'%(np.median(v),v.max(),val3[rr>=456].mean()))
print('fet')
