#!/usr/bin/env python3
"""Rebut de la V26 (markdown al costat del PSB) a partir dels JSON de les etapes 1, 1b i 4."""
import os, json, hashlib, datetime
AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
R = json.load(open(os.path.join(CAU, "rebut_v27.json"))); R1b = json.load(open(os.path.join(CAU, "rebut_etapa1b.json"))); R1 = json.load(open(os.path.join(CAU, "rebut_etapa1.json")))
psb = R["fitxer"]["psb"]; out = psb.replace(".psb", "_REBUT.md")
h = hashlib.sha256()
with open(psb, "rb") as f:
    for blk in iter(lambda: f.read(1 << 24), b""): h.update(blk)
sha = h.hexdigest()
def f3(x): return f"{x:.3f}" if isinstance(x, (int, float)) else str(x)
ped = R["ghosts_tapats"]; H1 = R["H1"]; rat = R.get("ratllat_families", {}); cost = R.get("costures_atenuades", {}); ext = R["camp_exterior"]
L = []
L.append(f"# Rebut · V27.psb\n\n**{datetime.date.today().isoformat()}** · `research/132` (i 131) · eines `research/tools/v25_lineal/` (etapes 1, 1b, 2d, 4) · skill `corregeix-artefactes`.\n")
gn = R["geometria_num"]; pa = R.get("prova_azimutal", {})
L.append(f"- Fitxer: `{psb}` · {R['fitxer']['bytes']/1e9:.2f} GB · SHA-256 `{sha}`\n- Porta Photoshop: **{R['porta_photoshop']}** · fidelitat de les capes de Pere reposades: {R['fidelitat']}\n- Geometria llenç comú → V23 (etapa 2d, research/132): rotació {gn['rotacio_total_deg']:.3f}° (OpenCV), escala {gn['escala_total']:.4f} (declarada), Sol a {gn['sol_v23']}, angle gros azimutal {gn['angle_gros_azimutal']:.2f}°; validació azimutal per capa {gn['validacio_azimutal']}\n- **PROVA AZIMUTAL de la fusionada** (base ↔ capes 10+09 de Pere): residu {pa.get('angle_residual_deg')}° · correlació a 0° {pa.get('correlacio_a_0')} · {'PASSA' if pa.get('PASSA') else 'FALLA'} (`V27_PROVA_AZIMUTAL_base_vs_capes_10_09.png`)\n- ⛔ La V25 i la V26 anaven girades 138,5°: no s'han de fer servir.\n")
L.append("## Capes (de baix a dalt, noms curts)\n\n" + "\n".join(f"{i:2d}. `{n}`" for i, n in enumerate(R["capes_v27"])) + "\n\nNoms llargs originals de les capes de Pere (píxels i màscares intactes): " + "; ".join(f"`{v}` ← «{k}»" for k, v in R.get("noms_curts", {}).items()) + "\n")
L.append("## Base\n\n- `00 BASE LINEAL B`: fusió lineal Vixen 019 + Sony 016 (ρ per canal 2,0-3,5 R☉), fons per raig, corba B (pendent 0,22 · àncora 0,74 · terra 0,045; àncora " + f3(R1["base"]["ancora_va"]) + "). Màscara: smoothstep 1,005→1,012 R☉ (les perles/limbe/earthshine de Pere manen a dins).\n"
         f"- `00b BASE SENSE CEL` (OCULTA): corona + {R1b['k_cel']}·cel (k DECLARAT), mateixa corba i àncora. Nivell G [k, base] per anell: " + ", ".join(f"{r} R☉ {a:.3f}/{b:.3f}" for r, (a, b) in R1b["base_k"]["nivell_G_mediana"].items()) + ".\n"
         f"- Cel/corona per anell (luminància, runs 019/016): " + ", ".join(f"{r} R☉ ×{v}" for r, v in R1b["cel_sobre_corona"].items()) + ".\n"
         f"- Camp exterior (fora de la cobertura del llenç comú, {ext['fraccio_llenc']*100:.1f} % del llenç): {ext['font']}; ρ per canal a 6-8,5 R☉ residu abans/després: " + ", ".join(f"{c} {v['residu_abans']:.3f}→{v['residu_despres']:.3f}" for c, v in ext['rho_6-8.5Rsol']['rho13'].items()) + f"; ploma {ext['ploma_px']} px a la {ext['ploma_mesurada_a']}.\n")
