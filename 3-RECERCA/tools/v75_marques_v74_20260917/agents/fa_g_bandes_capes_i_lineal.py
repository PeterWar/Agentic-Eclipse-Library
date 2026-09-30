import numpy as np, json, sys
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
import fa_lib as F
sys.path.insert(0,F.S4); import compo74 as c
C,a,P=c.recompon(exclou=(222,),retorna_passos=True)
ordre=[l['id'] for l in c.IDX['layers'] if l['visible'] and l['id']!=222]
azi=np.floor(F.AZ*2)/2
def prof_az(L,band,cells): return np.array([float(L[band&(azi==cc)].mean()) for cc in cells])
def fondaria(L,band,cells,az_c,half=1.0):
    p=prof_az(L,band,cells); sm=ndi.gaussian_filter1d(p,12); inm=(cells>=az_c-half)&(cells<=az_c+half)
    return float((p-sm)[inm].min()), float(p[inm].mean()), float(sm[inm].mean())
# HDR lineal (Vixen, sense filtres) en el marc del llenç: finestra 3000, ROI(y,x) -> (y+502, x+501)
H=np.load(F.OLD+'/corona_hdr_3000.npy'); V=np.load(F.OLD+'/corona_valid_3000.npy')
Hroi=H[502:2502,501:2501].astype(np.float64); Vroi=V[502:2502,501:2501]&(Hroi>0)
lnH=np.where(Vroi,np.log(np.maximum(Hroi,1e-6)),np.nan)
def prof_az_nan(A,band,cells): return np.array([float(np.nanmean(A[band&(azi==cc)])) for cc in cells])
res={}
# --- bandes: m2 (az 109, r 465-471), m4 (az 153, r 476-480), m3 flanc (az 123.5, r 470-474)
for nom,(azc,r0,r1,w) in {'m2_banda_az109':(109.0,465,471,1.0),'m4_banda_az153':(153.5,476,480,1.5),'m3_flanc_az123':(123.5,470,474,1.0),'m3_flanc_az109':(109.0,470,474,1.0)}.items():
    band=(F.RR>=r0)&(F.RR<=r1); cells=np.arange(np.floor((azc-25)*2)/2,azc+25,0.5)
    d={'r':[r0,r1],'az_c':azc,'per_capa':{}}
    for lid in ordre:
        f,pm,sm=fondaria(F.Lstar(P[lid][0]),band,cells,azc,w); d['per_capa'][lid]=dict(nom=c.LAYERS[lid]['name'][:24],dev_min=f,L_marca=pm,L_suau=sm)
    p=prof_az_nan(lnH,band,cells); ok=np.isfinite(p); sm=ndi.gaussian_filter1d(np.nan_to_num(p,nan=np.nanmean(p)),12); inm=(cells>=azc-w)&(cells<=azc+w)
    d['lineal_vixen']=dict(dev_min_ln=float((p-sm)[inm].min()),pct=float((np.exp((p-sm)[inm].min())-1)*100),n_valid=int(ok.sum()),n_cells=int(len(cells)))
    # extensió radial de la banda a l'HDR lineal i al final: dev a az_c per anells de 4 px de 459 a 520
    ext=[]
    Lf=F.Lstar(C)
    for ra in range(459,521,4):
        b=(F.RR>=ra)&(F.RR<ra+4); pf=prof_az(Lf,b,cells); pl=prof_az_nan(lnH,b,cells)
        smf=ndi.gaussian_filter1d(pf,12); sml=ndi.gaussian_filter1d(np.nan_to_num(pl,nan=np.nanmean(pl)),12)
        ext.append(dict(r=ra,dev_final=float((pf-smf)[inm].min()),dev_lineal_pct=float((np.exp((pl-sml)[inm].min())-1)*100)))
    d['extensio_radial']=ext; res[nom]=d
    print('==',nom); [print('  %4d %-24s dev %+6.2f  L %.1f / suau %.1f'%(lid,x['nom'],x['dev_min'],x['L_marca'],x['L_suau'])) for lid,x in d['per_capa'].items()]
    print('  LINEAL Vixen: dev %+.3f ln = %+.1f %%  (valid %d/%d)'%(d['lineal_vixen']['dev_min_ln'],d['lineal_vixen']['pct'],d['lineal_vixen']['n_valid'],d['lineal_vixen']['n_cells']))
    print('  extensió radial: '+' '.join('r%d:%+.1f/%+.0f%%'%(e['r'],e['dev_final'],e['dev_lineal_pct']) for e in ext))
# --- sector fosc SW (m7): L*(az 230-250) − L*(az 205-215) a r 459-470, per capa i lineal
band=(F.RR>=459)&(F.RR<=470); sA=band&(F.AZ>=230)&(F.AZ<=250); sB=band&(F.AZ>=205)&(F.AZ<=215)
d={'per_capa':{}}
for lid in ordre:
    L=F.Lstar(P[lid][0]); d['per_capa'][lid]=dict(nom=c.LAYERS[lid]['name'][:24],L_sector=float(L[sA].mean()),L_ref=float(L[sB].mean()),contrast=float(L[sA].mean()-L[sB].mean()))
