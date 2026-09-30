"""C5 (V39) · Rebut al costat del PSB (V39_REBUT.md), RESULTAT.md, manifest de lliurament i còpia IA. Només després de c4 publish."""
from comu39 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
RANGS = ('1,2–3', '3–5', '5–9')


def a3b_taula(L):
    for win in ('1.6R', '3.7R', '5.5R'):
        p = REB39 / f'A3b_injeccio_auchere_k2_tau1_f3_min8_{win}.json'
        if not p.exists(): continue
        d = json.loads(p.read_text()); res = d['finestres'][win]['resultats']; L.append(f"- **{win}**:")
        for op in ('MGN', 'WOW', 'ACHF01', 'ACHF04', 'ACHF06'):
            parts = []
            for amp in sorted({k.split('_a')[1] for k in res if k.startswith(op + '_s')}, key=float):
                cells = [(int(k.split('_s')[1].split('_a')[0]), res[k]) for k in res if k.startswith(op + '_s') and k.endswith('_a' + amp)]
                parts.append(f"{float(amp) * 100:g} %: " + ' '.join(f"{v['quocient']:.2f}({v['amp_en_sigma_soroll']:.0f}σ)" for s, v in sorted(cells)))
            L.append(f"  - {op}: " + ' · '.join(parts))


