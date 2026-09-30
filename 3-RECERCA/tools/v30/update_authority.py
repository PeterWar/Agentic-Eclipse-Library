"""Reconcile live entrypoints after proven V30 delivery; retain dated snapshots."""
from pathlib import Path
import json,hashlib,shutil,datetime
D=Path(__file__).parent;ROOT=D.parents[2];IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
CT=IA.parent/'Projecte photoshop/1-Unint Capes/Capes Totals'
HAND=ROOT/'.coordination/HANDOFF_2026-09-05_V30.md'
changes=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,text):
    old=None
    if p.exists():
        old=sha(p);rel=('IA/'+str(p.relative_to(IA))) if p.is_relative_to(IA) else str(p.relative_to(ROOT))
        b=D/'docs_before'/rel;b.parent.mkdir(parents=True,exist_ok=True)
        assert not b.exists(),f'already reconciled: {b}';shutil.copy2(p,b)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    changes.append({'path':str(p),'before':old,'after':sha(p)})
def main():
    delivery=json.loads((D/'delivery_manifest.json').read_text());assert delivery['PASS']
    h=delivery['sha256'];size=delivery['bytes'];final=CT/'V30.psb';assert final.exists()
    core=f'''V30.psb és el lliurable visual actual, creat el 05-09-2026: 10551 × 7506,
RGB16, 30 capes, {size:,} bytes. SHA-256 `{h}`.
Ruta: `{final}`.

Conserva les 25 capes de V29 corregida: píxels, alfa i màscares idèntics.
01 ACHF fi 2–32 i 02 Passa-alt24 acceptades per Pere continuen visibles.
La 03 V29 original es conserva oculta; la 03 V30 visible regularitza radialment
l'operador azimutal amb sigma4 px. 07 sigma8 és una alternativa més suau,
oculta. 04 micro1–16, 05 fi2–48 i 06 estructura4–64 són alternatives ocultes
del01; activar-ne una substituint el pare evita sumar contrast involuntari.

Minicercles suavitzats, no eliminació total certificada: RMS radial4–32 px
de quatre zones a0,476–0,550 de V29 amb03r4. La resposta injectada relativa
és0,967–1,011 a longituds96/160/256 px; r8 atenua96px a0,873–0,891 i ho
declara. No hi ha tall circular nou ni canvi de llenç/FOV. H1 i geometria
passen; avisos H1b declarats. Reobertura de canals, recomposició i Photoshop
real comprovats al rebut. El judici estètic final de Pere continua obert.

Represa: `{HAND}`; explicació `research/137_V30_minicercles_i_variants.md`,
auditoria `research/138_V30_auditoria_coherencia.md`, manifest
`research/tools/v30/delivery_manifest.json`. Les fotos Brno són jutges, mai
fonts de píxels. La comparació exterior >5R no valida el gra ni tota la corona.
'''
    hand=f'''# Handoff vigent — V30 — 05-09-2026

{core}
## Què no s'ha de desfer

- Codi canònic a Downloads sense Git des del02-09. Un sol escriptor via
  `.coordination/claim.lock/owner.json`; l'estat viu del lock mana.
- V29 corregida immutable, SHA67169f0345c8abdf3fb9c3fd940d5b9f13d260864954d776c5d9277e15630676.
- Ni màscares circulars de marques ni els fades/inpainting dels pilots
  V25–V28 s'hereten com a correccions vigents. La màscara lunar temporal
  conserva les observacions vàlides; disc i earthshine continuen ancorats a C2.
- `etapa6_compara_brno.py` històric té fonts fixes V27; una etiqueta V30
  no el converteix en una comparació V30. Usa `v30/compare_brno.py` amb fonts
  reals i hashes. No hi ha afirmació de superioritat V30 a tot radi.
- Skills locals i Codex sincronitzades. Llegir la referència nova
  `corregeix-artefactes/references/miniarcs_i_anisotropia.md` abans d'un
  altre filtre angular. H1 verd no exclou soroll convertit en arcs.

## Reconstrucció

Intèrpret verificat: `/Users/USUARI/.venvs/eines-ia-py312/bin/python`;
`PYTHONDONTWRITEBYTECODE=1`. La cadena RAW és `eclipse_determinista/cadena.py`;
V30 és una branca manifestada posterior, no un nou run RAW.

1. Verificar `v30/cau/input_manifest.json` i dependencies del manifest.
2. Fonts V29 a `v29/cau_final` i radiància corregida a `v29_c03_fix`
   (research/134 i136): no sobreescriure aquests caus ni runs019/016.
3. `angular_pilots.py`, `fine_variants.py`, `inject_angular.py`,
   `build_previews.py`, `compare_brno.py`; inspeccionar rebuts i vistes.
4. `package_v30.py`, `verify_v30.py`, `photoshop_gate.py` en destinació NOVA.
   El paquet refusa sobreescriure V30 existent. Per repetir, copiar scripts
   a una branca nova i declarar les noves destinacions abans d'executar.
5. Publicació no-clobber després de les portes; manifest de codi/inputs/output.

Els experiments d'ablació H1 i sigma2 no són lliurables. Les alternatives
ocultes no demostren nova resolució; a l'exterior poden reforçar textura
no corroborada. La forma dels kernels és un paràmetre, no una banda FFT pura.

## Deutes separats

El PSB és una fotografia editable, no un màster fotomètric lineal. Temps
EXIF nominals, darks sense selecció tèrmica i absència de variància per canal
de la cadena continuen com a deutes històrics declarats. No s'han recalibrat
RAW en aquesta ronda. Un FOV més gran és un projecte futur que requereix la
decisió de Pere; no és un bloqueig del llenç V30 ja demanat.

El lliurament no ordena feina posterior ni missió de càmeres. Per reprendre,
llegir AGENTS, CLAUDE, IA i l'última entrada dels diaris; adquirir un nou claim
quan l'actual indiqui RELEASED. No editar CLAUDE_STATUS des de Codex.
'''
    write(HAND,hand)
    p=ROOT/'AGENTS.md';t=p.read_text()
    t=t.replace('3. Executa `git status --short`. Tot canvi preexistent és de Pere: no facis\n   `reset`, `checkout`, `clean`, `stash` ni sobreescriptures globals.','3. No executis Git: el projecte no en té des del02-09-2026. Preserva tots\n   els fitxers preexistents i evita sobreescriptures globals.')
    t=t.replace('és l’únic\n   worktree canònic.','és l’única\n   arrel canònica de codi.').replace('l\'únic worktree Git canònic','l\'única arrel canònica de codi (sense Git)')
    a=t.index('`.coordination/HANDOFF_2026-09-05_CODEX_V28.md`');b=t.index('En cas de contradicció',a)
    t=t[:a]+'''`.coordination/HANDOFF_2026-09-05_V30.md`** (V30: minicercles suavitzats,
filtres originals preservats, alternatives i portes declarades). V28 i el
seu handoff són antecedents històrics. El del22-08 descriu l'alternança
Codex/Claude i continua vigent en això. Punt de represa: bloc inicial de
`CLAUDE.md`, `research/137` i `research/138`.

'''+t[b:];write(p,t)
    p=ROOT/'CLAUDE.md';t=p.read_text();t=t.replace('Última actualització efectiva: 22 d’agost de 2026.','Última actualització efectiva: 05 de setembre de 2026 (V30).',1)
    t=t.replace('El worktree Git continua exclusivament a','El codi canònic, sense Git des del02-09-2026, continua exclusivament a',1)
    marker='## 1. Punt de represa\n';assert marker in t
    t=t.replace(marker,marker+'\n'+core+'''\nLes entrades següents conserven la història, també errors després corregits.
No són una cua vigent ni autoritzen retalls, inpainting, fades o reprendre un
pilot antic. La constatació sobre Git del02-09 queda substituïda per AGENTS.

### Història anterior a V30 (no instruccions de represa)
''',1);write(p,t)
    p=ROOT/'README.md';t=p.read_text();t=t.replace("[traspàs viu d'alternança Codex ↔ Claude](.coordination/HANDOFF_2026-08-22_ALTERNANCA_CODEX_CLAUDE.md)","[traspàs vigent V30](.coordination/HANDOFF_2026-09-05_V30.md)");write(p,t)
    p=ROOT/'research/README.md';t=p.read_text().replace('../.coordination/HANDOFF_2026-08-22_ALTERNANCA_CODEX_CLAUDE.md','../.coordination/HANDOFF_2026-09-05_V30.md',1)
    t=t.replace('## Estat operatiu actual\n','''## Estat operatiu actual

- `137_V30_minicercles_i_variants.md` — V30: reducció d'arcs de soroll a03, originals preservats i cinc capes noves; evidència i límits.
- `138_V30_auditoria_coherencia.md` — punts d'entrada reconciliats, snapshots i scripts històrics que no s'han d'usar com a vigents.
- `136_V29_capa03_corregida.md` — correcció radiomètrica dels pentàgons de03 dinsV29; és l'entrada immutable deV30.
- `135_V29_pentagonals.md` — diagnòstic anterior a la correcció136.
- `134_V29_detall_unio_temporal.md` — construcció deV29 i preservació de corona temporal.

## Antecedents històrics (les receptes superades no són instruccions)
''',1);write(p,t)
    write(IA/'README.md',f'''# IA — punt d'entrada viu — 05-09-2026

{core}
## Lectura obligatòria

AGENTS i CLAUDE de Downloads manen les normes i el lock. Per a imatges:
README (aquest), ESTAT_ACTUAL i MAPA_RUTES_I_OUTPUTS, en aquest ordre; després
ACTIVE.json, NORMES_I_AUTORITAT i Coordinació/HANDOFF_VIGENT.
DECISIONS i les auditories datades preserven decisions històriques; l'estat
vigent resol qualsevol recepta després superada. No reprenguis S6/Gemini com
la branca visual actual. Els snapshots anteriors són a
`{D/'docs_before/IA'}`.

Downloads conté el codi sense Git; Desktop Eclipse2026, els actius; Desktop
Eclipse determinista, entrades i runs immutables. El4TB és backup, no arrel
de treball. JPEG i previsualitzacions noves van a IA/output, amb subcarpeta.
''')
    write(IA/'ESTAT_ACTUAL.md',f'''# Estat actual — V30 — 05-09-2026

{core}
## Demostrat i límits

Vegeu el manifest de lliurament per portes sobre el fitxer real. El compost
actual conserva els originals acceptats. No s'han recalibrat RAW ni ampliat
FOV. Detall nou interior parcialment corroborat entre trens; el gra exterior
no queda certificat. El judici estètic final és de Pere. No s'ha eliminat
tot artefacte ni tot soroll.

## Represa

Qualsevol feina nova parteix del handoff vigent i d'un nou claim quan el
vigent estigui alliberat. La tasca visual d'agost PAUSED, S6_ACCEPTED, els
pilots de sostre i Gemini són història, amb rebuts preservats a docs_before;
els seus resultats i deutes científics no es reetiqueten com a validacions V30.
No hi ha ordre pendent d'executar càmeres, PTP o una missió.
''')
    p=IA/'MAPA_RUTES_I_OUTPUTS.md';old=p.read_text();write(p,f'''# Mapa vigent — V30 — 05-09-2026

| Funció | Ruta |
|---|---|
| Codi canònic sense Git | `{ROOT}` |
| Lliurable editable actual | `{final}` |
| Manifest i scripts V30 | `{D}` |
| Diagnòstic visible V30 | `{IA/'output/v30_20260905'}` |
| V29 immutable / fonts | `research/tools/v29/cau_final` |
| Radiància corregida03 V29 | `research/tools/v29_c03_fix` |
| RAW/runs immutables | `/Users/USUARI/Desktop/Eclipse determinista/0-ENTRADES` i `1-RUNS` |
| Handoff | `{HAND}` |

Els S6, pilots d'agost i autoritats descrits a continuació són HISTÒRICS.
Les rutes originals continuen útils com a procedència; cap etiqueta «actual»,
«acceptat» o «pausat» del mapa antic sobreescriu ACTIVE.json/V30.

## Mapa conservat del22–25 d'agost

'''+old)
    p=IA/'Coordinació/HANDOFF_VIGENT.md';write(p,f'''# Handoff vigent — V30 — 05-09-2026

Llegir el handoff formal: `{HAND}`.

{core}
El handoff anterior d'agost està preservat a
`{D/'docs_before/IA/Coordinació/HANDOFF_VIGENT.md'}`; no és la represa viva.
''')
    p=IA/'NORMES_I_AUTORITAT.md';t=p.read_text();start=t.index('## Ordre d\'autoritat');end=t.index('Un rebut històric',start)
    t=t[:start]+'''## Ordre d'autoritat

1. Instrucció vigent de Pere i normes de seguretat d'AGENTS a Downloads.
2. `.coordination/claim.lock/owner.json` per a l'únic escriptor.
3. Bloc inicial de CLAUDE, ACTIVE.json i handoff vigent per a l'estat.
4. Últimes entrades dels diaris propis; cada agent només edita el seu.
5. Índexs, decisions i documents datats com a evidència històrica.

'''+t[end:];t=t.replace('Última actualització: 22-08-2026.','Última actualització: 05-09-2026 (reconciliació V30).')
    t=t.replace('Downloads és l\'únic worktree Git canònic','Downloads és l\'única arrel canònica de codi, sense Git des del02-09,')
    t=t.replace('llegeix els fitxers obligatoris, executa\n  `git status --short` al worktree i preserva tots els canvis preexistents.','llegeix els fitxers obligatoris i preserva tots els canvis\n  preexistents. Git no existeix al projecte; no hi executis ordres Git.')
    t=t.replace('- No facis `reset`, `checkout`, `clean`, `stash`, commits massius ni\n  sobreescriptures globals.','- No facis sobreescriptures globals ni restauracions sense abast autoritzat.')
    t=t.replace('- Earthshine queda fora de l\'abast fins que Pere el reprengui explícitament.','- Earthshine i estrelles ja formen part del PSB V30 heretat; es preserven.\n  No es recalculen en una tasca limitada als filtres de corona.');write(p,t)
    p=IA/'ACTIVE.json';old=json.loads(p.read_text());paths=old['paths'].copy()
    histkeys=[k for k in paths if any(z in k for z in ('s6_authority','stable_manifest','ldic_preflight','ldic_report','ldic_handoff','cross_train_v2','gemini_'))]
    for k in histkeys:paths.pop(k)
    paths['current_technical_editable']=str(final);paths['current_delivery_manifest']=str(D/'delivery_manifest.json');paths['current_visual_output']=str(IA/'output/v30_20260905')
    active={'schema_version':4,'updated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'post-eclipse-V30-delivered-editable-photo','coordination_mode':old['coordination_mode'],'entrypoint':str(IA/'README.md'),'asset_root':old['asset_root'],'code_root':str(ROOT),'code_worktree':str(ROOT),'git_present':False,'formal_worktree_handoff':str(HAND),'handoff':str(IA/'Coordinació/HANDOFF_VIGENT.md'),'status':str(IA/'ESTAT_ACTUAL.md'),'path_map':str(IA/'MAPA_RUTES_I_OUTPUTS.md'),'paths':paths,'current_product':{**{k:delivery[k] for k in ('path','sha256','bytes','size','depth','layers','published_utc','PASS','source','verification','photoshop','visual_acceptance','preservation','limitations')},'manifest':str(D/'delivery_manifest.json')},'processing_authority':{'type':'manifested-photo-derivative-not-linear-master','runs':'Vixen019/Sony016, immutable; exact dependencies in manifest','source':'V29 corrected03, immutable','fov_status':'same10551x7506; largerfutureFOVrequiresdecision','raw_calibration_reexecuted':False},'visual_task':{'status':'DELIVERED_PENDING_PERE_VISUAL_JUDGEMENT','target':str(final),'filters01_02':'preserved exactly','old03':'preserved hidden','next_action':'No automatic next task; new claim for follow-up'},'history':{'previous_active_snapshot':str(D/'docs_before/IA/ACTIVE.json'),'previous_active_sha256':sha(p),'meaning':'Entire former state retained as dated evidence; S6/pilots/Gemini/PAUSED no longer current routing'},'jpeg_output':old['jpeg_output']}
    write(p,json.dumps(active,ensure_ascii=False,indent=2)+'\n')
    p=ROOT/'.coordination/CODEX_STATUS.md';t=p.read_text();write(p,'> Diari append-only: llegiu l’ÚLTIMA entrada per a l’estat; la capçalera antiga no és vigent. Represa: HANDOFF_2026-09-05_V30.md. El lock viu mana.\n\n'+t)
    (D/'authority_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
    print('Reconciled',len(changes),'entrypoints; snapshots retained')
if __name__=='__main__':main()
