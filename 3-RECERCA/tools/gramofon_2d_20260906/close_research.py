"""Write research guide and provenance, without changing photographic inputs."""
from experiment import ROOT, D, RUN
from pathlib import Path
import hashlib, json, sys, platform
from datetime import datetime, timezone
import numpy, scipy, matplotlib, PIL

def record(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h.hexdigest()}

guide='''# Què hem après sobre els cercles

Hem provat una funció contínua bidimensional i una correcció abans del filtre. **Hi ha un resultat parcial útil, però encara no un remei complet validat.**

Una estimació local del fons evita que un punt brillant alteri tot l'anell del mateix radi. Això actua sobre un mecanisme del filtre que la interpolació entre cercles no elimina. Però també pot absorbir arcs reals o deixar halos locals; les proves ho mostren i aquests candidats no s'han aplicat a V31.

La prova més clara és injectar arcs que sabem que són reals. El refit robust conserva força bé un arc estret i intens, però falla amb arcs febles o amples. Amb soroll, fins i tot aquell arc estret supera lleugerament el límit d'error de forma. No hem canviat el límit per fer-lo passar.

![Arcs coneguts i resposta: amb soroll, mateixa escala per a tots els casos](/Users/USUARI/Downloads/Eclipse%202026/output/gramofon_2d_20260906/lliurables/vistes/06_arcs_robust_detall.png)

A cada fila: arc conegut, model quadràtic local i variant robusta. De dalt a baix l'arc és més ample. El blau més fosc al voltant indica una resposta negativa: un halo introduït pel filtre. La columna dreta és la resposta positiva d'una injecció de 0,02 en log sobre soroll de 0,001; no és una fotografia del Sol. Les amplades són sigma radial de 4/12/24 px. La [vista sintètica completa](</Users/USUARI/Downloads/Eclipse 2026/output/gramofon_2d_20260906/lliurables/vistes/05_arcs_robust_llenc_sencer.png>) conserva també el context.

També hem ajustat un pla additiu diferent per fotograma Sony a partir de les zones comunes. La corona compartida es cancel·la en les diferències: és una manera d'estudiar els desacords de font sense esborrar formes circulars. La millora global és petita i algunes parelles empitjoren. Encara falta demostrar que aquesta correcció elimina les marques al compost natiu i conserva el detall contra Vixen independent.

Un cercle ja present a la base pot ser corona o artefacte. La mateixa forma no permet distingir-los: necessitem les exposicions independents, els dos trens o altra informació física. Això és el que orienta la següent hipòtesi causal.

La V31 queda intacta. Les sis finestres reals s'han analitzat amb Sony sola i Vixen original fix; no s'ha produït una nova versió fotogràfica. L'estudi també rectifica l'abast d'independència d'algunes comparacions anteriors, perquè els marges del filtre podien arribar a píxels fusionats amb Vixen.

[Informe complet, equacions, resultats i reproducció](</Users/USUARI/Downloads/Eclipse 2026/research/143_GRAMOFON_FUNCIO_CONTINUA_2D_20260906.md>) · [Transferència del detall per escala](</Users/USUARI/Downloads/Eclipse 2026/output/gramofon_2d_20260906/lliurables/vistes/02_transferencia_Fourier.png>) · [Context real de les sis finestres](</Users/USUARI/Downloads/Eclipse 2026/output/gramofon_2d_20260906/lliurables/vistes/03_context_Sony_llenc_sencer.png>)
'''
# Markdown local paths are literal absolute paths, enclosed when needed.
guide=guide.replace('!['+'Arcs coneguts i resposta: amb soroll, mateixa escala per a tots els casos](/Users/USUARI/Downloads/Eclipse%202026/', '!['+'Arcs coneguts i resposta: amb soroll, mateixa escala per a tots els casos](</Users/USUARI/Downloads/Eclipse 2026/').replace('06_arcs_robust_detall.png)','06_arcs_robust_detall.png>)')
Path(RUN.lliurable('RESULTAT.md')).write_text(guide)

inputs=[ROOT/'research/tools/v29/cau_final'/f for f in
    ['sony_corrected_total.npy','vixen_total.npy','sony_support.npy','vixen_support.npy']]
inputs += [ROOT/'research/tools/v29_c03_fix'/f for f in
    ['sony_corrected_G.npy','sony_samples.npy','sony_confidence.npy','sony_sample_meta.json','offset_model.json']]
deps=[ROOT/'research/tools/v31_purs'/f for f in ['local_filters.py','common.py']]
deps += [ROOT/'research/tools/eclipse_determinista/comu.py']
deps += [ROOT/'research/tools/v31_purs/qa_science.py',ROOT/'research/tools/v31_purs/build_base.py']
inputs += [ROOT/'research/tools/v31_purs/cau/weight_vixen.npy']
product=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_FiltresPurs.psb')
pr=record(product)
expected='89d509bcc53982307cf9e3d78b0a84ed7548f4045e8cbb95d9f8594e4e877dfd'
assert pr['sha256']==expected, 'Existing V31 product differs from its previous delivery hash'
receipts=Path(RUN.rebut(''))
valid=[p for p in receipts.glob('*.json') if 'SUPERSEDED' not in p.name and p.name!='manifest.json']
for p in valid:json.loads(p.read_text())
artifacts=list(Path(RUN.vista('')).glob('*.png'))+list((D/'native_pilots').glob('*.npy'))
artifacts += [Path(RUN.lliurable('RESULTAT.md')),ROOT/'research/143_GRAMOFON_FUNCIO_CONTINUA_2D_20260906.md']
report={'created_utc':datetime.now(timezone.utc).isoformat(),
    'claim_id':'CODEX_GRAMOFON_2D_20260906',
    'status':'completed exploratory study; no candidate accepted as a full artifact correction',
    'core_implementation_PASS':json.loads((receipts/'core_validation.json').read_text())['PASS'],
    'product_unchanged':pr,'product_hash_matches_previous_delivery':True,
    'runtime':{'python':sys.version,'platform':platform.platform(),'numpy':numpy.__version__,
        'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'pillow':PIL.__version__},
    'inputs':[record(p) for p in inputs],
    'code':[record(p) for p in sorted(D.glob('*.py'))]+[record(p) for p in deps],
    'plan':record(D/'PLAN.md'),
    'valid_receipts':[record(p) for p in sorted(valid)],
    'superseded_not_evidence':[record(p) for p in sorted(receipts.glob('*SUPERSEDED.json'))],
    'artifacts':[record(p) for p in sorted(artifacts)],
    'scope':'G channel; synthetic full canvases; six native Sony-only windows; Vixen fixed; sparse per-frame plane fit',
    'visual_QA':'Full real context, six native panels, synthetic nulls, Fourier transfer, full robust scene and closeup inspected. Fixed displays; clipping declared.',
    'limitations':['No general smooth-null pass','No full-canvas preservation pass','Robust positive arcs only 1 of 18 passed',
       'Fine real coherence not established','Per-frame planes not projected to native data or independently validated'],
    'parallel_review':'Halley: algebra and per-frame source model; Raman: support geometry and validation scope; both read-only'}
(receipts/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'manifest':str(receipts/'manifest.json'),'V31_hash_match':True,
 'valid_receipts':len(valid),'artifacts':len(artifacts)},indent=2))
