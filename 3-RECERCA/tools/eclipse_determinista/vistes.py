"""Vistes i rebut llegible. ⛔ NORMA: sempre el llenç SENCER, mai un retall."""

from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import comu  # noqa: E402


def red(a, k):
    h, w = a.shape[:2]
    a = a[:h // k * k, :w // k * k]
    if a.ndim == 3:
        return a.reshape(h // k, k, w // k, k, 3).mean(axis=(1, 3))
    return a.reshape(h // k, k, w // k, k).mean(axis=(1, 3))


def superposa(b, d):
    return np.where(b <= 0.5, 2 * b * d, 1 - 2 * (1 - b) * (1 - d))


def tot(run: comu.Run, k: int = 8) -> dict:
    base = np.load(run.fase(3, "BASE_rgb.npy"))
    m = np.load(run.fase(3, "MASCARA.npy"))
    H, W = m.shape
    mm = red(m.astype(np.float32), k) > 0.5
    b = red(base, k)
    vistes = [("BASE corona (calibrada)", b)]
    for nom, fx in (("passa-alt", "PASSA_ALT"), ("radial · plomalls", "RADIAL"),
                    ("NRGF", "NRGF"), ("MGN", "MGN")):
        d = red(np.load(run.fase(3, f"DETALL_{fx}.npy")), k)
        vistes.append((f"base + {nom}", superposa(b, np.dstack([d] * 3))))
    P = red(np.load(run.fase(3, "MASCARA.npy")).astype(np.float32), k)
    fig, axs = plt.subplots(2, 3, figsize=(30, 22), facecolor="#000")
    for ax, (nom, im) in zip(axs.ravel(), vistes):
        ax.imshow(np.clip(np.where(mm[..., None], im, 0.0), 0, 1))
        ax.set_title(nom, color="#eee", fontsize=17); ax.set_xticks([]); ax.set_yticks([])
    axs.ravel()[-1].axis("off")
    LL = run.llegeix_rebut("F1.2_sol_llenc.json")["llenc"]
    fig.suptitle(f"{run.tren} · run {run.segell} · LLENÇ SENCER {W}x{H} px "
                 f"(±{LL['semi_Rsol'][0]:.2f} x ±{LL['semi_Rsol'][1]:.2f} R☉) · "
                 f"reduït {k}x · cap panell és un retall",
                 color="#fff", fontsize=22, y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    p = run.vista(f"LLIURAMENT_x{k}.png")
    fig.savefig(p, dpi=95, facecolor=fig.get_facecolor()); plt.close(fig)

    # ---- rebut llegible
    R = {n: run.llegeix_rebut(n) for n in sorted(os.listdir(os.path.join(run.dir, "4-rebuts")))
         if n.endswith(".json")}
    L = []
    L.append(f"# {run.tren} · run `{run.segell}`\n")
    L.append(f"Llenç **{W} × {H}** px = ±{LL['semi_Rsol'][0]:.2f} × "
             f"±{LL['semi_Rsol'][1]:.2f} R☉, nord amunt, Sol al centre.\n")
    f01 = R.get("F0.1_pedestal_blanc.json", {})
    if f01:
        L.append("## Fase 0 · calibració\n")
        L.append(f"- pedestal mesurat **{f01['resum_llums']['G1']['mediana']:.2f} DN** "
                 f"(libraw en deia `{f01['negre_libraw']}`) · porta {f01.get('porta')}")
        L.append(f"- saturació mesurada **{f01['saturacio_mesurada']}** (no {f01['blanc_libraw']})")
    f03 = R.get("F0.3_flat.json", {})
    if f03:
        L.append(f"- flat radial, centre declarat; desacord amb els invertits "
                 f"**{f03['desacord_pitjor_pct']:.2f} %** · porta {f03.get('porta')}")
    f12 = R.get("F1.2_sol_llenc.json", {})
    if f12:
        c = f12["contactes"]
        L.append("\n## Fase 1 · registre\n")
        L.append(f"- C2 **{c['C2_t']:.2f} s** · C3 **{c['C3_t']:.2f} s** · "
                 f"totalitat **{c['totalitat_s']:.2f} s**")
        L.append(f"- deriva **{f12['deriva_arcsec_s']:.4f} ″/s** · "
                 f"**{f12['n_coronals']}** fotogrames coronals")
    f13 = R.get("F1.3_registre.json", {})
    if f13:
        L.append(f"- registre fi per **correlació de fase**: {f13['n_refinats']}/{f13['n']}")
    f22 = R.get("F2.2_coherencia.json", {})
    if f22:
        L.append(f"\n## Fase 2 · LDIC\n")
        L.append(f"- guany per fotograma: dispersió **{f22['dispersio_pct']:.2f} %**, "
                 f"gauge {f22['gauge']}")
    f24 = R.get("F2.4_cel.json", {})
    if f24:
        L.append(f"- cel pel **color**: angle {f24['angle_graus']:.2f}°, condició "
                 f"{f24['condicio']:.2f}, **control {f24['control_residu_mediana_pct']:.3f} %** "
                 f"· porta {f24.get('porta')}")
        L.append(f"- color de la corona: **{f24.get('veredicte_color')}**")
        L.append("\n| r (R☉) | R/G | B/G |\n|---:|---:|---:|")
        for kk, vv in sorted(f24.get("color_corona", {}).items()):
            L.append(f"| {kk} | {vv['R/G']:.3f} | {vv['B/G']:.3f} |")
    f3 = R.get("F3_filtres.json", {})
    if f3:
        L.append(f"\n## Fase 3 · filtres\n")
        ct = f3["corba_to"]
        L.append(f"- **mode de color `{f3['mode_color']}`** — {f3['color_titol']}")
        L.append(f"  <br>{f3['color_per_que']}")
        L.append(f"- guany aplicat: **{tuple(round(g, 4) for g in f3['guany'])}** "
                 f"(després de la matriu de color de la càmera)")
        L.append(f"- una sola corba sobre la **lluminància**: pendent "
                 f"**{ct['pendent']}**/dècada, àncora **{ct['ancora']}** a 1,05–1,15 R☉, "
                 f"terra {ct['terra']} · valor d'àncora {ct['valor_ancora_L']:.4g}")
        L.append(f"- croma a baixa freqüència (σ {ct['sigma_croma_px']:.0f} px) · "
                 f"gamut acotat al **{ct['gamut_acotat_pct']:.2f} %** dels píxels "
                 f"(mai retallant per canal)")
        L.append(f"- croma de la base (p1–p99 de R−G): **{f3['croma_p1_p99_RmenysG']:.4f}** "
                 f"· porta {f3.get('porta')}")
        cs = f3.get("color_renderitzat_sRGB_lineal", {})
        if cs:
            L.append("\n**Color del que es lliura**, en sRGB lineal "
                     "(comparable amb Brno i amb el DSC06991):\n")
            L.append("| r (R☉) | R/G | B/G |\n|---:|---:|---:|")
            for kk, vv in sorted(cs.items()):
                L.append(f"| {kk} | {vv['R/G']:.3f} | {vv['B/G']:.3f} |")
        ex = f3.get("extincio_declarada", {})
        if ex:
            L.append(f"\n⏭️ **Extinció declarada**: {ex['lloc']}, Sol a "
                     f"{ex['alcada_sol_graus']}°, **X = {ex['massa_aire_X']}**, "
                     f"k_V {ex['k_V_mag_per_X']} mag/X, AOD(550) {ex['AOD_550']}. "
                     f"Vector d'extinció sola **{ex['nomes_extincio']}**. "
                     f"{ex['com_desfer_ho']} · control: {ex['control']}.")
    # ⏭️ D'ON VE CADA COSA. Perquè la dependència amb Brno sigui auditable a
    #    cada run i no depengui que algú se'n recordi (pregunta de Pere, 27-08).
    L.append("\n## D'on ve cada cosa\n")
    L.append("| | què | nota |\n|---|---|---|")
    for quin, que, nota in comu.PROCEDENCIA:
        L.append(f"| **{quin}** | {que} | {nota} |")
    L.append("\n⛔ Cap píxel ni cap correcció de Brno no entra al producte: a "
             "l'auditoria del `research/114` hi van fer de **jutge**, i "
             "l'única correcció que hauria pujat l'acord amb ells es va "
             "**refusar**. ⚠️ I els seus quatre composts **no** són quatre "
             "jutges independents (mateix equip, mateix pipeline): «Brno×Brno» "
             "és un **sostre**, no un control. El jutge independent de veritat "
             "és el **tren de la Sony**.")
    L.append("\n## Lliurables\n")
    for nom in ("F4.1_psb_resultat.json", "F4.2_capes_ldic.json", "F4.3_contactes.json"):
        v = R.get(nom)
        if v:
            L.append(f"- `{v['fitxer']}` — {v['bytes']/1e9:.2f} GB")
    cad = R.get("CADENA.json")
    if cad:
        L.append(f"\nCadena sencera en **{cad['segons_total']/60:.1f} min**.")
    txt = "\n".join(L) + "\n"
    with open(run.lliurable("REBUT.md"), "w") as fh:
        fh.write(txt)
    # ⏭️ NORMA DE PERE: tot el que ell ha de veure surt per `run.vista()`, i
    #    SEMPRE amb el llenç sencer. Res de retalls i res a fora de l'Output.
    #    (El 27-08 li vaig deixar un retall a /tmp: dues normes alhora.)
    extres = []
    fp = run.fase(3, "PROTUBERANCIES_rgb.npy")
    if os.path.exists(fp):
        pr = np.load(fp); mk = np.load(run.fase(3, "PROTUBERANCIES_msk.npy"))
        bs = np.load(run.fase(3, "BASE_rgb.npy"))
        for nom, arr in (("PROTUBERANCIES_capa", np.where(mk[..., None], pr, 0.0)),
                         ("PROTUBERANCIES_sobre_base",
                          np.where(mk[..., None], np.fmax(bs, pr), bs))):
            q = run.vista(f"{nom}_x{k}.png")
            Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)) \
                 .resize((arr.shape[1] // k, arr.shape[0] // k), Image.LANCZOS).save(q)
            extres.append(os.path.basename(q))
    return {"vista": os.path.basename(p), "rebut": "REBUT.md", "extres": extres}
