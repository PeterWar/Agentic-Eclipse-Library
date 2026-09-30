import numpy as np, rawpy, os, json
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse"
M="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/Calibrated_Claude/_masters/"
O="/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/masters_corregits/"
VIS=(slice(108,108+4639),slice(172,172+6959))
j=json.load(open(M+"master_10.json")); files=j['darks']; print(len(files),"darks al master de 10 s")
print(files)
raws=[]
for f in files:
    with rawpy.imread(os.path.join(D,f)) as r: raws.append(r.raw_image.copy())
st=np.stack(raws); del raws
print("pila",st.shape,st.dtype)
H=st.shape[1]; CH=600
med=np.empty(st.shape[1:],np.float32); mean=np.empty(st.shape[1:],np.float32)
for i in range(0,H,CH):
    blk=st[:,i:i+CH].astype(np.float32)
    med[i:i+CH]=np.median(blk,axis=0); mean[i:i+CH]=blk.mean(axis=0)
ref=np.load(M+"master_10.npy")
print("reproduccio del master de 10 s: dif max = %.6f"%np.abs(med-ref).max())
def desc(a,nm):
    v=a[VIS]; print(f"  {nm:36s} med_vis={np.median(v):8.4f} mitjana_vis={v.mean():9.4f} std_vis={v.std():7.4f} obEsq={a[108:,:172].mean():8.4f}")
desc(ref,"original (25, mediana)"); desc(mean,"25, MITJANA per pixel")
d=(mean-med)[VIS]; print("  mitjana - mediana a la imatge: %+.5f ADU (std %.4f, |max| %.1f)"%(d.mean(),d.std(),np.abs(d).max()))
# families de temperatura
import csv
T={}
for line in open("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/darks_exif.tsv"):
    p=line.rstrip().split('\t'); T[p[0]]=float(p[3])
fred=[i for i,f in enumerate(files) if T[f]<=40]; calent=[i for i,f in enumerate(files) if T[f]>=43]
print("fred (T<=40 C):",len(fred)," calent (T>=43 C):",len(calent))
for nm,idx in [("fred T<=40",fred),("calent T>=43",calent)]:
    m=np.empty(st.shape[1:],np.float32)
    for i in range(0,H,CH):
        m[i:i+CH]=st[idx,i:i+CH].astype(np.float32).mean(axis=0)
    desc(m,"MITJANA nomes "+nm)
    np.save(O+f"master_10_mitjana_{nm.split()[0]}.npy",m)
np.save(O+"master_10_mitjana_25.npy",mean); np.save(O+"master_10_mediana_25.npy",med)
