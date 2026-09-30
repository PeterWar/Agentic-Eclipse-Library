"""No-clobber publication after reopened-pixel and real Photoshop verification."""
from pathlib import Path
import json,hashlib,os,datetime,sys
D=Path(__file__).parent;ROOT=D.parents[2];C=D/'cau'
CT=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
def fp(p):
    p=Path(p);st=p.stat();h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    assert (st.st_size,st.st_mtime_ns)==(p.stat().st_size,p.stat().st_mtime_ns)
    return {'path':str(p),'bytes':st.st_size,'sha256':h.hexdigest()}
def main():
    q=json.loads((D/'psb_verification.json').read_text());assert q['PASS']
    qa=json.loads((D/'candidate_qa.json').read_text());assert qa['status']=='CHECKS_PASS'
    gate=(D/'porta_photoshop.log').read_text().strip();assert gate=='OBRE 10551 px x 7506 px · 30 capes'
    gm=json.loads((D/'photoshop_gate_meta.json').read_text());assert gm['restored'] and gm['closed_without_saving_by_canonical_gate']
    visual=json.loads((D/'visual_review.json').read_text());assert visual['review_completed']
    assert json.loads((D/'rotation_controls.json').read_text())['PASS']
    judge=json.loads((D/'fixed_judge.json').read_text());assert len(judge['layers'])==5
    brno=json.loads((C/'brno_comparison.json').read_text());assert 'V31_merged' in brno['results']['1.0']
    stage=CT/'V31_verificacio.psb';final=CT/'V31.psb';assert not final.exists()
    assert fp(stage)['sha256']==q['sha256']
    old=fp(CT/'V30.psb');assert old['sha256']=='0d1f23fe5c56acf60bb35d3e24acea02fffaaf333d04d7a3aa17e0aac4f3f8c0'
    pack=json.loads((D/'packaging_receipt.json').read_text())
    dependencies=[old,fp(ROOT/'research/tools/v30/delivery_manifest.json'),fp(D/'input_manifest.json'),fp(ROOT/'research/tools/v29/cau_final/fusion_support.npy')]
    sourcefiles=sorted(D.glob('*.py'))+[ROOT/f'research/tools/{p}' for p in ['v29/common.py','v29/inspect_inputs.py','v29/build_canvas.py','v29/qa_rasters.py','v29/audit_geometry.py','v29_c03_fix/package_only03.py','v30/compare_brno.py','v30/photoshop_gate.py','eclipse_determinista/comu.py','eclipse_determinista/f3.py','encaix_sony/psb_utils.py','capes_totals_v14/porta_photoshop.sh']]
    # Complete all manifest work before publishing the unique filename.
    manifest={'PASS':True,'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':str(final),'sha256':q['sha256'],'bytes':q['bytes'],'size':q['size'],'depth':16,'layers':30,'source':old,'dependencies':dependencies,'code':[fp(p) for p in sourcefiles],'new_rasters':[fp(C/f'{tag}_final_u16.npy') for tag in ('01','02','04','05','06')],'composite':fp(C/'composite.npy'),'sigma_px':qa['sigma_px'],'verification':str(D/'psb_verification.json'),'photoshop':gate,'judges':[str(D/'fixed_judge.json'),str(C/'brno_comparison.json')],'preservation':'25 layers entirely identical; five non-azimuthal layers only RGB and version name changed; all masks, alpha, opacity, visibility, order and azimuthal03/07 preserved','visual_acceptance':'Pere final visual judgement pending','limitations':['Smoothing also attenuates real fine structures: sigma3 retains about74-75 percent coherent16-32px detail in four inner windows; about92 percent at32-64px.','H1b warnings remain for01/04/05; no certification of total microcircle elimination.','Outer detail beyond5R remains unvalidated by Brno; no crop or mask added.','Photographic derivative, same canvas/FOV; no RAW recalibration.'],'runtime':{'python':sys.version,'executable':sys.executable}}
    manifest['evidence']=[fp(D/p) for p in ['candidate_qa.json','rotation_controls.json','fixed_judge.json','visual_review.json','packaging_receipt.json','psb_verification.json','porta_photoshop.log','photoshop_gate_meta.json','cau/brno_comparison.json']]
    os.link(stage,final);stage.unlink()
    (D/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    rows='\n'.join(f"| {tag} | {qa['sigma_px'][tag]} | {qa['layers'][tag]['H1']['worst']['error']:.6f} | {qa['layers'][tag]['H1b']:.6f} |" for tag in qa['layers'])
    jr=judge['layers']['01']['median'];br=brno['results']['1.0']
    report=f'''# V31 — suavitzat dels filtres no azimutals

Lliurable: `{final}`. 10551 × 7506, RGB16, 30 capes; {q['bytes']:,} bytes.
SHA-256 `{q['sha256']}`.

## Correcció de l'abast

Pere ha precisat: «els minicercles els veig només en els filtres que NO son azimutals».
V31 segueix aquesta observació: modifica01/02/04/05/06. Les capes03 i07 deV30
continuen exactament igual, inclosa visibilitat. El fet que les marques blaves
del document anterior fossin pintades a03 no identifica el filtre causant
quan es veu un compost de capes. La interpretació anterior deV30 no s'ha de
reutilitzar com a diagnòstic dels minicercles que Pere acaba d'identificar.

## Operador i selecció

Gaussiana cartesiana positiva sobre el detall relatiu al gris neutre:
`0.5 + G_sigma((F-0.5)*support)/G_sigma(support)`; fora suport,32768.
Entrada: RGB gris REAL delPSBV30 congelat. Cinc ràsters delpilot i els reals
coincideixen dins1DN16. No es refitaH1 ni contrast; cap tall circular, nova
màscara, reescalat, polarització o canvi deFOV. V30 queda immutable.

| Capa | Sigma px | H1 màxim | H1b |
|---|---:|---:|---:|
{rows}

H1 comprova tots els píxels del suport en200anells, també els parcials del
limbe. Llindar0,05: passen els cinc.04sigma3 s'ha rebutjat perquè H1=0,075372;
04sigma1,5 passa amb0,036522 sense afegir recentrat radial. H1b>2 és un AVÍS
que es conserva; no s'ha declarat absència de tota estructura espúria.
Sigma5 es descarta visualment per pèrdua excessiva de detall. Sigma1,5 general
deixa més granulat; es reserva al filtre04més fi.

## Jutge fix i cost de detall

SonyBlnG FIX sense suavitzar; quatre finestres256×256 a1,6R dominades perVixen.
Retirada d'un pla, Hann2D, FFT2, bandes fixes i mediana entre finestres.
El compost comparteix fonts amb el jutge: aquesta comprovació entre trens
és útil a l'interior dominat perVixen, no una prova independent universal.
Rebut amb coordenades i totes les capes: `fixed_judge.json`.

01, sigma3: RMS restant8–16px={jr['8-16']['RMS_new_over_old']:.4f}; component
coherent restant16–32px={jr['16-32']['coherent_gain']:.4f},32–64px={jr['32-64']['coherent_gain']:.4f},
64–128px={jr['64-128']['coherent_gain']:.4f}. Correlació16–32px
{jr['16-32']['r_old']:.4f}→{jr['16-32']['r_new']:.4f}. Es redueix també detall
real fi, no només soroll.04sigma1,5 conserva aproximadament93% del coherent
16–32px. Injecció additiva sobre el detall abans de l'únic operador nou a
`candidate_qa.json`; és transferència d'aquest suavitzat, no MTF delsRAW.

Brno usa els merged REALS deV30/V31, registre i referències congelats,
mateixa descodificació sRGB i mètodeV30. Pearson mediana a1° per1,2–3/3–5/5–9R:
V30={br['V30_merged']['r']}; V31={br['V31_merged']['r']}.
El resultat exterior>5R continua sense validació i no prova el microgra.
Les referències només jutgen; mai aporten píxels.

## Integritat i inspecció

25 capes deV30 preservades íntegrament; cinc canvien nomésRGB i nomV31.
Alfa, màscares, opacitats, visibilitats i ordre dels30 elements intactes;
metadades globals intactes. Recomposició delPSB reobert≤1DN16.
Fora la unió de màscares visibles modificades: {pack['outside_changed_visible_masks']}.
Photoshop real: **{gate}**. Document propi tancat sense desar; diàlegs restaurats.
Vistes a `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v31_20260905`:
llenç sencer, quatre limbes, filaments i sectors marcats al100%.
Suavitzat visible, amb textura residual; acceptació estètica final dePere pendent.

## Reproducció

Manifest de fonts i hashes: `research/tools/v31/delivery_manifest.json`.
Intèrpret `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, amb
`PYTHONDONTWRITEBYTECODE=1`. Ordre: pilot_isotropic → check_candidate →
package_v31 → verify_v31/fixed_judge/compare_brno_v31 → photoshop_gate →
inspeccióvisual → finalize_delivery. Els scripts refusen sobreescriureV31;
una reconstrucció requereix noves destinacions declarades en una còpia.
No s'han modificatRAW, runs, maquinari niCLAUDE_STATUS.
'''
    (ROOT/'research/139_V31_mes_suavitzat.md').write_text(report)
    (CT/'V31_REBUT.md').write_text(report)
    print('V31 published',q['sha256'],flush=True)
if __name__=='__main__':main()