def main():
    pub = json.loads((REB39 / 'C4_publish.json').read_text()); ver = json.loads((REB39 / 'C4_verification.json').read_text()); gate = json.loads((REB39 / 'C4_photoshop_gate.json').read_text())
    c3 = json.loads((REB39 / 'C3_portes.json').read_text()); pk = json.loads((REB39 / 'C4_packaging.json').read_text()); tau = json.loads((CAU39 / 'tau.json').read_text())
    c3b = json.loads((REB39 / 'C3b_transferencia_real.json').read_text()); c3c = json.loads((REB39 / 'C3c_jutge_brno.json').read_text()); b4a = json.loads((REB39 / 'B4a_capes_cadena.json').read_text())
    L = ['# V39 — el soroll dels filtres fora de la corona: guany per banda amb el soroll MESURAT i el que els dos telescopis confirmen (research/156) · candidata amb portes declarades', '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere (/goal V39 a partir de `V38_everythingNOTawesome.psb`). Font del projecte: el teu `V38_everythingNOTawesome.psb` (SHA-256 `{pk['font_sha256']}`): capes, modes, opacitats, visibilitats i màscares tal com les vas deixar.", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Verificació capa a capa: {sum(1 for r in ver['rows'] if r['exact'])} de {len(ver['rows'])} exactes.", '',
         '## Què canvia', '',
         f"1. **MGN (P03), WOW (P04), WOW bilateral (P05) i ACHF (01/04/05/06)**: cada BANDA d'escala (entre σ consecutives; el WOW ja treballa per bandes) es multiplica, abans de la normalització o del tanh, per un guany g = max(g_Auchère, g_creuat): "
         f"g_Auchère = erf(|w| / (√2 · k · σ_banda(x))) amb k = {tau['k']:g} (llindar tou per coeficient, Auchère et al. 2023) i σ_banda el soroll MESURAT de la banda en aquell lloc (les dues meitats de fotogrames alternats de cada tren passades pels mateixos nuclis, A2/A4; per canal R/G/B a l'ACHF, A2c); "
         "g_creuat = clip((⟨b_V·b_S⟩ − guarda)/⟨b_F²⟩, 0, 1) (potència que la Vixen i la Sony veuen ALHORA a la banda, finestra σ = max(6 ℓ, 24 px), guarda d'1 σ de l'estimador; els sorolls dels dos sensors són independents, o sigui que el producte creuat només conté el que és real: corona i cel). "
         "El llindar protegeix el compacte (porta d'injecció A3b); el creuat protegeix el difús que els dos telescopis confirmen. Res més canvia: mateixos farcits, tanh, S/N, H1, LUT de pantalla. Amb τ = 0 (o k → 0 i creuat = false) surt exactament la V38 (provat: 4·10⁻⁹ a l'ACHF, 8·10⁻⁵ al MGN).",
         "2. **Dues bases de pantalla noves amb la corba declarada** (recepta exacta de la V29 `new_tone`: L = (R+2G+B)/4, corba pend 0,22 · àncora 0,74 · terra 0,045, color local conservat): `00 Base corba (total) · V39` (visible) i `00 Base (cel/4) · V39` (oculta; el cel per tren de la V29 combinat amb els pesos i el ρ de la fusió V38). Les bases de la V32 que tenies actives queden OCULTES (no esborrades).",
         "3. **02 Passa-alt 24: deprecat** (supersedit per l'ACHF, com vas dir). P06 NAFE, P07/P08 precursors, P09 SWAP i C01 control: deprecats (els vas esborrar).",
         "4. **P01b**: μ/σ dels anells parcials extrapolats en ln r (llei de potència) en lloc de en r (la V38 aixecava tota la vora +0,24 σ). P01 i P02: com la V38.", '',
         '## Tres rectificacions d\'aquesta ronda (mesurades)', '',
         "- **El «jutge extern» de les versions V34–V38 (Vixen original a quatre finestres «on la base és Sony») NO era independent**: des de la V34 la Vixen entra a la fusió de 2,65 R☉ enfora i a aquelles finestres hi pesa 0,37–0,44 (corr(original, Vixen V38) = 1,000): la base CONTÉ el jutge. No hi ha cap finestra de 768 px amb pes Vixen < 0,03 (mediana 0,34–0,47 a tot el camp). Es manté la taula com a comprovació de coherència, i el jutge independent passa a ser **Brno** (mètode congelat de la v30: anells polars 1,2–9 R☉, estructura azimutal, Pearson per anell contra les quatre fotos de Druckmüller, control nul a 180°).",
         "- **L'estimador de soroll per meitats era invàlid a la vora del forat lunar**: les dues meitats hi tenen la vora a distància sub-píxel i, amb el gradient del limbe, ln(E/O) hi val ×32 el rms a 1 px, ×3 fins a 7 px, ×1,2 a 16 px (est, fora de la franja); el «soroll» a 0,98–1,06 R☉ sortia 100–200× el d'1,15–1,30 i el guany hi feia un anell (biaix d'anell del P04 0,37→0,62 σ). Cura a la font: els 16 px que toquen la vora del forat surten de l'estimador (`comu39.lluny_del_forat`; dins, el soroll es pren dels veïns de fora: s'hi subestima → es conserva el detall del limbe).",
         "- **El guany per passa-alt (primera versió) atenuava l'estructura confirmada gairebé tant com el soroll** (a 3,5–4 R☉, covariància amb la Vixen original ×0,40–0,70 a les bandes ≤ 32 px): un passa-alt barreja el gra fi amb l'estructura gran, i la correlació es conservava només perquè l'atenuació era uniforme. Per això el guany passa a ser per BANDA i s'hi afegeix el terme creuat: els dos trens comparteixen estructura a 3,5–4 R☉ només de 8 px enllà (corr V×S 0,01–0,03 a 2–8 px; 0,12–0,50 a 8–32; 0,59–0,95 a 32–64), i és això el que es conserva.", '',
         '## Soroll per anell (rms de capa−0,5, unitats 0–1) · 1,1–1,5 / 1,5–2 / 2–2,65 / 2,65–3,5 / 3,5–5 / 5–7 R☉', '', '| capa | V38 | V39 |', '|---|---|---|']
    for k, row in c3['soroll_per_anell'].items():
        L.append(f"| {k} | {' / '.join(f'{x:.3f}' for x in row['V38'])} | {' / '.join(f'{x:.3f}' for x in row['V39'])} |")
    bb = c3c.get('BrnoBrno_1deg', {}).get('r', [None] * 3)
    fmt = lambda v: 'n/d' if v is None or not np.isfinite(v) else f'{v:.2f}'
    L += ['', f"## Jutge INDEPENDENT: Brno (estructura azimutal per anell; rangs {' / '.join(RANGS)} R☉; control Brno×Brno a 1°: {' / '.join(f'{v:+.2f}' for v in bb)})", '',
          "Transferència = quocient de covariàncies AGREGADES (sumes sobre les 4 fotos de Brno, els anells del rang i els azimuts) cov(V39, Brno)/cov(V38, Brno), només on la correlació agregada V38×Brno ≥ 0,10 (si no, «n/d»: Brno no hi pot jutjar); entre claudàtors, el mínim i el màxim deixant una foto de Brno fora; entre parèntesis, p16/mediana/p84 de 8 sectors azimutals de 45°.", '',
          '| capa | angle | corr Brno V38 | corr Brno V39 | nul V39 | transferència [un Brno fora] (sectors) | rms V39/V38 |', '|---|---|---|---|---|---|---|']
    for k, row in c3c['capes'].items():
        for deg in ('1deg', '4.5deg'):
            d1 = row[deg]; tr = ' / '.join(f"{fmt(t)} [{fmt(a)},{fmt(b)}] ({fmt(s0)}/{fmt(s1)}/{fmt(s2)})" for t, (a, b), (s0, s1, s2, _) in zip(d1['transferencia_cov'], d1['transferencia_un_brno_fora_min_max'], d1['transferencia_sectors_p16_med_p84_n']))
            L.append(f"| {k} | {deg.replace('deg', '°')} | {' / '.join(f'{v:+.2f}' for v in d1['corr_V38'])} | {' / '.join(f'{v:+.2f}' for v in d1['corr_V39'])} | {' / '.join(f'{v:+.2f}' for v in d1['nul_V39'])} | {tr} | {' / '.join(f'{v:.2f}' for v in d1['rms_V39_V38'])} |")
    L += ['', "Lectura: a 1,2–3 R☉ Brno×Brno val ≈ 0,99 (estructura clara) i a 3–5 només ≈ 0,38 (les quatre fotos de Brno ja hi discrepen entre elles); de 5 enfora Brno NO pot jutjar (0,04): el rms que hi baixa és «no corroborat per Brno», no «soroll demostrat». La transferència és la fracció de la component correlacionada amb Brno que la V39 conserva respecte de la V38; el rms, quant baixa l'amplitud total (soroll inclòs). Les correlacions amb Brno canvien menys de ±0,01 a 1,2–3 R☉ (01/05/06 baixen 0,004–0,006, sense interval d'incertesa: no es pot dir si és real) i pugen 0,01–0,05 a 3–5.", '',
          '## Comprovació de coherència (NO independent: Vixen original a 4 finestres 3,5/4 R☉ amb pes Vixen 0,37–0,44 a la base) · bandes 2–8 / 8–32 / 32–64 px', '', '| capa | corr V38 | corr V39 | cov V39/V38 | rms V39/V38 |', '|---|---|---|---|---|']
    for k, rows in c3b.items():
        f = lambda key, fmt: ' / '.join(fmt % np.mean([rw[key] for rw in rows[i::3]]) for i in range(3))
        L.append(f"| {k} | {f('corr_V38', '%+.2f')} | {f('corr_V39', '%+.2f')} | {f('cov_ratio_V39_V38', '%.2f')} | {f('rms_ratio_V39_V38', '%.2f')} |")
    cs = b4a.get('creuat', {}).get('stats', {}).get('1', {})
    if cs:
        L += ['', '## Terme creuat (canal G de l\'ACHF): guany creuat mitjà al suport comú i coherència mediana Vixen×Sony per banda', '', '| banda | g_creuat mitjà | coherència mediana |', '|---|---|---|']
        for kk, v in cs.items(): L.append(f"| {kk} | {v['g_creuat_mitja_suport_comu']:.3f} | {v['coherencia_mediana']:.3f} |")
    L += ['', '## Porta d\'injecció cega (A3b, final): quocient resposta V39/V38 d\'un blob DoG ± (σ 2/8/24 px) a 1/3/10 % de la mediana local (entre parèntesis, l\'amplitud en σ de soroll de l\'escala)', '',
          "Les injeccions entren només a la fusió (no a la Vixen ni a la Sony): el terme creuat no les veu, o sigui que aquests quocients són una COTA INFERIOR (només el llindar tou hi actua). Un quocient < 0,90 a una cel·la diu que un tret aïllat d'aquella mida i amplitud, sense confirmació de l'altre tren, s'atenua en aquesta proporció; no és una cura sense preu i es declara.", '']
    a3b_taula(L)
    L += ['', '## Estat de les portes (declarat, sense maquillar)', '',
          "- **Injecció cega (A3b, 0,90–1,10 per cel·la):** NO PASSA a les cel·les d'1 % (5–7 σ per píxel) amb blobs de 2 px fora de la corona (0,73–0,82) ni del tot dins (0,82–0,85 a l'ACHF a 1,6 R☉); passa (≥ 0,85–0,99) a tot el 3 % i el 10 % i als blobs de 8–24 px. 36 de 135 cel·les < 0,90 (mínim 0,73). Un tret aïllat de 2 px a 5–7 σ que l'altre tren no confirma s'atenua un 15–27 %: és el preu del llindar, declarat; el terme creuat no el veu perquè les injeccions no entren als trens (cota inferior).",
          "- **H1 (nivell per anell ≤ 0,05):** 01 0,077, 04 0,063, 05 0,056 (06 0,044): HERETATS de la V38 (0,078 / 0,063 / 0,056 / 0,044: idèntics al tercer decimal); H1b millora (2,53→1,71; 2,66→2,37; 1,86→1,41; 1,57→1,22). El residu és el limbe de l'ACHF (V37/V38), no d'aquesta ronda.",
          "- **Jutge Brno:** transferència agregada 0,95–1,00 a 1,2–3 R☉ a totes les capes (tots els subconjunts de Brno i tots els sectors ≥ 0,88); a 3–5 R☉, on Brno constreny (correlació ≥ 0,10): 01 0,97, 05 1,00, 06 1,01, P04 0,96 (sectors p16 ≥ 0,87); 04, P03 i P05 hi tenen correlació agregada < 0,10 amb Brno (no jutjables per rang; per sectors, medianes 0,81 / 1,03 / 0,97). De 5 enfora Brno no jutja.",
          "- **Terme creuat a prop de la vora d'entrada d'un tren** (fora del suport d'un tren hi ha la fusió: el nucli hi pot fabricar coherència): quantificat al canal G: a 2,0–2,4 R☉ el g_creuat val 0,98–1,00 a σ ≥ 16 on, amb el suport comú eroditat 3ℓ, no hi ha estimació; el guany final hi canvia ≤ 0,1 perquè el llindar tou ja hi val 0,89–1,00 (la banda hi és ≥ 99 % senyal); lluny de les vores no hi ha inflació (σ32: 0,28 a prop contra 0,40 lluny). Cura pendent: erosió per escala o convolució normalitzada per tren.",
          "- **Guarda del terme creuat** (1 σ amb N_ef = 2σ_c²/ℓ², heurística): sense nul empíric (rotacions Vixen–Sony, particions de meitats). Pendent.",
          "- **Photoshop (OBRE) i verificació capa a capa:** vegeu la capçalera.", '']
    L += ['', '## Limbe (mediana per anell / σ de la capa; anells 1,00 · 1,01 · 1,02 · 1,03 R☉)', '',
          '- P03 MGN: V38 +4,3 · +2,2 · +1,8 · +1,2 → V39 +1,4 · +0,6 · +0,8 · +0,8 (el pic de la vora del forat baixa; els anells 1,04–1,12 pugen 0,1–0,2 σ).',
          '- P04 WOW: V38 +2,7 · +1,8 · +1,2 · +0,5 → V39 +0,1 · −0,6 · −0,2 · −0,1.',
          '- P05 WOW bilateral: V38 +2,0 · +0,6 · +0,3 · 0,0 → V39 +2,2 · +0,8 · +0,3 · +0,1 (el pic de 2 σ és de la V38; queda, +0,2 σ).',
          "- ⚠️ La mètrica de b4c («màxim relatiu a > 1,3 R☉»: 1,63→1,81 / 0,37→0,51 / 2,24→2,63) es mou amb la línia de base; el perfil absolut és el que compta."]
    L += ['', '## Capes del projecte (de baix a dalt)', ''] + [f"- {c['name']} — {c['kind']}{' (visible)' if c.get('visible') else ''}" for c in pk['capes']]
    L += ['', "Vistes: `output/v39_20260909/lliurables/vistes/` (retalls V38|V39 a 1,6/3,7/5,5 R☉, polar del limbe, mapes de guany, bases corbades, compost). Codi: `research/tools/v39_20260909/`. Rebuts: `output/v39_20260909/4-rebuts/`.", '',
          "Límits: el RHEF (P02) no s'ha tocat (la part nord ensenya el rang del soroll on la corona és feble: la mateixa idea de soroll mesurat s'hi podria aplicar); P01 i P01b tots dos visibles com els tenies (dupliquen el NRGF: si en vols més, puja l'opacitat d'un); anells del canal blau, taca NE; les meitats de la Sony són les de la cadena V29 (aproximació declarada); una sola partició de meitats (sense interval d'incertesa del soroll). Judici visual de Pere obert."]
    txt = '\n'.join(L) + '\n'; (CT / 'V39_REBUT.md').write_text(txt); (OUT39 / 'lliurables').mkdir(parents=True, exist_ok=True); (OUT39 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE39 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'tau': tau, 'report': 'research/156'})
    shutil.copytree(OUT39 / 'lliurables', IAOUT39 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB39, IAOUT39 / '4-rebuts', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
