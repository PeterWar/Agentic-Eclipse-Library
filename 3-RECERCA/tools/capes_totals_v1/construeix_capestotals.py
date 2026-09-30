"""CapesTotalsV1.psb: les 12 capes de CapesInteriorsV5 (amb les màscares de 04/03 acabades per
ordre de Pere) + PONT radial + la cadena exterior de CapesExteriors amb màscares × porta radial
(earthshine de Pere conservat dins la Lluna) + els 15 filtres de FiltresSEMIFINAL10 tal qual +
capa PERFIL. Variant via CT1_R1, CT1_R2, CT1_PONT_ON, CT1_TRIM, CT1_MERGED."""
import os, sys, time, json, numpy as np
sys.path.insert(0, os.path.expanduser('~/Downloads/Eclipse 2026/research/tools/encaix_sony'))
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression, ChannelID
from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
from psd_tools.psd.layer_and_mask import MaskData, MaskFlags
from psd_tools.psd.layer_and_mask import ChannelInfo, ChannelData

t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)

D = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(D, 'ext'); SF = os.path.join(D, 'sf10')
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 446.15; LLUNA = (4034.7, 2736.7)
R1 = float(os.environ.get('CT1_R1', 2.2)); R2 = float(os.environ.get('CT1_R2', 2.9))
PONT_ON = float(os.environ.get('CT1_PONT_ON', 1.35))
OUT = os.path.expanduser(os.environ.get('CT1_OUT', '~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV1.psb'))
MERGED = os.environ.get('CT1_MERGED')   # npy uint16 del compost final (de prototip_ct1)

V5PSB = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/CapesInteriorsV5.psb')
EXTPSB = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes exteriors/CapesExteriors.psb')
SFPSB = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/FiltresSEMIFINAL10.psb')

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot(xx - SOL[0], yy - SOL[1]) / R_SOL
r_ll = np.hypot(xx - LLUNA[0], yy - LLUNA[1])
def sstep(t):
    t = np.clip(t, 0, 1); return t*t*t*(t*(t*6-15)+10)
GATE = sstep((r - R1)/(R2 - R1))
W_MOON = sstep((448.0 - r_ll)/7.0)

def add_mask16_bg(layer, mask16, top, left, bg=0, compression=Compression.ZIP_WITH_PREDICTION):
    Hm, Wm = mask16.shape
    version = layer._psd._record.header.version
    cd = ChannelData(compression)
    cd.set_data(np.ascontiguousarray(mask16).astype('>u2').tobytes(), Wm, Hm, 16, version)
    layer._record.mask_data = MaskData(top=top, left=left, bottom=top+Hm, right=left+Wm,
                                       background_color=bg, flags=MaskFlags())
    layer._record.channel_info.append(ChannelInfo(id=ChannelID.USER_LAYER_MASK, length=len(cd.data)+2))
    layer._channels.append(cd)
    layer._psd._mark_updated()

BLEND = {'BlendMode.NORMAL': BlendMode.NORMAL, 'BlendMode.LINEAR_LIGHT': BlendMode.LINEAR_LIGHT,
         'BlendMode.OVERLAY': BlendMode.OVERLAY}

