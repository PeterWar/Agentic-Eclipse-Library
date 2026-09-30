"""CapesTotalsV14 — la V13_Pere registrada a la corona i amb el limbe lunar net.

Encàrrec de Pere (27-08-2026, nit): «Agafa CapesTotalsV13_Pere.psd i estudia'l en
profunditat […] fes CapesTotalsV14.psd (overwrite de l'actual, que no serveix per
res), limita't a: (1) alinear totes les imatges ja existents amb la corona, movent
només una mica cada imatge; (2) retocar només una mica les màscares perquè el limbe
lunar aparegui ben net a cada capa i no introdueixi artefactes.»

⛔ A diferència de la V14 anterior (`fes_v14.py`, research/117), aquí NO es canvia
cap dada: els píxels de la V13_Pere —amb la corba de to que Pere hi va coure a mà—
es conserven byte a byte. L'edició és QUIRÚRGICA sobre el fitxer obert:

- **moviments = només rectangles**: el registre de capa i el de màscara es
  desplacen l'enter mesurat; cap canal de píxels no es re-codifica ni es
  re-mostreja (round-trip de psd-tools verificat byte a byte);
- **màscares**: les úniques que canvien de contingut són les que el mesurament
  diu que embruten el limbe, i només dins del disc lunar + 3,5 px;
- **fusionada**: es recompon (RGBA, matte blanc, RAW — mai ZIP a Image Data).

## D'on surten els moviments (mesurats, no suposats)

`mesura_desalineacio.py` correlaciona l'estructura de la corona (plomalls,
passa-alt, anell comú, saturats i limbe exclosos) entre parelles de capes, amb el
signe autocalibrat i mitges bandes per a la dispersió. El resultat NO és cap de
les dues hipòtesis de partida (geometria comuna de research/78, o cada capa al seu
fotogramade research/117): les capes cauen en CLÚSTERS separats per desplaçaments
quasi exactament ENTERS — l'empremta de retocs manuals amb les fletxes del teclat
sobre DNG que ja compartien la geometria de 572A2969:

    P (posició del contingut respecte de la capa 10, px):
      10, 11        → ( 0,  0)          (senzills, geometria de referència)
      09, 07, 05, 03 → (−1.87, −0.1)    ≈ retoc (−2, 0)
      08, 06, 04    → (−1.04, −0.9)     ≈ retoc (−1, −1)
      02            → (−2.85, +1.0)     ≈ retoc (−3, +1)   (2 parelles independents)
      01            → (−1.03, −0.0)     ≈ retoc (−1, 0)    (contra referència apilada
                       de 05+04+03+02, banda 2.02-2.55 R☉, resposta 0.238 — la banda
                       exterior degrada exactament com mana la trampa del patró fix)
      12            → (−2.86, +0.38)    per triangulació del LIMBE: P = limbe_mesurat
                       − (lluna−sol)(efemèride) − sol(ref) − biaix (calibrat amb les
                       capes 10/11, on P és conegut); el sol del fotograma s'hi
                       CANCEL·LA, o sigui que no depèn del registre de 572A2956.
                       La correlació de fase en banda fina deia (−1.98, −1.41) amb
                       resposta 0.13; mana el limbe, i la 11 tapa la 12 gairebé tota.

Els moviments són M = −P arrodonit a l'enter (cap re-mostreig; residual ≤0.15 px
llevat de la 12, ±0.5): 8 de les 12 capes es mouen d'1 a 3 px, la corona queda
alineada al marc de la capa 10 (geometria crua de 572A2969, la del llenç V13).

## Què embrutava el limbe (mesurat, i NO era on s'esperava)

Pere assenyalava les màscares de les capes 10, 11 i 12. El pes efectiu per anell
diu una altra cosa: **el vel dins del disc el posa la capa 01** (10,3 s; màscara
0,08-0,11 dins del disc × píxels de bloom a 0,50-0,87 → aporta 0,04-0,09 de nivell)
amb cues de la 09 i la 05; les màscares de la 10 i la 11 hi aporten 0,0003 (els
seus píxels dins del disc són negres). És la mateixa malaltia que `research/87` §1
(la màscara de 10,3 s a 0,33 dins del disc: Pere ja l'havia abaixada a mà a ~0,10).

La cura mínima que fa el limbe net DE VERITAT, aplicada aquí:

- es DECLARA el disc de C2 —el limbe mesurat de la mateixa capa 12, el mateix
  instant que perles i protuberàncies («només C2», decisió de Pere)— i **totes les
  màscares menys la de la 12 s'hi multipliquen per zero a dins**, amb rampa de 3 px;
- les capes 11 i 10 es multipliquen també pel SEU propi disc (mesurat a cadascuna),
  perquè el limbe surti net també capa a capa quan Pere les miri soles;
- els apilats (09…01) es multipliquen pel disc del seu fotograma de referència
  (sol(2969) + (lluna−sol) d'efemèride, radi 453,5 + 2 px de guarda: la seva Lluna
  hi és escombrada i la seva dada legítima comença a 1,4 R☉ o més enllà);
- la màscara de la 12 NO es toca: el seu contingut ÉS el limbe (i el disc fosc a
  0,024 que Pere va deixar).

⚠️ Fora d'abast, DECLARAT: la màscara de la 01 també posa un rentat groc de bloom
FORA del limbe (a 1,05-1,2 R☉; pes 0,125 de blanc pur a 1,07 R☉ vora la
protuberància). És a la zona del limbe però no és el disc: treure-ho canvia
l'aspecte del glow de la protuberància i Pere no ho ha demanat. Es reporta al rebut.
"""
from __future__ import annotations

