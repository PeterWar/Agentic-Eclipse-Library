"""Record geometry/PSF audit and the narrow-epoch source negative."""
from a4_sources import *

def main():
 out=O/'R03_lessons';out.mkdir();b0p=R/'4-RESULTATS/earthshine_v50_limb_20260912/B0_native_star_psf.json';c0p=R/'4-RESULTATS/earthshine_max_detail_20260913/C0_stars_psf.json';f4p=R/'4-RESULTATS/v44_earthshine_20260910/4-rebuts/F4_contorn.json';b0=json.loads(b0p.read_text());c0=json.loads(c0p.read_text());f4=json.loads(f4p.read_text())
 save(O/'GEOMETRY_PSF_R03.json',{
  'status':'CONDITIONAL_INFORMATION_NOT_A_VALIDATED_LIMB_RESPONSE',
  'geometry':{'F4_method':f4['method'],'F4_half_rms_px':f4['half_rms'],'F4_interframe_median_sigma_px':f4['interframe_median_sigma'],
   'historical_table_correction':'F4 is maximum radial derivative; m1_vores fits that contour directly. Other table rows use a50percent crossing. The2px difference is not a universal physical radius error.',
   'F1_3_peer_audit':{'refined':29,'insufficient_band':35,'correlation_rejected':3,'all19short_train_model_only':True},
   'F4_peer_component1_current_weighted_D_center_outer_inner':[4.045,7.153,1.259],
   'model_current_weighted_D_center_outer_inner':[2.916,6.222,.0028],
   'inner_weight_fraction_F4_D_gt4':.0001967,
   'geometry_limits':'optical apparent contour is not physical occultation boundary; transporting B_model to D_F4 without recalibrating its abscissa changes the correction arbitrarily'},
  'PSF':{'B0_accepted':b0['accepted'],'B0_core_sigma_native_percentiles':b0['core_sigma_native_percentiles'],'B0_limits':b0['limits'],'B0_wings':'fixed conditional lunar A1 fit, total mass.162430; not independent stellar wings','B0_frame_exposures_seconds':{'2978':1,'2979':2,'2996':1},'C0_qualified':c0['qualified_local'],'C0_decision':c0['decision'],'independent_local_short_epoch_PSF_available':False},
  'previous_failed_optical_models':'4-RESULTATS/earthshine_v50_limb_20260912/RESULTAT_V50_NO_VALIDADA.md; naive repeated inversion is not a new hypothesis',
  'sources':[{'path':str(p.relative_to(R)),'sha256':sha(p)} for p in [b0p,c0p,f4p]],
  'review':'filter_sources PSF; limb_diagnosis geometry; root read producers/receipts and confirmed detector mismatch',
  'no_new_RAW_fit':True,'no_reserved_N_read':True,'PSB_unchanged':True})
 m=json.loads((O/'early_epoch_R03/METRICS.json').read_text());done=json.loads((O/'early_epoch_R03/COMPLETE.json').read_text());brno=json.loads((O/'early_epoch_R03/brno/QA.json').read_text())
 save(O/'early_epoch_R03/DECISION.json',{
  'status':'NOT_PROMOTED','reason':'The narrow-epoch source does not give a general improvement; the upper arc already receives essentially these early short frames. Other changes mix exposure selection with noise and improve one external component while worsening another.',
  'scope':'source-only Vixen ROI, no full-canvas filters regenerated for this rejected candidate',
  'h4_common_triplets':902,'component1_early_same19_C_exact':True,
  'component6_h4_rms_mixed_early':[.014316972297705746,.07185315182880422],
  'valid_pixels':{k:v['valid_pixels'] for k,v in done['source_arrays'].items()},
  'Brno_nominal_Pearson':{str(r['component']):{k:v['Pearson'] for k,v in r['groups'].items()} for r in brno['rows'] if r['smoothing']=='nominal'},
  'limits':['mixed61 means full Vixen B2+tiers counterfactual, not actual D4 splice/Sony/stellar-subtracted source','neff_G is CFA-G weight concentration, not transformed RGB-G noise variance','early3+3 differences include calibration/registration/time effects','small early6/same19 differences do not prove temporal motion harmless where actual contributing populations coincide','no new fullRGB-positive source certification: this is sourceG diagnostic only'],
  'independent_review':'qa_regeneration code/metrics; fixed Brno method inherited reviewed a79','no_PSB_change':True})
 # Update only the specifically contradicted historical detector claim.
 lock=R/'.coordination/claim.lock/owner.json';claim=json.loads(lock.read_text());assert claim['claim_id']==CID
 rel=Path('corregeix-artefactes/references/limbe_lunar_earthshine.md');newrel=Path('corregeix-artefactes/references/lunar_boundary_and_display.md');targets=[R/'.claude/skills'/rel,Path('/Users/USUARI/.codex/skills')/rel,R/'.claude/skills'/newrel,Path('/Users/USUARI/.codex/skills')/newrel]
 for path in targets:
  if str(path) not in claim['scope']:claim['scope'].append(str(path))
 for scope in ['IA/Skills/README.md','explicitly authorized memory note']:
  if scope not in claim['scope']:claim['scope'].append(scope)
 save(lock,claim);changes=[]
 for i,path in enumerate(targets):
  before=path.read_text();(out/(str(i)+'_'+path.name)).write_text(before)
  if path.name=='limbe_lunar_earthshine.md':
   old='## Diagnòstic històric V50–V53: mesurar TOTES les vores al mateix marc amb el MATEIX detector';assert old in before
   after=before.replace(old,'## Diagnòstic històric V50–V53: comparar vores al mateix marc, distingint detectors')
   old='Al marc de la ROI lunar (1400², centre lunar (699,57; 699,65)), 1440 azimuts, detector = 50 % del trànsit al llarg de cada raig, ajust de cercle robust `r(θ) = R + dx cosθ + dy sinθ` (`m1_vores.py`):';assert old in after
   after=after.replace(old,'Al marc de la ROI lunar (1400², centre lunar (699,57; 699,65)), 1440 azimuts i ajust de cercle robust `r(θ) = R + dx cosθ + dy sinθ` (`m1_vores.py`). **Rectificació V85 R03:** F4 usa el màxim de derivada radial amb σ0,75 px; `m1_vores.py` ajusta directament aquest contorn. El detector del 50 % s’aplica a les altres vores. La diferència de radis inclou aquesta diferència de definició i no prova un error físic uniforme de 2 px:')
   after=after.replace('| silueta aparent de la font lunar (F4) | 453,5 | (−1,0; −0,6) | on s\'acaba la Lluna de veritat |','| silueta aparent de la font lunar (F4) | 453,5 | (−1,0; −0,6) | màxim de derivada òptica aparent; no contorn físic independent |')
  else:
   after=before+'''
## R03: contorn aparent, PSF i selecció temporal

F4 mesura el màxim de derivada radial, mentre altres vores de la taula
històrica M1 usen el 50 %. No convertir-ne la diferència en un canvi físic
uniforme de radi. B(D) es va calibrar respecte del model: si es canvia la
coordenada de distància, cal transportar o recalibrar també la resposta,
no substituir simplement l'argument de la mateixa corba.

Les PSF estel·lars existents són condicionals, distants o d'altres èpoques;
les ales B0 són heretades d'un ajust lunar. No constitueixen una mesura
independent local per als curts d'1/3200. Es conserven com a informació per
a models futurs, sense promoure una desconvolució ni repetir inversions
òptiques ja refusades.

El pilot de sis curts primerencs, comparat amb dinou de la mateixa exposició
i seixanta-un de mixtes, no resol totes les marques. A l'arc superior els
primers ja dominen; altres millores de contrast conviuen amb més variació
i jutges Brno mixtos. Canviar època també pot canviar exposicions i soroll:
fer servir un comparador de la mateixa exposició i publicar-ne el suport.
Evidència: `GEOMETRY_PSF_R03.json` i `early_epoch_R03/DECISION.json`.
'''
  path.write_text(after);changes.append({'path':str(path),'before':sha(out/(str(i)+'_'+path.name)),'after':sha(path)})
 assert targets[0].read_bytes()==targets[1].read_bytes();assert targets[2].read_bytes()==targets[3].read_bytes();prior=json.loads((O/'SKILL_R02_QA.json').read_text());prior.update(reference_codex_exact=True,lunar_reference_sha256=sha(targets[2]),historical_limb_reference_sha256=sha(targets[0]),historical_limb_reference_codex_exact=True,R03_status='bounded source/geometry/PSF diagnosis; no native candidate promoted',reference_changes=changes);save(O/'SKILL_R03_QA.json',prior)
 index=R/'IA/Skills/README.md';before=index.read_text();(out/'skill_index_before.md').write_text(before);index.write_text(before.replace('diagnosi R02.','diagnosi R03.').replace('SKILL_R02_QA.json','SKILL_R03_QA.json')+'\nR03 rectifica els detectors del contorn F4/M1, qualifica la PSF disponible i documenta el pilot d’època estreta rebutjat.\n')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ');p=Path('/Users/USUARI/.codex/memories/extensions/ad_hoc/notes')/(stamp+'-eclipse-v85-r03-geometry-response.md');p.write_text('''# Eclipse V85 R03 — actualització dins l'encàrrec autoritzat

