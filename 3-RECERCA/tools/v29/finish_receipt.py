"""Write the delivery receipt only after reopening and Photoshop pass."""
from common import *
from inspect_inputs import sha
import shutil,datetime

def main():
    qa=json.loads((CAU/'psb_verification.json').read_text());assert qa['PASS']
    gate=(HERE/'porta_photoshop.log').read_text().strip();assert gate.startswith('OBRE '),gate
    inputs=json.loads((HERE/'cau/input_manifest.json').read_text());rq=json.loads((CAU/'raster_qa.json').read_text());cfg=json.loads((CAU/'delivery_config.json').read_text())
    manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':{'path':qa['path'],'sha256':qa['sha256'],'bytes':qa['bytes']},'inputs':{},'code':{},'final_rasters':{},'Photoshop':gate}
    for name,v in inputs['sources'].items():
        actual=sha(v['snapshot']);assert actual==v['sha256'];manifest['inputs'][name]={'path':v['original'],'snapshot':v['snapshot'],'sha256':actual,'bytes':v['bytes']}
    for p in sorted(HERE.glob('*.py')):manifest['code'][p.name]=sha(p)
    for n in ['fusion_support.npy','gran_support.npy','achf_u16.npy','passalt24_u16.npy','gran_u16.npy','achf_mask_final.npy','passalt24_mask_final.npy','gran_mask_final.npy','base_cel4_final.npy','base_amb_cel_final.npy','composite_delivery.npy']:
        manifest['final_rasters'][n]=sha(CAU/n)
    savejson(CAU/'delivery_manifest.json',manifest)
    tr=json.loads((CAU/'transfer_receipt.json').read_text());ac=json.loads((CAU/'angular_control_receipt.json').read_text());warn=json.loads((CAU/'passalt_spectral_warning.json').read_text());g=json.loads((CAU/'gran_azimuthal_receipt.json').read_text())
    hrows='\n'.join(f"| {n} | {v['worst']['error']:.6f} |" for n,v in rq['H1'].items())
    crows='\n'.join(f"| {n} | {v['at_zero_pearson']:.6f} | {v['null_180_pearson']:.6f} | {v['peak_angle_deg']:.2f}° |" for n,v in rq['geometry'].items())
    text=f'''# V29 — detall exterior, ghost i unió temporal de la corona

Derivat visual editable del 05-09-2026, sobre el mateix llenç de Pere.

## Fitxer i comprovació real

- PSB: `{qa['path']}`.
- {FW} × {FH} píxels, RGB de 16 bits, {qa['layers']} capes, {qa['bytes']:,} bytes.
- SHA-256: `{qa['sha256']}`.
- Photoshop: **{gate}**. Obert i tancat sense desar.
- Reobertura psd-tools: 20 capes originals preservades amb tots els canals comprimits, alfa, màscares, coordenades, modes i opacitats idèntics. Les cinc capes noves coincideixen exactament amb els ràsters i les màscares de construcció. El merged coincideix exactament amb la previsualització; la recomposició de capes reobertes difereix com a màxim {max(v['reopened_layers_max_DN'] for v in qa['composite'].values()):.0f} DN de 16 bits per quantització.

## Canvis A–E

**A — ACHF fi i corona exterior.** S'ha eliminat el tall que reduïa el filtre a zero a partir de 5 R☉. L'ACHF 2/4/8/16/32 i el passa-alt 24 treballen sobre ln TOTAL, amb normalització de contrast després del filtre, mediana de les realitzacions RGB vàlides, resolució contrastada per bandes i centrat H1. No es resten perfils radials abans del filtre ni s'apliquen les antigues osques direccionals globals. Això conserva resposta exterior sense identificar tot el gra de V25 com a detall solar.

**B — 03 ACHF azimutal i marques blaves.** La font Sony B és primària dins del seu camp; A només aporta les vores de cobertura o el camp que B no cobreix. Al ghost, el resultat és RGB idèntic a B en 1.200 × 1.200 píxels: desapareix el canvi circular de donant. El filtre ample final és angular: G8 − (G32 + G64 + G128)/3, amb sigmes expressades en píxels d'arc i convolució FFT periòdica. Cada tren es filtra amb la seva pròpia màscara abans de combinar-los. No s'introdueix la normalització fotomètrica entre càmeres dins del filtre ni es filtra deliberadament en radi. La interpolació bilineal de la graella polar continua sent una aproximació declarada. Les marques de Pere són finestres de verificació, mai màscares d'esborrat.

El judici independent amb el mateix operador angular dona Vixen–Sony r=0,365 al ghost (corroboració moderada), r=0,496–0,941 al SE i r=0,931–0,994 en moltes marques petites/NW. La fidelitat del nou gran a Sony al ghost és r=0,986. Els 161 cercles de control al voltant de 2 i 2,65 R☉ no detecten un anell additiu de la barreja: mitjana crua màxima 1,51×10⁻⁶ i 7,61×10⁻⁷. La taula completa i els límits són a `independent_review.json`.

**C — 04 ACHF ample 9R.** S'ha retirat: el seu desenfoc azimutal molt ample i el límit polar no aportaven una capa útil diferenciada. No hi ha una còpia oculta que es pugui activar accidentalment.

**D — Passa-alt 24 i ghost del fi.** Comparteixen la font Sony neta i recuperen cobertura exterior. Els filtres es conserven a amplitud completa dins del PSB. La força inicial resideix només en l'opacitat editable: ACHF fi {36/255*100:.2f}%, passa-alt {20/255*100:.2f}%, azimutal {38/255*100:.2f}%, tots en Superposar. Aquesta escala inicial és una decisió visual; no s'han esborrat píxels de detall per aconseguir-la.

**E — Geometria i Lluna en moviment.** S'ha mantingut la transformació V27/V28 ajustada contra les capes de Pere, corregint la referència del centre a l'índex real de l'apilat. Centre solar del PSB: ({CX:.6f}, {CY:.6f}); R☉={RS:.9f} px. Les dades s'han recompost directament des dels plans CFA cap al llenç PSB existent amb una sola interpolació bilineal. No hi ha canvi de FOV, dimensions o retall. Base i detall utilitzen la unió real de la corona observada en les diferents fotografies; no un forat circular d'1,05 R☉.

El suport té {rq['support']['pixels']:,} píxels i recupera {rq['support']['inner_1_05R']:,} píxels dins d'1,05 R☉. La intersecció que sempre fou ocultada continua exclosa. El filtre ample G descarta només {g['invalid_G_excluded']} píxels sense G positiu/finit en cap dels dos trens; el fi/PAL poden usar altres realitzacions RGB vàlides. El càlcul directe recupera 11.159.171 píxels respecte de l'antic rectangle intermedi. Només es modula la vora física exterior segons el suport del nucli del filtre: 96 px al fi, 72 al passa-alt i 384 a l'azimutal. No hi ha una amputació circular de la corona externa.

## Mesures i límits

H1 estricte: totes les medianes dels anells observats, inclosos els parcials del limbe i de les vores, es comproven sense excloure la franja recuperada. Llindar 0,05:

| Filtre | Màxim absolut de mediana − 0,5 |
|---|---:|
{hrows}

Alineament solar amb Pearson real, control girat 180° i controls ±1° rebutjats:

| Filtre | Pearson a 0° | Control 180° | Pic residual |
|---|---:|---:|---:|
{crows}

Les capes originals s'han auditades segons el seu marc: solar, lunar, estel·lar o comparació. L'antic `Fons per raig` té un pic feble desplaçat −0,75° i queda ocult com a font històrica; no s'ha girat a cegues ni es declara que totes les capes històriques passin el mateix control. La capa ampla antiga també fallava aquest control i s'ha retirat. L'alineament solar no s'aplica a earthshine, estrelles, LROC o perles com si fossin la mateixa referència temporal.

Les injeccions aparellades a la correcció Sony i els controls de transferència de la resolució passen: {tr['PASS']}. Els controls analítics angulars i el nul radial passen: {ac['PASS']}. Els controls angulars validen el nucli FFT; no certifiquen automàticament tota la interpolació ni tota textura fotogràfica.

**Avís que es manté:** H1b del passa-alt és {warn['after_final_H1']:.3f}, per damunt del llindar d'avís 2 (abans del darrer centrat: {warn['before_final_H1']:.3f}). No es declara resolt aquest avís espectral. No s'ha aplicat una osca global destructiva només per fer baixar aquest número. L'ACHF fi i l'azimutal tenen H1b {rq['H1']['achf']['bin_frequency_diagnostic']:.3f} i {rq['H1']['gran']['bin_frequency_diagnostic']:.3f}.

L'evidència independent de 8–16 px a l'exterior és feble o nul·la en els controls estudiats. Les bandes de 32–64 i 64–128 px estan més ben corroborades segons el sector. La textura fina no es presenta íntegrament com a estructura solar demostrada. Usar B com a font primària redueix el nombre d'observacions combinades i pot augmentar el soroll respecte d'A+B; les dades d'A es conserven i aporten el camp descobert. Les capes són derivats visuals, no nous màsters radiomètrics acceptats.

La reproducció exacta de 11.794 píxels interiors recuperats en la graella comuna anterior queda a `cau/limb_receipt.json`: 301 tenien una única observació. Aquest recompte és d'aquella graella, no s'ha confós amb el recompte nou del PSB.

## Reproducció i evidència

Arrel de codi: `{HERE}`. Branca de càlcul lliurada: `cau_final`, amb `V29_FINAL_GRID=1`. `cau` conté entrades congelades i diagnòstics previs; els pilots isotrops i de donant circular són rebutjats i no són V29.

Ordre principal: `prepare_final_grid.py` → `merge_pointings.py` → `coherent_resolution.py` → `fuse_and_filter.py --source-only` → `refine_detail.py` → **`gran_azimuthal.py`** → `build_canvas.py --base-only` → `qa_rasters.py`, `qa_transfer.py`, `qa_angular_controls.py` → `select_delivery.py` → `make_delivery.py` → inspecció visual → `package_psb.py` → `verify_psb.py` → `porta_photoshop.sh`. L'empaquetat del PSB impedeix sobreescriure un V29 existent; els scripts de càlcul sí que regeneren els NPY de treball. El centrat final és PCHIP amb els centres radials realment observats, 200 bins, extrems de pendent zero i mínimes passades fins al llindar declarat.

Entrades RAW i calibracions: runs Vixen 019 i Sony 016 d'`Eclipse determinista/1-RUNS`; geometria i cel preexistents declarats en els scripts. Els hashes dels scripts V29, dels PSB d'entrada i dels ràsters lliurats són a `delivery_manifest.json`.

Evidència de QA: `raster_qa.json`, `psb_verification.json`, `pointing_merge_receipt.json`, `gran_azimuthal_receipt.json`, `independent_review.json`, `transfer_receipt.json`, `angular_control_receipt.json`, `footprint_taper_receipt.json` i `passalt_spectral_warning.json` a `{CAU}`.

Previsualització real i panells 1:1: `{OUT}` (`V29_…`). Els altres fitxers `PILOT_…` i `CANDIDAT_…` són evidència de treball.
'''
    receipt_path=CT/'V29_REBUT.md';research_path=ROOT/'research/134_V29_detall_unio_temporal.md'
    for p in (receipt_path,research_path):
        with p.open('x') as f:f.write(text)
    target=OUT/'ENTREGA';target.mkdir(exist_ok=True)
    for p in OUT.glob('V29_*.png'):
        if p.name.startswith(('V29_COMPOST','V29_VERIFICADA','V29_1a1','V29_QA')):shutil.copy2(p,target/p.name)
    shutil.copy2(receipt_path,target/receipt_path.name)
    log('receipt and delivery manifest written')

if __name__=='__main__':main()
