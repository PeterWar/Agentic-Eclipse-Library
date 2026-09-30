#!/usr/bin/env python3
"""V28 · comparació amb les fotos finals de Brno (Trigaza 800 mm i DHS 200/400/530 mm), anell a anell.

Per a cada anell (1,2-9 R☉): estructura azimutal = (x − mediana)/MAD del perfil polar (research/114),
a dues escales angulars (suavitzat 1° i 4,5°). Correlació de Pearson de cada producte nostre amb
cada compost de Brno; sostre = Brno × Brno (200 vs 400 vs 530 vs 800 on se solapen). I el CONTRAST
(MAD de ln del display per anell) dels seus composts contra el nostre V27, que és el que Pere veu.
Registre de Brno: `auditoria_estructura/registre2.json` (research/114). Tot al llenç comú (Sol al
centre, nord amunt).
"""
import os, sys, json, numpy as np
from scipy.ndimage import gaussian_filter1d
AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
sys.path.insert(0, os.path.join(AQUI, "..", "auditoria_estructura")); import nucli as N
OUT = "/Users/USUARI/Desktop/Eclipse 2026/IA/output/v28_20260905"
NOMS = ["TSE_2026_200mm_DHS.png", "TSE_2026_400mm_DHS.png", "TSE_2026_530mm_DHS.png", "TSE2026_Trigaza_800mm.png"]
RADIS = np.round(np.arange(1.2, 9.01, 0.2), 2); NTH = 1440
ETIQ = sys.argv[1] if len(sys.argv) > 1 else "V27"


def suau(p, deg):
    return gaussian_filter1d(np.nan_to_num(p, nan=0.0), deg / 360.0 * NTH, axis=1, mode="wrap")


def estr(p, deg):
    q = suau(p, deg); q = np.where(np.isfinite(p), q, np.nan); return N.estructura(q)


def overlay(b, d, op):
    return np.where(b < 0.5, 2 * b * (0.5 + (d - 0.5) * op), 1 - 2 * (1 - b) * (1 - (0.5 + (d - 0.5) * op)))


