"""C5 (V37) · Rebut al costat del PSB i a lliurables, manifest i còpia IA. Només després de c4 publish."""
from comu37 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')


def main():
    pub = json.loads((REB37 / 'C4_publish.json').read_text()); ver = json.loads((REB37 / 'C4_verification.json').read_text()); gate = json.loads((REB37 / 'C4_photoshop_gate.json').read_text())
    c3 = json.loads((REB37 / 'C3_portes.json').read_text()); a11 = json.loads((REB37 / 'A11_roi_rivet.json').read_text()); b4 = json.loads((REB37 / 'B4a_capes_cadena.json').read_text())
    L = ['# V37 — les marques de la V36: el limbe (research/154). Condició de contorn al forat lunar també per a les capes ACHF, i farcit que conserva els anells parcials', '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere («els d'a prop del limbe els veig claríssims»). PSB LLEUGER: base lineal V36 (idèntica) + les 10 capes. V36.psb intacta.", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Modes/màscares de les capes: de `V32.psb`.", '',
         '## Què hi havia a la V36 al limbe (23 marques; les del limbe a P01–P05, oest; les altres, contorns interiors i el quadrat dels 8 s)', '',
         "1. **Les capes ACHF (01/02/04/05/06) estaven SATURADES al voltant de la Lluna**: la mitjana d'un sol costat contra el forat (gradient ×2 cada 44 px) donava |d/escala| > 25 al limbe i > 1 fins a 1,08 (01), 1,10 (02), 1,16 (06) R☉: la tanh saturava, l'anivellament per anell ho deixava pla i el detall començava de cop a 20–70 px del limbe (banda sense estructura, std 0,05 contra 0,17–0,26). Era així des de la V29.",
         "2. **Rivet clar a la vora del forat al MGN i als dos WOW (+1,5–2 σ), només on la vora és més a prop del Sol que el primer anell sencer**: el farcit de la V35 extrapolava el perfil des del primer anell SENCER (1,046) amb el seu pendent (−0,023 ln/px), 7× més suau que el del limbe (−0,167): a les corones parcials (1,005–1,046) el farcit quedava fosc → mitjana local baixa → rivet. Correlat amb la fondària de la franja per sector (A11).",
         "3. **La franja de la unió temporal**: el forat és la unió de les posicions de la Lluna (radi 1,005–1,046 segons l'azimut); a la franja 1,005–1,046 només hi ha 13–16 fotogrames amb pes total 3–4× menor i el gra de la base és 7–9 % (10× el de fora). El NRGF/RHEF hi tenen estadístiques d'anell parcial (banda apagada −0,4…−1 σ). És dada real i pobra; la norma del 27-08 diu conservar-la. **Decisió pendent de Pere** (rebut §Límits).", '',
         '## Què canvia la V37', '',
         "1. **Condició de contorn també per a les capes ACHF** (b4a): l'entrada de les gaussianes (ln TOTAL per canal) porta el forat lunar i el fora-de-suport omplerts pel perfil azimutal mitjà continuat; la convolució va sense màscara; la sortida es desa només al suport. Recepta (σ, perfils de contrast, tanh, mapa de resolució, H1, σ extern) intacta.",
         "2. **Farcit B** a tots dos llocs (ACHF i P03/P04/P05): mitjanes dels anells PARCIALS conservades, continuació cap endins des del primer anell amb dada amb el pendent local que decau (L 60 px, pujada ≤ 5 ln). Operadors purs de v31_purs amb una màscara, com la V35. P01/P02 = V36 byte a byte (mateixa base; NRGF amb estadístiques parcials i RHEF amb rang continu).", '',
         '## Portes al limbe (V36 → V37)', '', '| capa ACHF | r on la saturació de la tanh cau al 50 % | std de la capa a 1,03 R☉ | H1 pitjor (R☉) |', '|---|---|---|---|']
    for k, row in c3['limbe_cadena'].items():
        f = lambda v: '–' if v is None else f'{v:.3f}'
        L.append(f"| {k} | {f(row['V36']['r_on_saturacio_cau_a_0.5'])} → {f(row['V37']['r_on_saturacio_cau_a_0.5'])} | {row['V36']['std'][3]:.3f} → {row['V37']['std'][3]:.3f} | {row['V36']['H1']['error']:.4f} ({row['V36']['H1']['R']:.2f}) → {row['V37']['H1']['error']:.4f} ({row['V37']['H1']['R']:.2f}) |")
    L += ['', '| capa pura | rivet a la vora del forat, màx / mediana per sector (σ) | biaix d\'anell 1,03–1,3 (σ) |', '|---|---|---|']
    for k, row in c3['rivet_purs'].items():
        L.append(f"| {k} | {row['V36']['rivet_max_abs']:.2f} / {row['V36']['rivet_mediana_abs']:.2f} → {row['V37']['rivet_max_abs']:.2f} / {row['V37']['rivet_mediana_abs']:.2f} | {row['V36']['biaix_anell_1.03_1.3']:.2f} → {row['V37']['biaix_anell_1.03_1.3']:.2f} |")
    L += ['', 'Gra fi a 4 R☉ per capa (no ha de canviar): ' + ', '.join(f"{k} {g['V36']:.4f}→{g['V37']:.4f}" for k, g in c3['gra_4R'].items()) + '.',
          f"Prova en ROI (A11): rivet màxim per sector MGN {a11['A/MGN']['rivet_max_abs']:.2f} → {a11['B/MGN']['rivet_max_abs']:.2f} σ, WOW {a11['A/WOW']['rivet_max_abs']:.2f} → {a11['B/WOW']['rivet_max_abs']:.2f} σ; dues màscares (C) i NRGF amb μ/σ extrapolats (b) REFUSATS (rivet 9,7 σ i 5,2 σ).", '',
          '## Límits i decisió pendent', '',
          "- H1 al primer anell (1,00–1,02 R☉) queda per damunt de 0,05 a algunes capes: és el limbe físic (cromosfera, protuberàncies) que ara la capa deixa passar en lloc de saturar-lo; de 1,04 R☉ enfora H1 ≤ 0,02. Declarat.",
          "- **La franja de la unió temporal (oest, 18 px)** continua al producte tal com la norma del 27-08 demana: 13–16 fotogrames, pes 3–4× menor, gra 7–9 %. El NRGF/RHEF hi mostren una banda apagada; el MGN/WOW, gra. L'alternativa és un forat circular al radi màxim de la unió (1,046 R☉), que la norma prohibeix: Pere decideix.",
          "- Vora dels 8 s (quadrat pel vinyetatge), contorns d'entrada dels fotogrames a l'interior: com la V36 (origen de captura).",
          "- Judici visual de Pere obert. Vistes: `output/v37_20260908/lliurables/vistes/` (polar del limbe V36|V37 de sis capes, retalls a les seves marques, A10/A11).", '',
          "Codi: `research/tools/v37_20260908/` (comu37, b4a, b4c_purs, a11_roi_rivet, c3, c4, c5, d1). Rebuts: `output/v37_20260908/4-rebuts/`. Revisió: `revisio_marques_v36_20260908`."]
    txt = '\n'.join(L) + '\n'; (CT / 'V37_REBUT.md').write_text(txt); (OUT37 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE37 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'base': 'fusion_total_v36 (idèntica)', 'canvis': REP_CANVIS})
    shutil.copytree(OUT37 / 'lliurables', IAOUT37 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB37, IAOUT37 / '4-rebuts', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
