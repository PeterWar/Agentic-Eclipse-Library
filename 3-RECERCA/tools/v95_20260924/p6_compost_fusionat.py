"""p6 · PORTA DEL COMPOST FUSIONAT: el compost que el PSB porta desat (Image Data, màxima compatibilitat) ha de coincidir amb la vista del llenç sencer
que el Photoshop ha renderitzat del mateix document (vistes/V95_llenc_sencer.tif, 2400 px d'ample). Lliçó del 24-09: un desament natiu de la V95 (16:43)
va sortir amb les capes bones i el compost fusionat fet malbé (mitjana 51.182 en lloc de 10.396, alfa aleatòria). Ús: p6_compost_fusionat.py <psb> <vista.tif>"""
import sys, struct, os
import numpy as np, cv2, tifffile
psb, vista = sys.argv[1], sys.argv[2]
with open(psb, 'rb') as f:
    hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]; H, W = struct.unpack('>II', hdr[14:22])
    n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
    pos = f.tell(); comp = struct.unpack('>H', f.read(2))[0]
assert comp == 0, f'compressió del compost {comp} (esperat 0, cru)'
mm = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
alfa = np.asarray(mm[3, ::7, ::7]) if nch > 3 else None
C = np.stack([np.asarray(mm[c]) for c in range(3)], -1).astype(np.float32)
V = tifffile.imread(vista).astype(np.float32); Cr = cv2.resize(C, (V.shape[1], V.shape[0]), interpolation=cv2.INTER_AREA)
dif = np.abs(Cr - V[..., :3]); rel = float(np.median(dif) / max(float(np.median(V)), 1)); mitj = [round(float(Cr[..., i].mean()), 1) for i in range(3)], [round(float(V[..., i].mean()), 1) for i in range(3)]
ok = rel < 0.01 and (alfa is None or (float(alfa.min()) > 60000 and float(alfa.mean()) > 65000))
print(('PASSA' if ok else 'FALLA'), f'· mediana |compost − vista| / mediana = {rel:.4f} · mitjanes compost {mitj[0]} vista {mitj[1]} · alfa mín {float(alfa.min()) if alfa is not None else None}')
sys.exit(0 if ok else 1)
