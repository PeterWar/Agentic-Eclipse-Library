"""C5 (V36) · Rebut al costat del PSB i a lliurables, manifest i còpia IA. Només després de c4 publish."""
from comu36 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')


def main():
    pub = json.loads((REB36 / 'C4_publish.json').read_text()); ver = json.loads((REB36 / 'C4_verification.json').read_text()); gate = json.loads((REB36 / 'C4_photoshop_gate.json').read_text())
    b3 = json.loads((REB36 / 'B3_fusio.json').read_text()); c3 = json.loads((REB36 / 'C3_portes.json').read_text()); b4 = json.loads((REB36 / 'B4a_capes_cadena.json').read_text()); a8 = json.loads((REB36 / 'A8_roi_farcit.json').read_text())
    recs = {t: json.loads((HERE36 / 'purs/receipts' / (t + '.json')).read_text()) for t in ('P01_NRGF', 'P02_RHEF', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral')}
    prof = b3['trains']['perfil_pesos']; g8 = c3['vora_8s']['perfil_gra_base']; bins = g8['base_V35']['bins_px']
    def pick(d, lo, hi):
        v = [x for b, x in zip(bins, d) if x is not None and lo <= b < hi]; return float(np.mean(v)) if v else float('nan')
    L = ['# V36 — les marques de la V35: l\'errata de la LUT Sony corregida, el rang continu de la RHEF, i la vora dels 8 s mesurada i declarada (research/153)', '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere («mira V35_Artefactes»). PSB LLEUGER: base lineal V36 + les 10 capes iterades. V35.psb intacta.", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Modes/màscares de les capes: de `V32.psb`.", '',
         '## Què hi havia a la V35 (26 marques; 0 a la base i a 01/02/04/05)', '',
         "1. **Quadrat gruixut al P05 i franja al 06 a 3,3–3,8 R☉**: la vora d'entrada dels dos fotogrames de 8 s de la Sony és un quadrat arrodonit alineat amb el llenç (vinyetatge del 300 mm f/2,8 sobre el cel: rombe al sensor, que va a 45°), i el gra del compost hi baixava ~35 % en ~110 px (la variància canvia mentre el pes dels 8 s encara és petit).",
         "2. **Arcs fins a 1,04–1,06 al NRGF (oest)**: el forat lunar és la unió de les posicions de la Lluna (radi 1,005–1,046 segons l'azimut); els anells 1,005–1,046 són parcials i la V35 en prenia la mitjana parcial → salt al primer anell sencer.",
         "3. **Tres línies horitzontals a la RHEF (az 178°)**: bandes de fase del rang discret amb anells d'1 px prop dels eixos.",
         "4. **Arcs fins a 1,03–1,08 al MGN/WOW (oest)**: franja de la unió temporal (píxels vistos només abans que la Lluna els tapés) i graó del farcit; dues alternatives de farcit provades en ROI i refusades (A8).",
         "5. ⛔ **ERRATA**: la LUT de linealitat de la Sony declarada a la V34 i la V35 no s'havia aplicat mai (`run.tren == 'sony'` contra `SONYTOT`). La V36 l'aplica de debò.", '',
         '## Què canvia la V36', '',
         f"1. Vora dels 8 s de la Sony: RESIDU DECLARAT. Dues cures provades i refusades (finestra quadràtica 0,10→0,85 als 8 s: +14 % de gra a tot el camp on són al 10–50 % de saturació; esvaïment espacial ss(d,0,900)³: bony de gra +30 % en 1200 px). Gra fi de la base contra la distància al contorn de mig pes (V35 → V36, ha de ser igual llevat de la LUT): dins (+50…+250 px) {pick(g8['base_V35']['gra_fi_pct'], 50, 250):.3f} → {pick(g8['base_V36']['gra_fi_pct'], 50, 250):.3f} %; fora (−250…−50) {pick(g8['base_V35']['gra_fi_pct'], -250, -50):.3f} → {pick(g8['base_V36']['gra_fi_pct'], -250, -50):.3f} %.",
         "2. LUT de linealitat de la Sony aplicada (fins a +1,9 % als píxels més brillants dels fotogrames Sony; abans, 0).",
         f"3. RHEF (b4d) amb rang en radi CONTINU (CDF dels dos anells veïns interpolades per la posició subpíxel): les bandes horitzontals de fase a l'eix −x desapareixen als retalls. La compleció dels {recs['P01_NRGF']['parameters']['n_inner_partial_rings']} anells parcials interiors (1,005–{recs['P01_NRGF']['parameters']['r_in_R']:.3f} R☉) es va provar i refusar (empitjorava 1,003–1,02); NRGF com la V35.",
         "4. P03/P04/P05: recepta V35 (farcit del perfil mitjà); les alternatives provades empitjoraven (A8). 01–06: recepta exacta.", '',
         '## Portes (V35 → V36)', '', '| capa | graó aparellat al contorn dels 8 s (÷ rms; nul) | biaix d\'anell al limbe 1,03–1,3 (σ) | gra fi 4 R☉ |', '|---|---|---|---|']
    for k, row in c3['vora_8s']['capes'].items():
        g = lambda d: f"{d['grao_sobre_rms']:+.2f} ({d['nul_sobre_rms']:+.2f})"; lb = c3['limbe_biaix_anell_sigma'][k]; gr = c3['gra'][k]; rr = np.array(gr['V35']['r']); i4 = int(np.argmin(np.abs(rr - 4)))
        L.append(f"| {k} | {g(row['V35'])} → {g(row['V36'])} | {lb['V35']:.2f} → {lb['V36']:.2f} | {gr['V35']['fi'][i4]:.4f} → {gr['V36']['fi'][i4]:.4f} |")
    ns = c3['nrgf_salt_primer_anell']; rb = c3['rhef_bandes_eix']
    L += ['', f"NRGF, salt màxim entre anells de 0,005 R☉ a 1,00–1,10: V35 {ns['V35']['max_salt_entre_anells_0.005_sigma']:.2f} σ (a {ns['V35']['r_salt']:.3f}) → V36 {ns['V36']['max_salt_entre_anells_0.005_sigma']:.2f} σ (a {ns['V36']['r_salt']:.3f}).",
          f"RHEF, bandes prop de l'eix −x (rms del passa-alt de la mediana per fila, ÷ control a 45°): V35 {rb['V35']['quocient']:.2f} → V36 {rb['V36']['quocient']:.2f}.",
          f"Porta A+B: {'acceptada' if b3['pointings']['porta']['acceptada_A+B'] else 'refusada'}; δ holdout G {b3['trains']['channels']['1']['holdout_delta_despres_median_abs_pct']:.2f} %; pes Vixen 1,0–1,9 R☉: " + ', '.join(f"{z['frac_vixen_p50']:.2f}" for z in prof[:6]) + '.',
          '', '| r (R☉) | gra fi base V35 | V36 (%) |', '|---|---|---|']
    g35, g36 = c3['gra']['base_V35'], c3['gra']['base_V36']
    for r_ in (1.3, 2.0, 2.4, 2.65, 3.0, 3.3, 3.6, 4.0, 5.0, 6.0, 8.0):
        rr = np.array(g35['r']); i = int(np.argmin(np.abs(rr - r_))); L.append(f"| {r_} | {g35['fi_pct'][i]:.3f} | {g36['fi_pct'][i]:.3f} |")
    L += ['', '## Límits i preu declarat', '',
          "- La vora dels 8 s (quadrat pel vinyetatge, graó de gra del 14 % en ~200 px) queda: origen de captura (salt ×4); les dues cures provades costaven més senyal/soroll del que arreglaven.",
          "- Farcit dels operadors isotròpics: el de la V35; el residu fi al limbe oest (1,04–1,06) inclou la franja de la unió temporal (menys fotogrames), que la norma diu conservar. Les línies fines de l'à trous (CX+694, CX−1152) són del mètode amb un objecte compacte brillant al centre.",
          "- Contorns d'entrada dels fotogrames de la Vixen (interior): sense canvis (Pere no els ha marcat a la V35).",
          "- Judici visual de Pere obert. Vistes: `output/v36_20260908/lliurables/vistes/` (retalls V35|V36 a les marques, polars, gra per radi, A6–A8).", '',
          "Codi: `research/tools/v36_20260908/` (comu36, a1, b1, b2, b3, b4a, b4c_purs (=V35), b4d, c3, c4, c5, d1; a8 i b4c_purs_experimental = prova refusada). Rebuts: `output/v36_20260908/4-rebuts/`. Revisió de marques: `revisio_marques_v35_20260908`."]
    txt = '\n'.join(L) + '\n'; (CT / 'V36_REBUT.md').write_text(txt); (OUT36 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE36 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'base': 'fusion_total_v36', 'canvis': REP_CANVIS})
    shutil.copytree(OUT36 / 'lliurables', IAOUT36 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB36, IAOUT36 / '4-rebuts', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
