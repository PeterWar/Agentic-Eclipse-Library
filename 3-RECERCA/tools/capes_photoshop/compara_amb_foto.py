import numpy as np, cv2, tifffile, sys, math
sys.path.insert(0,"/Users/USUARI/Downloads/Eclipse 2026/research/tools"); import hdr_corona_vixen as M
SCR="/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad"
with tifffile.TiffFile("/Users/USUARI/Downloads/UnintCapes3.tif") as t:
    P=t.pages[0].asarray().astype(np.float32)/65535.0        # 4640×6960 (Sol al centre 3480,2320 aprox)
Fo=tifffile.imread(M.OUT/"corona_vixen_FOTO.tif").astype(np.float32)/65535.0   # retallada
# posa la meva a la mateixa reixa 4640×6960 (la meva reixa és 4638×6958; +1 de marge)
F=np.full_like(P,np.nan); F[M.RETALL[0]+1:M.RETALL[1]+2, M.RETALL[2]+1:M.RETALL[3]+2]=Fo
H,W,_=P.shape; cy,cx=2319+1,3479+1
yy=(np.arange(H)-cy)[:,None]; xx=(np.arange(W)-cx)[None,:]
rs=np.hypot(xx,yy)/M.R_SOL_PX; th=np.degrees(np.arctan2(-yy,xx))%360
NA=4096
def bandes(img,r0,r1):
    nr=int(min(H,W)/2)
    pol=cv2.warpPolar(np.nan_to_num(img).astype(np.float32),(nr,NA),(cx,cy),float(nr),cv2.INTER_LINEAR+cv2.WARP_POLAR_LINEAR)
    rr=np.arange(nr)/M.R_SOL_PX; sel=(rr>r0)&(rr<r1)
    b=pol[:,sel].astype(np.float64); b=b/np.maximum(b.mean(0,keepdims=True),1e-12)-1
    Pw=(np.abs(np.fft.rfft(b*np.hanning(NA)[:,None],axis=0))**2).mean(1); esc=2/(NA*(np.hanning(NA)**2).sum())
    return {(lo,hi):math.sqrt(max(Pw[lo:hi].sum()*esc,0)) for lo,hi in [(5,20),(20,60),(60,180),(180,400),(400,900),(900,2000)]}
print("=== nivell (G) i color per radi: PERE vs FOTO ===")
print(f"{'R☉':>4} {'G Pere':>7} {'G FOTO':>7}   {'R/G P':>6} {'R/G F':>6}   {'B/G P':>6} {'B/G F':>6}")
for r0 in (1.1,1.3,1.5,2.0,2.5,3.0,4.0,5.0,6.0,6.8):
    m=(rs>r0-0.05)&(rs<r0+0.05)&np.isfinite(F[...,1])
    gp,gf=np.median(P[...,1][m]),np.median(F[...,1][m])
    print(f"{r0:4.1f} {gp:7.3f} {gf:7.3f}   {np.median(P[...,0][m])/gp:6.3f} {np.median(F[...,0][m])/gf:6.3f}   {np.median(P[...,2][m])/gp:6.3f} {np.median(F[...,2][m])/gf:6.3f}")
print("\n=== contrast per banda azimutal (verd), Pere / FOTO ===")
for r0,r1 in ((1.35,1.65),(2.05,2.55),(3.15,3.85)):
    bp=bandes(P[...,1],r0,r1); bf=bandes(np.nan_to_num(F[...,1]),r0,r1)
    print(f"  {r0}–{r1} R☉: " + "  ".join(f"{360/hi:.1f}–{360/lo:.0f}°: {bp[(lo,hi)]:.4f}/{bf[(lo,hi)]:.4f}" for lo,hi in bp))
print("\n=== anells per sector (residu quadràtic pic-vall del perfil G, finestres de 0,8 R☉) ===")
sect={"dalt":(60,120),"dreta":(-30,30),"baix":(240,300),"esq":(150,210)}
ib=(rs*40).astype(int)
for nom,img in (("PERE",P[...,1]),("FOTO",F[...,1])):
    fila=[]
    for sn,(a,b) in sect.items():
        t=th if a>=0 else np.where(th>180,th-360,th)
        msk=(t>a)&(t<b)&np.isfinite(img)
        prof=np.array([np.nanmean(img[(ib==k)&msk]) if ((ib==k)&msk).sum()>200 else np.nan for k in range(int(6.0*40))])
        res=[]
        for a0,a1 in ((1.4,2.2),(2.2,3.0),(3.0,3.8),(3.8,4.6),(4.6,5.4)):
            seg=prof[int(a0*40):int(a1*40)]; ok=np.isfinite(seg)
            if ok.sum()<10: res.append(np.nan); continue
            x=np.arange(len(seg))[ok]; rr_=seg[ok]-np.polyval(np.polyfit(x,seg[ok],2),x); res.append(100*(rr_.max()-rr_.min())/np.nanmean(seg))
        fila.append(f"{sn}: "+" ".join(f"{v:4.2f}" for v in res))
    print(f"  {nom}: " + " | ".join(fila) + "   (finestres 1,4–2,2 · 2,2–3 · 3–3,8 · 3,8–4,6 · 4,6–5,4)")
# soroll de gra fi (passa-alt de 2 px) al cel i a la corona
for nom,img in (("PERE",P[...,1]),("FOTO",np.nan_to_num(F[...,1]))):
    hp=img-cv2.GaussianBlur(img,(0,0),2)
    out=[]
    for r0,r1 in ((1.3,1.6),(2,2.5),(3.5,4.5)):
        m=(rs>r0)&(rs<r1)&np.isfinite(F[...,1]); out.append(f"{r0}–{r1}: {100*np.std(hp[m])/np.mean(img[m]):.2f} %")
    print(f"  gra fi (2 px) {nom}: "+"  ".join(out))
# previes
cv2.imwrite(f"{SCR}/pere_2400.jpg",cv2.resize((np.clip(P,0,1)*255).astype(np.uint8)[...,::-1],(2400,1600),interpolation=cv2.INTER_AREA),[int(cv2.IMWRITE_JPEG_QUALITY),92])
cy_,cx_=int(cy),int(cx); R=int(M.R_SOL_PX)
Z=[("plomalls",cx_-450,int(cy_-1.05*R-820),900,820),("corona int.",cx_-500,int(cy_-1.75*R),1000,700),("cel 3,5 Rsol",int(cx_+3.1*R),int(cy_-1.2*R),900,600)]
Fh=cv2.FONT_HERSHEY_SIMPLEX; cols=[]
for nom,img in (("PERE",P),("FOTO",np.nan_to_num(F))):
    tir=[]
    for z,x0,y0,w,h in Z:
        c=np.ascontiguousarray((np.clip(img[y0:y0+h,x0:x0+w],0,1)*255).astype(np.uint8)[...,::-1])
        if w!=900: c=cv2.resize(c,(900,int(h*900/w)),interpolation=cv2.INTER_AREA)
        cv2.rectangle(c,(0,0),(900,40),(0,0,0),-1); cv2.putText(c,f"{nom} - {z}",(12,29),Fh,0.8,(255,255,255),2); tir.append(c)
    cols.append(np.concatenate(tir,axis=0))
cv2.imwrite(f"{SCR}/cmp_pere.png",np.concatenate(cols,axis=1)); print("previes ok")
