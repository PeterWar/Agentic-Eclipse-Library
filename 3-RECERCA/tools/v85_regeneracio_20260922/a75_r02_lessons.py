"""Authorized correction of skill guidance and append-only memory note."""
from a4_sources import *
import yaml

def main():
 out=O/'R02_lessons';rel=Path('corregeix-artefactes/references/lunar_boundary_and_display.md');p=R/'.claude/skills'/rel;g=Path('/Users/USUARI/.codex/skills')/rel
 assert p.read_bytes()==g.read_bytes();backup=out/'lunar_reference_before_identifiability.md';assert not backup.exists();backup.write_bytes(p.read_bytes());index=R/'IA/Skills/README.md';(out/'skill_index_before_R02.md').write_bytes(index.read_bytes())
 text=p.read_text()+'''
## Calibració existent i identificabilitat de la franja interior

Abans d'afegir una correcció temporal, seguir els numeradors: F2.2 ja aplica
guanys de coherència per fotograma; V36 incorpora offsets RGB i camps suaus
phi. Els residus temporals de R02 són posteriors a aquestes correccions.
No atribuir-los automàticament a transparència no calibrada.

La resposta B(D) s'ha de jutjar amb la població de fotogrames de cada punt,
també als veïns que usa el filtre. Un pes molt petit al centre d'una marca
no acota el pes al seu costat interior. A l'arc superior de V85, l'ablació
train mostra que B(D) canvia el signe del contrast normal, però el veí
interior no té cap observació train amb D>4. Això explica la sensibilitat;
no identifica la radiància correcta. No retirar B(D) ni ajustar-la per
aplanar la marca sense referència independent o model validat.

Una prova amb la font anterior a S4 ha de restaurar B3/B2 real, amb la
substracció estel·lar preservada i els suports auxiliars coherents. Posar
només la màscara B3 sobre D4 no elimina la radiància S4. Declarar els punts
que perden suport; que una marca deixi de ser mesurable no és recuperació
de corona. No aplicar una ampliació circular per ocultar-la.

Comparar la gravetat de les fallades, no només comptar-les. En el pilot de
moments quadràtics, 04 passa de 19 a 9 cel·les fora del llindar, però algunes
injeccions canvien de signe respecte de l'oracle. Els nulls polinòmics,
la bona condició numèrica i les millores exteriors de Brno no ho anul·len.
Aquest pilot no s'ha promogut. Els controls amb injecció oculta no mesuren
directament un percentatge de senyal observat perdut.

Evidències: `TEMPORAL_CALIBRATION_R02.json`, `bias_component_R02/RECEIPT.json`,
`fixed_pairs_R02/SUMMARY.json`, `MOMENT_R02_DECISION.json` i els rebuts de
cada domini dins del paquet V85. R02 continua en diagnosi; cap nova versió
PSB acceptada ni absència global d'artefactes acreditada per aquestes proves.
'''
 p.write_text(text);g.write_bytes(p.read_bytes());rows=[]
 for name in ['apilatge-imatges-eclipsi','postprocessat-corona','corregeix-artefactes']:
  q=R/'.claude/skills'/name/'SKILL.md';body=q.read_text();front=yaml.safe_load(body.split('---',2)[1]);assert isinstance(front,dict) and front.get('name');row={'name':name,'canonical':str(q.relative_to(R)),'sha256':sha(q),'yaml_valid':True}
  if name!='apilatge-imatges-eclipsi':row['codex_entrypoint_exact']=q.read_bytes()==(Path('/Users/USUARI/.codex/skills')/name/'SKILL.md').read_bytes();assert row['codex_entrypoint_exact']
  rows.append(row)
 save(O/'SKILL_R02_QA.json',{'skills':rows,'lunar_reference_sha256':sha(p),'reference_codex_exact':sha(p)==sha(g),'previous_delivery_receipt_retained':'SKILL_FINAL_QA.json','scope':'two entrypoints and one reference; no claim all assets synchronized','R02_status':'diagnostic ongoing, no new PSB promotion'})
 s=index.read_text().replace('Actualitzat el 22-09-2026 per V85.','Actualitzat el 22-09-2026 per V85, diagnosi R02.').replace('Rebut: `4-RESULTATS/v85_regeneracio_20260922/SKILL_FINAL_QA.json`.','Rebut vigent de skills: `4-RESULTATS/v85_regeneracio_20260922/SKILL_R02_QA.json`. El rebut `SKILL_FINAL_QA.json` es conserva com a fotografia del lliurament R01.')
 s+='\nR02 rectifica la prescripció universal sobre el domini d’entrada, documenta la calibració temporal ja existent i separa sensibilitat a B(D) de radiància identificada. Els candidats físic, solar i de moments no s’han promogut. La prova pre-S4 continua pendent de judici.\n';index.write_text(s)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ');note=Path('/Users/USUARI/.codex/memories/extensions/ad_hoc/notes')/(stamp+'-eclipse-v85-r02-domain-correction.md');assert not note.exists();note.write_text('''# Eclipse V85 R02 — rectificació demanada dins l'actualització de memòria

project_id: Eclipse 2026
canonical_cwd: /Users/USUARI/Desktop/Eclipse 2026

Rectifica la nota 2026-09-22T02-20-45Z-eclipse-v85-lunar-boundary.md: l'exclusió de tota la foto lunar és obligatòria a la sortida dels filtres autoritzats, però no és una regla universal per al domini d'entrada. Cal distingir suport físic, validesa coronal i màscara de presentació. Tampoc conservar tot suport històric prova que sigui net. No expandir radis per ocultar la franja.

V85 R01 continua sent una millora amb límits, no tot arreglat. En R02 no s'han promogut els candidats de domini físic, solar ni moments quadràtics: reduir el recompte de fallades pot amagar regressions de severitat. Brno exterior no avala la franja interior; l'oracle amb injecció oculta també prova una hipòtesi de continuació.

F2.2 i V36 ja calibren guanys temporals, offsets RGB i camps suaus: no afegir una correcció de transparència per suposar que falta. Al veí interior de l'arc superior no hi ha observació train D>4; B(D) explica la sensibilitat del contrast però no identifica la radiància correcta. Cap reajustament per aplanar la marca. Una prova anterior a S4 ha de restaurar la radiància B3/B2, no només canviar la màscara, i declarar la pèrdua de suport.

Autoritat viva: 4-RESULTATS/v85_regeneracio_20260922/WORKING_STATE_R02.json i rebuts de cada candidat; SKILL_R02_QA.json. Diagnosi R02 encara activa, PSB lliurada R01 intacta en aquest checkpoint. Consultar l'estat viu abans de reprendre o donar la feina per acabada.
''')
 save(out/'IDENTIFIABILITY_UPDATE.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_sha256':sha(p),'memory_note':str(note),'skill_receipt':'SKILL_R02_QA.json','no_PSB_change':True});print('R02_LESSONS_CORRECTED',note,flush=True)

if __name__=='__main__':guard();main()
