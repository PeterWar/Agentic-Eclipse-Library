import numpy as np, sys, warnings, json
warnings.filterwarnings("ignore")
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import SCALE
from core import prep, build, fwhm_of
from widths import widths

FR={ "DSC06973.ARW":"1/800 C2-3.4","DSC06974.ARW":"1/6400 C2-3.4","DSC06975.ARW":"1/100 C2-3.4",
     "DSC06976.ARW":"1/800 C2-0.5","DSC06977.ARW":"1/6400 C2-0.5","DSC06978.ARW":"1/100 C2-0.5",
     "DSC06979.ARW":"1/800 C2+2.5","DSC06980.ARW":"1/6400 C2+2.5","DSC06981.ARW":"1/100 C2+2.5",
     "DSC06982.ARW":"1/4 mid","DSC06983.ARW":"1/30 mid","DSC06986.ARW":"1/8 anc1",
     "DSC06989.ARW":"1/8 anc2","DSC06992.ARW":"1/8 anc3",
     "DSC06994.ARW":"1/4 mid2","DSC06995.ARW":"1/30 mid2","DSC06997.ARW":"1/4 mid3","DSC06998.ARW":"1/30 mid3",
     "DSC07000.ARW":"1/800 C3-2.5","DSC07001.ARW":"1/6400 C3-2.5","DSC07002.ARW":"1/100 C3-2.5",
     "DSC07003.ARW":"1/800 C3+1.5","DSC07004.ARW":"1/6400 C3+1.5","DSC07005.ARW":"1/100 C3+1.5"}
res=[]
for nm,tag in FR.items():
    for ch in ['R','G1','G2','B']:
        try:
            pr=prep(nm,ch)
        except Exception as e:
            print(nm,ch,"prep fail",e); continue
        if len(pr['ok_sec'])<8:
            print("%-14s %-3s %-11s  sectors=%d  SKIP"%(nm,ch,tag,len(pr['ok_sec']))); continue
        ctr,prof,cnt=build(pr)
        try:
            f,f2d,rr,r=fwhm_of(ctr,prof)
        except Exception as e:
            print(nm,ch,"fit fail",e); continue
        w=widths(ctr,prof)
        fin=2*abs(w['d50']-w['in_0.1'])*0.919*2*SCALE if np.isfinite(w['in_0.1']) else np.nan
        fout=2*abs(w['out_0.9']-w['d50'])*0.919*2*SCALE if np.isfinite(w['out_0.9']) else np.nan
        res.append(dict(frame=nm,tag=tag,ch=ch,fwhm=f,fin=fin,fout=fout,nsec=len(pr['ok_sec']),R=pr['R'],resid=rr))
        print("%-14s %-3s %-11s sec=%3d R=%.2f  FWHM_fit=%5.2f\"  FWHM_in=%5.2f\"  FWHM_out=%5.2f\"  resid=%.4f"%(
            nm,ch,tag,len(pr['ok_sec']),pr['R'],f,fin,fout,rr))
json.dump(res,open("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony/sweep.json","w"),indent=1)
