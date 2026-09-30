"""Munta el projecte de Photoshop dels DOS trens, amb els filtres com a capes.

## Què hi posa

| capa | què és |
|---|---|
| `00 BASE corona` | el compost **calibrat** dels dos trens, estirat en log |
| `01 DETALL fusionat` | el detall de la fase 3, els dos trens per inversa de variància |
| `02…` | un filtre per capa: passa-alt, desenfoc azimutal, NRGF, FNRGF, MGN, WOW, NAFE |

⛔ **La base és l'única capa amb sentit fotomètric.** Tota la resta són maneres
de veure; cap no conserva la fotometria i cap no s'ha de mesurar.

⛔ **Norma del rectangle**: cap capa es retalla a una circumferència. El retall
és **quadrat** i el que limita cada capa és el seu mapa de dada, no un cercle.

⚠️ Les capes de filtre van en mode **Superposar** i **apagades** menys la
primera: són per dosar-les d'una en una, que és com treballa Pere.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "encaix_sony"))
import comu as C  # noqa: E402
import filtres_druckmuller as FD  # noqa: E402


def estira_log(hdr: np.ndarray, pes: np.ndarray, *, baix=0.5, alt=99.7) -> np.ndarray:
    """Compost calibrat → 16 bits, en logaritme.

    ⛔ El logaritme no és cosmètic: la corona abasta més de deu magnituds i
    qualsevol estirament lineal l'ensenya o cremada o negra. Els extrems surten
    de percentils de la **dada**, no d'un número triat.
    """
    w = np.asarray(pes) > 0
    x = np.asarray(hdr, np.float32)
    v = np.log(np.maximum(x, 1e-12))
    if v.ndim == 3:
        bo = w[..., None] & np.isfinite(v) & (x > 0)
    else:
        bo = w & np.isfinite(v) & (x > 0)
    if not bo.any():
        return np.zeros(x.shape, np.uint16)
    lo, hi = np.percentile(v[bo], [baix, alt])
    y = np.clip((v - lo) / max(hi - lo, 1e-9), 0.0, 1.0)
    return np.where(bo, (y * 65535.0), 0.0).astype(np.uint16)


def estira_simetric(d: np.ndarray, pes: np.ndarray, *, k: float = 3.0) -> np.ndarray:
    """Detall (zero-mig) → 16 bits amb el zero al gris mig.

    L'escala és `k` vegades la desviació típica de la pròpia capa, o sigui que
    cada filtre surt amb el seu contrast natural i no amb un guany triat a ull.
    """
    w = np.asarray(pes) > 0
    x = np.asarray(d, np.float32)
    if not w.any():
        return np.full(x.shape, 32768, np.uint16)
    s = float(np.std(x[w])) or 1.0
    y = np.clip(0.5 + x / (2.0 * k * s), 0.0, 1.0)
    return np.where(w, y * 65535.0, 32768.0).astype(np.uint16)


def cel_per_asimptota(I: np.ndarray, pes: np.ndarray, radis: np.ndarray, *,
                      r0: float = 2.5, r1: float = 6.0) -> tuple[float, dict]:
    """El cel, ajustant `I(r) = a·r^−p + c` al perfil per anell de fora.

    ⛔ **No és la mediana d'un anell exterior.** A 4-5 R☉ encara hi ha corona, i
    prendre-hi la mediana sobresostreu: el 24-08-2026 una estimació un 9 % alta
    deixava el 64,5 % dels píxels de blau en negatiu. Aquí el cel és el terme
    **constant** d'un ajust de dos paràmetres més l'exponent, o sigui el que
    queda quan la llei de potència de la corona ja s'ha esgotat.

    ⚠️ Serveix per **veure**, no per mesurar: la separació bona és la del color
    (`research/100` §D). Aquí només es tracta de treure el pendent que impedeix
    que cap filtre d'aparença funcioni al camp ample.
    """
    from scipy.optimize import least_squares
    w = np.asarray(pes) > 0
    r = np.asarray(radis, np.float32)
    m = w & (r >= r0) & (r <= r1) & np.isfinite(I) & (I > 0)
    if m.sum() < 5000:
        return 0.0, {"cel": 0.0, "nota": "sense prou dada per ajustar"}
    vores = np.linspace(r0, r1, 60)
    idx = np.clip(np.searchsorted(vores, r[m], "right") - 1, 0, len(vores) - 2)
    rc, ic = [], []
    vals, rads = I[m], r[m]
    for k in range(len(vores) - 1):
        sel = idx == k
        if sel.sum() > 200:
            rc.append(float(np.mean(rads[sel]))); ic.append(float(np.median(vals[sel])))
    rc, ic = np.array(rc), np.array(ic)
    if rc.size < 8:
        return 0.0, {"cel": 0.0, "nota": "poques mostres"}
    def res(q):
        a, p, c = q
        return (a * rc ** (-abs(p)) + c) - ic
    q0 = [float(ic[0]) * rc[0] ** 2.5, 2.5, float(ic[-1]) * 0.5]
    sol = least_squares(res, q0, method="lm", max_nfev=4000)
    a, p, c = sol.x[0], abs(sol.x[1]), float(sol.x[2])
    c = max(0.0, min(c, float(np.min(ic))))       # ⛔ mai més que el mínim vist
    return c, {"cel": c, "exponent": float(p), "amplitud": float(a),
               "residu_rms": float(np.sqrt(np.mean(res(sol.x) ** 2))),
               "fraccio_del_minim_del_perfil": float(c / max(np.min(ic), 1e-30)),
               "rang_ajust_rsol": [r0, r1], "n_anells": int(rc.size)}


def a_rgb(g: np.ndarray) -> np.ndarray:
    return np.repeat(g[..., None], 3, axis=2)


def verifica_psb(desti: Path) -> dict:
    """Comprova que el fitxer desat és consistent, i falla si no ho és.

    ⛔ Existeix per un defecte concret: un PSB de 12 capes que `psd_tools` obria
    perfectament i que Photoshop refusava amb «final de fitxer inesperat». Cap
    longitud de secció estava malament; el que fallava era que la secció «Image
    data» tenia **la meitat** dels bytes, perquè la previsualització s'havia
    reescrit a 8 bits en un document de 16.

    O sigui: **que la llibreria que l'escriu el pugui tornar a llegir no demostra
    res**. La comprovació ha de ser contra el que diu la capçalera.
    """
    import struct
    mida = desti.stat().st_size
    with open(desti, "rb") as f:
        cap = f.read(26)
        if cap[:4] != b"8BPS":
            raise SystemExit(f"⛔ {desti.name}: no és un fitxer de Photoshop")
        versio = struct.unpack(">H", cap[4:6])[0]
        canals = struct.unpack(">H", cap[12:14])[0]
        alt = struct.unpack(">I", cap[14:18])[0]
        ample = struct.unpack(">I", cap[18:22])[0]
        prof = struct.unpack(">H", cap[22:24])[0]
        # color mode data i image resources: longitud de 4 bytes sempre
        for _ in range(2):
            n = struct.unpack(">I", f.read(4))[0]
            f.seek(n, 1)
        # ⚠️ layer and mask information: 8 bytes en PSB (versió 2), 4 en PSD
        amplada_lm = 8 if versio == 2 else 4
        n = struct.unpack(">Q" if amplada_lm == 8 else ">I", f.read(amplada_lm))[0]
        f.seek(n, 1)
        inici_dades = f.tell()
        compressio = struct.unpack(">H", f.read(2))[0]
    presents = mida - inici_dades - 2
    esperats = ample * alt * canals * (prof // 8)
    d = {"fitxer": desti.name, "versio": versio, "amplada_de_les_longituds": amplada_lm,
         "mida": mida, "dimensions": [ample, alt], "canals": canals, "profunditat": prof,
         "image_data_inici": inici_dades, "compressio": compressio,
         "bytes_presents": presents, "bytes_esperats_si_RAW": esperats}
    if compressio == 0 and presents != esperats:
        raise SystemExit(
            f"⛔ {desti.name}: la secció «Image data» té {presents} bytes i la capçalera "
            f"({ample}×{alt}, {canals} canals, {prof} bits) n'exigeix {esperats}. "
            f"Diferència {esperats - presents:+d} (raó {esperats / max(presents, 1):.4f}). "
            f"Photoshop hi trobarà un final de fitxer inesperat.")
    if compressio == 0 and presents == esperats:
        d["estat"] = "PASS"
    else:
        d["estat"] = f"comprimit ({compressio}), la mida no es pot comprovar directament"
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arrel", type=Path, required=True,
                    help="directori amb dos_trens_filtrats/, dos_trens/, sony_llenc_comu_coh/")
    ap.add_argument("--sortida", type=Path, required=True)
    ap.add_argument("--radi-max", type=float, default=6.0,
                    help="mig costat del retall QUADRAT, en R☉")
    ap.add_argument("--nom", default="Eclipsi_2026_dos_trens.psb")
    ap.add_argument("--sense-psb", action="store_true", help="només els TIFF")
    # ⏭️ 26-08-2026, demanat per Pere (desplegar el camp COMPLET): sense igualar,
    # el graó de nivell entre petjades (Sony/Vixen ×1,12 mesurat per radi al
    # dos_trens.json) entra a tots els filtres per anell com una discontinuïtat
    # i (graó)/(σ d'anell) fabrica els artefactes de vora que Pere va marcar el
    # 25-08. ⚠️ NOMÉS PER VEURE (D1): la capa 00 continua sent la calibrada
    # sense tocar; la igualació s'aplica a la base dels filtres i al 00b.
    ap.add_argument("--igualar-trens", action="store_true",
                    help="iguala la Sony a la Vixen amb el quocient per radi i "
                         "cus la costura amb una rampa; exigeix cobertura Sony >= 3")
    a = ap.parse_args()

    dtf = a.arrel / "dos_trens_filtrats"
    det = np.load(dtf / "DETALL_ln.npy", mmap_mode="r")
    H, W = det.shape
    cy, cx = H / 2.0, W / 2.0
    m = int(round(a.radi_max * C.R_SOL_PX))
    y0, y1 = max(0, int(cy) - m), min(H, int(cy) + m)
    x0, x1 = max(0, int(cx) - m), min(W, int(cx) + m)
    print(f"llenç {W}×{H} → retall {x1-x0}×{y1-y0} px  (±{a.radi_max:.1f} R☉)")
    sl = (slice(y0, y1), slice(x0, x1))
    hc, wc = y1 - y0, x1 - x0

    D = np.asarray(det[sl], np.float32)
    qui = np.load(dtf / "QUI_MANA.npy", mmap_mode="r")[sl]
    pes = (np.asarray(qui) > 0).astype(np.float32)
    if not pes.any():                    # QUI_MANA pot ser un índex de tren
        pes = np.isfinite(D).astype(np.float32)
    pes = (pes > 0) & np.isfinite(D)
    pes = pes.astype(np.float32)

    import tifffile
    base = tifffile.memmap(str(a.arrel / "dos_trens" / "VIXEN_al_llenc_BBsol_float32.tif"),
                           mode="r")[sl]
    sony = np.load(a.arrel / "sony_llenc_comu_coh" / "SONY_LLENC_BBsol.npy",
                   mmap_mode="r")[sl]
    base = np.asarray(base, np.float32)
    sony = np.asarray(sony, np.float32)
    # ⛔ la base: la Vixen on hi arriba i la Sony a fora. Cap frontera dibuixada:
    # el criteri és tenir dada, i prou.
    hi_ha_v = np.isfinite(base).all(2) & (base[..., 1] > 0)
    dq_igualar = None
    if a.igualar_trens:
        import json as _json
        from scipy.ndimage import binary_fill_holes, distance_transform_edt
        _dt = _json.loads((a.arrel / "dos_trens.json").read_text())
        _pr = _dt["quocient_sony_entre_vixen"]["per_radi"]
        _rq = np.array([f["r_rsol"] for f in _pr], np.float32)
        _q = np.array([f["sony_entre_vixen"] for f in _pr], np.float32)
        yyq = (np.arange(hc, dtype=np.float32)[:, None] + y0 - cy)
        xxq = (np.arange(wc, dtype=np.float32)[None, :] + x0 - cx)
        rr_q = np.hypot(xxq, yyq) / np.float32(C.R_SOL_PX)
        del yyq, xxq
        q_px = np.interp(rr_q, _rq, _q, left=float(_q[0]), right=float(_q[-1]))
        sony = (sony / q_px[..., None].astype(np.float32)).astype(np.float32)
        # cobertura mínima de la Sony: la franja esfilagarsada de la vora són
        # píxels amb 1-2 contribucions i soroll gegant — criteri de dada, no cercle
        _cob = np.load(a.arrel / "sony_llenc_comu_coh" / "SONY_COBERTURA.npy",
                       mmap_mode="r")[sl][..., 1]
        sony = np.where((np.asarray(_cob) >= 3)[..., None], sony, np.nan).astype(np.float32)
        # costura cosida amb rampa smoothstep de 150 px des de la vora de la
        # petjada Vixen (forats interiors plens ABANS: la trampa canònica)
        _ext = binary_fill_holes(hi_ha_v)
        _dist = distance_transform_edt(_ext).astype(np.float32)
        _u = np.clip(_dist / 150.0, 0.0, 1.0)
        pv = (_u * _u * (3.0 - 2.0 * _u)).astype(np.float32)
        pv = np.where(hi_ha_v, pv, 0.0)
        hi_ha_s = np.isfinite(sony).all(2) & (sony[..., 1] > 0)
        num_f = (pv[..., None] * np.nan_to_num(base)
                 + ((1.0 - pv) * hi_ha_s)[..., None] * np.nan_to_num(sony))
        den_f = pv + (1.0 - pv) * hi_ha_s
        fons = np.where(den_f[..., None] > 0, num_f / np.maximum(den_f[..., None], 1e-9),
                        np.nan).astype(np.float32)
        dq_igualar = {"quocient_mediana": float(_dt["quocient_sony_entre_vixen"]["mediana"]),
                      "rampa_px": 150.0, "cobertura_sony_minima": 3,
                      "avis": "NOMES PER VEURE (D1): la capa 00 calibrada no es toca"}
        del num_f, den_f, _dist, _ext, _u
    else:
        fons = np.where(hi_ha_v[..., None], base, sony).astype(np.float32)
    pes_base = (np.isfinite(fons).all(2) & (fons[..., 1] > 0)).astype(np.float32)

    yy = (np.arange(hc, dtype=np.float32)[:, None] + y0 - cy)
    xx = (np.arange(wc, dtype=np.float32)[None, :] + x0 - cx)
    rr = (np.hypot(xx, yy) / C.R_SOL_PX).astype(np.float32)
    ph = np.arctan2(yy * np.ones_like(xx), xx * np.ones_like(yy)).astype(np.float32)
    centre = (cy - y0, cx - x0)

    cel, dcel = cel_per_asimptota(fons[..., 1], pes_base, rr)
    print(f"  cel per asímptota: {cel:.4g}  ({100*dcel.get('fraccio_del_minim_del_perfil', 0):.1f} %"
          f" del mínim del perfil, exponent {dcel.get('exponent', 0):.2f})")
    sense_cel = np.maximum(fons[..., 1] - np.float32(cel), 0.0).astype(np.float32)
    # ⛔ els filtres d'aparença van sobre la base SENSE cel: amb el cel posat, a
    # 5 R☉ n'hi ha nou vegades més que corona i tots ells acaben ensenyant el cel.
    lnI = np.where((pes_base > 0) & (sense_cel > 0),
                   np.log(np.maximum(sense_cel, 1e-12)), 0.0).astype(np.float32)

    capes = [("00 · BASE corona · dos trens (calibrada)",
              a_rgb(estira_log(fons[..., 1], pes_base)), pes_base, "normal", True),
             ("00b · BASE corona · cel tret per asímptota",
              a_rgb(estira_log(sense_cel, pes_base)), pes_base, "normal", False)]
    # ⏭️ 26-08 (demanat per Pere): la base EN COLOR. Balanç de blancs de
    # l'anell 2-3 R☉ (el criteri de sempre de les vistes) i el MATEIX
    # estirament log per als tres canals (mateixos lo/hi, trets del G):
    # així el color són les DIFERÈNCIES en log i no s'inventa res. Per a
    # l'estil clàssic: posar-la en mode «Color» damunt de la lluminància.
    _w3 = pes_base > 0
    _anell = _w3 & (rr > 2.0) & (rr < 3.0)
    if _anell.sum() > 10000:
        _wb = [float(np.nanmedian(fons[..., 1][_anell]) /
                     max(np.nanmedian(fons[..., i][_anell]), 1e-30)) for i in range(3)]
    else:
        _wb = [1.0, 1.0, 1.0]
    _g = np.where(_w3, fons[..., 1], np.nan)
    _v = np.log(np.maximum(_g, 1e-12))
    _bo = _w3 & np.isfinite(_v) & (_g > 0)
    _lo, _hi = np.percentile(_v[_bo], [0.5, 99.7])
    _col = np.zeros(fons.shape[:2] + (3,), np.uint16)
    for i in range(3):
        _vi = np.log(np.maximum(fons[..., i] * np.float32(_wb[i]), 1e-12))
        _yi = np.clip((_vi - _lo) / max(_hi - _lo, 1e-9), 0.0, 1.0)
        _col[..., i] = np.where(_bo, _yi * 65535.0, 0.0).astype(np.uint16)
    capes.append(("00c · BASE corona en COLOR (wb anell 2-3 R☉; mode Color per a l'estil clàssic)",
                  _col, pes_base, "normal", False))
    del _col, _g, _v

    def afegeix(nom, arr, diag=None):
        # visible només la primera capa de filtre (el detall fusionat): la
        # resta s'encenen d'una en una, que és com es dosen.
        capes.append((nom, a_rgb(estira_simetric(arr, pes)), pes, "overlay",
                      len(capes) == 2))
        print(f"  {nom}", "" if diag is None else f"· rms {diag.get('rms', 0):.5f}")

    afegeix("01 · DETALL fusionat · ACHF multi-σ (fase 3)", D)
    d, g = FD.passa_alt(D, pes, 8.0);            afegeix("02 · PASSA-ALT σ=8 px", d, g)
    d, g = FD.passa_alt(D, pes, 32.0);           afegeix("03 · PASSA-ALT σ=32 px", d, g)
    d, g = FD.desenfoc_radial(D, pes, centre, sigma_az_graus=1.5)
    afegeix("04 · DESENFOC AZIMUTAL 1,5° (realça els raigs)", d, g)
    d, g = FD.desenfoc_radial(D, pes, centre, sigma_r_px=6.0)
    afegeix("05 · DESENFOC RADIAL 6 px (realça el que és circular)", d, g)
    d, g = FD.nrgf(lnI, pes_base, rr);           afegeix("06 · NRGF", d, g)
    d, g = FD.fnrgf(lnI, pes_base, rr, ph, ordre=6); afegeix("07 · FNRGF ordre 6", d, g)
    d, g = FD.mgn(lnI, pes_base);                afegeix("08 · MGN", d, g)
    d, g = FD.wow(lnI, pes_base, n_escales=6);   afegeix("09 · WOW", d, g)
    d, g = FD.nafe(lnI, pes_base, sigma=40.0);   afegeix("10 · NAFE", d, g)

    a.sortida.mkdir(parents=True, exist_ok=True)
    rebut = {"cel_per_asimptota": dcel, "igualar_trens": dq_igualar,
             "llenc_original": [int(W), int(H)], "retall": [int(wc), int(hc)],
             "origen_del_retall": [int(x0), int(y0)], "radi_max_rsol": a.radi_max,
             "r_sol_px": float(C.R_SOL_PX), "escala_arcsec_px": float(C.ESCALA),
             "capes": [c[0] for c in capes], "arrel": str(a.arrel)}
    def _net(x: str) -> str:
        """Nom de fitxer sense símbols: σ, °, comes i parèntesis no hi ajuden."""
        tr = {"σ": "sigma", "°": "graus", "☉": "sol", "·": "-", "," : ".",
              "(": "", ")": "", "/": "-", "=": "", " ": "_", "à": "a", "è": "e",
              "é": "e", "í": "i", "ò": "o", "ó": "o", "ú": "u", "ç": "c"}
        return "".join(tr.get(c, c) for c in x).strip("_")

    for nom, rgb, _, _, _ in capes:
        parts = nom.split(" · ")
        f = a.sortida / (_net(parts[0]) + "_" + _net(parts[1]) + ".tif")
        tifffile.imwrite(str(f), rgb, photometric="rgb", compression="zlib")
        print(f"  → {f.name}")

    if not a.sense_psb:
        from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
        psd = new_psb(wc, hc)
        for nom, rgb, w, blend, vis in capes:
            from psd_tools.constants import BlendMode
            bm = BlendMode.OVERLAY if blend == "overlay" else BlendMode.NORMAL
            add_pixel_layer(psd, rgb, nom, mask8=(w > 0).astype(np.uint8) * 255,
                            blend=bm, visible=vis)
        # ⛔ L'ORDRE MANA, i el 25-08-2026 el vaig posar al revés: la docstring de
        # `finalize_lr16` diu «DESPRÉS de l'últim append i ABANS de set_merged».
        # Amb l'ordre invertit, `set_merged` posa `_updated = False` i tot seguit
        # `finalize_lr16` crida `_update_record()`, que el torna a posar a True;
        # llavors `save()` es refà la previsualització amb `composite()`, que
        # retorna una imatge **PIL de 8 bits**, i la secció «Image data» queda amb
        # la MEITAT exacta dels bytes que la capçalera de 16 bits promet.
        # Photoshop hi topa amb l'EOF; psd_tools no, perquè el seu lector RAW es
        # menja el que queda. Al PSB de 3966×3966 hi faltaven 47.187.468 bytes.
        finalize_lr16(psd)
        set_merged(psd, capes[0][1])
        dst = a.sortida / a.nom
        # ⛔ I no ens refiem NOMÉS de l'ordre. La causa arrel d'aquell defecte no
        # és que dues línies estiguessin canviades de lloc: és que `set_merged`
        # promet «no recomponguis» amb una bandera que qualsevol altra crida pot
        # tornar a activar sense dir-ho. Aquí es torna a apagar just abans de
        # desar, que és l'únic instant en què la promesa ha de ser certa.
        if getattr(psd, "_updated", False):
            psd._updated = False
        psd.save(str(dst))
        ver = verifica_psb(dst)          # ⛔ falla tancat si el fitxer no quadra
        print(f"  verificació: {ver['estat']}  ·  image data {ver['bytes_presents']} bytes "
              f"de {ver['bytes_esperats_si_RAW']} exigits")
        rebut["psb"] = {"fitxer": str(dst), "bytes": dst.stat().st_size,
                        "sha256": C.sha256(dst), "verificacio": ver}
        print(f"\n  → {dst}  ({dst.stat().st_size/2**30:.2f} GiB)")
    C.desa_json(a.sortida / "munta_photoshop.json", rebut)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
