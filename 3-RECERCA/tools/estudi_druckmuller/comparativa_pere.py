import os
import numpy as np, tifffile
from PIL import Image, ImageDraw, ImageFont
OUT = "/Users/USUARI/Desktop/Eclipse determinista/2-OUTPUT/ESTUDI_DRUCKMULLER"
RUN = (__import__("glob").glob(os.path.expanduser("/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/*20260826T112542Z*")) + [""])[0] + "/"
P3_XYZ = np.array([[0.48657095,0.26566769,0.19821728],[0.22897456,0.69173852,0.07928691],[0.,0.04511338,1.04394437]])
XYZ_SRGB = np.array([[3.24096994,-1.53738318,-0.49861076],[-0.96924364,1.87596750,0.04155506],[0.05563008,-0.20397696,1.05697151]])
M = (XYZ_SRGB @ P3_XYZ).astype(np.float32)
a_lin = lambda c: np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
a_srgb = lambda c: np.where(c <= 0.0031308, 12.92*np.clip(c,0,1), 1.055*np.clip(c,0,1)**(1/2.4)-0.055)

a = tifffile.imread("/Users/USUARI/Downloads/GraduantColor.tif")[:, :, :3]
v = a[::6, ::6].astype(np.float32)/65535.0; del a
pere = (a_srgb(np.einsum("ij,hwj->hwi", M, a_lin(v)))*255+0.5).astype(np.uint8); del v

def ov(x, y): return np.where(x < 0.5, 2*x*y, 1.0-2.0*(1.0-x)*(1.0-y))
base = np.load(RUN+"3-filtres/BASE_rgb.npy").astype(np.float32)
det = np.load(RUN+"3-filtres/DETALL_PASSA_ALT.npy").astype(np.float32)
if det.ndim == 3: det = det.mean(axis=2)
H, W = base.shape[:2]
vell = np.asarray(Image.fromarray((np.clip(ov(base, det[:,:,None]),0,1)*255+0.5).astype(np.uint8)).resize((W//8,H//8), Image.LANCZOS))
nou = np.asarray(Image.open(os.path.join(OUT,"EL_QUE_VAS_VEURE_v1_x8.png")).convert("RGB"))

pans=[(pere,"1. EL QUE VAS VEURE TU  ·  GraduantColor.tif  (el centre hi es cremat)"),
      (nou,"2. LA NOSTRA DADA renderitzada TAL COM HO VAS VEURE  ·  llenc sencer  ·  PROVA"),
      (vell,"3. EL QUE LLIURAVEM  ·  llenc sencer")]
alt = max(p.shape[0] for p,_ in pans)
ims=[]
for p,t in pans:
    im = Image.fromarray(p)
    im = im.resize((int(im.width*alt/im.height), alt), Image.LANCZOS)
    ims.append((im,t))
mg,cap = 24,46
lien = Image.new("RGB",(sum(i.width for i,_ in ims)+mg*(len(ims)+1), alt+cap+mg*2),(12,12,14))
d = ImageDraw.Draw(lien)
try: fo = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 19)
except Exception: fo = ImageFont.load_default()
x = mg
for im,t in ims:
    lien.paste(im,(x,cap)); d.text((x,cap-28), t, fill=(232,232,236), font=fo); x += im.width+mg
d.text((mg, alt+cap+8), "El groc NO era un error: l'extincio a X=6,12 prediu R/G 1,758 i B/G 0,498, i la dada en mesura 1,755 i 0,498. El defecte era la DERIVA amb el radi.",
       fill=(150,150,158), font=fo)
lien.save(os.path.join(OUT,"COMPARATIVA_EL_QUE_VAS_VEURE.png"))
print("desat", lien.size)
