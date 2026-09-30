"""Package the completed diagnostic study; never alter photographic products."""
from geometry import ROOT,D,RUN
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,platform
import numpy,scipy,cv2,matplotlib,PIL

def record(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h.hexdigest()}

guide='''# Geometria dels arcs: resultat de la comprovació

**Mesurem una preferència tangencial respecte del Sol, però no podem confirmar que els arcs visibles siguin cercles perfectes amb un centre comú.** El resultat geomètric de les capes finals 01/02 és indeterminat.

En cadascuna de les dues capes, 19 dels 24 sectors estudiats tenen orientació preferentment tangencial. La intensitat d’aquesta preferència varia molt segons la zona. Una orientació compatible amb arcs solars no demostra que les marques formin circumferències senceres.

La prova ha deixat moure el centre i ha comparat cercles amb el·lipses, ajustant uns sectors i comprovant-ne uns altres. Els controls coneguts permeten recuperar el seu centre amb menys de 0,1 píxel d’error, però els ajustos de les capes reals són inestables. Alguns perfils tenen també radis amb informació insuficient: aquests errors no s’han utilitzat per rebutjar la hipòtesi circular.

**Sí que hi ha una component circular molt clara en el delta de la correcció H1 de la capa 01.** El seu centre coincideix amb el centre solar emprat pel programa i el model explica aproximadament el 98% de l’energia d’aquest senyal filtrat als sectors reservats. H1 ja es calcula per radi; això confirma la geometria d’aquesta operació, però no demostra que origini tots els minicercles visibles.

Els centres de referència solar i lunar C2 estan separats només 1,01 píxels. Aquest assaig no els pot distingir amb confiança.

![Orientació segons sector](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906/lliurables/vistes/04_orientacio_per_sectors.png>)

Valors positius indiquen preferència tangencial; negatius, radial. No són percentatges de píxels circulars ni correlacions de brillantor. La prova cobreix 2,5–4,5 radis solars i no és un traçat individual de cada arc.

**La nova observació de Pere sobre la corona interior aporta una pista concreta.** En 01/02, l’orientació és fortament radial fins a 2 radis del centre i es torna progressivament tangencial cap a fora. Just a 2 radis comencen tant la barreja Vixen→Sony com el canvi del suavitzat adaptatiu; les transicions acaben a 2,65 radis. La coincidència mereix una prova causal, però no demostra si els arcs es creen en la barreja o ja venen d’una font. La dominància radial interior tampoc demostra absència absoluta d’arcs febles.

[Comparació per radi](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906/lliurables/vistes/05_orientacio_per_radi.png>) · [Finestres natives de dins a fora](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906/lliurables/vistes/06_finestres_per_radi.png>)

La V31 queda intacta, amb el mateix SHA-256 que al lliurament anterior. No s’ha aplicat cap correcció ni generat cap PSB nou.

[Informe complet i limitacions](</Users/USUARI/Downloads/Eclipse 2026/research/144_GEOMETRIA_ARCS_SOLARS_20260906.md>) · [Context del llenç complet](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906/lliurables/vistes/01_context_llenc_sencer.png>) · [Finestres natives](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906/lliurables/vistes/02_finestres_natives.png>) · [Centres ajustats i controls](</Users/USUARI/Downloads/Eclipse 2026/output/geometria_arcs_20260906/lliurables/vistes/03_centres_i_controls.png>)
'''
Path(RUN.lliurable('RESULTAT.md')).write_text(guide)
inputs=[ROOT/f'research/tools/v31/cau/{tag}_final_u16.npy' for tag in ['01','02']]
inputs += [ROOT/'research/tools/v29/cau_final'/name for name in
    ['achf_smoothed.npy','passalt24_smoothed.npy','achf_u16.npy','passalt24_u16.npy',
     'fusion_support.npy','vixen_support.npy','sony_support.npy','achf_mask_final.npy','passalt24_mask_final.npy','direct_grid_receipt.json']]
inputs += [ROOT/'research/tools/capes_totals_v14/cau_v21/limbe_v23.json']
inputs += [ROOT/'research/tools/v29/cau_final/resolution_sigma.npy']
product=record('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_FiltresPurs.psb')
assert product['sha256']=='89d509bcc53982307cf9e3d78b0a84ed7548f4045e8cbb95d9f8594e4e877dfd'
receipts=Path(RUN.rebut(''));valid=sorted(p for p in receipts.glob('*.json') if p.name!='manifest.json')
assert len(valid)==23
for p in valid:json.loads(p.read_text())
audit=json.loads((receipts/'profile_support_audit.json').read_text())['rows']
weak=sum(r['weak_or_zero_knot_support_predictions']>0 for r in audit)
assert len(audit)==72 and weak==27
artifacts=sorted(D.glob('*.npz'))+sorted(Path(RUN.vista('')).glob('*.png'))
artifacts += [Path(RUN.lliurable('RESULTAT.md')),ROOT/'research/144_GEOMETRIA_ARCS_SOLARS_20260906.md']
report={'created_utc':datetime.now(timezone.utc).isoformat(),'claim_id':'CODEX_GEOMETRIA_ARCS_20260906',
    'status':'COMPLETED_DIAGNOSTIC; real final-layer circularity INDETERMINATE',
    'accepted_physical_center':None,'accepted_physical_axis_ratio':None,
    'product_unchanged':product,'product_hash_matches_previous_delivery':True,
    'runtime':{'python':sys.version,'platform':platform.platform(),'numpy':numpy.__version__,
        'scipy':scipy.__version__,'opencv':cv2.__version__,'matplotlib':matplotlib.__version__,'pillow':PIL.__version__},
    'inputs':[record(p) for p in inputs],
    'code':[record(p) for p in sorted(D.glob('*.py'))]+[record(ROOT/'research/tools/eclipse_determinista/comu.py')]+[record(ROOT/'research/tools/v29'/f) for f in ['fuse_and_filter.py','coherent_resolution.py','refine_detail.py']],
    'protocol':record(D/'PLAN.md'),'final_receipts':[record(p) for p in valid],
    'artifacts':[record(p) for p in artifacts],
    'superseded_not_final_evidence':[record(p) for p in sorted(receipts.glob('*SUPERSEDED/*.json'))],
    'profile_audit':{'model_folds':72,'weak_support_detected':weak,'no_weak_knot_detected':72-weak,
        'limitation':'diagonal support only; not a full rank or conditioning audit'},
    'scope':'Original Cartesian coordinates; geometry 01/02 at 2.5-4.5 solar radii; radial orientation extension at 1.2-4.5 solar radii; H1 deltas and fixed synthetic controls; not tracing each visible arc',
    'visual_QA':'Full native-canvas context, native windows, center/control plot, orientation sectors and representative profile plots inspected; fixed diagnostic displays',
    'limitations':['No accepted center or ellipticity for real final layers','No exact-circle or constant-spacing claim',
        'Some profile predictions unsupported; no rejection inferred from extreme CV errors',
        'Controls are fixed examples, not universal false-positive calibration',
        'Upstream radial operations prevent physical independence of sectors',
        'H1 delta precedes final smoothing; amplitude not exact current PSB contribution',
        'Solar versus lunar centers not discriminated'],
    'parallel_review':'Halley: algebra and statistical qualification; Raman: geometry and provenance; read-only; corrections incorporated'}
(receipts/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'manifest':str(receipts/'manifest.json'),'product_hash_match':True,
    'final_receipts':len(valid),'artifacts':len(artifacts),'profile_support_partial':weak},indent=2))
