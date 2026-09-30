"""Publish validated staging in-place with a compare-before-replace guard."""
from package_only03 import *
from datetime import datetime,timezone

def main():
    manifest=json.loads((D/'input_manifest.json').read_text());v=json.loads((D/'psb_verification.json').read_text());qa=json.loads((D/'candidate_qa.json').read_text());loc=json.loads((D/'local_preview_receipt.json').read_text());judge=json.loads((D/'independent_judge.json').read_text())
    gate=(D/'porta_photoshop.log').read_text().strip()
    assert v['PASS'] and qa['PASS'] and loc['outside03_mask']['PASS'] and judge['accepted_for_layer03']
    assert gate=='OBRE 10551 px x 7506 px · 25 capes',gate
    assert sha(TARGET)==v['sha256'],'staged file changed since verification'
    live=Path(manifest['source']);assert sha(live)==manifest['sha256'],'Live V29 changed: preserve user edits; do not replace'
    assert sha(Path(manifest['backup']))==manifest['sha256']
    owner=json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text());assert owner['claim_id']=='CODEX_V29_C03_FIX_20260905'
    now=datetime.now(timezone.utc).isoformat();os.replace(TARGET,live)
    assert live.stat().st_size==v['bytes'];assert sha(live)==v['sha256']
    hashes={p.name:sha(p) for p in sorted(D.glob('*.py'))}
    for name in ['offset_model.json','gran_u16.npy','composite.npy','candidate_qa.json','psb_verification.json','independent_judge.json','local_preview_receipt.json']:
        hashes[name]=sha(D/name)
    final={'completed_utc':now,'path':str(live),'sha256':v['sha256'],'bytes':v['bytes'],'backup':manifest,'photoshop_gate':gate,'all_other24_layers_identical':True,'only_layer20_RGB_changed':True,'mask_opacity_visibility_metadata_preserved':True,'hashes':hashes}
    savejson(D/'delivery_manifest.json',final)
    OUT='/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_c03_fix_20260905'
    report=f'''# V29 — correcció exclusiva de la capa 03

Lliurada el {now}. Autorització de Pere: «corretgeix doncs aquesta capa en la V29».

## Resultat i preservació

S'han substituït només els tres canals de color de `03 ACHF azimutal 8-128 · V29` (índex 20) dins del mateix `V29.psb`. Les altres 24 capes, incloses les acceptades `01 ACHF fi 2-32 · V29` i `02 Passa-alt 24 · V29`, conserven exactament els canals comprimits i el registre complet de metadades. La 03 conserva alfa, màscara, nom, posició, geometria, visibilitat, mode Superposar i opacitat 38/255. El merged s'ha actualitzat per reflectir la capa corregida.

- Fitxer: `{live}`.
- 10551 × 7506 píxels, RGB16, 25 capes; {v['bytes']:,} bytes.
- SHA-256 nou: `{v['sha256']}`.
- Còpia anterior: `{manifest['backup']}`.
- SHA-256 anterior: `{manifest['sha256']}`.
- Photoshop real: **{gate}**. Obert el PSB de verificació amb nom propi i tancat sense desar; després, substitució atòmica de V29 amb comprovació que el fitxer viu encara coincidia amb la còpia inicial.
- Error màxim entre merged i recomposició de les capes reobertes: {max(x['max_reopened_layers_DN'] for x in v['composite'].values()):g} DN de 16 bits.

## Correcció del desnivell HDR

El diagnòstic `research/135_V29_pentagonals.md` identificava els contorns amb l'entrada dels Vixen de 10 s i el Sony B de 8 s al compost. S'ha ajustat un offset additiu global per fotograma i canal natiu, amb diferències de captures del mateix cel en zones comunes vàlides. Referència: una captura de 2 s per grup (Vixen, Sony A, Sony B). Ajust robust sobre sectors azimutals alterns; l'altra meitat queda reservada per validar. Els guanys de coherència k originals es conserven i no es dupliquen.

La correcció es projecta com Σ(w·b)/Σw amb els mateixos pesos HDR, interpolacions CFA, registres i geometries lunars originals. Es recalcula només la font G destinada a 03; els RAW, runs, màsters i les capes acceptades queden intactes. La correspondència de baixa freqüència Sony A/B s'actualitza per incorporar els nous nivells; B continua sent primària i A aporta la seva cobertura complementària.

El filtre angular G8 − (G32 + G64 + G128)/3, els perfils de contrast, l'escala tanh, el mapa de resolució, el centrat H1 i l'opacitat són els mateixos. La validesa original es calcula abans dels pesos entre trens, preservant el fallback Sony al limbe. Cap retall circular, màscara dibuixada amb les marques, osca, clonació o inpainting. Les finestres dels PNG són només ampliacions diagnòstiques; el llenç de sortida no canvia.

## Validació i jutge independent

- Model revisat per un agent independent de només lectura; comprovació amb exposicions i sectors reservats, seguida de comparació entre Vixen i Sony i inspecció dels contorns al 100%.
- Indicador local de pas al SE (6142,4081): cru 0,0444 → 0,00019; visible 0,0217 → 0,00436 (−80%). Al sud (5148,4426): visible 0,0241 → 0,00262. Al contorn exterior llarg: indicador cru −78%. Són indicadors de pas amb pendent local retirada; també poden contenir gradients coronals, no són una mesura pura d'artefacte.
- Filaments de 20–100 px d'arc: correlació abans/després 0,997 / 0,991 / 0,978 a 1,12–2 / 2–2,65 / 2,65–3,8 R☉. Correlació independent Vixen–Sony 0,964 / 0,916 / 0,563.
- H1 estricte: error màxim de mediana respecte de 0,5 = {qa['H1']['worst']['error']:.6f} (<0,05), incloent els anells parcials observats.
- Alineament solar: pic 0°, Pearson {qa['solar_geometry']['at_zero_pearson']:.6f}; control 180° {qa['solar_geometry']['null_180_pearson']:.6f}. Controls ±1° i 180° rebutjats.
- Suport de 03: {qa['support_pixels']:,} píxels, {qa['inner_1_05R_pixels']:,} dins d'1,05 R☉, idèntic a l'original. Als {loc['outside03_mask']['pixels']:,} píxels amb màscara 03 zero, diferència del compost exactament zero.
- Injecció comuna al nivell de mostres calibrades, amb pesos i offsets fixos: error de transferència <1,8×10⁻¹⁰; el senyal comú es cancel·la en les diferències entre captures. Aquesta prova no és una injecció RAW amb pesos de saturació recalculats.
- Inspecció 100% de NE, SE, contorn exterior Sony i limbe N/S/E/W. Jutge: PASS de la correcció de la capa03; cap polígon comparable al precedent ni anell nou visible.

## Límits declarats

El zero additiu absolut no està físicament identificat: és relatiu a una captura de 2 s. Les captures curtes desconnectades del graf mantenen offset zero. La validació de les rampes, excloses de l'ajust, conserva residuals de fins a −1,84% al Vixen 2984 i −1,23% al Sony 6993; la correcció no certifica una calibració radiomètrica absoluta perfecta.

L'RMS de la banda de detall queda al 99,1% / 95,3% / 82,8% de l'anterior en els tres intervals indicats: a l'exterior baixa un 17,2%, incloent un 16–19% del component correlacionat amb els trens. La forma es conserva molt bé, però no tota l'amplitud anterior. No s'ha abaixat l'opacitat per obtenir-ho.

H1b de 03: {qa['H1b']:.6f}, per damunt del llindar d'avís 2 (abans 0,799590). La inspecció independent no identifica un anell nou; l'avís es conserva, sense aplicar una osca per fer baixar el número. Continua intacte l'avís H1b 2,976378 del passa-alt acceptat per Pere. L'acord entre dos trens processats amb el mateix mètode no exclou per si sol un artefacte compartit.

Aquesta és una correcció d'un **derivat visual editable**; no promociona nous màsters científics ni reobre l'acceptació de les capes 01/02.

## Reproducció i evidència

Codi i rebuts: `{D}`. Ordre: `sample_frames.py` → `fit_offsets.py` → `apply_offsets.py` → `filter03.py` → `qa_candidate.py` + `local_previews.py` → revisió independent → `package_only03.py` → `verify_only03.py` → `porta_photoshop.sh` sobre el PSB de verificació → `finalize_delivery.py`. `package_only03.py` exigeix revisió independent acceptada i prohibeix trepitjar un staging existent. `finalize_delivery.py` comprova els hashes i la porta real abans de substituir el fitxer viu; no està pensat per ser reexecutat sobre la versió ja substituïda.

Fonts originals i caches: `research/tools/v29/cau_final`, runs Vixen 019 i Sony 016. Cap d'aquests s'ha regenerat. Els hashes de codi, model, ràster, merged i rebuts són a `delivery_manifest.json`. El rebut complet de la V29 anterior es conserva al costat de la còpia anterior del PSB.

Previsualitzacions: `{OUT}`. `V29_CORREGIDA_VERIFICADA.png` prové de la recomposició de les capes del PSB reobert; `AB_03_zona_pentagonals.png` compara 03 abans/després; `QA_100_*` conserva una mostra per píxel i inclou diferències.
'''
    (ROOT/'research/136_V29_capa03_corregida.md').write_text(report)
    (CT/'V29_REBUT.md').write_text(report)
    log('V29 delivered in-place; receipt updated')
if __name__=='__main__':main()