project_id: Eclipse 2026
canonical_cwd: /Users/USUARI/Desktop/Eclipse 2026

Rectificació: F4 és màxim de derivada radial; M1 només aplica detector50% a les altres vores. No usar la diferència453,5/455,5 com un canvi uniforme del radi físic. No passar D_F4 directament a B_model sense transportar/recalibrar l'abscissa. Les PSF disponibles no identifiquen independentment la resposta local dels curts1/3200; ales B0 provenen d'ajust lunar. Inversions òptiques anteriors ja refusades.

PilotV85R03 early6/same19/mixed61, sense N reservat: les sis primerenques ja dominen l'arc superior. Més curts tardans no canvien aquell contrast. Altres marques canvien però apareixen regressions i Brno mixt; no font viable general deWOW. No s'ha incorporat cap candidat R03. V85 continuaR01 amb límits, no tot arreglat. Consultar GEOMETRY_PSF_R03.json, early_epoch_R03/DECISION.json i SKILL_R03_QA.json al paquet4-RESULTATS/v85_regeneracio_20260922.
''');save(out/'UPDATE_RECEIPT.json',{'changes':changes,'memory_note':str(p),'no_native_change':True});print('R03_EVIDENCE_AND_LESSONS_RECORDED')

if __name__=='__main__':guard();main()
