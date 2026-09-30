"""C5 (V40) · Rebut al costat del PSB (V40_REBUT.md), RESULTAT.md, manifest i còpia IA. Llegeix les portes del pilot (REB39: C3, C3c, C3d, A3b wg) i el
paquet (REB40: C4_*). Només després de c4_projecte_v40 publish."""
from comu40 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals'); RANGS = ('1,2–3', '3–5', '5–9')
fmt = lambda v: 'n/d' if v is None or (isinstance(v, float) and not np.isfinite(v)) else f'{v:.2f}'


def main():
    pub = json.loads((REB40 / 'C4_publish.json').read_text()); ver = json.loads((REB40 / 'C4_verification.json').read_text()); gate = json.loads((REB40 / 'C4_photoshop_gate.json').read_text()); pk = json.loads((REB40 / 'C4_packaging.json').read_text())
    tau = json.loads((CAU39 / 'tau.json').read_text()); c3 = json.loads((REB39 / 'C3_portes.json').read_text()); c3c = json.loads((REB39 / 'C3c_jutge_brno.json').read_text()); c3d = json.loads((REB39 / 'C3d_vores_i_gra_candidata.json').read_text())
    L = ['# V40 — el gra fora de la corona, ara sí: guany per banda = màxim de Wiener regional i garrote, amb el soroll mesurat a totes les vores (research/157)', '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere (la V39 «no havia millorat el soroll en res» i el terme creuat dibuixava el rectangle de la Vixen). Regla acordada amb Codex (xhigh, 09-09). Font de capes: `V39.psb` (SHA-256 `{pk['font_sha256']}`), només les 15 capes que vas deixar a `V39_Artefactes.psb` més les teves 06 a 12.", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Verificació capa a capa: {sum(1 for r in ver['rows'] if r['exact'])} de {len(ver['rows'])} exactes.", '',
         '## Què canvia respecte de la V39', '',
         f"1. **Guany per banda g = max(g_Wiener, g_garrote)** a MGN (P03), WOW (P04), WOW bilateral (P05) i ACHF (01/04/05/06): g_Wiener = 1 − N/E (N el soroll MESURAT de la banda, E l'energia regional del coeficient, finestra σ = max(3 ℓ, 8 px)): on una banda és 95 % soroll val 0,05 i el gra desapareix; on és senyal val 1. g_garrote = 1 − (k σ)²/w² amb k = {tau['k']:g}: protegeix el compacte fort (5 σ 0,64, 7 σ 0,82, 10 σ 0,91). Residu de soroll pur: 0,06 (la V39, amb el llindar tou k = 2, en deixava 0,58: per això no es veia cap millora). Amb τ = 0 surt la V38 exacta.",
         "2. **Cap terme creuat com a guany.** A la V39 dibuixava el rectangle de la Vixen (dins del camp els dos trens confirmaven, fora no). Queda com a validació (Brno).",
         "3. **Soroll mesurat amb totes les vores excloses, per escala** (forat lunar, vora exterior de la Vixen, vores de la Sony: d ≥ max(16 px, ℓ)) i **dues particions independents de fotogrames** (alternats i parelles alternades): N és la mitjana i la dispersió queda anotada.",
         "4. **Capes:** només les que vas deixar; res del que vas treure.", '',
         '## Soroll per anell (rms de capa − 0,5) · 1,1–1,5 / 1,5–2 / 2–2,65 / 2,65–3,5 / 3,5–5 / 5–7 R☉', '', '| capa | V38 | V40 |', '|---|---|---|']
    for k, row in c3['soroll_per_anell'].items():
        L.append(f"| {k} | {' / '.join(f'{x:.3f}' for x in row['V38'])} | {' / '.join(f'{x:.3f}' for x in row['V39'])} |")
    L += ['', '## Porta de GRA (residu per banda candidata/V38 a finestres on la banda és soroll; objectiu ≤ 0,08 per banda fina, ≤ 0,12 agregat) · bandes ≤1 / 1–2 / 2–4 / 4–8 / 8–16 / 16–32 / 32–64 px', '', '| capa | finestra | residu per banda | total V40/V38 | (V39/V38) |', '|---|---|---|---|---|']
    for k, g in c3d['gra'].items():
        for wn, per in g.items():
            if 'residu_candidata_sobre_V38' in per: L.append(f"| {k} | {wn} | {' / '.join(f'{v:.2f}' for v in per['residu_candidata_sobre_V38'])} | {per['residu_total']:.2f} | {per['V39']['total'] / max(per['V38']['total'], 1e-9):.2f} |")
    L += ['', '## Porta de VORES (rms per bins de distància a la vora exterior del camp Vixen; salt dins/fora no pitjor que la V38)', '', '| capa | salt V38 | salt V39 | salt V40 |', '|---|---|---|---|']
    for k, rows in c3d['vora_vixen'].items(): L.append(f"| {k} | ×{rows.get('V38_salt', float('nan')):.2f} | ×{rows.get('V39_salt', float('nan')):.2f} | ×{rows.get('candidata_salt', float('nan')):.2f} |")
    bb = c3c.get('BrnoBrno_1deg', {}).get('r', [None] * 3)
    L += ['', f"## Jutge INDEPENDENT: Brno (rangs {' / '.join(RANGS)} R☉; control Brno×Brno a 1°: {' / '.join(f'{v:+.2f}' for v in bb)}). Transferència = covariàncies agregades, només on Brno correlaciona ≥ 0,10 («n/d» = no jutjable); [un Brno fora]; (sectors p16/med/p84)", '',
          '| capa | angle | corr V38 | corr V40 | nul | transferència | rms V40/V38 |', '|---|---|---|---|---|---|---|']
    for k, row in c3c['capes'].items():
        for deg in ('1deg', '4.5deg'):
            d1 = row[deg]; tr = ' / '.join(f"{fmt(t)} [{fmt(a)},{fmt(b)}] ({fmt(s0)}/{fmt(s1)}/{fmt(s2)})" for t, (a, b), (s0, s1, s2, _) in zip(d1['transferencia_cov'], d1['transferencia_un_brno_fora_min_max'], d1['transferencia_sectors_p16_med_p84_n']))
            L.append(f"| {k} | {deg.replace('deg', '°')} | {' / '.join(f'{v:+.2f}' for v in d1['corr_V38'])} | {' / '.join(f'{v:+.2f}' for v in d1['corr_V39'])} | {' / '.join(f'{v:+.2f}' for v in d1['nul_V39'])} | {tr} | {' / '.join(f'{v:.2f}' for v in d1['rms_V39_V38'])} |")
    L += ['', "## Corba de preu (A3b): quocient resposta V40/V38 d'un blob DoG ± (σ 2/8/24 px) a 1/3/10 % de la mediana local (σ de soroll entre parèntesis). Ja NO és porta universal: fora de la corona, un tret feble aïllat per sota del S/N regional de la seva banda s'atenua, i es declara.", '']
    for win in ('1.6R', '3.7R', '5.5R'):
        p = REB39 / f"A3b_injeccio_{tau['mode']}_k{tau['k']:g}_tau{tau['tau']:g}_f{tau['se_factor']:g}_min{tau['se_min']:g}_{win}.json"
        if not p.exists(): continue
        res = json.loads(p.read_text())['finestres'][win]['resultats']; L.append(f"- **{win}**:")
        for op in ('MGN', 'WOW', 'ACHF01', 'ACHF04', 'ACHF06'):
            parts = []
            for amp in sorted({kk.split('_a')[1] for kk in res if kk.startswith(op + '_s')}, key=float):
                cells = [(int(kk.split('_s')[1].split('_a')[0]), res[kk]) for kk in res if kk.startswith(op + '_s') and kk.endswith('_a' + amp)]
                parts.append(f"{float(amp) * 100:g} %: " + ' '.join(f"{v['quocient']:.2f}({v['amp_en_sigma_soroll']:.0f}σ)" for s, v in sorted(cells)))
            L.append(f"  - {op}: " + ' · '.join(parts))
    L += ['', '## Capes del projecte (de baix a dalt)', ''] + [f"- {c['name']} — {c['kind']}{' (visible)' if c.get('visible') else ''}" for c in pk['capes']]
    L += ['', "Fora, per ordre teva: " + ', '.join(pk['fora_per_ordre_de_pere']) + '.', '',
          "Vistes: `output/v40_20260909/lliurables/vistes/` i `output/v39_20260909/lliurables/vistes/` (retalls V38|V40 a 1,6/3,7/5,5 R☉, retalls 1:1 a la vora de la Vixen V38|V39|V40, compost). Codi: `research/tools/v39_20260909/` (operadors, estimador, portes) i `research/tools/v40_20260909/` (muntador, rebut). Informe: `research/157`.", '',
          "Límits: les capes P01/P01b/P02 (NRGF/RHEF) i 03/07 no canvien; H1 de 01/04/05 heretat de la V38; meitats de la Sony de la V29; la guarda del soroll és per escala (≥ max(16, ℓ) px). Judici visual de Pere obert."]
    txt = '\n'.join(L) + '\n'; (CT / 'V40_REBUT.md').write_text(txt); (OUT40 / 'lliurables').mkdir(parents=True, exist_ok=True); (OUT40 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE40 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'tau': tau, 'report': 'research/157'})
    shutil.copytree(OUT40 / 'lliurables', IAOUT40 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB40, IAOUT40 / '4-rebuts', dirs_exist_ok=True); shutil.copytree(REB39, IAOUT40 / '4-rebuts-pilot-v39tools', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