def main():
    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))
    B = {}
    for n in NOMS:
        br, _, _, _ = N.carrega_brno(n)
        B[n] = N.mostreja(br, reg[n]["cy"], reg[n]["cx"], reg[n]["R_sol_px"], RADIS, NTH, ang0=np.deg2rad(reg[n]["gir_deg"]))
    lum, pes, LL, S = N.carrega_nostre(run="/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z"); H, W = lum.shape; cy, cx = H / 2.0, W / 2.0; Rs = LL["R_sol_px"]
    ok = np.isfinite(pes) & (pes > 0)
    prods = {"corona sola (run 019)": np.where(ok, lum, np.nan)}
    del lum
    base = np.load(os.path.join(CAU, "base_B_rgb16.npy")).astype(np.float32) / 65535.0; Lb = (base[..., 0] + 2 * base[..., 1] + base[..., 2]) / 4; del base
    bk = np.load(os.path.join(CAU, "base_B_k025_rgb16.npy")).astype(np.float32) / 65535.0; Lk = (bk[..., 0] + 2 * bk[..., 1] + bk[..., 2]) / 4; del bk
    A = np.load(os.path.join(CAU, "capa_achf_u16.npy")).astype(np.float32) / 65535.0; P = np.load(os.path.join(CAU, "capa_passalt24_u16.npy")).astype(np.float32) / 65535.0; G = np.load(os.path.join(CAU, "capa_achf_gran_u16.npy")).astype(np.float32) / 65535.0
    pam = os.path.join(CAU, "capa_achf_ample_u16.npy"); AM = np.load(pam).astype(np.float32) / 65535.0 if os.path.exists(pam) else None
    # esvaïments com a l'etapa 4 (fi 3,5→5; el gran ja porta els seus)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rad = np.hypot(yy - cy, xx - cx) / Rs; del yy, xx
    t = np.clip((rad - 3.5) / 1.5, 0, 1); fade = 1 - t * t * (3 - 2 * t)
    A = 0.5 + (A - 0.5) * fade; P = 0.5 + (P - 0.5) * fade
    if AM is not None: Lb = overlay(Lb, AM, 0.5); Lk = overlay(Lk, AM, 0.5)
    comp = overlay(overlay(overlay(Lb, G, 0.5), A, 0.7), P, 0.4); compk = overlay(overlay(overlay(Lk, G, 0.5), A, 0.7), P, 0.4)
    mfz = np.load(os.path.join(CAU, "mascara_fusio.npy"))
    for nom, im in (("V27 base (amb cel)", Lb), ("V27 base k (cel/4)", Lk), ("V27 compost (base+detalls)", comp), ("V27 compost k", compk), ("capa ACHF fi", A), ("capa passa-alt", P), ("capa ACHF gran", G)) + ((("capa ACHF ample", AM),) if AM is not None else ()):
        prods[nom] = np.where(mfz, im, np.nan)
    Pn = {k: N.mostreja(v, cy, cx, Rs, RADIS, NTH) for k, v in prods.items()}
    # --- correlacions per anell ---
    res = {"radis": RADIS.tolist(), "corr": {}, "contrast": {}}
    for deg in (1.0, 4.5):
        Eb = {n: estr(B[n], deg) for n in NOMS}; En = {k: estr(v, deg) for k, v in Pn.items()}
        ctrl = np.nanmean(np.stack([N.corr_per_anell(Eb[a], Eb[b]) for i, a in enumerate(NOMS) for b in NOMS[i + 1:]]), axis=0)
        res["corr"][f"{deg}°"] = {"Brno×Brno (control)": ctrl.tolist()}
        for k in En:
            cs = np.stack([N.corr_per_anell(En[k], Eb[n]) for n in NOMS]); res["corr"][f"{deg}°"][k] = np.nanmean(cs, axis=0).tolist()
    # --- contrast azimutal (MAD de ln per anell) del DISPLAY: Brno (lineal del sRGB) vs V27 compost (lineal) ---
    def contrast(p):
        q = np.log(np.maximum(suau(p, 1.0), 1e-6)); q = np.where(np.isfinite(p), q, np.nan)
        med = np.nanmedian(q, axis=1, keepdims=True); return (1.4826 * np.nanmedian(np.abs(q - med), axis=1)).tolist()
    for n in NOMS: res["contrast"][n] = contrast(B[n])
    for k in ("V27 compost (base+detalls)", "V27 compost k", "V27 base (amb cel)", "corona sola (run 019)"): res["contrast"][k] = contrast(Pn[k])
    json.dump(res, open(os.path.join(OUT, "compara_brno_" + ETIQ + ".json"), "w"), indent=1)
    # --- taula ---
    print("CORRELACIÓ per anell (mitjana dels 4 composts de Brno) · escala 4,5° | 1°   —  control = Brno×Brno")
    keys = ["Brno×Brno (control)", "corona sola (run 019)", "V27 base (amb cel)", "V27 compost (base+detalls)", "V27 compost k", "capa ACHF gran"] + (["capa ACHF ample"] if AM is not None else [])
    print("  r   " + " ".join(f"{k[:14]:>15s}" for k in keys))
    for i, r in enumerate(RADIS):
        print(f"{r:4.1f}  " + " ".join(f"{res['corr']['4.5°'][k][i]:+6.2f}|{res['corr']['1.0°'][k][i]:+5.2f} " for k in keys))
    print("\nCONTRAST azimutal (MAD de ln, suavitzat 1°) per anell:")
    ck = list(res["contrast"].keys()); print("  r   " + " ".join(f"{k[:12]:>13s}" for k in ck))
    for i, r in enumerate(RADIS):
        print(f"{r:4.1f}  " + " ".join(f"{res['contrast'][k][i]:13.3f}" for k in ck))
    # --- figura ---
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 1, figsize=(11, 10))
        for k in keys: ax[0].plot(RADIS, res["corr"]["4.5°"][k], label=k)
        ax[0].set_ylim(-0.2, 1.05); ax[0].set_ylabel("correlació amb Brno (4,5°)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3); ax[0].set_title("Estructura azimutal per anell: nosaltres × Brno (mitjana dels 4) · control Brno × Brno")
        for k in ck: ax[1].plot(RADIS, res["contrast"][k], label=k)
        ax[1].set_yscale("log"); ax[1].set_xlabel("r (R☉)"); ax[1].set_ylabel("contrast azimutal (MAD ln)"); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)
        fig.tight_layout(); fig.savefig(os.path.join(OUT, "compara_brno_" + ETIQ + ".png"), dpi=110); print("figura:", os.path.join(OUT, "compara_brno_" + ETIQ + ".png"))
    except Exception as e: print("sense figura:", e)


if __name__ == "__main__":
    main()