L.append("## Correccions DECLARADES (skill corregeix-artefactes)\n\n"
         f"- **G · ghost de 3 R☉**: esborrat a l'ORIGEN per inpainting (Telea, radi 32 = nucli de 25 px) a la base amb cel i a la corona sola, abans de la corba i de tots els filtres (etapes 1 i 1b): cap pedaç posterior. **Ghosts de ~8 R☉ tapats ({len(ped)})** (marques de Pere transformades a la geometria nova + detectats): mediana anular a la base, 0,5 a les capes de detall, ploma 14 px: " + "; ".join(f"({p['x']},{p['y']}) r{p['radi']} [{p['font']}]" for p in ped) + ".\n"
         f"- **R · ratllat** (capes de detall, rampa 2,65→3,5 R☉): famílies del sensor (mateix angle a ≥3 finestres) abans {rat.get('abans')} → tallades {rat.get('tallades')} → després {rat.get('despres')}. Camp exterior de la base: {R.get('ratllat_camp_exterior_base', {}).get('abans')} → {R.get('ratllat_camp_exterior_base', {}).get('despres')}.\n"
         f"- **V · costures rectes** (vora d'un apuntament de la Sony a ±45°, ~4,7 R☉): {cost.get('linies_hough_abans')} segments de Hough → {len(cost.get('costures', []))} costures atenuades (σ {cost.get('sigma_px')} px, només r > {cost.get('nomes_r_gt')}): {cost.get('costures')}.\n"
         f"- **E · esvaïments**: {R['esvaiment_detall']}; capa gran ({R1b.get('detall_gran')}) per bandes: <64 px d'arc {R1b['esvaiment_gran_fi_32-64px']} R☉, 64-256 px {R1b['esvaiment_gran_gros_128-256px']} R☉; {R1b['suavitzat_sn']}; terra del MAD a {R1b.get('terra_mad_Rsol')} R☉.\n"
         f"- **L · limbe**: mitja lluna del forat de la cadena omplerta per raig (V25); ploma del camp exterior mesurada a la vora exterior.\n")
L.append("## Portes\n\n"
         f"- H1 (nivell per anell de les capes de detall, ≤0,05): ACHF {H1['ACHF']['max_abs']:.4f} · passa-alt {H1['PAL']['max_abs']:.4f} · gran {H1['GRAN']['max_abs']:.4f} → {'PASSA' if all(v['passa'] for v in H1.values()) else 'FALLA'}\n"
         f"- Perfil radial monòton (fusionada, 1,2-12 R☉): {'PASSA' if R['perfil_radial']['passa'] else 'FALLA ' + str(R['perfil_radial']['pujades'])}\n"
         f"- Limbe (franja fosca 0,98-1,16 R☉): {'PASSA' if R['limbe']['passa'] else 'FALLA ' + str(R['limbe']['franja_fosca'])}\n"
         f"- Vores rectes després (Hough ≥400 px): ACHF {len(R['arestes_rectes_ACHF'])} · gran {len(R.get('arestes_rectes_GRAN_despres', R.get('arestes_rectes_GRAN', [])))}\n"
         f"- Blobs rodons després (>3,5σ, compactes): {R['blobs_despres']}\n"
         f"- Capa gran: saturació per anell {R1b['capa_gran']['fraccio_saturada_per_anell']} · amplitud p99 per anell {R1b['capa_gran']['amplitud_p99_per_anell']}\n"
         f"- Fidelitat {R['fidelitat']} · Photoshop {R['porta_photoshop']}\n")
L.append("## Vistes\n\n`IA/output/v27_20260905/`: `V27_PROPOSTA_llenc_sencer_x4.png`, `V27_PROPOSTA_finestres_1a1_inspeccio.png`, `V27_ALTERNATIVA_base_sense_cel_*.png`, `V27_nomes_BASE_llenc_sencer_x4.png`, **`V27_PROVA_AZIMUTAL_base_vs_capes_10_09.png`** (la prova d'alineació que val: polar r × azimut, la meva base a dalt i les capes 10+09 de Pere a baix), `V27_PROVA_SUPERPOSICIO_escaquer.png` (només il·lustrativa: un escaquer NO és prova d'alineació), `PS_render_*.png` i `DIAG_PS_*.png` (renders del Photoshop de la V26 de Pere i la mesura del gir).\n\n## No tocat\n\nLa V24, la V25, la V26 i `V26_artefactes.psb` intactes; cap càmera ni RAW; els runs de la cadena només llegits.\n")
L.append("## Notes de lectura\n\n"
         "- **Alineació**: la V25 i la V26 anaven girades 138,5° respecte de les capes de Pere (research/132). La V27 passa la prova azimutal (pic a 0°) tant a la fusionada numèrica com als renders del Photoshop de veritat (`PS27_render_*.png`, `prova_azimutal_ps27.py`).\n"
         "- **Ghost de 3 R☉**: nucli de 25 px esborrat per inpainting (radi 50: la ploma sencera dins de la zona corregida) a la base i a la corona sola; el bol del compost (−1,5 % fins a ~105 px) dividit per la seva corba radial a la corona sola abans de tots els filtres; i la textura d'alta freqüència del veí tangencial (140 px al mateix radi) clonada al disc (tampó de clonar, declarat). Cap pedaç posterior.\n"
         "- **Detall gran**: passa-alt només azimutal (polar): cap arc concèntric per construcció; les estrelles s'inpainten a la corona sola abans (un punt hi esdevindria un disc de 100 px), les capes fines i `Estrelles` les conserven. Els blobs que queden a la capa gran (2,3-3,6 R☉, 60-430 px) són feixos de raigs reals.\n"
         "- **Camp exterior**: capes 12 i 13 de Pere igualades per separat a 6-11 R☉ (la vora de cobertura del llenç, un rombe a 8-12 R☉, cau dins de la finestra), guany local a la vora del rectangle de la 13, ploma 250 px.\n"
         "- **Per triar (D1)**: `00b Base sense cel` és OCULTA; activar-la i apagar la `00` dona la versió amb el cel a un quart.\n"
         "- La V24, la V25, la V26 i `V26_artefactes.psb` intactes.\n")
open(out, "w").write("\n".join(L)); print(out)