def copia_capa(psd_nou, l, nom=None, mask_mult=None, mask_override=None, visible=None, opacity=None):
    """Copia una capa (contingut exacte) d'un PSB obert; la màscara es pot multiplicar per un mapa del llenç."""
    arr = l.numpy('color')
    rgb16 = np.clip(np.rint(arr*65535.0), 0, 65535).astype(np.uint16)
    layer = add_pixel_layer(psd_nou, rgb16, nom or l.name, top=l.top, left=l.left,
                            blend=BLEND[str(l.blend_mode)],
                            opacity=l.opacity if opacity is None else opacity,
                            visible=l.visible if visible is None else visible)
    m = l.mask
    if mask_override is not None:
        add_mask16_bg(layer, np.clip(np.rint(mask_override*65535.0),0,65535).astype(np.uint16), 0, 0, bg=0)
    elif m is not None:
        marr = l.numpy('mask')[..., 0]
        if mask_mult is not None:
            mt, ml = m.top, m.left
            Hm, Wm = marr.shape
            mult = np.ones((Hm, Wm), np.float32)
            dy0, dx0 = max(0, mt), max(0, ml)
            sy0, sx0 = max(0, -mt), max(0, -ml)
            hh = min(m.bottom, H) - dy0; ww = min(m.right, W) - dx0
            mult[sy0:sy0+hh, sx0:sx0+ww] = mask_mult[dy0:dy0+hh, dx0:dx0+ww]
            marr = marr * mult
        add_mask16_bg(layer, np.clip(np.rint(marr*65535.0),0,65535).astype(np.uint16),
                      m.top, m.left, bg=m.background_color)
    del arr, rgb16
    return layer

log('obrint fonts')
psd_v5 = PSDImage.open(V5PSB); psd_ext = PSDImage.open(EXTPSB); psd_sf = PSDImage.open(SFPSB)
icc = psd_v5.image_resources.get_data(1039)
psd = new_psb(W, H, icc_bytes=icc, resources_from=psd_v5)

# 1) les 12 capes de CapesInteriorsV5. Contingut tal qual; les màscares de 04 (i=10) i 03 (i=11)
#    s'ACABEN amb la protecció P (ordre de Pere 20-08: protuberàncies, vora lunar i perles):
#    màscara × (1 − P), P = anell del limbe (ple ≤~470 px, rampa a 540) ∪ el·lipse estreta de la
#    protuberància, gaussiana σ8. Vegeu acaba_mask0403.py i el LLEGEIX-ME.
P = np.load(os.path.join(D, 'proteccio_P.npy'))
UNMENYS_P = (1.0 - P).astype(np.float32)
for i, l in enumerate(psd_v5):
    mm = UNMENYS_P if i in (10, 11) else None
    copia_capa(psd, l, mask_mult=mm); log('V5', i, l.name[:40], '(màscara acabada)' if mm is not None else '')

# 1 bis) VORA · aixeca el fossat del limbe (Linear Light, radial centrat a la LLUNA): restaura la
#        mediana per anell del vel que l'acabat de màscares treu (sense les bombolles, que eren
#        azimutals), començant a 455 px perquè la vora lunar estricta i les perles quedin intactes.
vora = np.load(os.path.join(D, os.environ.get('CT1_VORA', 'vora_F100.npz')))
vrc, vprof = vora['rcx'], vora['prof']
vm = np.zeros((H, W, 3), np.float32)
for c in range(3):
    vm[..., c] = np.interp(r_ll, vrc, vprof[:, c], left=0, right=0)
v16 = np.clip(np.rint((0.5 + vm/2.0)*65535.0), 0, 65535).astype(np.uint16)
add_pixel_layer(psd, v16, 'VORA · resplendor de la corona arran de limbe (Linear Light; corba radial centrada a la LLUNA: mediana per anell al nivell del benchmark des de 452 px; les bombolles, azimutals, no poden tornar; capa_vora3.py, panell 20-08)',
                blend=BlendMode.LINEAR_LIGHT)
del vm, v16; log('VORA')

# 2) PONT radial (LL): porta el perfil per anell de V5 al de la base de 1,35 R☉ enfora (per canal)
p = np.load(os.path.join(D, 'pont_delta.npz'))
rc, delta_s = p['rc'], p['delta']
w_on = sstep((r - PONT_ON)/0.15)
pont = np.zeros((H, W, 3), np.float32)
for c in range(3):
    pont[..., c] = np.interp(r, rc, delta_s[:, c]) * w_on
pont16 = np.clip(np.rint((0.5 + pont/2.0)*65535.0), 0, 65535).astype(np.uint16)
add_pixel_layer(psd, pont16, f'PONT V5→exterior · Linear Light · porta el perfil per anell de la V5 al de la base exterior des de {PONT_ON} R☉ (mediana azimutal per canal, suau; research CapesTotalsV1)',
                blend=BlendMode.LINEAR_LIGHT)
