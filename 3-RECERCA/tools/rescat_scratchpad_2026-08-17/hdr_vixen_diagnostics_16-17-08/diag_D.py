import sys, os, numpy as np, cv2, math
sys.path.insert(0,"/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
hdr=np.load(M.OUT/"hdr_vixen_countss.npy"); varm=np.load(M.OUT/"hdr_vixen_var.npy")
H,W,_=hdr.shape; cy,cx=H/2.,W/2.
r=M.anells(H,W,cy,cx); rs=r/M.R_SOL_PX
valid=np.all(np.isfinite(hdr),axis=2)
caixa=np.zeros_like(valid); caixa[M.RETALL[0]:M.RETALL[1]+1, M.RETALL[2]:M.RETALL[3]+1]=True; valid&=caixa
R_,G_=hdr[...,0],hdr[...,1]
ref=valid&(rs>1.3)&(rs<1.5); kr=float(np.median(G_[ref])/np.median(R_[ref]))
L=np.where(valid,0.5*(np.nan_to_num(G_)+kr*np.nan_to_num(R_)),np.nan); del hdr
cel_z=valid&(rs>4.0)&(rs<5.1)
vG=np.nan_to_num(varm[...,1]); del varm
Ls=M.desenfoca_valid(np.where(valid,L,0.0).astype(np.float32),valid,6.0)
Ls=np.maximum(Ls,1e-3*float(np.median(np.nan_to_num(L)[cel_z])))
sig_log=(np.sqrt(np.maximum(vG,0))/Ls).astype(np.float32)
lnL=np.log(np.maximum(np.nan_to_num(L),1e-3*float(np.median(np.nan_to_num(L)[cel_z])))).astype(np.float32)
_ks,t_hp=M.transferencia_soroll(M.BANDES_PX)
obs=float(np.std((lnL-M.desenfoca(lnL,2.0))[cel_z]))/t_hp; esp=float(np.median(sig_log[cel_z]))
sig_log*= obs/esp
D=M.detall_logpolar(lnL,valid,sig_log,cel_z,cy,cx)
np.save("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/D_lp.npy",D)
ib=(rs*20).astype(int)
print("\nmitjana i desviació azimutal de D per anell de 0,05 R☉ (només vàlids):")
for k in range(int(1.0*20), int(9.0*20), 2):
    m=valid&(ib==k)
    if m.sum()>2000:
        print(f"  {(k+0.5)/20:5.2f} R☉  mitjana {float(D[m].mean()):+.4f}   sd {float(D[m].std()):.4f}   n={m.sum()}")
