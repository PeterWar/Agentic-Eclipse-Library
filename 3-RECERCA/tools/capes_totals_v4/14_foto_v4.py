"""14 — FOTO de la V4b amb el pipeline de presentació VALIDAT del projecte
(`hdr_corona_vixen.py`, etapa `foto`: detall log-polar amb porta de soroll, corba del sketch,
color de dos ancoratges amb protuberàncies protegides, cel per corba, disc negre amb ploma).

El compost s'hi alimenta en FLOAT lineal de càmera (ADU/s), compost en stream dels DNG amb els
pesos efectius de la cadena — NO del PSB (16 bits): així els fenòmens brillants hi entren sense
el clip a 1,0 del codificat, i l'etapa `foto` els tracta com al màster (que és float).
La versió codificada del mateix compost hi és idèntica fora del clip (les matrius commuten amb
la barreja: totes les capes hi passen per la mateixa).
"""
import os, sys, math, json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import rawpy
from v4_lib import *

WORK = V4W / 'foto'
WORK.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE.parent / 'revelat_normalitzat'))
import render_lineal as RL
sys.path.insert(0, str(HERE.parent))
import hdr_corona_vixen as H

W07 = 13995 - 512
T_REF = 1 / 15

def main():
    # 1) compost en float: suma de pes_i × capa_i (lineal càmera, ADU/s) directament dels DNG
    masks = {i: np.load(V4W / f'masks/mask_{i}.npy', mmap_mode='r') for i in ORDER
             if (V4W / f'masks/mask_{i}.npy').exists()}
    Weff = effective_weights(masks)
    Y0, Y1, X0, X1 = 463, 5012, 625, 7417          # retall de llenç centrat al Sol
    Hh, Ww = Y1 - Y0, X1 - X0
    adus = np.zeros((Hh, Ww, 3), np.float32)
    t_ref = RL.exif_time_s(RL.APILATS / RL.LAYERS['07'])
    for i in ORDER:
        prefix = LAYER_PREFIX[i]
        src = RL.dng_font(prefix)
        with rawpy.imread(str(src)) as raw:
            s = raw.sizes
            x = raw.raw_image[..., :3].astype(np.float32)
            black = np.array(raw.black_level_per_channel[:3], np.float32)
            white = float(raw.white_level)
            if (s.crop_width, s.crop_height) == (FW, FH) and (s.crop_left_margin or s.crop_top_margin):
                x = x[s.crop_top_margin:s.crop_top_margin + s.crop_height,
                      s.crop_left_margin:s.crop_left_margin + s.crop_width, :]
        lin = np.maximum((x - black) / (white - black), 0.0)
        # SENSE guany WB: l'etapa foto aplica ella el balanç (WB_DIURN @ CAM_A_SRGB), com al màster
        t_s = RL.OVERRIDE_T.get(prefix, RL.exif_time_s(RL.APILATS / RL.LAYERS[prefix]))
        cam = lin * (t_ref / t_s) * (W07 / T_REF)    # ADU/s de càmera, sense clip de codificat
        l, t = FRAME_XY[i]
        ay0, ay1 = max(t, Y0), min(t + FH, Y1)
        ax0, ax1 = max(l, X0), min(l + FW, X1)
        w_ = np.asarray(Weff[i], np.float32)[ay0:ay1, ax0:ax1]
        adus[ay0 - Y0:ay1 - Y0, ax0 - X0:ax1 - X0] += cam[ay0 - t:ay1 - t, ax0 - l:ax1 - l] * w_[..., None]
        print(f'capa {prefix} afegida (w mitjà {w_.mean():.3f})', flush=True)
        del cam, lin, x
    # sanejador fora de gàmut (soroll extrem dels fotogrames únics): si la conversió a sRGB
    # dona luminància ~0, la croma de l'etapa explota (l'arc magenta de la 1a passada)
    srgb_test = (adus * H.WB_DIURN) @ H.CAM_A_SRGB.T
    Lr_test = srgb_test @ np.array([0.2126, 0.7152, 0.0722])
    bad = (srgb_test.min(axis=2) <= 0) | (Lr_test <= 1.0)
    if bad.any():
        from scipy.ndimage import gaussian_filter as _gf
        wb_ok = (~bad).astype(np.float32)
        for k in range(3):
            c_k = adus[..., k]
            adus[..., k] = np.where(bad, _gf(c_k * wb_ok, 3) / np.maximum(_gf(wb_ok, 3), 1e-9), c_k)
        print(f'sanejats {int(bad.sum())} px fora de gàmut ({100 * bad.mean():.4f} %)', flush=True)
    # 2) disc: ple amb el nivell de cel (el pou NaN generava un arc de Gibbs); el disc es
    #    pinta de negre al post, amb ploma de 14 px
    from v4_tests import lunar_coords
    d7, _, R7 = lunar_coords(7)
    d7c = np.asarray(d7[Y0:Y1, X0:X1])
    disc = d7c <= R7 + 1
    cel_est = float(np.nanmedian(adus[..., 1][d7c > R7 + 40])) * 0.9
    adus[disc] = cel_est
    # 3) variància (model; l'etapa la recalibra al cel)
    Lg = adus[..., 1]
    varG = (0.20 * np.maximum(Lg, 0) + 25.0).astype(np.float32)
    varm = np.stack([varG * 1.3, varG, varG * 1.6], axis=2)
    np.save(WORK / 'hdr_vixen_countss_v4.npy', adus)
    np.save(WORK / 'hdr_vixen_var_v4.npy', varm)
    json.dump({'nota': 'compost V4b FLOAT (sense clip de codificat) en ADU/s de càmera; disc ple de cel; '
                       'var = model 0,2·L+25 (G), recalibrada a l\'etapa foto',
               'crop_llenc': [Y0, Y1, X0, X1]}, open(WORK / 'fonts_v4.json', 'w'), indent=1)
    # 4) etapa foto original
    H.RETALL = (2, Hh - 3, 2, Ww - 3)
    os.environ['HDR_SUFIX'] = '_v4'
    os.environ['FOTO_SUFIX'] = '_v4'
    H.LLUNA = 'negra'
    H.OUT = WORK
    H.etapa_foto(SimpleNamespace(etapa='foto'))
    # 5) post: disc negre amb ploma de 14 px + croma suau dins els nuclis P3/P4
    import tifffile, cv2
    from PIL import Image
    f = WORK / 'corona_vixen_FOTO_v4.tif'
    img = tifffile.imread(str(f)).astype(np.float32) / 65535.0
    dd = d7c[2:2 + img.shape[0], 2:2 + img.shape[1]]
    dist = cv2.distanceTransform(((dd > R7 + 1)).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32)
    pes = np.clip(1.0 - dist / 14.0, 0, 1)[..., None]
    img = img * (1 - pes)
    img = np.clip(img, 0, 1)
    # NOTA: ja NO es suavitza croma als nuclis P3/P4 — amb el compost float els nuclis porten
    # l'estructura i el color reals de la 1/3200; suavitzar-los rentava el rosa de la protuberància.
    tifffile.imwrite(str(f), (img * 65535).astype(np.uint16), photometric='rgb')
    Image.fromarray((np.clip(img[::2, ::2], 0, 1) * 255).astype(np.uint8)).save(WORK / 'corona_vixen_FOTO_v4_1de2.png')
    print('->', f)

if __name__ == '__main__':
    main()
