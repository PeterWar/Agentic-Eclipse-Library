from pathlib import Path
import json,hashlib,datetime,os
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v57_integracio_20260913';T=R/'research/tools/v57_integracio_20260913';IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_CAPES_TOTALS_V57_20260913'
pub=json.loads((O/'E0_publish.json').read_text());qa=json.loads((O/'D2_final_QA.json').read_text());choice=json.loads((O/'C3_final_choice.json').read_text());opened=(O/'E1_open_final.txt').read_text().strip();assert 'V57.psb | 35 layers | saved=' in opened
now=datetime.datetime.now(datetime.timezone.utc).isoformat();handoff=R/'.coordination/HANDOFF_2026-09-13_CODEX_CAPES_TOTALS_V57.md';report=O/'RESULTAT.md';manifest=T/'delivery_manifest.json'
sources=json.loads((O/'A0_sources.json').read_text())
body=f'''# Capes Totals V57 · integració de V42 i Earthshine V56

Pere demana muntar a Photoshop una nova versió general amb l'earthshine millorat i totes les capes de l'últim projecte general. Lliurada **V57.psb**, oberta i activa a Photoshop, amb la capa Earthshine V56 seleccionada. Aquesta és una integració fotogràfica; no una nova campanya de recuperació de detall.

## Producte i fonts

- Producte: `{pub['path']}`.
- SHA-256: `{pub['sha256']}`; {pub['bytes']} bytes; 10551 × 7506, RGB16, Adobe RGB (1998), **35 capes**.
- General vigent d'entrada: `{sources['V42']['path']}`, SHA `{sources['V42']['sha256']}`, 32 capes.
- Earthshine: `{sources['V56']['path']}`, SHA `{sources['V56']['sha256']}`, 26 capes.
- Ambdues fonts s'han tornat a llegir i verificar després del muntatge: fitxers exactes. No hi havia documents oberts amb canvis pendents a l'inici.

## Com està muntat

Les 32 capes de la V42 es conserven en el mateix ordre relatiu. RGB, alfa, màscares, geometria, opacitats i modes de fusió exactes. Únicament s'oculten la base total antiga (índex 8 de V42) i l'earthshine POWAAAH3 antic (índex 26); continuen disponibles com a alternatives.

S'hi incorporen tres capes de V56, amb els canals i màscares comprimits exactes:

1. **00 Base corba · limbe corregit V56**, visible, al lloc de la base anterior, sota estrelles i filtres.
2. **09 Compost de perles i protuberàncies · V56**, oculta com a alternativa. El muntatge manté actives les capes de perles/protuberàncies de V42.
3. **Earthshine V56 · detall i revelat de Pere**, visible a dalt de tot, mateix rectangle 1400 × 1400 a (4677, 3077).

No s'han creat màscares, recortat, remostrejat, mogut ni rotat capes. No s'ha aplicat Camera Raw o cap filtre nou. L'earthshine és el revelat desat de V56; els filtres de corona conserven l'estat de V42.

## Verificació i decisió de composició

- 32/32 capes originals preservades; tres incorporacions amb píxels i màscares exactes.
- Photoshop real: **{qa['Photoshop']}**. ImageMagick confirma PSB 10551 × 7506, 16 bits.
- Caché composta refeta amb Photoshop; reobertura i nova recomposició: **0 DN16** de diferència a tot el llenç.
- Corona fora de r520 al voltant de (5377, 3777): **0 píxels diferents de V42** en la versió lliurada.
- Interior r435 comparat amb el compost natiu V56: màxim {choice['moon_r435_V56']['max_DN16']} DN16, p99 {choice['moon_r435_V56']['p99_DN16']} DN16. És efecte de la composició sota la transparència; RGB i alfa de la capa lunar són exactes.
- Revisió visual del llenç sencer i retall lunar 1:1, amb conversió Adobe RGB → sRGB només a les vistes PNG.

La primera prova activava també el compost solar V56; canviava 1.992.145 píxels fora de r520 (màxim 1978 DN16, mitjana 1,527 DN16). Per conservar la corona general s'ha deixat ocult com a alternativa. La prova i els rebuts queden conservats; `V57_work.psb` és treball intermedi amb caché antiga i **no és el lliurable**.

## Límit visible

Els filtres heretats de V42 encara accentuen una **línia fina exterior al limbe**, visible en el muntatge general i menys marcada en l'earthshine sense aquests filtres. La V57 no declara resolt aquest efecte, ni introdueix un retoc cosmètic o una màscara nova per amagar-lo. El judici visual de Pere sobre el conjunt resta pendent. Tampoc es declara nova resolució ni equivalència DHS.

## Evidència i represa

Codi: `{T}`. Rebuts i vistes: `{O}`. Manifest: `{manifest}`.

- A0: fonts i empremtes de capes; B0: muntatge inicial.
- C1/C2/C3: comparació visual i prova d'activar/desactivar el compost solar.
- D0: empaquetat i empremtes finals; D1: porta Photoshop; D2: readback i fonts; D3: revisió visual.
- E0: publicació; E1: document final obert. Photoshop marca `saved=false` en obrir-lo, amb només l’estat d’historial «Abrir»; no s’hi ha fet cap edició de píxels. El fitxer de disc està desat, verificat i correspon al SHA publicat. Una futura desada nativa pot canviar-ne la serialització i el SHA. Les autoritats anteriors es preserven senceres a `receipts/`.

Per continuar, llegir AGENTS, CLAUDE complet i IA README → ESTAT → MAPA; comprovar el lock viu i adquirir-ne un de nou. No importar scripts antics amb claims implícits. No tocar les fonts V42/V56 ni els RAW. El límit de la línia exterior requereix diagnòstic de la contribució dels filtres si Pere en demana correcció; no canviar la geometria lunar acceptada. Estat d'alliberament efectiu: `F3_release.json` i CODEX_STATUS. Cap treball llançat a Claude.
'''
for p in (report,handoff):assert not p.exists();p.write_text(body)
m={**pub,'Photoshop':qa['Photoshop'],'native_readback_max_DN16':0,'source_files_unchanged':qa['sources_unchanged'],'report':str(report),'handoff':str(handoff),'artifact_free':False,'PASS_scope':'Exact layer integration, sources preserved, native Photoshop open and recomposition; visual acceptance by Pere pending','open_document':opened,'corona_outside_r520_exact_V42':True,'sources':{k:{j:v[j] for j in ['path','sha256','bytes']} for k,v in sources.items()}}
assert not manifest.exists();manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
prefix=f"> **13-09-2026 · Projecte general V57 muntat a Photoshop.** Totes les 32 capes de la V42 + base corregida, alternativa de protuberàncies i Earthshine V56: **35 capes**, 10551 × 7506 RGB16. Canals/màscares/geometria exactes; base i earthshine antics ocults, compost solar V56 ocult per preservar exactament la corona V42 fora de r520. Photoshop OBRE i readback 0 DN16; fonts V42/V56 intactes. Persisteix una línia fina exterior al limbe accentuada pels filtres V42; no s'ha retocat ni declarat resolta. Producte `{pub['path']}`, SHA `{pub['sha256']}`. Represa `{handoff}`; informe `{report}`. Aquest és el projecte general vigent; Earthshine independent continua V56. Les entrades següents conserven la història.\n\n"
rec=O/'receipts';rec.mkdir(exist_ok=True);rows=[]
for i,p in enumerate([R/'AGENTS.md',R/'CLAUDE.md',IA/'README.md',IA/'ESTAT_ACTUAL.md',IA/'MAPA_RUTES_I_OUTPUTS.md',IA/'Coordinació/HANDOFF_VIGENT.md']):
 assert not p.is_symlink();old=p.read_bytes();snap=rec/f'F2_before_{i}_{p.name}';assert not snap.exists();snap.write_bytes(old);tmp=p.with_name(p.name+'.V57.tmp');assert not tmp.exists();tmp.write_bytes(prefix.encode()+old);assert p.read_bytes()==old;os.replace(tmp,p);assert p.read_bytes().endswith(old);rows.append(dict(path=str(p),snapshot=str(snap),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),old_content_exact_suffix=True))
