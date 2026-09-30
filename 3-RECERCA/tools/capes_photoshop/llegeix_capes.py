"""Lector de capes d'un TIFF de Photoshop (ImageSourceData V0002, little-endian)."""
import struct, sys, tifffile, json
CAMI = sys.argv[1] if len(sys.argv) > 1 else "/Users/USUARI/Downloads/UnintCapes3.tif"

def u32(b,i): return struct.unpack("<I", b[i:i+4])[0]
def i32(b,i): return struct.unpack("<i", b[i:i+4])[0]
def u16(b,i): return struct.unpack("<H", b[i:i+2])[0]
def i16(b,i): return struct.unpack("<h", b[i:i+2])[0]
def u64(b,i): return struct.unpack("<Q", b[i:i+8])[0]

with tifffile.TiffFile(CAMI) as t:
    p=t.pages[0]
    isd = p.tags["ImageSourceData"].value
b = isd if isinstance(isd,(bytes,bytearray)) else bytes(isd)
# La signatura és «...Data Block\x00» o «...Data V0002\x00»: 36 bytes totes dues.
i=36
# ⚠️ Dos formats segons la mida del document (17-08-2026):
#   GRAN (UnintCapes3, 6960x4640 x 12 capes): longitud del bloc Lr16 de 8 bytes i
#         longituds de canal de 8 bytes (estil PSB);
#   PETIT (Ajust.tif, 4425x2835 x 2 capes): longitud del bloc de 4 bytes i
#         longituds de canal de 4 bytes.
# S'autodetecta amb la primera capa: rect plausible i longitud de canal <= w*h*2+2.
def _capes(d, LN):
    j=0; n_capes=i16(d,j); j+=2
    n=abs(n_capes)
    if not (1<=n<=2000): raise ValueError("recompte de capes implausible")
    return n_capes, j
key=b[i+4:i+8][::-1].decode("latin1")
if key not in ("Layr","Lr16","Lr32"):
    sys.exit(f"el primer bloc no és de capes: {key}")
mode=None
for LN in (4,8):
    ln=(u32 if LN==4 else u64)(b,i+8); off=i+8+LN
    if ln>len(b)-off: continue
    d=b[off:off+ln]
    try:
        n_capes,j0=_capes(d,LN)
        top,left,bottom,right=i32(d,j0),i32(d,j0+4),i32(d,j0+8),i32(d,j0+12)
        nch=u16(d,j0+16)
        w,h=right-left,bottom-top
        clen=(u32 if LN==4 else u64)(d,j0+18+2)
        if 0<w<100000 and 0<h<100000 and 1<=nch<=8 and 0<clen<=w*h*2+2:
            mode=LN; break
    except Exception:
        continue
if mode is None: sys.exit("no he sabut llegir la capçalera de capes")
CLEN=(u32 if mode==4 else u64)
print(f"bloc de capes: {key} ({ln} bytes), longituds de {mode} bytes")
j=0
n_capes=i16(d,j); j+=2
print("nombre de capes (signat; negatiu = el primer canal alfa és transparència):", n_capes)
n=abs(n_capes)
capes=[]
for k in range(n):
    top,left,bottom,right=i32(d,j),i32(d,j+4),i32(d,j+8),i32(d,j+12); j+=16
    nch=u16(d,j); j+=2
    canals=[]
    for c in range(nch):
        cid=i16(d,j); j+=2
        clen=CLEN(d,j); j+=mode      # 8 bytes al document gran, 4 al petit
        canals.append((cid,clen))
    s8=d[j:j+4][::-1]; j+=4
    blend=d[j:j+4][::-1].decode(errors="replace"); j+=4
    opac=d[j]; clip=d[j+1]; flags=d[j+2]; j+=4
    extra=u32(d,j); j+=4
    e0=j
    mlen=u32(d,j); j+=4+mlen
    blen=u32(d,j); j+=4+blen
    nl=d[j]; nom=d[j+1:j+1+nl].decode("macroman",errors="replace"); j+=1+nl
    j+=(-(1+nl))%4
    # blocs addicionals fins a e0+extra
    extres={}
    while j < e0+extra:
        s=d[j:j+4][::-1]; k4=d[j+4:j+8][::-1].decode(errors="replace")
        if k4 in ("LMsk","Lr16","Lr32","Layr","Mt16","Mt32","Mtrn","Alph","FMsk","lnk2","FEid","FXid","PxSD","cinf"):
            L=u64(d,j+8); j+=16
        else:
            L=u32(d,j+8); j+=12
        extres[k4]=L
        if k4=="luni":
            nn=u32(d,j); nom_u=d[j+4:j+4+2*nn].decode("utf-16-le",errors="replace"); extres["nom_unicode"]=nom_u
        if k4=="lsct":
            extres["tipus_seccio"]=u32(d,j)
        if k4=="iOpa":
            extres["fill_opacity"]=d[j]
        j+=L+(L&1)
    j=e0+extra
    capes.append(dict(nom=extres.get("nom_unicode",nom),blend=blend,opac=opac,clip=clip,flags=flags,
                      visible=not(flags&2),rect=(top,left,bottom,right),canals=canals,extres={k:v for k,v in extres.items() if k not in("nom_unicode",)}))
print(f"\n{'#':>2} {'capa':32s} {'blend':6s} {'op%':>4} {'vis':>3} {'clip':>4}  {'mida':>12}  canals / extres")
for k,c in enumerate(capes):
    t,l,bo,r=c["rect"]
    print(f"{k:2d} {c['nom'][:32]:32s} {c['blend']:6s} {100*c['opac']/255:4.0f} {'V' if c['visible'] else '-':>3} {c['clip']:4d}  {r-l:5d}x{bo-t:5d}  {[cid for cid,_ in c['canals']]} {list(c['extres'].keys())[:8]}"
          + (f"  secció={c['extres'].get('tipus_seccio')}" if 'tipus_seccio' in c['extres'] else ""))
json.dump(capes, open("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/capes.json","w"), default=str, indent=1)