import json
import os
import subprocess
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v13pere")
SRC = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
       "Capes Totals/CapesTotalsV13_Pere.psd")
DST = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
       "Capes Totals/CapesTotalsV14.psd")

SENSOR_A_V13 = (285.0, 355.0)

# M = −P arrodonit (vegeu el docstring); P mesurat a `desalineacio.json` + reforç
MOVIMENTS = {"12": (3, 0), "11": (0, 0), "10": (0, 0), "09": (2, 0),
             "08": (1, 1), "07": (2, 0), "06": (1, 1), "05": (2, 0),
             "04": (1, 1), "03": (2, 0), "02": (3, -1), "01": (1, 0)}
P_MESURAT = {"12": (-2.86, 0.38), "11": (0.0, -0.04), "10": (0.0, 0.0),
             "09": (-1.87, -0.13), "08": (-1.04, -0.90), "07": (-1.87, -0.06),
             "06": (-1.06, -0.92), "05": (-1.87, -0.04), "04": (-1.02, -0.93),
             "03": (-1.90, -0.07), "02": (-2.85, 0.97), "01": (-1.03, -0.01)}

RAMPA_INICI = 0.5      # px fora del limbe on comença a obrir-se la màscara
RAMPA_AMPLE = 3.0      # px d'amplada de la rampa
GUARDA_APILAT = 2.0    # px de guarda del disc de referència dels apilats


def _discos():
    """Els discos lunars (coordenades FINALS del llenç, després dels moviments)."""
    pos = json.load(open(os.path.join(CAU, "posicions.json")))
    F = pos["fotogrames"]
    limbe = json.load(open(os.path.join(AQUI, "limbe_v13.json")))
    decl = {c["num"]: c["declarat"] for c in pos["capes"]}
    ref = pos["referencia"]
    sref = np.array([F[ref]["sol_x"] + SENSOR_A_V13[0],
                     F[ref]["sol_y"] + SENSOR_A_V13[1]])

    def mesurat(num):
        L = limbe[num]
        return (np.array([L["lluna_sensor_x"] + SENSOR_A_V13[0],
                          L["lluna_sensor_y"] + SENSOR_A_V13[1]])
                + np.array(MOVIMENTS[num], float), L["R_px"])

    d = {}
    c2_centre, c2_R = mesurat("12")
    d["C2"] = (c2_centre, c2_R)
    for num in ("11", "10"):
        d[num] = mesurat(num)
    for num in ("09", "08", "07", "06", "05", "04", "03", "02", "01"):
        fr = decl[num]
        centre = (sref + np.array([F[fr]["lluna_dx"], F[fr]["lluna_dy"]])
                  + np.array(P_MESURAT[num]) + np.array(MOVIMENTS[num], float))
        d[num] = (centre, 453.5 + GUARDA_APILAT)
    return d


def _rampa(dist, R):
    return np.clip((dist - R - RAMPA_INICI) / RAMPA_AMPLE, 0.0, 1.0).astype(np.float32)


def factor_mascara(num: str, W: int, H: int, discos) -> np.ndarray | None:
    """El factor [0,1] que s'aplica a la màscara de la capa `num` al llenç FINAL.

    None vol dir «no es toca» (capa 12). La multiplicació val 1 pertot fora del
    disc + rampa: cap altre píxel de màscara no canvia (exacte en enters de 16 bits).
    """
    if num == "12":
        return None
    xx = np.arange(W, dtype=np.float32)[None, :]
    yy = np.arange(H, dtype=np.float32)[:, None]
    (cc, cR) = discos["C2"]
    f = _rampa(np.hypot(xx - cc[0], yy - cc[1]), cR)
    if num in discos:
        (oc, oR) = discos[num]
        f *= _rampa(np.hypot(xx - oc[0], yy - oc[1]), oR)
    return f


