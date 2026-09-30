"""Update current routing only, with full snapshots of every prior document."""
from pathlib import Path
import json,hashlib,shutil,datetime
D=Path(__file__).parent;ROOT=D.parents[2];IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');HAND=ROOT/'.coordination/HANDOFF_2026-09-05_V31.md';changes=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,t):
    before=None
    if p.exists():
        before=sha(p);rel='IA/'+str(p.relative_to(IA)) if p.is_relative_to(IA) else str(p.relative_to(ROOT));b=D/'docs_before'/rel
        b.parent.mkdir(parents=True,exist_ok=True);assert not b.exists();shutil.copy2(p,b)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t);changes.append({'path':str(p),'before':before,'after':sha(p)})
def main():
    m=json.loads((D/'delivery_manifest.json').read_text());assert m['PASS'];final=Path(m['path']);assert final.exists()
    core=f'''V31 és el lliurable editable actual: `{final}`.
10551 × 7506, RGB16, 30 capes; {m['bytes']:,} bytes.
SHA-256 `{m['sha256']}`.

Pere ha precisat que veu els minicercles només als filtres NO azimutals.
V31 suavitza les capes 01, 02, 05 i 06 amb una gaussiana cartesiana de sigma
3 px, i la 04 amb sigma 1,5 px. Les altres 25 capes, incloses les azimutals
03 i 07, són íntegrament idèntiques. Les 30 màscares, alfa, opacitats,
visibilitats i ordre es preserven. V30 queda immutable. No hi ha retall
circular, canvi de FOV ni nou perfil radial.

H1 passa als cinc filtres, inclòs el limbe parcial; H1b conserva avisos a 01,
04 i 05. El suavitzat també atenua detall real petit: sigma 3 conserva
aproximadament un 74–75% del coherent a 16–32 px i un 92% a 32–64 px en
quatre finestres interiors.
No s'afirma eliminació completa de minicercles ni validació del gra exterior.
Reobertura de canals, recomposició amb error màxim d'1 DN16 i obertura de les
30 capes a Photoshop comprovades. L'acceptació visual final de Pere queda pendent.

Handoff: `{HAND}`. Explicació: `research/139_V31_mes_suavitzat.md`.
Manifest: `{D/'delivery_manifest.json'}`. Vistes: `{IA/'output/v31_20260905'}`.
'''
    hand='''# Handoff vigent — V31 — 05-09-2026

'''+core+'''
## Observació de Pere que mana

«els minicercles els veig només en els filtres que NO son azimutals».
No activar 07 ni tornar a corregir 03 com a resposta a aquesta petició.
La pintura blava en una capa no identifica l'origen del defecte en un compost.
La diagnosi d'anisotropia de V30 és una prova del seu operador, no la
identificació dels minicercles assenyalats posteriorment per Pere.

## Represa i reproducció

Downloads és el codi canònic, senseGit. LlegirAGENTS, CLAUDE iIA; un sol
escriptor via claim.lock. Aquest lliurament no ordena feina addicional.
V30immutable SHA0d1f23fe5c56acf60bb35d3e24acea02fffaaf333d04d7a3aa17e0aac4f3f8c0.
Fonts congelades a `v31/cau/input_V30.psb`; suport físic originalV29.
Intèrpret `/Users/USUARI/.venvs/eines-ia-py312/bin/python`,
`PYTHONDONTWRITEBYTECODE=1`. Veure scripts i ordre a research/139.
Els paquets refusen sobreescriure fitxers existents; reconstruir en una nova
destinació declarada. No recalibrarRAW, substituir màscares ni recentrarH1
per repetir aquesta correcció. Rebut d'H1rebutjat de04sigma3 conservat.

## Límits i estat heretat

ElPSB és una fotografia editable, no un màster fotomètric. Brno jutja els
merged reals; el camp>5R continua sense corroboració suficient. No es retalla
dada per fer passar un jutge. Darks,EXIF,variància i calibratge conserven els
deutes anteriors. ElsRAW i runs019/016 continuen immutables. Earthshine,
estrelles i reflex s'hereten. No hi ha ordre de tocar càmeres oPTP.

04/05/06 continuen ocultes com a alternatives de01: comparar substituint
la capa pare, a la mateixa opacitat. DiariCodexappend-only; no editarCLAUDE_STATUS.
El lock viu mana sobre qualsevol estat històric. HandoffV30 preservat.
'''
    write(HAND,hand)
    p=ROOT/'AGENTS.md';t=p.read_text();a=t.index('`.coordination/HANDOFF_2026-09-05_V30.md`');b=t.index('En cas de contradicció',a)
    t=t[:a]+'''`.coordination/HANDOFF_2026-09-05_V31.md`** (V31: suavitzat dels filtres
NO azimutals01/02/04/05/06; azimutals i màscares intactes; portes i cost de
detall declarats). Els handoffs anteriors són història; el del22-08 conserva
la norma d'alternançaCodex/Claude. Represa: bloc inicial deCLAUDE i research/139.

'''+t[b:];write(p,t)
    p=ROOT/'CLAUDE.md';t=p.read_text().replace('05 de setembre de 2026 (V30)','05 de setembre de 2026 (V31)',1);marker='## 1. Punt de represa\n';assert marker in t
    write(p,t.replace(marker,marker+'\n'+core+'\n### Història anterior a V31 (no instruccions de represa)\n',1))
    p=ROOT/'README.md';t=p.read_text().replace('[traspàs vigent V30](.coordination/HANDOFF_2026-09-05_V30.md)','[traspàs vigent V31](.coordination/HANDOFF_2026-09-05_V31.md)');write(p,t)
    p=ROOT/'research/README.md';t=p.read_text().replace('../.coordination/HANDOFF_2026-09-05_V30.md','../.coordination/HANDOFF_2026-09-05_V31.md',1)
    write(p,t.replace('## Estat operatiu actual\n','## Estat operatiu actual\n\n- `139_V31_mes_suavitzat.md` — actual: minicercles en filtres NO azimutals segonsPere; cinc suavitzats, azimutals intactes i cost de detall declarat.\n\n### Antecedents V30 i V29\n',1))
    write(IA/'README.md','# IA — punt d’entrada viu — V31\n\n'+core+'\nLlegir README, ESTAT_ACTUAL i MAPA_RUTES_I_OUTPUTS en aquest ordre; després ACTIVE.json i el handoff. AGENTS/CLAUDE i el lock de Downloads manen les normes. Snapshots V30 a `'+str(D/'docs_before/IA')+'`.\n')
    write(IA/'ESTAT_ACTUAL.md','# Estat actual — V31\n\n'+core+'\nLa petició de suavitzar els no azimutals està executada; no hi ha nova missió ni tasca automàtica. Els experiments sigma5 i04sigma3 no són lliurables.\n')
    p=IA/'MAPA_RUTES_I_OUTPUTS.md';t=p.read_text().replace('# Mapa vigent — V30','# Mapa vigent — V31',1)
    for a,b in [('Capes Totals/V30.psb','Capes Totals/V31.psb'),('| Manifest i scripts V30 |','| Manifest i scripts V31 |'),('research/tools/v30`','research/tools/v31`'),('| Diagnòstic visible V30 |','| Diagnòstic visible V31 |'),('output/v30_20260905','output/v31_20260905'),('HANDOFF_2026-09-05_V30.md','HANDOFF_2026-09-05_V31.md'),('ACTIVE.json/V30','ACTIVE.json/V31')]:t=t.replace(a,b,1)
    write(p,t);write(IA/'Coordinació/HANDOFF_VIGENT.md','# Handoff vigent — V31\n\n'+core)
    p=IA/'ACTIVE.json';a=json.loads(p.read_text());prev=sha(p);a['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();a['phase']='post-eclipse-V31-delivered-editable-photo';a['formal_worktree_handoff']=str(HAND)
    a['paths'].update(current_technical_editable=str(final),current_delivery_manifest=str(D/'delivery_manifest.json'),current_visual_output=str(IA/'output/v31_20260905'))
    a['current_product']={k:m[k] for k in ('path','sha256','bytes','size','depth','layers','published_utc','PASS','source','verification','photoshop','visual_acceptance','preservation','limitations')};a['current_product']['manifest']=str(D/'delivery_manifest.json')
    a['processing_authority']['source']='V30 frozen PSB; only non-azimuthal RGB smoothed, original physical support'
    a['visual_task']={'status':'DELIVERED_PENDING_PERE_VISUAL_JUDGEMENT','target':str(final),'filters01_02_04_05_06':'Cartesian Gaussian; sigma3 except04sigma1.5','azimuthal03_07':'completely unchanged fromV30','next_action':'No automatic task; new claim for follow-up'}
    a['history']={'previous_active_snapshot':str(D/'docs_before/IA/ACTIVE.json'),'previous_active_sha256':prev,'meaning':'V30 preserved as historical evidence; Pere corrected artifact attribution to non-azimuthal layers'}
    write(p,json.dumps(a,ensure_ascii=False,indent=2)+'\n');(D/'authority_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write('\n## '+a['updated']+' — V31 DELIVERED\n\n'+core+'\nClaim held until final checks.\n')
    print('V31 routing updated; snapshots retained',len(changes))
if __name__=='__main__':main()
