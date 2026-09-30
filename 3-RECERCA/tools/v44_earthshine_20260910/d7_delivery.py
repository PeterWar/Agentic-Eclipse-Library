"""Receipts and narrow authority updates after C5 publication. No Photoshop calls.

prepare writes only inside the canonical code tree. desktop installs the already
prepared documents after checking their original hashes. local installs local
authority pointers. All modes require the V44 writer claim and published checks.
"""
from comu44 import *
import datetime, shutil, os
from c5_psb import SOURCE, CI, FINAL

REPORT=ROOT/'research/162_EARTHSHINE_V44_CONTORN_VIXEN_DETALL_I_REGISTRE_20260910.md'
HANDOFF=ROOT/'.coordination/HANDOFF_2026-09-10_CODEX_EARTHSHINE_V44.md'
IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
DOCS=HERE44/'authority_prepared';BEFORE=HERE44/'docs_before'
MANIFEST=HERE44/'delivery_manifest.json'

def info(p):
    return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)

def prepare_delivery():
    claim();pub=json.loads((REB44/'C5_publish.json').read_text());check=json.loads((REB44/'C5_photoshop_readback.json').read_text())
    gate=json.loads((REB44/'C5_photoshop_gate.json').read_text());ver=json.loads((REB44/'C5_verify.json').read_text())
    assert ver['PASS'] and check['PASS'] and sha(FINAL)==pub['sha256']==gate['sha256']==ver['sha256']==check['source_sha256']
    a0=json.loads((REB44/'A0_inventari_psb.json').read_text())
    sources=[]
    for name in ['Earthshine_V43.psb','Earthshine_V43_detall.psb']:
        p=CI/name;assert sha(p)==a0[name]['sha256'];sources.append(info(p))
    assert not MANIFEST.exists();DOCS.mkdir(exist_ok=True);BEFORE.mkdir(exist_ok=True)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt=f'''# Earthshine V44 — rebut i guia de capes

Lliurada el {now}. Nou PSB verificat amb Photoshop real.

- Fitxer: `{FINAL}`.
- SHA-256: `{pub['sha256']}`.
- {pub['bytes']:,} bytes; 10551 × 7506; RGB16; 18 capes.
- Canals comprimits de les quinze capes de la V43 anotada conservats byte a byte;
  visibilitats adaptades per mostrar la V44.
- Capa visible: `Earthshine V44 · natural 12 % · contorn Vixen · aportació`.
- Alternativa oculta: `Earthshine V44 · relleu 24 % · alternativa (activar sola)`.
- HDR mesurat ocult per a diagnòstic. La capa antiga amb marques queda oculta.

Per comparar les dues intensitats, apaga la natural abans d'encendre la de
24 %. Mantén `09 1/60 x2` visible: aquestes dues capes afegeixen earthshine
sobre aquesta base. No són un disc autònom per copiar damunt de qualsevol
altra corona; una altra base necessita verificar-ne la unió de pantalla.
L'opacitat de l'aportació permet abaixar la llum afegida.

S'han reapilat 88 entrades amb rellotge comú i registre lunar; 14 tessel·les
regenerades des del RAW, la resta reutilitzades amb una sola interpolació.
El contorn es mesura en 17 exposicions curtes Vixen. El detall exterior
corroborat s'estén fins a 0,96 del radi lunar; l'última franja continua
limitada pel senyal. Sony B només aporta detall interior fora del ghost.
Ni el camp ni l'escala lunar han canviat. LROC només és un jutge extern.

Porta Photoshop: obertura, 18 capes, recomposició forçada i TIFF de readback.
Desviació màxima respecte dels píxels previstos a la ROI lunar: {check['max_abs_DN16']} DN16;
a tots els píxels visibles del llenç: {check['full_visible_canvas']['max_abs_DN16']} DN16
(tolerància 6). Fonts V43 i V43 anotada revalidades intactes.
Els 19.112 píxels protegits pel criteri fotomètric, incloses perles brillants,
no canvien; queden transicions locals febles i no
s'afirma recuperació de tot el relleu immediatament al limbe.

Informe complet: `{REPORT}`.
Manifest: `{MANIFEST}`.
Vistes: `{IA/'output/v44_earthshine_20260910/vistes'}`.
Les Capes Totals continuen a V42. Judici visual de Pere obert.
'''
    (DOCS/'Earthshine_V44_REBUT.md').write_text(receipt)
    handoff=f'''# Represa — Earthshine V44 — Codex — 10-09-2026

{receipt}

## Autoritat i continuació

Encàrrec de Pere: millorar l'earthshine de la V43 amb les marques verdes/cian.
La ronda entrega V44; no ordena una nova ronda automàtica ni passa feina a
Claude sense petició. Abans de qualsevol mutació, segueix AGENTS.md, llegeix
CLAUDE.md i el lock viu. Només CODEX_STATUS.md és el diari d'aquesta ronda.

Represa tècnica: `research/tools/v44_earthshine_20260910/`,
`output/v44_earthshine_20260910/4-rebuts/`, research/162.
El manifest conserva hashes de fonts, scripts i rebuts; els caus V42/V43
continuen sent dependències. Les temptatives F3 lineal i F4 amb llindar de
pes no són la recepta final. Porta GUI inicial rebutjada; s'ha reprès
només després de l'autorització explícita de Pere.

Límits: no relleu corroborat a 0,96–0,995 R; detall exterior direccional;
incertesa de registre dels febles d'1–5 px per sectors; no deconvolució del
moviment intraexposició; resposta angular de pantalla empírica, no PSF
física identificada; transicions locals febles residuals. No inserir B al
limbe ni dades LROC al producte. No engrandir el disc a ull.

L'alliberament efectiu del claim i els processos es comprova a l'última
entrada de CODEX_STATUS.md i a l'absència del lock, no en aquesta plantilla.
'''
    assert not HANDOFF.exists();HANDOFF.write_text(handoff)
    pointer=f'''**10-09-2026 — EARTHSHINE V44 LLIURADA.** Represa: `{HANDOFF}`;
informe `research/162_EARTHSHINE_V44_CONTORN_VIXEN_DETALL_I_REGISTRE_20260910.md`.
`Capes interiors/Earthshine_V44.psb`, SHA `{pub['sha256']}`, 18 capes,
mateix 10551 × 7506 RGB16. Originals de Pere byte a byte; contorn Vixen,
rellotge comú, reapilat de 88 entrades, detall corroborat fins a 0,96 R,
perles protegides. Natural 12 % visible; 24 % i HDR ocults. Photoshop i
readback PASS. Detall de l'última franja no corroborat; resposta de pantalla
empírica; judici de Pere obert. Capes Totals continua V42.
'''
    plan=[]
    def stage(path,name,transform,where):
        old=path.read_text();(BEFORE/name).write_text(old);new=transform(old)
        assert new!=old;(DOCS/name).write_text(new)
        plan.append(dict(path=str(path),prepared=name,before_sha256=sha(path),after_sha256=sha(DOCS/name),where=where))
    stage(ROOT/'CLAUDE.md','CLAUDE.md',lambda s:s.replace('Última actualització efectiva: 07 de setembre de 2026 (handoff Codex → Claude, revisió de marques V31).','Última actualització efectiva: 10 de setembre de 2026 (Earthshine V44 de Codex).',1).replace('## 1. Punt de represa\n','## 1. Punt de represa\n\n'+pointer,1),'local')
    stage(ROOT/'AGENTS.md','AGENTS.md',lambda s:s.replace('## Autoritat viva i escriptura única\n','## Autoritat viva i escriptura única\n\n'+pointer+'\nEls paràgrafs següents conserven la successió anterior de handoffs.\n',1),'local')
    stage(ROOT/'research/README.md','research_README.md',lambda s:'- [162 — Earthshine V44: contorn Vixen, reapilat i registre lunar, detall exterior corroborat i preservació de les perles](162_EARTHSHINE_V44_CONTORN_VIXEN_DETALL_I_REGISTRE_20260910.md)\n'+s,'local')
    stage(IA/'README.md','IA_README.md',lambda s:pointer+'\n---\n\nHistòria conservada; la capçalera anterior queda a sota.\n\n'+s,'desktop')
    stage(IA/'ESTAT_ACTUAL.md','IA_ESTAT_ACTUAL.md',lambda s:pointer+'\n---\n\nHistòria conservada; la capçalera anterior queda a sota.\n\n'+s,'desktop')
    stage(IA/'MAPA_RUTES_I_OUTPUTS.md','IA_MAPA_RUTES_I_OUTPUTS.md',lambda s:pointer+'\nVistes i rebuts V44: `IA/output/v44_earthshine_20260910/`.\n\n---\n\n'+s,'desktop')
    stage(IA/'Coordinació/HANDOFF_VIGENT.md','IA_HANDOFF_VIGENT.md',lambda s:pointer+'\n---\n\nHandoff històric conservat (no vigent):\n\n'+s,'desktop')
    def active(s):
        d=json.loads(s);d['updated']=now;d['phase']='post-eclipse-earthshine-V44-delivered'
        d['formal_worktree_handoff']=str(HANDOFF)
        d['paths']['current_earthshine_editable']=str(FINAL)
        d['paths']['current_earthshine_manifest']=str(MANIFEST)
        d['paths']['current_earthshine_visual_output']=str(IA/'output/v44_earthshine_20260910')
        d['current_earthshine_product']=dict(path=str(FINAL),sha256=pub['sha256'],bytes=pub['bytes'],size=[W,H],depth=16,layers=18,PASS=True,PASS_scope='original compressed channels exact; new uint16 channels exact; independent reader; actual Photoshop recomposition and TIFF pixel readback; scientific and visual limits in research/162',artifact_free=False,source=str(SOURCE),report=str(REPORT),manifest=str(MANIFEST),limitations=['outer0.96-0.995R not corroborated','outer detail directional','display-response model is empirical','visual judgement by Pere pending'])
        d['earthshine_task']=dict(status='DELIVERED_V44_PENDING_PERE_VISUAL_JUDGEMENT',target=str(FINAL),next_action='Pere compares natural12 and relief24 alternatives; integration into Capes Totals needs a matched display join')
        return json.dumps(d,ensure_ascii=False,indent=2)+'\n'
    stage(IA/'ACTIVE.json','IA_ACTIVE.json',active,'desktop')
    savejson(DOCS/'install_plan.json',plan)
    files=[*HERE44.glob('*.py'),*REB44.glob('*.json'),REPORT,HANDOFF,DOCS/'Earthshine_V44_REBUT.md']
    manifest=dict(created_utc=now,product=pub,source_files_unchanged=sources,photoshop_readback=check,files=[info(p) for p in files],scope='this execution, not a second full reproduction; inherited dependencies recorded in imports and B2_inputs.json')
    savejson(MANIFEST,manifest)
    print('PREPARED',MANIFEST,flush=True)

