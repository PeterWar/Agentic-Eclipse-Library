#!/usr/bin/env python3
"""Classificació A/B/rebutjada, ajust gaussià amb angle fix −45,05° a les piles llarga i curta (traça, FWHM), magnitud INFERIDA amb ZP=9,57e5 → catalog_vixen_fonts.csv (32 files: 21 A + 3 B).

Origen: rescat_scratchpad_2026-08-17/estrelles_placa_flats_16-08/vixen/cat_final.py
Canvis: només el bloc comu + os.chdir(comu.work("vixen")); cap constant,
llindar ni ordre de fotogrames tocat.
"""
import sys, os; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("vixen"))

import numpy as np, json, warnings; warnings.filterwarnings('ignore')
from scipy.optimize import least_squares
fin=json.load(open('final.json')); rb=np.load('rb.npy'); cand=np.load('cand.npy')
FL=np.load('g_long_flux.npy'); DL=np.load('g_long_den.npy')
FS=np.load('g_short_flux.npy'); DS=np.load('g_short_den.npy')
TH=np.radians(-45.05); c,s=np.cos(TH),np.sin(TH)
def fitfix(F,D,x,y,box=9):
    x0,y0=int(round(x)),int(round(y))
    if x0<box+2 or y0<box+2 or x0>=F.shape[1]-box-2 or y0>=F.shape[0]-box-2: return None
    sub=F[y0-box:y0+box+1,x0-box:x0+box+1].astype(np.float64)
    sig=1.0/np.sqrt(np.maximum(D[y0-box:y0+box+1,x0-box:x0+box+1],1e-12))
    yy,xx=np.mgrid[-box:box+1,-box:box+1].astype(float)
    def model(p):
        A,cx,cy,sp,sq,B=p
        u=(xx-cx)*c+(yy-cy)*s; v=-(xx-cx)*s+(yy-cy)*c
        return A*np.exp(-0.5*((u/sp)**2+(v/sq)**2))+B
    r=least_squares(lambda p:((model(p)-sub)/sig).ravel(),[max(sub.max(),1e-6),0,0,1.6,1.4,0.0],
        bounds=([0,-4,-4,0.4,0.4,-abs(sub).max()],[np.inf,4,4,6,6,abs(sub).max()]))
    return r.x
ZP=9.57e5   # ADU/s for V=0, INFERIT +-1 mag
rows=[]
for d in fin:
    i=d['id']
    if i==22: cls='REBUTJADA (a 13 px de la vora; no mesurable)'
    else:
        nl=d['nlong']; R=rb[i,1]
        if nl==3 and R>=3.0 and d['snr']>=8: cls='A'
        elif nl>=2 and d['snr']>=6: cls='B'
        else: cls='REBUTJADA'
    a=fitfix(FL,DL,d['x'],d['y']); b=fitfix(FS,DS,d['x'],d['y'])
    L=np.nan; fw=np.nan
    if a is not None and b is not None:
        dd=a[3]**2-b[3]**2
        L=np.sqrt(12*dd)*2.158 if dd>0 else np.nan
        fw=2.355*np.sqrt(max(b[3]*b[4],1e-6))*2.158
    m=-2.5*np.log10(d['flux']/ZP) if d['flux']==d['flux'] and d['flux']>0 else np.nan
    rows.append((i,cls,d['x'],d['y'],d['r'],d['r']/451.0,d['r']*2.158/3600,d['flux'],d['snr'],
                 d['nfr'],d['nlong'],rb[i,0],rb[i,1],rb[i,2],rb[i,3],L,fw,m))
hdr=['id','classe','x_px','y_px','r_sol_px','r_sol_Rlluna','r_sol_deg','flux_G_ADUs','SNR_pila',
     'n_fotogrames_3s','n_10.3s','flux_R_ADUs','SNR_R','flux_B_ADUs','SNR_B','traç_arcsec','FWHM_arcsec','V_aprox_INFERIT']
with open('catalog_vixen_fonts.csv','w') as fh:
    fh.write(','.join(hdr)+'\n')
    for r in rows:
        fh.write('%d,%s,%.2f,%.2f,%.0f,%.2f,%.3f,%.1f,%.1f,%d,%d,%.1f,%.1f,%.1f,%.1f,%s,%s,%s\n'%(
            r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9],r[10],r[11],r[12],r[13],r[14],
            '%.2f'%r[15] if r[15]==r[15] else '',' %.2f'%r[16] if r[16]==r[16] else '','%.1f'%r[17] if r[17]==r[17] else ''))
print('%3s %-6s %8s %8s %7s %6s %9s %7s %5s %5s %6s %6s %7s %7s %6s'%('id','cl','x','y','r_px','r_Rm','fluxG','SNR','nfr','nlg','SNR_R','SNR_B','traç"','FWHM"','V~'))
for r in rows:
    print('%3d %-6s %8.2f %8.2f %7.0f %6.2f %9.1f %7.1f %5d %5d %6.1f %6.1f %7s %7s %6s'%(
        r[0],r[1][:6],r[2],r[3],r[4],r[5],r[7],r[8],r[9],r[10],r[12],r[14],
        '%.2f'%r[15] if r[15]==r[15] else '  -','%.2f'%r[16] if r[16]==r[16] else '  -','%.1f'%r[17] if r[17]==r[17] else '  -'))
nA=sum(1 for r in rows if r[1]=='A'); nB=sum(1 for r in rows if r[1]=='B')
print('\nclasse A (confirmades): %d   classe B (probables): %d   rebutjades: %d'%(nA,nB,len(rows)-nA-nB))