d['lineal_vixen']=dict(ratio=float(np.nanmean(Hroi[sA&Vroi])/np.nanmean(Hroi[sB&Vroi])),pct=float((np.nanmean(Hroi[sA&Vroi])/np.nanmean(Hroi[sB&Vroi])-1)*100))
res['m7_sector_230_250_vs_205_215']=d
print('== m7 sector'); [print('  %4d %-24s sector %.1f ref %.1f contrast %+.1f'%(lid,x['nom'],x['L_sector'],x['L_ref'],x['contrast'])) for lid,x in d['per_capa'].items()]; print('  LINEAL Vixen ratio %.3f (%+.1f %%)'%(d['lineal_vixen']['ratio'],d['lineal_vixen']['pct']))
# --- solcs al limbe (r 459-467 vs 470-485) per capa a az 111, 129, 150, 156, 168, 171, 174, 177
azi1=np.floor(F.AZ); b_in=(F.RR>=459)&(F.RR<=467); b_out=(F.RR>=470)&(F.RR<=485)
d={}
for A in (102,111,123,129,150,156,159,168,171,174,177):
    si=b_in&(azi1==A); so=b_out&(azi1==A); d[A]={}
    for lid in ordre:
        L=F.Lstar(P[lid][0]); d[A][lid]=float(L[si].min()-L[so].mean())
    hi=Hroi[si&Vroi]; ho=Hroi[so&Vroi]; d[A]['lineal_pct']=float((hi.min()/ho.mean()-1)*100) if len(hi) and len(ho) else None
    d[A]['lineal_mean_pct']=float((hi.mean()/ho.mean()-1)*100) if len(hi) and len(ho) else None
res['solcs_limbe']=d
print('== solcs (min L* 459-467 − mitjana 470-485) per capa; columnes = az'); print('  capa   '+' '.join('%6d'%A for A in d))
for lid in ordre: print('  %4d   '%lid+' '.join('%+6.1f'%d[A][lid] for A in d))
print('  lin min%%'+' '.join('%+6.0f'%(d[A]['lineal_pct'] or 0) for A in d)); print('  lin mean%%'+' '.join('%+6.0f'%(d[A]['lineal_mean_pct'] or 0) for A in d))
json.dump(res,open(F.S4+'/fa_g_bandes_capes_i_lineal.json','w'),indent=1)
# --- vista: N limb az 95-135 al 300 %: final V74, HDR lineal (log, mateix retall), amb la banda az 109 i 123.5 marcades
Lf=F.Lstar(C); y0,y1,x0,x1=520,640,760,960; Z=3
def to8(A): return Image.fromarray((np.clip(A[y0:y1,x0:x1],0,1)*255).astype(np.uint8)).resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST)
lg=np.log10(np.maximum(Hroi,1)); v=lg[(F.RR>458)&(F.RR<520)&Vroi]; lo,hi=np.percentile(v,1),np.percentile(v,99); lg8=np.clip((lg-lo)/(hi-lo),0,1); lg8[~Vroi]=0
pan=[to8(C),to8(np.dstack([lg8]*3))]
for im,nom in zip(pan,('final V74','HDR lineal Vixen (log, sense filtres)')):
    d_=ImageDraw.Draw(im)
    for azc,col in ((109,(255,0,255)),(123.5,(0,255,255)),(101.5,(255,255,0))):
        for r in (459,495):
            x=F.CX+r*np.cos(np.radians(azc)); y=F.CY-r*np.sin(np.radians(azc)); d_.ellipse([(x-x0)*Z-3,(y-y0)*Z-3,(x-x0)*Z+3,(y-y0)*Z+3],outline=col)
    d_.text((3,3),nom,fill=(255,255,0))
out=Image.new('RGB',(pan[0].width*2+6,pan[0].height),(40,40,40)); out.paste(pan[0],(0,0)); out.paste(pan[1],(pan[0].width+6,0)); out.save(F.S4+'/v_fa_m2m3_final_vs_lineal.png')
# vista W: az 140-185
y0,y1,x0,x1=760,1060,470,640
pan=[to8(C),to8(np.dstack([lg8]*3)),to8(P[30][0])]
for im,nom in zip(pan,('final V74','HDR lineal Vixen (log)','abans de les fotos de Pere')): ImageDraw.Draw(im).text((3,3),nom,fill=(255,255,0))
out=Image.new('RGB',(pan[0].width*3+12,pan[0].height),(40,40,40)); [out.paste(p,(i*(pan[0].width+6),0)) for i,p in enumerate(pan)]; out.save(F.S4+'/v_fa_m4m5_final_vs_lineal.png')
# vista SW: az 215-260
y0,y1,x0,x1=1260,1460,560,860
pan=[to8(C),to8(np.dstack([lg8]*3))]
for im,nom in zip(pan,('final V74','HDR lineal Vixen (log)')): ImageDraw.Draw(im).text((3,3),nom,fill=(255,255,0))
out=Image.new('RGB',(pan[0].width*2+6,pan[0].height),(40,40,40)); [out.paste(p,(i*(pan[0].width+6),0)) for i,p in enumerate(pan)]; out.save(F.S4+'/v_fa_m7_final_vs_lineal.png')
print('vistes ok')