def install(where):
    claim();pub=json.loads((REB44/'C5_publish.json').read_text());assert FINAL.exists() and sha(FINAL)==pub['sha256']
    rows=json.loads((DOCS/'install_plan.json').read_text());selected=[r for r in rows if r['where']==where]
    for r in selected:
        assert sha(Path(r['path']))==r['before_sha256'],r['path']
        assert sha(DOCS/r['prepared'])==r['after_sha256']
    if where=='desktop':
        dest=IA/'output/v44_earthshine_20260910';assert not dest.exists()
        dest.mkdir();shutil.copytree(VIS44,dest/'vistes');shutil.copytree(REB44,dest/'4-rebuts')
        shutil.copy2(REPORT,dest/REPORT.name);shutil.copy2(MANIFEST,dest/MANIFEST.name)
        for p in [CI/'Earthshine_V44_REBUT.md',dest/'Earthshine_V44_REBUT.md']:
            with open(p,'xb') as f:f.write((DOCS/'Earthshine_V44_REBUT.md').read_bytes())
    for r in selected:
        p=Path(r['path']);p.write_bytes((DOCS/r['prepared']).read_bytes());assert sha(p)==r['after_sha256']
    savejson(REB44/f'D7_{where}_installed.json',dict(installed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=selected))
    print('INSTALLED',where,len(selected),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare_delivery()
    else:install(sys.argv[1])
