"""Publish auditable sources and limits. Never promote a clean-limb claim."""
from comu45 import *
from c5_fonts_psb import CI,FINAL,jsx
import shutil,datetime,hashlib

REPORT=ROOT/'research/163_V44_ARTEFACTES_I_V45_FONTS_LIMBE_TEMPORAL_20260910.md'
HANDOFF=ROOT/'.coordination/HANDOFF_2026-09-10_CODEX_V44_ARTEFACTES_I_V45_FONTS.md'
IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
DESKOUT=IA/'output/v45_earthshine_20260910'
DATA=CI/'Earthshine_V45_Fonts_dades'

def cp(p,q):
    assert not q.exists(),q;q.parent.mkdir(parents=True,exist_ok=True)
    with p.open('rb') as src,q.open('xb') as dst:shutil.copyfileobj(src,dst,8<<20)
    assert sha(p)==sha(q)
    return dict(source=str(p),path=str(q),sha256=sha(q),bytes=q.stat().st_size)

def main():
    claim45();pub=json.loads((REB45/'C5_publish.json').read_text());assert Path(pub['path'])==FINAL and sha(FINAL)==pub['sha256']
    assert json.loads((REB45/'C5_photoshop_readback.json').read_text())['PASS']
    assert json.loads((REB45/'F7_HDR_photoshop.json').read_text())['PASS']
    f6=json.loads((REB45/'F6_reference_transfer.json').read_text());assert f6['complete'] and all(x['passes'] for x in f6['rows'])
    f9=json.loads((REB45/'F9_fixed_last_limb_judge.json').read_text());assert all(v['triple_pass_sectors']==0 for v in f9['results'].values())
    assert f6['F2_receipt_sha256']==f9['F2_sha256']==sha(REB45/'F2_temporal.json')
    f7=json.loads((REB45/'F7_fonts.json').read_text());assert f7['F2_sha256']==sha(REB45/'F2_temporal.json')
    originals={CI/'Earthshine_V43.psb':'52ac5cfd90d7b1434eec49274b694b72c19e3159a490a2b3e2f27119b8d025b1',CI/'Earthshine_V43_detall.psb':'609c3a5f2a1f03930629e1e163d33f40e3541d69e0b7835a58552ea6acc0c8e4',CI/'Earthshine_V44.psb':'49fe61696845014160278d431969972ea59d1566b33ed0250bdcc4d9d8e33220',Path('/Users/USUARI/Downloads/Earthshine_V44_artefactes.tif'):'2e73cd404f760ed894ad9805e812a828ebf357e55a98ce49317d491d1159bd4a',CI.parent/'Capes Totals/V42.psb':'c33804adb3859e26e1a5b71d19d78d6929c2127d10c987e3efbd6e3ab89ee5c2'}
    for p,h in originals.items():assert sha(p)==h,p
    frames=json.loads((REB45/'B1_inputs.json').read_text())['frames']
    for m in frames:assert sha(Path(m['native']['file']))==m['native']['sha256'],m['stem']
    assert len(frames)==88
    savejson(REB45/'D7_integrity.json',dict(originals=[dict(path=str(p),sha256=h,unchanged=True) for p,h in originals.items()],native_frames_verified=88,F2_sha256=sha(REB45/'F2_temporal.json'),source_science_status='ALL_LIMB_RECOVERY_NOT_DEMONSTRATED'))
    print('Originals and88native caches verified',flush=True)

    copies=[];DATA.mkdir(exist_ok=False);DESKOUT.mkdir(parents=True,exist_ok=False)
    for item in [f7['linear_float32'],f7['numerical_sources']]:
        p=Path(item['path']);assert sha(p)==item['sha256'];copies.append(cp(p,DATA/p.name))
    selected=['A0_anotat_lluna_1a1.png','F8_comparacio_temporal_lila.png','C5_Photoshop_real_lluna_1a1.png','C5_Photoshop_real_llenc_quart.png']+[f'F7_{key}.png' for key in ['vixen_C2_11s','vixen_C2_73s','sony_reference','vixen_reference','combined_all','combined_reference']]
    for name in selected:copies.append(cp(VIS45/name,DESKOUT/'vistes'/name))

    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    readme=f'''# Earthshine V45 — fonts mesurades; limbe encara no resolt

La cremallera de V44 era un artefacte del filtre de finestres. S'ha refet la font des dels88 RAW registrats i revisat la contribució temporal dels dos telescopis. Alguns instants tardans Vixen tenen menys contaminació a l'oest.

**No s'ha recuperat amb garanties el detall de tot l'últim limbe ni s'ha validat una resta del vel.** Aquest paquet conserva les dades observades, inclosa la llum dispersada; no és un disc fotogràfic net. Cap textura de LROC incorporada.

- PSB: `{FINAL.name}` ·24 capes ·10551×7506 RGB16 · SHA `{pub['sha256']}`.
- Les18capes anteriors són byte a byte. Les sis noves són fonts monocromesG amb una sola corba global; activar-les d'una en una. La superior és la combinada amb preferència temporal. Les màscares de visualització són editables; les fonts no es retallen amb un esvaïment de detall.
- `Earthshine_V45_HDR_G_lineal.tif`: mateix llenç, RGBfloat32; tres canals idènticsG/65535, alfa geomètrica no associada. Conserva valors lineals sense la corba de pantalla. No és radiància absoluta.
- `Earthshine_V45_font_i_pesos.npz`: dades originals de la tessel·la lunar, Vixen/Sony, totes les èpoques, pesos, alfa i origen. Cap remostreig addicional.
- CorbaPSB: `0.20+0.045*asinh((G-528.312744140625)/20)`. Zero clipping lunar; la quantificacióRGB16 pot amagar amplituds molt petites al limbe. El TIFFfloat32 evita aquest límit.

Photoshop real:24capes, composició verificada amb error màxim3/65535 i alfa exacte; fonts prèvies intactes. Aquest PASS és de fitxer/píxels, no d'absència d'artefactes o de recuperació científica.

Informe complet: [{REPORT.name}]({REPORT}).
Comparació lila: [{(DESKOUT/'vistes/F8_comparacio_temporal_lila.png').name}]({DESKOUT/'vistes/F8_comparacio_temporal_lila.png'}).
Handoff: [{HANDOFF.name}]({HANDOFF}).
Publicació verificada: {now}.
'''
    rp=CI/'Earthshine_V45_Fonts_REBUT.md';assert not rp.exists();rp.write_text(readme)
    (DATA/'LLEGEIX_ME.md').write_text(readme);(DESKOUT/'LLEGEIX_ME.md').write_text(readme)
    copies.append(cp(REPORT,DESKOUT/REPORT.name))
    handoff=f'''# Handoff de revisió V44 i fonts V45 — {now}

**Prioritat viva de Pere: màxim detall real de tot el limbe. El resultat complet continua sense resoldre.** Aquesta ronda acaba amb causes comprovades, fonts refetes i un paquet editable validat com a fitxer; no hi ha nova candidata de disc net acceptada. Autorització desatesa/Photoshop vigent; no és falta de permís. No hi ha canvi de FOV ni de Capes TotalsV42.

## Arrencada exacta

Arrel de codi: `{ROOT}`, sense Git. Actius: Desktop/Eclipse2026. LlegirAGENTS,CLAUDE,IA/README,ESTAT,MAPA,ACTIVE i aquest handoff. ConsultarCODEX_STATUS per aRELEASED i adquirir un nouclaim abans d'escriure. No editarCLAUDE_STATUS.

Informe principal: `{REPORT}`. Manifest: `{HERE45/'delivery_manifest.json'}`. Scripts: `{HERE45}`. Fonts natives verificades88/88 al rebutD7. Snapshot anterior a pesosFPN: `cau/pre_FPN/manifest.json`.

## Què s'ha establert

1. V44cremallera és causal: FFTlocal64/pas8 crea textura des d'un nul radial; correlació0,904 al radi419; suma de pesos1,69848. PhotoshopPASS no certificava aquesta ciència.
2. El perfil sectorial també absorbeix paquets radials reals. Retirar només el mosaic no basta. G-AZI(research127) prohibeix tractar l'eliminació de modes angulars baixos com si conservés tota la Lluna.
3. Vixen2972 versus2990, totsdos1/2s: zona lila té menysG contaminant i cobertura vàlida74,47→92,67% als darrers píxels del sector fix. No extrapolar que l'instant més tardà és sempre millor.
4. RAWG1/G2 nadius, quatre petjades<85%, sense llindar de brillantor, una sola interpolació, registre acceptat Sony6982 addicional. Quinze HDRtemporals i referència convexa; pesos empíricsFPN percomponent, limitats8–64. No variància física completa ni independència entre components.
5. F6injecció posteriorCFA:12/12pass, guany0,999790–1,000648; no prova òptica. F9jugtefix últimlimbe:0/24pass triples enlog i lineal, fontfinalhashes al rebut. No absència física de senyal demostrada.
6. CincRAWnominals extra revisats aA3: guarda1s, noF1.3; no cobertura millor ni referènciaSony més neta demostrades a lila. Pes addicional projectat0,004390% a449–454; no cota universal. Possible ús de contacte requereix geometria/rellotge verificats.

## Productes i verificació

`{FINAL}` · SHA `{pub['sha256']}` ·1.266.007.766bytes ·24capesRGB16. Les18capesV44 intactes;6fontsnoves Normal100%, una visible. Corba globalmonòtona, velpresent. FontGcombinada:`cau/combined_reference.npy`, SHA `faeec8deff41d2092b866a1e7aa146ceb22daad35d14a268268f21a818f60fb7`.

HDRfloat32 iNPZ a `{DATA}`. TIFF32télecturanumèrica exacta i oberturaPhotoshop32. PSBporta real24capes, TIFFrecomposatRGBA16: màxim3DN16, alfaexacte; mateixSHA verificat/publicat. Vistes reals inspeccionades, vora lluminosa encara present. V43,V43_detall,V44,TIFFPere iCapesTotalsV42 hashes intactes.

## No repetir ni promoure aquests negatius

`*_corrected.npy`: resta diferencialF2 amb negatius/sobrepassos. F3global+sectors: menja textura radial. F3bpoquesbasesradials: halo negre/blanc. F3charmònics: elimina modes lunars i deixa falslimbe. F5pilot: render d'experimenth2 amb metadades antigues; REBUTJAT, no producte. `candidate_h2*` no és candidat acceptat. Els scripts i caches resten com a evidència.

PSF comuna temporal empitjora parella tardana reservada29,79→61,93DN. Coeficientlocaldiferencial redueix velvariable però no recuperaLROCúltimlimbe; absoluta produeix negatius. Estrelles: nucli detectat, ales9–26px només1,5–2σ sense error sistemàtic de corona; no identificació absoluta útil. `halo_sony2_full.py` usaLROC alfit, no independent.

## Si es reprèn la ciència

Començar per la font nadiua i una hipòtesi física nova amb prova reservada. La component comuna del vel no s'identifica només amb diferències temporals. No provar més perfils sectorials o cercles cosmètics ni afegir detallLROC. Cal mostrar millora simultània de font/transferència/contaminació i jutge independent amb el mateixsuport. No dir que hem esgotat matemàticament totes les vies: els models provats han fallat; el detall demanat continua pendent.

No hi ha tasca automàtica programada ni nova petició de permís. Estat de l'escriptor i zero processos a la líniaRELEASED final deCODEX_STATUS. Les fonts es deixen disponibles perPere sense substituir-ne originals ni desar altres documents oberts dePhotoshop.
'''
    assert not HANDOFF.exists();HANDOFF.write_text(handoff)
    note=f'''**Revisió del10-09-2026 — V44 amb artefacte confirmat; V45 només FONTS.**
La cremallera marcada perPere ve del mosaicFFT64/pas8 i és amplificada per pesos superposats; no queda validada la recuperació de tot l'últim limbe. Reapilat88RAW nadius, selecció temporal i pesosFPN; instantsVixen tardans menys contaminats a l'oest. Jutge final435–449:0/24pass triples. No nova resta devel promoguda.
`Capes interiors/Earthshine_V45_Fonts.psb` ·24capesRGB16 · SHA `{pub['sha256']}`:18capesV44 exactes+6fonts, velobservat present. HDRlineal32bits iNPZ a `Capes interiors/Earthshine_V45_Fonts_dades`. PhotoshopPASS de fitxer/recomposició, màxim3DN16; noPASS de recuperació completa. Originals iCapesTotalsV42 intactes.
Represa: `{HANDOFF}`. Informe `{REPORT.name}`; manifest `research/tools/v45_earthshine_20260910/delivery_manifest.json`. El resultat fotogràfic de TOT el limbe continua sense resoldre. Les afirmacions V44 de sota són història i queden qualificades per aquesta revisió.

'''
    docs={'AGENTS':ROOT/'AGENTS.md','CLAUDE':ROOT/'CLAUDE.md','research_README':ROOT/'research/README.md','IA_README':IA/'README.md','IA_ESTAT':IA/'ESTAT_ACTUAL.md','IA_MAPA':IA/'MAPA_RUTES_I_OUTPUTS.md','IA_ACTIVE':IA/'ACTIVE.json','IA_HANDOFF':IA/'Coordinació/HANDOFF_VIGENT.md'}
    snap=HERE45/'docs_before';snap.mkdir(exist_ok=False);old={}
    for key,p in docs.items():old[key]=p.read_bytes();(snap/(key+p.suffix)).write_bytes(old[key])
    installed=[]
    for key,p in docs.items():
        text=old[key].decode();assert p.read_bytes()==old[key],p
        if key=='AGENTS':
            marker='## Autoritat viva i escriptura única\n\n';assert marker in text;text=text.replace(marker,marker+note,1)
        elif key=='CLAUDE':
            marker='## 1. Punt de represa\n\n';assert marker in text;text=text.replace(marker,marker+note,1)
            text=text.replace('(Earthshine V44 de Codex)','(revisió V44 i fonts V45 de Codex)',1)
        elif key=='research_README':text='- [163 — V44: cremallera causal; V45 fonts temporals, últim limbe encara no resolt]('+REPORT.name+')\n'+text
        elif key=='IA_ACTIVE':
            a=json.loads(text);previous_product=a['current_product'];a['updated']=now;a['phase']='post-eclipse-V44-reviewed-V45-observed-sources-only';a['formal_worktree_handoff']=str(HANDOFF)
            a['current_earthshine_product']['review_status']='V44_ZIPPER_CONFIRMED; COMPLETE_LAST_LIMB_RECOVERY_NOT_ACCEPTED';a['current_earthshine_product']['review_report']=str(REPORT)
            a['current_earthshine_product']['limitations'].append('Pere V44 TIFF review confirms FFTpatch zipper and overlap amplification; old detail acceptance cannot imply all-limb recovery')
            a['current_earthshine_sources']=dict(path=str(FINAL),sha256=pub['sha256'],bytes=pub['bytes'],layers=24,size=[W,H],depth=16,scope='OBSERVED_SOURCES_ONLY_WITH_RESIDUAL_GLARE',complete_limb_recovery=False,photoshop_pixels_PASS=True,report=str(REPORT),manifest=str(HERE45/'delivery_manifest.json'),data=str(DATA))
            a['paths']['latest_earthshine_sources']=str(FINAL);a['paths']['latest_earthshine_source_data']=str(DATA);a['paths']['latest_earthshine_review_output']=str(DESKOUT)
            a['earthshine_task']=dict(status='ALL_LIMB_DETAIL_UNRESOLVED__V45_SOURCES_DELIVERED',target=str(FINAL),completed_work='V44causalreview;88RAWnativegreenrebuild; temporalcleanliness andweights; validatedsourcepackage',next_action='new independently validated source/PSF hypothesis required before any clean-limb promotion; do not rerun rejected cosmetic models',handoff=str(HANDOFF))
            assert a['current_product']==previous_product;text=json.dumps(a,ensure_ascii=False,indent=2)+'\n'
        else:text=note+'---\n\nHistòria conservada; aquesta revisió és el punt de represa.\n\n'+text
        p.write_text(text);installed.append(dict(path=str(p),sha256=sha(p),before_sha256=hashlib.sha256(old[key]).hexdigest(),snapshot=str(snap/(key+p.suffix))))
    # Opening the new source package changes no pixels or other documents.
    answer=jsx('var d=app.open(new File('+json.dumps(str(FINAL))+')); d.name+"|"+d.layers.length+"|"+d.saved;')
    savejson(REB45/'C5_open_published.json',dict(path=str(FINAL),sha256=sha(FINAL),result=answer,other_documents='no close/save/mutation'))
    files=set(HERE45.glob('*.py'))|set(REB45.glob('*.json'))|{REPORT,HANDOFF,FINAL,rp,DATA/'LLEGEIX_ME.md',DESKOUT/'LLEGEIX_ME.md'}|set(DATA.glob('*.tif'))|set(DATA.glob('*.npz'))
    files|={Path(x['path']) for x in copies};files|={Path(x['path']) for x in installed};files|={Path(x['snapshot']) for x in installed}
    manifest=dict(created_utc=now,scope='SOURCE_PACKAGE_AND_FAILED_CLEAN_LIMB_REVIEW; not a fully recovered earthshine product',product=pub,files=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)],copies=copies,authorities=installed,report=str(REPORT),handoff=str(HANDOFF),originals_receipt=str(REB45/'D7_integrity.json'),source_chain=['B1','F2w','F2reference','F6','F7','C5'],rejected=['F2corrected','F3','F3b','F3c','F5candidate_h2'],scientific_goal_complete=False)
    target=HERE45/'delivery_manifest.json';assert not target.exists();savejson(target,manifest)
    for row in manifest['files']:assert sha(Path(row['path']))==row['sha256'],row['path']
    assert json.loads((IA/'ACTIVE.json').read_text())['current_product']==json.loads(old['IA_ACTIVE'])['current_product']
    savejson(REB45/'D8_final_verify.json',dict(PASS=True,scope='files/copies/authority/originals; scientific full-limb goal NOT achieved',manifest_sha256=sha(target),files_verified=len(manifest['files']),originals_verified=len(originals),native_frames_verified=88,authorities_verified=len(installed),photoshop_open=answer,complete_limb_recovery=False))
    print('SOURCE DELIVERY VERIFIED',len(manifest['files']),answer,flush=True)
if __name__=='__main__':main()
