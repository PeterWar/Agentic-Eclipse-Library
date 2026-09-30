import numpy as np, rawpy, os, json
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse"
M="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/Calibrated_Claude/_masters/"
O="/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/masters_corregits/"
os.makedirs(O,exist_ok=True)
VIS=(slice(108,108+4639),slice(172,172+6959))

def stack(files):
    arrs=[]
    for f in files:
        with rawpy.imread(os.path.join(D,f)) as raw:
            arrs.append(raw.raw_image.copy())
    return np.stack(arrs).astype(np.float32)

def desc(a,nm):
    v=a[VIS]
    print(f"  {nm:34s} med_vis={np.median(v):7.3f} mitjana_vis={v.mean():9.4f} std_vis={v.std():7.4f} max={a.max():8.1f} top6={a[:6].mean():8.2f}")

j05=json.load(open(M+"master_0.5.json")); f05=j05['darks']
print("=== 0,5 s ===")
st=stack(f05)
med_all=np.median(st,axis=0)
ref=np.load(M+"master_0.5.npy")
print("  reproduccio del master existent: diferencia maxima = %.6f ADU"%np.abs(med_all-ref).max())
desc(ref,"master original (16, mediana)")
dolents=["572A3444.CR3","572A6843.CR3","572A3558.CR3","572A3462.CR3","572A3576.CR3"]
keep=[f for f in f05 if f not in dolents]
idx=[i for i,f in enumerate(f05) if f not in dolents]
med_keep=np.median(st[idx],axis=0)
desc(med_keep,"sense els 5 mes calents (11, mediana)")
d=(med_keep-ref)[VIS]
print("  canvi a la IMATGE: mitjana %+.5f ADU, mediana %+.5f, |max| %.3f, std %.4f"%(d.mean(),np.median(d),np.abs(d).max(),d.std()))
dt=(med_keep-ref)[:6]
print("  canvi a les files 0-5 emmascarades: mitjana %+.2f ADU"%dt.mean())
mean_all=st.mean(axis=0)
desc(mean_all,"els 16, MITJANA per pixel")
dm=(mean_all-ref)[VIS]
print("  mitjana-mediana a la imatge: %+.5f ADU, std %.4f"%(dm.mean(),dm.std()))
np.save(O+"master_0.5_mediana_16.npy",med_all.astype(np.float32))
np.save(O+"master_0.5_mediana_11.npy",med_keep.astype(np.float32))
np.save(O+"master_0.5_mitjana_16.npy",mean_all.astype(np.float32))
del st,med_all,med_keep,mean_all
