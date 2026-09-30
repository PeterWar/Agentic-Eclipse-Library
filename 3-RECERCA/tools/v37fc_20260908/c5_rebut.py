"""C5 (V37fc) · Rebut curt de la variant V37_forat_circular.psb: què és, què canvia respecte de la V37, números de comparació i on són les vistes."""
from comu37fc import *
import shutil


def main():
    pub = json.loads((REB37FC / 'C4_publish.json').read_text()); ver = json.loads((REB37FC / 'C4_verification.json').read_text()); gate = json.loads((REB37FC / 'C4_photoshop_gate.json').read_text()); cmp_ = json.loads((REB37FC / 'C3_compara.json').read_text())
    a0 = json.loads((REB37FC / 'A0_forat_circular.json').read_text()) if (REB37FC / 'A0_forat_circular.json').exists() else {}
    files = sorted(p.name for p in VIS37FC.glob('*.png'))
    L = ['# V37_forat_circular.psb · REBUT (variant de comparació, 08-09-2026)', '',
         'Demanat per Pere: «pots fer-me les dues versions? les vull veure i després decidir». Aquesta és la **segona versió**: la V37 amb el forat lunar fet **circular** al radi màxim de la unió temporal de la Lluna. La **primera versió** és la V37.psb tal com es va lliurar (franja de la unió temporal conservada, norma del 27-08).', '',
         '## Què és exactament', '',
         f"- Base lineal: la mateixa fusió de la V37 (`fusion_total_v36.npy`) amb els píxels a **r < {RADI_FORAT_PX} px del centre del Sol** ({RADI_FORAT_PX / RS:.3f} R☉, el radi màxim de la unió de posicions lunars) posats a zero i trets del suport. {a0.get('px_trets', 36119)} píxels menys (la mitja lluna de l'oest que a la V37 té 13–16 fotogrames en lloc de 22–36).",
         '- Filtres: **la recepta exacta de la V37** (ACHF amb farcit A, MGN/WOW amb farcit B, bilateral amb farcit A, NRGF/RHEF amb rang continu), regenerats sobre aquest suport. Cap altre canvi.',
         '- El forat circular NO és una cura de cap artefacte: és una tria d\'enquadrament del limbe. La causa dels residus de la franja (menys fotogrames, gra 7–9 %, estadística d\'anell parcial) queda documentada a `research/154` §4; aquí simplement s\'exclou la franja del producte.', '',
         '## Fitxer', '',
         f"- `{pub['path']}`", f"- SHA-256 `{pub['sha256']}` · {pub.get('bytes', '?')} bytes · Photoshop: {gate['result']}", f"- Verificació de les 11 capes contra les fonts: {'PASS' if ver['PASS'] else 'FALLA'} ({sum(1 for r in ver.get('rows', []) if r.get('exact'))} de {len(ver.get('rows', []))} capes byte a byte iguals a la font)", '',
         '## Comparació V37 (franja) | V37fc (forat circular) al limbe (0,98–1,30 R☉)', '',
         'Rivet = (mitjana dels 8 px tocant el forat − mitjana a 20–40 px) / σ de la capa a 1,05–1,6 R☉, per 24 sectors; màxim i mediana en valor absolut.', '',
         '| Capa | V37 màx | V37 mediana | V37fc màx | V37fc mediana |', '|---|---:|---:|---:|---:|']
    for k, row in cmp_.items():
        a, b = row['V37 franja'], row['V37fc forat circular']; L.append(f"| {k} | {a['rivet_max_abs']:.2f} | {a['rivet_mediana_abs']:.2f} | {b['rivet_max_abs']:.2f} | {b['rivet_mediana_abs']:.2f} |")
    L += ['', '## El que he vist a la comparació (mesurat, no opinió)', '',
         '- **NRGF (P01) i RHEF (P02)**: el forat circular els neteja el limbe oest. La línia fina i els arcs de la franja desapareixen (rivet mediana 0,25 → 0,08 i 0,34 → 0,07; a l\'oest, az −157°, P01 passa de −1,05 a −0,23 σ). Era la causa del §4 del 154, confirmada per l\'altra banda.',
         '- **ACHF 01/02/06**: una mica millor (màx 2,5 → 2,1; 2,1 → 1,5; 2,2 → 1,6).',
         '- **WOW (P04): PITJOR a la vora**: apareix un rivet clar d\'1,3–2,2 σ en dues bandes d\'azimut (−172…−97° i −22…+52°) on la V37 era neutra o lleugerament fosca (−0,2…−1,0). Es veu com una vora prima més clara resseguint el cercle (retall «limbe oest», meitat dreta). Mecanisme: el farcit B posa sota el forat la mitjana azimutal dels anells; a la V37 els anells parcials de 1,005–1,046 li donaven informació local i amb el forat circular ja no n\'hi ha cap (0 anells parcials), o sigui que la condició de contorn és una pura extrapolació i on la corona local és més brillant que la mitjana l\'operador veu un graó. NO l\'he corregit perquè la comparació havia de ser amb la MATEIXA recepta; si tries el forat circular, la cura és un farcit per sector d\'azimut (canvi de recepta, mesurable), no cap retoc.',
         '- **WOW bilateral (P05)**: pràcticament igual (mediana 0,63 → 0,58); el biaix per sectors que hi havia hi continua (+1,1 a l\'oest, −1,5 a l\'est): no és de la franja.',
         '- **MGN (P03)**: igual (0,22 → 0,23).',
         '- **La protuberància de l\'oest queda RETALLADA**: al retall «limbe oest» de P01 es veu que la part de la protuberància que era dins de 1,005–1,046 R☉ (dada real, amb 13–16 fotogrames) desapareix amb el forat circular. És el preu més visible de la variant.', '']
    L += ['', '## Vistes (mira-les abans de decidir)', '', f'`{VIS37FC}` (còpia a `{IAOUT37FC}`):', ''] + [f'- `{f}`' for f in files] + ['',
         '## El que has de decidir', '',
         '- **V37 (franja conservada)**: la dada de la unió temporal hi és tota (Lluna a 1,005–1,046 R☉ segons l\'azimut); a l\'oest queda una mitja lluna amb menys fotogrames i un residu fi als filtres. Respecta la norma del 27-08.',
         '- **V37fc (forat circular)**: limbe net i circular a 1,046 R☉ a tots els azimuts; es perden els 18 px de corona interior de 1,005 a 1,046 R☉ a l\'oest (dada real, però amb 13–16 fotogrames i 10× més gra); a l\'est la unió ja arribava a 1,046 i no s\'hi perd res.',
         '- Cap dels dos PSB substitueix l\'altre: tots dos són a `Capes Totals/`. Quan triïs, la versió no triada es pot esborrar o arxivar.', '']
    (REB37FC / 'V37_forat_circular_REBUT.md').write_text('\n'.join(L)); shutil.copy(REB37FC / 'V37_forat_circular_REBUT.md', CT / 'V37_forat_circular_REBUT.md')
    for f in files: shutil.copy(VIS37FC / f, IAOUT37FC / f)
    shutil.copy(REB37FC / 'V37_forat_circular_REBUT.md', IAOUT37FC / 'V37_forat_circular_REBUT.md'); log('C5 fet')


if __name__ == '__main__':
    main()
