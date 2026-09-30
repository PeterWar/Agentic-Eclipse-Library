"""Test d'anell independent de la composició: mitjana per anell sobre un
conjunt FIX d'angles (els vàlids fins a r_max_test), residu respecte d'una
quadràtica per finestra."""
import sys, numpy as np, tifffile
sys.path.insert(0,"/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
H,W=4638,6958; cy,cx=H/2,W/2
yy=(np.arange(H)-cy)[:,None]; xx=(np.arange(W)-cx)[None,:]
r=np.hypot(xx,yy); rs=r/M.R_SOL_PX; th=np.arctan2(yy,xx)
R_TEST=6.0
half=min(cy-M.RETALL[0], M.RETALL[1]-cy)/(R_TEST*M.R_SOL_PX)
sect=np.abs(np.sin(th))<half*0.98      # angles vàlids fins a R_TEST
ib=(rs*40).astype(int)
def perfil(nom):
    a=tifffile.imread(M.OUT/nom).astype(np.float32)/65535.0
    g=np.full((H,W),np.nan); g[M.RETALL[0]:M.RETALL[1]+1, M.RETALL[2]:M.RETALL[3]+1]=a[...,1]
    g=np.where(sect,g,np.nan)
    return np.array([np.nanmean(g[ib==k]) if np.isfinite(g[ib==k]).sum()>300 else np.nan for k in range(int(R_TEST*40))])
print(f"sector fix: |sin θ| < {half*0.98:.3f}  (±{np.degrees(np.arcsin(half*0.98)):.0f}° al voltant de 0° i 180°)")
for nom in sys.argv[1:]:
    p=perfil(nom)
    out=[]
    for a0,a1 in ((4.2,5.0),(4.6,5.4),(5.0,5.8)):
        seg=p[int(a0*40):int(a1*40)]; ok=np.isfinite(seg)
        x=np.arange(len(seg))[ok]; res=seg[ok]-np.polyval(np.polyfit(x,seg[ok],2),x)
        out.append(f"{a0}–{a1}: {100*(res.max()-res.min())/np.nanmean(seg):.2f} %")
    print(f"  {nom:30s} " + "   ".join(out))
    seg=p[int(4.6*40):int(5.4*40)]; ok=np.isfinite(seg); x=np.arange(len(seg))[ok]
    res=seg[ok]-np.polyval(np.polyfit(x,seg[ok],2),x)
    print("      residu 4,6–5,4 (%): "+" ".join(f"{100*v/np.nanmean(seg):+.2f}" for v in res[::2]))
