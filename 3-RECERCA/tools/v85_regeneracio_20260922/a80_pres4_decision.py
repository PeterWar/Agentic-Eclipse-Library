"""Persist the negative pre-S4 result; keep native delivery unchanged."""
from a4_sources import *

def main():
 loss=json.loads((O/'marks246_pres4_R02/SUPPORT_LOSS.json').read_text());inner=json.loads((O/'inner_brno_pres4_R02/QA.json').read_text());brno=json.loads((O/'BRNO_PRES4_R02_QA.json').read_text());row=next(r for r in loss['coverage'] if r['component']==1 and r['rotation_deg']==0 and r['h_px']==4);assert (row['old_triplets'],row['common_triplets'])==(80,0)
 save(O/'domain_pres4_R02/CORRIGENDUM.json',{'support_mask_loss':2862,'effective_positive_finite_G_loss':2880,'additional_restored_nonpositive_G':18,'outside_changed_ROI_existing_invalid_G':8153,'input_unknown_expression':'~(support_v42 & ~photoMoon & isfinite(G_preS4) & (G_preS4>0)), restricted to lunar diagnostic box','generic_PHYSICAL_DOMAIN_superseded':True,'scope':'whole S4 package ablation; source radiance, source support, estimated radial fill profile and padding all change together; WOW coarse-plane global SD normalization can propagate effects','heldout_limit':'No individual reserved N read for fitting or diagnosis here; frozen production B2/B3 composites already include their historical frames. This is not a new blind heldout score.'})
 save(O/'PRES4_R02_DECISION.json',{
  'status':'NOT_PROMOTED','operators':['P04_WOW','P05_WOW_bilateral'],
  'construction_integrity':'PASS; exact S4 replacement locus restored from B3/B2, zero stellar overlap, original masks and side supports consistent',
  'reason':'Support loss removes all component1 h4 triplets; modest contrast decreases elsewhere coexist with worse independent bilateral morphology. This does not establish a corrected limb or retained detail.',
  'lost_support_mask':2862,'lost_effective_support':2880,'h4_triplets_old_common':[902,822],'component1_h4_old_common':[80,0],
  'common_domain_h4_rms_old_new':{'WOW':[.09108,.08926],'bilateral':[.06064,.05877]},
  'inner_reference233_nominal_delta_Pearson':{'WOW_comp2':.008553383259071401,'WOW_comp3':-.006395986569942946,'bilateral_comp2':-.03204204963673957,'bilateral_comp3':.0013933560359475905},
  'outer_reference233_inner1_15to1_35_band13to30_delta':{'WOW':.004110765177756548,'bilateral':-.0305203665047884},
  'limitations':['No external reference for component1','Removal of S4 cannot distinguish source-value, source-support, radial-profile and continuation effects alone','No new transfer controls were run after this negative actual-source/external-reference result','Native PSB not modified; source gaps have not been silently converted into black filter contribution'],
  'evidence':['marks246_pres4_R02/METRICS.json','marks246_pres4_R02/SUPPORT_LOSS.json','marks246_pres4_R02/WOW_comparison.png','inner_brno_pres4_R02/QA.json','BRNO_PRES4_R02_QA.json','bias_component_R02/DECOMPOSITION.json'],
  'PSB_unchanged':True,'all_artifacts_resolved':False})
 text='''# V85 R02 — diagnosi, sense nova promoció de PSB

La V85 lliurada continua sent R01, SHA d8005f05369eecbd71de6fa58a2e9044c7171a5a4fe9b55232040469a9a17458. R02 no ha modificat cap PSB. La petició de tot el llimb resolt continua oberta.

## Resultats negatius preservats

- Domini físic amb biharmònic lliure: sobreoscil·lacions; no promogut.
- Domini físic amb tensió: menys cel·les fallides però regressions de transferència i Brno; `PHYSICAL_T_R02_DECISION.json`.
- Exclusió del disc solar de radi congelat: regressions amples, no marges ajustats; `SOLAR_R02_DECISION.json`.
- Moments quadràtics: nulls i condició numèrica correctes, però inversions d'algunes injeccions i noves fallades; `MOMENT_R02_DECISION.json`.
- Font anterior a S4 per WOW: restaura B3/B2 real, però perd 2.880 píxels de domini efectiu i els 80 triplets h4 de l'arc superior. Les altres marques milloren modestament; bilateral empitjora Brno local i angular ample. `PRES4_R02_DECISION.json`.

## Mecanisme local i límit del coneixement

Al component1, el factor B(D) canvia el contrast normal del compost train: efecte logG centre/+4/−4 = +0,034045/+0,002491/+0,293000; delta del contrast −0,113701. Al costat interior domina curts/S4. El selector dur de D4 no és necessari perquè aparegui aquest efecte; el contrafactual train ja el mostra sense selector.

Cap cantonada bilineal del veí interior dels 80 triplets té una observació Vixen train amb D>4. Això no prova que B(D) sigui incorrecta ni autoritza ajustar-la per aplanar la marca. F2.2 i V36 ja inclouen coherència temporal, offsets i camps suaus; no falta simplement un guany de transparència. `bias_component_R02/DECOMPOSITION.json`, `TEMPORAL_CALIBRATION_R02.json`.

La cobertura geomètrica Brno dels triplets h4 és 0/44/0/428 per 230/231/232/233. A 233 només les components2/3 tenen prou cobertura; component1 no queda validada. La nova comparació interior fixa registre, normals, h4 i suavitzat nominal; exigeix tot el kernel dins suport comú. És morfologia parcial, no veritat fotomètrica ni PSF mesurada.

## Protecció i continuació

Original V84 i lliurament R01 protegits. No fer passar la desaparició de suport per recuperació de corona. No reobrir els numeradors reservats per ajustar un candidat. Skills i nota de memòria han rectificat la prescripció universal del domini d'entrada; rebut viu `SKILL_R02_QA.json`, rebut R01 preservat.

Resta una comprovació geomètrica acotada: si Sony ofereix una observació independent neta del veí interior del component1. Només després d'això es pot formular amb precisió què falta per validar-ne la radiància. Estat viu `WORKING_STATE_R02.json`.
'''
 (O/'R02_DIAGNOSTIC_STATE.md').write_text(text)
 state=json.loads((O/'WORKING_STATE_R02.json').read_text());state.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='ACTIVE_LAST_INDEPENDENT_SUPPORT_AUDIT_NO_PSB_CHANGE',active='Read-only Sony support check at component1; independent a79 QA review',next=['assess any independent clean support route','checkpoint full negative evidence and native delivery integrity'],goal_complete=False);state['completed']+=['preS4 source/WOW/marks/outerBrno/innerBrno','root B(D) decomposition reproduced','skill index/consumer copy/memory correction'];state['not_promoted']+=['preS4 WOW'];save(O/'WORKING_STATE_R02.json',state)
 index=R/'IA/Skills/README.md';s=index.read_text().replace('La prova pre-S4 continua pendent de judici.','La prova pre-S4 tampoc no s’ha promogut; pèrdua de suport i jutges externs mixtos.');index.write_text(s)
 print('PRES4_NEGATIVE_RECORDED')

if __name__=='__main__':guard();main()