def _canal_mascara(layer):
    """Índex i ChannelData del canal de màscara d'una capa."""
    from psd_tools.constants import ChannelID
    idx = next(i for i, ci in enumerate(layer._record.channel_info)
               if int(ci.id) == int(ChannelID.USER_LAYER_MASK))
    return idx, layer._channels[idx]


def _decodifica_mascara(layer, W, H):
    """La màscara al llenç sencer, float32 0-1, i el contingut cru uint16.

    ⛔ NO es pot passar per `topil()`: als documents de 16 bits psd-tools
    converteix la màscara a 8 bits i el primer intent d'escriure-la va deixar
    el canal a MIG (40,9 MB per 81,9: profunditat 8 dins d'un canal de 16).
    Es descodifica el canal directament, amb la profunditat del document.
    """
    from psd_tools.compression import decompress
    md = layer._record.mask_data
    x0, y0, x1, y1 = md.left, md.top, md.right, md.bottom
    w, h = x1 - x0, y1 - y0
    _, cd = _canal_mascara(layer)
    depth = layer._psd.depth
    raw = decompress(cd.data, cd.compression, w, h, depth, layer._psd.version)
    dt = ">u2" if depth == 16 else np.uint8
    a = np.frombuffer(raw, dt).reshape(h, w).astype(
        np.uint16 if depth == 16 else np.uint8)
    esc = 65535.0 if depth == 16 else 255.0
    bg = float(getattr(layer.mask, "background_color", 0)) / 255.0
    full = np.full((H, W), bg, np.float32)
    sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    full[sy0:sy1, sx0:sx1] = (a[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
                              .astype(np.float32) / esc)
    return full, a, (x0, y0, x1, y1)


def main():
    from psd_tools import PSDImage
    from psd_tools.constants import ChannelID, Compression
    from psd_tools.psd.image_data import ImageData

    t0 = time.time()
    print(f"origen : {SRC}\ndestí  : {DST} (overwrite autoritzat per Pere)")
    psd = PSDImage.open(SRC)
    W, H = psd.width, psd.height
    assert psd._record.header.channels == 4, "s'esperava RGBA a la fusionada"
    discos = _discos()
    print(f"llenç {W}×{H} · disc C2 a ({discos['C2'][0][0]:.2f}, "
          f"{discos['C2'][0][1]:.2f}) R={discos['C2'][1]:.2f} px")

    compost = np.zeros((H, W, 3), np.float32)
    alfa = np.zeros((H, W), np.float32)
    rebut = {"origen": SRC, "desti": DST, "moviments": MOVIMENTS,
             "P_mesurat": P_MESURAT,
             "rampa_px": [RAMPA_INICI, RAMPA_INICI + RAMPA_AMPLE],
             "discos": {k: {"centre": list(map(float, v[0])), "R_px": float(v[1])}
                        for k, v in discos.items()}, "capes": []}

    for layer in psd:            # de BAIX a DALT
        num = layer.name.split("_")[0]
        dx, dy = MOVIMENTS[num]
        rec = layer._record

        # 1) màscara: decodifica al llenç ABANS de moure rectangles
        mfull, mcru, mbbox = _decodifica_mascara(layer, W, H)
        # el contingut de la màscara es mou amb la capa (rectangle), o sigui que
        # el factor —definit en coordenades FINALS— s'aplica al contingut MOGUT:
        # equival a avaluar el factor a (x−dx, y−dy) sobre el contingut quiet.
        f = factor_mascara(num, W, H, discos)
        canviats = 0
        if f is not None:
            fq = f if (dx, dy) == (0, 0) else np.roll(
                np.roll(f, -dy, axis=0), -dx, axis=1)
            nou = mfull * fq
            canviats = int((np.abs(nou - mfull) > 1e-6).sum())
            if canviats:
                depth = psd._record.header.depth
                esc = 65535.0 if depth == 16 else 255.0
                x0, y0, x1, y1 = mbbox
                sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
                a = mcru.copy()
                a[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = np.clip(
                    np.rint(nou[sy0:sy1, sx0:sx1] * esc), 0, esc).astype(a.dtype)
                idx, cd = _canal_mascara(layer)
                comp_old = cd.compression
                raw = (a.astype(">u2") if depth == 16 else a.astype(np.uint8)).tobytes()
                cd.set_data(raw, x1 - x0, y1 - y0, depth,
                            psd._record.header.version)
                rec.channel_info[idx] = type(rec.channel_info[idx])(
                    rec.channel_info[idx].id, len(cd.data) + 2)
                # ⛔ round-trip immediat del canal editat: la lliçó del topil.
                #    L'escriptor no pot ser l'únic lector, i no només a la
                #    fusionada: CADA canal tocat es torna a descodificar aquí.
                from psd_tools.compression import decompress
                relegit = decompress(cd.data, cd.compression, x1 - x0, y1 - y0,
                                     depth, psd._record.header.version)
                if relegit != raw:
                    raise SystemExit(f"⛔ el canal de màscara de la capa {num} "
                                     "no fa round-trip: no es desa")
                print(f"  {num}: màscara retocada ({canviats/1e3:.0f} kpx dins "
                      f"del disc; compressió {comp_old}, {depth} bits)", flush=True)
            mfinal = nou
        else:
            mfinal = mfull
            print(f"  {num}: màscara INTACTA", flush=True)

        # 2) el moviment: rectangles de capa i de màscara
        if (dx, dy) != (0, 0):
            rec.top += dy; rec.bottom += dy; rec.left += dx; rec.right += dx
            md = rec.mask_data
            md.top += dy; md.bottom += dy; md.left += dx; md.right += dx

        # 3) compost (per a la fusionada): contingut mogut × màscara moguda
        rgb = np.load(os.path.join(CAU, f"rgb_{num}.npy"), mmap_mode="r")
        c = json.load(open(os.path.join(CAU, "info.json")))
        cc = next(x for x in c["capes"] if x["num"] == num)
        bx0, by0, bx1, by1 = cc["bbox"]
        bx0 += dx; bx1 += dx; by0 += dy; by1 += dy
        pix = np.zeros((H, W, 3), np.float32)
        cob = np.zeros((H, W), np.float32)
        sy0, sy1 = max(0, by0), min(H, by1)
        sx0, sx1 = max(0, bx0), min(W, bx1)
        pix[sy0:sy1, sx0:sx1] = (rgb[sy0 - by0:sy1 - by0, sx0 - bx0:sx1 - bx0]
                                 .astype(np.float32) / 65535.0)
        cob[sy0:sy1, sx0:sx1] = 1.0
        mmoguda = mfinal if (dx, dy) == (0, 0) else np.roll(
            np.roll(mfinal, dy, axis=0), dx, axis=1)
        al = mmoguda * cob * (layer.opacity / 255.0)
        if layer.visible:
            compost = compost * (1.0 - al[..., None]) + pix * al[..., None]
            alfa = alfa + al * (1.0 - alfa)
        rebut["capes"].append({
            "num": num, "nom": layer.name, "moviment_px": [dx, dy],
            "P_mesurat_px": list(P_MESURAT[num]),
            "px_mascara_canviats": canviats,
            "mascara_mitjana_abans": float(mfull.mean()),
            "mascara_mitjana_despres": float(mfinal.mean())})
        del pix, cob, mmoguda, al, mfull, mfinal, f

    # 4) la fusionada: RGBA, matte BLANC (com la desa Photoshop), RAW
    print("  fusionada… ", flush=True)
    rgbW = compost + (1.0 - alfa[..., None])
    plans = [np.clip(np.rint(rgbW[..., j] * 65535.0), 0, 65535)
             .astype(">u2").tobytes() for j in range(3)]
    plans.append(np.clip(np.rint(alfa * 65535.0), 0, 65535).astype(">u2").tobytes())
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(plans, psd._record.header)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False

    print("  desant… ", flush=True)
    psd.save(DST)
    mida = os.path.getsize(DST)
    print(f"  {DST} · {mida/1e9:.2f} GB · {time.time()-t0:.0f} s")

    # 5) obrible amb DOS lectors independents (la lliçó del 27-08)
    p2 = PSDImage.open(DST)
    assert (p2.width, p2.height) == (W, H) and len(list(p2)) == 12
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", DST],
                       capture_output=True, text=True)
    txt = r.stdout + r.stderr
    if f"pixelWidth: {W}" not in txt or f"pixelHeight: {H}" not in txt:
        raise SystemExit("⛔ ImageIO no llegeix la fusionada: Photoshop tampoc "
                         "l'obrirà.\n" + txt)
    print("  obrible ✓ (psd-tools + ImageIO)")
    rebut["bytes"] = mida
    json.dump(rebut, open(os.path.join(CAU, "rebut_construccio.json"), "w"),
              indent=1, ensure_ascii=False)
    np.save(os.path.join(CAU, "compost_v14.npy"),
            np.clip(np.rint(compost * 65535.0), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAU, "alfa_v14.npy"),
            np.clip(np.rint(alfa * 255.0), 0, 255).astype(np.uint8))
    return rebut


if __name__ == "__main__":
    main()
