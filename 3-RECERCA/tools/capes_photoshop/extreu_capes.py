"""Extreu, capa a capa, RGB i màscara del TIFF de Photoshop (LE, estil PSB), reduït ×4."""
import struct, sys, json, numpy as np, tifffile, zlib, cv2
from psd_tools.compression import decompress
CAMI = sys.argv[1] if len(sys.argv) > 1 else "/Users/USUARI/Downloads/UnintCapes3.tif"
SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad"
def u32(b,i): return struct.unpack("<I", b[i:i+4])[0]
def i32(b,i): return struct.unpack("<i", b[i:i+4])[0]
def u16(b,i): return struct.unpack("<H", b[i:i+2])[0]
def i16(b,i): return struct.unpack("<h", b[i:i+2])[0]
def u64(b,i): return struct.unpack("<Q", b[i:i+8])[0]

with tifffile.TiffFile(CAMI) as t:
    isd=t.pages[0].tags["ImageSourceData"].value
    H,W=t.pages[0].shape[:2]
b=isd if isinstance(isd,(bytes,bytearray)) else bytes(isd)
i=36   # signatura «...Data Block\x00» o «...Data V0002\x00», 36 bytes totes dues
key=b[i+4:i+8][::-1].decode()
# ⚠️ document GRAN: longitud del bloc i dels canals de 8 bytes; PETIT: de 4 (vegeu llegeix_capes.py)
mode=None
for LN in (4,8):
    ln=(u32 if LN==4 else u64)(b,i+8); off=i+8+LN
    if ln>len(b)-off: continue
    d=b[off:off+ln]
    try:
        n=abs(i16(d,0)); top,left,bottom,right=i32(d,2),i32(d,6),i32(d,10),i32(d,14); nch=u16(d,18)
        clen=(u32 if LN==4 else u64)(d,22)
        if 1<=n<=2000 and 0<right-left<100000 and 0<bottom-top<100000 and 1<=nch<=8 and 0<clen<=(right-left)*(bottom-top)*2+2:
            mode=LN; break
    except Exception: continue
if mode is None: sys.exit("no he sabut llegir la capçalera de capes")
CLEN=(u32 if mode==4 else u64)
print(f"bloc {key}: {ln} bytes, longituds de {mode} bytes, llenç {W}x{H}")
j=0; n=abs(i16(d,j)); j+=2
capes=[]
K64=("LMsk","Lr16","Lr32","Layr","Mt16","Mt32","Mtrn","Alph","FMsk","lnk2","FEid","FXid","PxSD","cinf")
for k in range(n):
    rect=[i32(d,j),i32(d,j+4),i32(d,j+8),i32(d,j+12)]; j+=16
    nch=u16(d,j); j+=2
    canals=[]
    for c in range(nch):
        cid=i16(d,j); clen=CLEN(d,j+2); j+=2+mode; canals.append((cid,clen))
    j+=4; blend=d[j:j+4][::-1].decode(); j+=4
    opac,clip,flags=d[j],d[j+1],d[j+2]; j+=4
    extra=u32(d,j); j+=4; e0=j
    mlen=u32(d,j); mrect=None
    if mlen>=20: mrect=[i32(d,j+4),i32(d,j+8),i32(d,j+12),i32(d,j+16)]
    j+=4+mlen
    blen=u32(d,j); j+=4+blen
    nl=d[j]; nom=d[j+1:j+1+nl].decode("macroman","replace"); j+=1+nl; j+=(-(1+nl))%4
    while j<e0+extra:
        k4=d[j+4:j+8][::-1].decode("latin1")
        if k4 in K64: L=u64(d,j+8); j+=16
        else: L=u32(d,j+8); j+=12
        if k4=="luni":
            nn=u32(d,j); nom=d[j+4:j+4+2*nn].decode("utf-16-le","replace")
        j+=L+(L&1)
    j=e0+extra
    capes.append(dict(nom=nom,rect=rect,mrect=mrect,canals=canals,visible=not(flags&2)))
# dades d'imatge dels canals: comencen a j (arrodonit?)
pos=j
print("inici de les dades de canal a", pos, "de", ln)
sortida={}
for k,c in enumerate(capes):
    t,l,bo,r=c["rect"]; h,w=bo-t,r-l
    capa={}
    for cid,clen in c["canals"]:
        comp=u16(d,pos); dat=d[pos+2:pos+clen]
        if cid==-2 and c["mrect"]:
            mt,ml,mb,mr=c["mrect"]; hh,ww=mb-mt,mr-ml
        else:
            hh,ww=h,w
        try:
            raw=decompress(bytes(dat),comp,ww,hh,16,version=2)
            arr=np.frombuffer(raw,dtype=">u2").reshape(hh,ww)
            # comprovació d'endianitat: si els bytes són LE, els valors alts salten
            arr_le=arr.byteswap()
            # tria la versió més suau (menys gradient)
            g_be=float(np.mean(np.abs(np.diff(arr[::64,::64].astype(np.int32),axis=1))))
            g_le=float(np.mean(np.abs(np.diff(arr_le[::64,::64].astype(np.int32),axis=1))))
            arr=arr_le if g_le<g_be else arr
            petit=cv2.resize(arr.astype(np.float32)/65535.0,(ww//4,hh//4),interpolation=cv2.INTER_AREA)
            capa[cid]=petit
            print(f"  capa {k} canal {cid:2d} comp={comp} {ww}x{hh} → mitjana {petit.mean():.4f} min {petit.min():.3f} max {petit.max():.3f}  (endian {'LE' if g_le<g_be else 'BE'})")
        except Exception as e:
            print(f"  capa {k} canal {cid} comp={comp}: ERROR {e}")
        pos+=clen
    np.savez_compressed(f"{SCR}/capa_{k:02d}.npz", **{str(cid):v for cid,v in capa.items()}, nom=c["nom"], visible=c["visible"], mrect=np.array(c["mrect"] or [0,0,0,0]))
    print(f"capa {k} «{c['nom']}» desada")