del pont, pont16; log('PONT')

# 3) cadena exterior amb porta radial (i earthshine dins la Lluna per a EDITAT PERE)
noms_ext = {
 1: f"02_2s_572A2979_apilat3.dng · de CapesExteriors · MÀSCARA × porta radial {R1}→{R2} R☉ (l'interior és de la V5)",
 2: f"01_10.3s_572A2982_apilat3.dng · de CapesExteriors · MÀSCARA × porta radial {R1}→{R2} R☉",
 3: f"EDITAT PERE: Earthshine i textures · MÀSCARA × màx(porta {R1}→{R2}, finestra earthshine dins la Lluna r_ll<448 px): l'earthshine és el de Pere, el limbe i les perles són de la V5",
 4: f"Correcció del graó HDR al contorn del 10,3 s (sector) · LINEAR LIGHT · MÀSCARA × porta {R1}→{R2} (corregia el compost antic; a dins ja no cal)",
 5: "Detall tangencial MITJA (només azimutal, 0,6–16°, rampa 3,2→4,4 R☉) · LINEAR LIGHT · MÀSCARA × porta",
 6: "Extensió radial k 1→1,4 (3,4→6 R☉) sobre base − cel · LINEAR LIGHT · MÀSCARA × porta",
 7: "Cel pla (cosmètic: luminància del camp llunyà al nivell de 6 R☉, rampa 4,8→6,2) · LINEAR LIGHT · MÀSCARA × porta",
}
for i, l in enumerate(psd_ext):
    if i == 0: continue      # 03_1s: ja hi és a la V5
    mm = np.maximum(GATE, W_MOON) if i == 3 else GATE
    if l.mask is None:
        copia_capa(psd, l, nom=noms_ext.get(i), mask_override=mm)
    else:
        copia_capa(psd, l, nom=noms_ext.get(i), mask_mult=mm)
    log('EXT', i, l.name[:40])

# 4) filtres de la SEMIFINAL10 (1..15): contingut, màscares i visibilitats tal qual, ANELL inclòs
#    (l'ANELL de la SF10 és zero per dins de 3 R☉ a propòsit, i a fora el nostre exterior = la seva base)
for i, l in enumerate(psd_sf):
    if i == 0: continue      # la base: la substitueix tota la cadena d'aquí sobre
    copia_capa(psd, l); log('SF10', i, l.name[:40])

# 5) PERFIL · allisa l'arrissat radial fi del compost (Linear Light, radial per canal, 1,28→3,0 R☉)
trim = np.load(os.path.join(D, os.environ.get('CT1_TRIM', 'perfil_trim_D_pont_135_195.npz')))
rcx, dtr = trim['rcx'], trim['delta']
pm = np.zeros((H, W, 3), np.float32)
for c in range(3):
    pm[..., c] = np.interp(r, rcx, dtr[:, c], left=0, right=0)
p16 = np.clip(np.rint((0.5 + pm/2.0)*65535.0), 0, 65535).astype(np.uint16)
add_pixel_layer(psd, p16, 'PERFIL · porta el perfil radial del compost al del benchmark entre 1,28 i 3,0 R☉ (Linear Light; radial per canal, mediana per anell del benchmark − la del compost, suau; recalcular si canvies capes o opacitats — perfil_trim.py)',
                blend=BlendMode.LINEAR_LIGHT)
del pm, p16; log('PERFIL')

# 6) fusionada + desar
finalize_lr16(psd)
if MERGED:
    merged = np.load(MERGED)
    set_merged(psd, np.ascontiguousarray(merged), compression=Compression.RAW)
psd._record.header.channels = 3
psd._updated = False
assert not os.path.exists(OUT), 'ja existeix: ' + OUT
psd.save(OUT)
log('desat', OUT, round(os.path.getsize(OUT)/1e9, 2), 'GB')