p=IA/'ACTIVE.json';old=p.read_bytes();snap=rec/'F2_before_ACTIVE.json';assert not snap.exists();snap.write_bytes(old);a=json.loads(old);earth=json.dumps(a['current_earthshine_product'],sort_keys=True);prior=a['current_product'];a['previous_general_product_V42']=prior;a['current_product']={**m,'source':prior};a['updated']=now;a['phase']='post-eclipse-general-V57-with-earthshine-V56-delivered';a['formal_worktree_handoff']=str(handoff);a['paths']['current_technical_editable']=pub['path'];a['paths']['current_delivery_manifest']=str(manifest);a['paths']['current_visual_output']=str(O/'vistes');a['general_integration_task']={'status':'V57_DELIVERED_OPEN_IN_PHOTOSHOP','handoff':str(handoff),'report':str(report),'pending':'Pere visual review; inherited exterior limb line remains'};assert json.dumps(a['current_earthshine_product'],sort_keys=True)==earth
tmp=p.with_name(p.name+'.V57.tmp');assert not tmp.exists();tmp.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');assert p.read_bytes()==old;os.replace(tmp,p);rows.append(dict(path=str(p),snapshot=str(snap),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(O/'F2_authorities.json').write_text(json.dumps(dict(time=now,rows=rows,CLAUDE_STATUS_untouched=True),ensure_ascii=False,indent=2))
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} · CAPES TOTALS V57 LLIURADA · CLAIM HELD\n\n35 capes, V42 general + Earthshine V56. Photoshop obert amb V57, capa lunar seleccionada; fitxer de disc desat i verificat. La bandera nativa saved=false apareix en obrir-lo, historial només Abrir. Fonts exactes; canals/màscares/geometria exactes. Readback final 0 DN16; corona fora r520 exacta V42. Compost solar V56 preservat ocult. Línia fina exterior del limbe accentuada pels filtres V42 encara visible; no curada. Producte SHA {pub["sha256"]}. Informe {report}; handoff {handoff}. Alliberament després de comprovació final de processos.\n')
print('DOCUMENTED',handoff,flush=True)
