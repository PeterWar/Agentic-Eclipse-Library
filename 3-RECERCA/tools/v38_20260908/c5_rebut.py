"""C5 (V38) · Rebut al costat del PSB (V38_REBUT.md), RESULTAT.md, manifest de lliurament i còpia IA. Només després de c4 publish."""
from comu38 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')


def main():
    pub = json.loads((REB38 / 'C4_publish.json').read_text()); ver = json.loads((REB38 / 'C4_verification.json').read_text()); gate = json.loads((REB38 / 'C4_photoshop_gate.json').read_text())
    c3 = json.loads((REB38 / 'C3_portes.json').read_text()); pk = json.loads((REB38 / 'C4_packaging.json').read_text()); nul = c3['control_nul_fusio']
    L = ['# V38 — la Lluna a l\'inici, la franja de l\'oest mesurada a la font, i el projecte complet (research/155)', '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere («fem A aplicant les correccions necessàries; fes la V38 ja amb totes les capes… munta-ho tot en un projecte»). V32.psb i V37.psb intactes.", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Verificació capa a capa contra les fonts: {sum(1 for r in ver['rows'] if r['exact'])} de {len(ver['rows'])} exactes.", '',
         '## La Lluna a l\'INICI (t 15 s)', '',
         "- Radi 455,5 px (1,034 R☉); centre a (+14,8, +0,9) px del Sol; les cinc capes fixes a la Lluna (Earthshine v2, Compara D87, Compara LROC, Earthshine V24e, Reflex) desplaçades (+15, +1) px. Totes les capes de base i de filtre porten màscara nova: fora del disc (R + 2 px de guarda, rampa 2 px).",
         "- A l'oest la vora del disc coincideix amb la vora de la dada: la flamarada i la cromosfera (els primers 3–4 anells, vistos per 2–10 fotogrames de 1/3200 s) queden SENCERES. Al SE i a l'E el disc tapa la franja dels últims fotogrames (les miniflamarades del SE, az +31…+50°, queden sota la Lluna fins a 1,061 R☉: és el preu de l'opció A, triada per Pere).",
         "- Millora possible anotada (opció D, no feta): la corona de la franja del SE dibuixada per sobre de la vora del disc (compost de dos instants, només declarat).", '',
         '## Què s\'ha mesurat a la franja (research/155 §2) i què s\'ha corregit', '',
         "- El forat és la INTERSECCIÓ de les posicions lunars (1,005–1,046 R☉). La franja de l'oest té 15–17 fotogrames (pes 4–7× menor → soroll ×2–2,6, no ×10 com deia el 154); els 3–4 primers anells (1,005–1,012) són cromosfera (+107/+72/+41/+11 % sobre la tendència). No hi ha arcs coherents d'1 px (coherència azimutal t < 1).",
         "- Sí que hi ha un dèficit de llum de cada fotograma prop de la seva pròpia vora lunar (ala de dispersió del limbe fosc: curts −7 % a 2,5 px, −3,4 % a 4,5, −1,5 % a 10): la V38 el corregeix a l'origen (B2) amb la taula mesurada per classe d'exposició; residu 0,000; control nul exacte al ROI.",
         f"- Fusió V38 contra V36: lluny de tota vora lunar (r > 1,12) diferència relativa màxima {nul['rel_max_lluny_r>1.12']:.1e} (idèntica); a 1,00–1,06 mediana {100*nul['rel_p50_prop_r<1.06']:.2f} %, p99 {100*nul['rel_p99_prop']:.1f} %. Suport idèntic: {nul['suport_identic']}.", '',
         '## Portes al limbe: rivet a la vora del forat per sector (24), |màx| / |mediana| en σ, V37 → V38 (03: V32 → V38)', '', '| capa | abans | V38 |', '|---|---|---|']
    for k, row in c3['rivet_per_sector'].items():
        L.append(f"| {k} | {row['V37_max']:.2f} / {row['V37_med']:.2f} | {row['V38_max']:.2f} / {row['V38_med']:.2f} |")
    r72 = c3.get('rivet_72_P01', {})
    if 'P01_resum' in r72 and 'P01x_resum' in r72:
        a, b = r72['P01_resum'], r72['P01x_resum']
        L += ['', '## P01 (NRGF amb estadístiques dels anells parcials) contra P01b (μ/σ extrapolats): rivet per azimut (72 sectors de 5°)', '',
              f"- P01: on hi ha cromosfera (W i SE) mediana {a['cromosfera_W_SE_mediana']:+.2f} σ (màx {a['cromosfera_max']:+.2f}); a la resta del contorn mediana {a['resta_mediana']:+.2f}, p95 {a['resta_p95']:+.2f}, |màx| {a['resta_max_abs']:.2f} σ.",
              f"- P01b: on hi ha cromosfera mediana {b['cromosfera_W_SE_mediana']:+.2f} σ (màx {b['cromosfera_max']:+.2f}); a la resta mediana {b['resta_mediana']:+.2f}, p95 {b['resta_p95']:+.2f}, |màx| {b['resta_max_abs']:.2f} σ.",
              "- Lectura: si el rivet clar de la P01b és gran on hi ha cromosfera i petit a la resta, és SENYAL (la cromosfera respecte de la corona mitjana d'aquell radi) i el «5,2 σ» refusat al 154 era això. Les dues capes són al projecte (P01b oculta): la tria és de Pere."]
    L += ['', '## Capes del projecte (de baix a dalt)', '']
    for c in pk['capes']:
        L.append(f"- {c['name']} — {c['kind']}{' (visible)' if c.get('visible') else ''}")
    L += ['', "Vistes: `output/v38_20260908/lliurables/vistes/` (polar del limbe V37|V38, retalls al limbe W/SW/NW amb el disc de la Lluna, A1/A2 de la franja, compost sencer). Codi: `research/tools/v38_20260908/`. Rebuts: `output/v38_20260908/4-rebuts/`.", '',
          "Límits: les miniflamarades del SE sota la Lluna (opció A); els contorns d'entrada dels fotogrames i la vora dels 8 s (captura); anells del canal blau, taca NE; les capes P06–P09/C01 i les dues bases són de la V32 (no regenerades). Judici visual de Pere obert."]
    txt = '\n'.join(L) + '\n'; (CT / 'V38_REBUT.md').write_text(txt); (OUT38 / 'lliurables').mkdir(parents=True, exist_ok=True); (OUT38 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE38 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'lluna_inici': pk['lluna_inici'], 'base': 'fusion_total_v38 (Vixen amb correcció de la vora lunar per fotograma; Sony V36)', 'report': 'research/155'})
    shutil.copytree(OUT38 / 'lliurables', IAOUT38 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB38, IAOUT38 / '4-rebuts', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
