"""Publish the V46 receipt and update live restart pointers after all gates."""
from comu46 import *
from b1_package import CI,FINAL,NAME
import shutil,datetime

def main():
    claim46();pub=json.loads((REB46/'B1_publish.json').read_text());qa=json.loads((REB46/'B2_protection.json').read_text())
    px=json.loads((REB46/'B1_photoshop_readback.json').read_text());integ=json.loads((REB46/'D1_original_integrity.json').read_text())
    assert qa['PASS'] and px['PASS'] and integ['PASS'] and sha(FINAL)==pub['sha256']
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    ia=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');dest=ia/'output/v46_earthshine_20260911';dest.mkdir(exist_ok=False);(dest/'vistes').mkdir()
    report=ROOT/'research/164_EARTHSHINE_V46_CONTORN_FOSC_GRADUAL_20260911.md'
    handoff=ROOT/'.coordination/HANDOFF_2026-09-11_CODEX_EARTHSHINE_V46.md'
    assert not report.exists() and not handoff.exists()
    snapshot=json.loads((REB46/'A0_snapshot.json').read_text())
    r=f'''# Earthshine V46 — contorn fosc gradual, 11-09-2026

Pere considera la millora V45 significativa i autoritza una V46 desatesa per enfosquir els últims píxels, amb degradats i protecció especial de les protuberàncies petites de dalt i de la dreta. La captura de referència és `Downloads/Captura de pantalla 2026-09-11 a las 3.12.25.png`.

## Lliurable i ús

`{FINAL}`

SHA-256 `{pub['sha256']}`. {pub['bytes']:,} bytes; 10551 × 7506, RGB16, 25 capes. Mateix llenç, escala, contorn Vixen i màscara lunar. No retall ni remostreig del producte.

Capa superior **{NAME}**, mode Restar, opacitat100%. Reduir-ne l'opacitat disminueix l'enfosquiment; apagar-la retorna a la composició V45 que Pere tenia oberta. Les 24 capes d'aquell estat es conserven amb els canals comprimits, màscares, geometria, modes i visibilitats exactes.

## Preservació de l'estat obert

Photoshop tenia `Earthshine_V45_Fonts.psb` amb canvis sense desar. La capa lunar visible tenia píxels diferents dels publicats; la capa09 RGB era exactament igual. La màscara només diferia1DN16 per quantització de Photoshop. No s'ha substituït l'estat obert pel fitxer de disc.

S'ha duplicat el document complet i desat exclusivament la còpia a `{snapshot['snapshot']}`, SHA `{snapshot['sha256']}`. El document original ha continuat obert i sense desar abans i després. L'exportació TIFF prèvia i els canals de la còpia reprodueixen el mateix estat dins6DN16. La V46 parteix d'aquesta còpia completa.

## Ajust declarat

Aquesta és una **variant fotogràfica de to demanada expressament per Pere**, no una nova recuperació científica de relleu ni una correcció física de PSF. Aquesta instrucció concreta autoritza el degradat de pantalla; les exclusions anteriors de resta cosmètica continuen aplicant-se a les afirmacions científiques.

S'utilitza la distància interior al contorn Vixen existent. Un perfil robust de luminància de pantalla, en passos0,25px amb sigma0,5px només sobre la referència1D, defineix un camp positiu de guany. Cap píxel de la textura s'ha difuminat. Variant `h`: objectiu0,18 al contorn, transició smootherstep de8px fins0,22905; alliberament gradual complet als100px. Als60px el guany ja és0,94967, als80px0,99480 i a partir de100px és exactament1. Això evita el salt entre una línia fosca i el vel clar interior.

Si L és la capa lunar, B la capa09 i w la màscara existent, la composició anterior és B(1−w)+Lw. La capa nova conté S=L_G(1−g), igual als tres canals, i el pes w s'aplica a S abans de la fusió: **C46=C45−wS**. La capa Restar conté aquest producte ja calculat, per evitar que Photoshop retalli valors intermedis abans d'aplicar una màscara parcial. La contribució B(1−w) queda intacta, igual que les diferències cromàtiques que defineixen les protuberàncies. El contrast lunar absolut baixa amb el to; la textura fraccional de G es conserva dins la quantització. El perfil no es presenta com una estimació física del vel ni com terrain recuperat.

## Verificació real

- `porta_photoshop.sh`: OBRE10551×7506 ·25capes. Photoshop ha recomposat les capes després d'apagar i encendre l'ajust, i ha exportat TIFF RGB16 amb transparència.
- Diferència màxima sobre tot el llenç visible: **{px['max_full_DN16']}DN16**; alfa: **{px['max_alpha_DN16']}DN16**. No és una validació basada només en la miniatura incrustada.
- Les24capes de la còpia viva: canals comprimits exactes; nouRGB: descodificació exacta; màscares originals intactes. Segon lector ImageMagick correcte.
- Píxels de la ROI sense ajust: desviació màxima real **{qa['actual_no_grade_max_DN16']}DN16**; diferència cromàtica màxima **{qa['actual_chromatic_max_delta_DN16']}DN16**.
- Verd mediana als últims píxels amb màscara>95%: **{qa['median_edge_green_before']:.4f} → {qa['median_edge_green_after']:.4f}** en escala0–1.
- Interior a100px: font exacta. Cap nou negre retallat en la font lunar dins la zona graduada; inversió del guany recupera G amb màxim{qa['inverse_gain_max_DN16']:.3f}DN16 de quantització.
'''
    for x in qa['rows']:
        r+=f"- Protuberàncies/zona {x['name']}: màxim canviR−G {x['red_signal_max_delta_DN16']}DN16, desplaçament del centroide cromàtic {x['red_signal_centroid_shift_px']:.6f}px.\n"
    r+='''
Inspecció visual feta al disc sencer, llenç complet i retalls de dalt, dreta, oest i baix a coordenades idèntiques. Les protuberàncies petites continuen visibles. La variació de contorn heretada no s'ha allisat ni substituït per un cercle.

## Proves descartades i límits

Els primers degradats directes exponencials de24–48px produïen una franja negra massa ampla; descartats. Les variants amb transicions24–32px també deixaven una vora massa marcada. La variant final usa8px i una correcció suau del vel de pantalla per enllaçar-la amb l'interior.

El primer PSB de prova va passar el lector independent però Photoshop el va refusar. Causa de format: la conversió del PSD de la còpia viva a PSB necessitava les signatures8B64 dels blocs globals FMsk/cinf, com al PSB nadiu. Es va corregir només la serialització; la prova rebutjada i el seu rebut queden a staging. Una segona prova es podia obrir però no reproduïa el càlcul: Photoshop retallava C−S abans d'interpolar la màscara parcial. La versió final incorpora w a S abans de Restar i evita aquest retall intermedi. El tercer PSB és el lliurat i ha passat obertura i comparació de tots els píxels.

La V46 no afegeix cap dada a la V45 ni torna a validar científicament les textures de l'últim limbe. La recuperació total no demostrada de research163 continua sent el límit de les fonts, compatible amb la valoració fotogràfica positiva de Pere. No es modifica Capes Totals ni cap RAW.

## Reproducció

Arrel de codi: `research/tools/v46_earthshine_20260911/`. Estat viu preservat a `V45_live_source.psd`; derivats exactes a `cau/`. Cadena `a2_grade_live.py` (variant h) → `b1_package.py build/verify/gate/readback` → `b2_protection.py` → `b1_package.py publish` → `d2_deliver.py`. El build/publish refusen sobreescriure fitxers; per repetir cal una destinació nova.

Rebuts a `output/v46_earthshine_20260911/4-rebuts/`. Vistes finals a `IA/output/v46_earthshine_20260911/vistes/`. Original V43, V43_detall, V44, TIFF anotat V44, V45 de disc i Capes TotalsV42 verificats perSHA i intactes. Manifest final `research/tools/v46_earthshine_20260911/delivery_manifest.json`.
'''
    report.write_text(r)
    summary=f'''# Earthshine V46 preparada

Contorn més fosc amb transició gradual, conservant l'estat V45 que Pere tenia obert.

Fitxer: `{FINAL}`
SHA-256 `{pub['sha256']}`. 10551 × 7506, RGB16, 25 capes.

La capa superior **{NAME}** regula l'ajust: opacitat100% és la proposta; reduir-la suavitza l'efecte; apagar-la recupera la composició anterior. La V45 de disc i les24capes de la còpia oberta estan preservades. Les protuberàncies de dalt i dreta s'han revisat ampliades i el seu senyal cromàtic es conserva dins la quantització.

Photoshop: obertura i recomposició real verificades; error màxim{px['max_full_DN16']}DN16. És un ajust fotogràfic de to, sense nova recuperació de dades.

Informe: `{report}`. Represa: `{handoff}`.
'''
    (dest/'LLEGEIX_ME.md').write_text(summary);(CI/'Earthshine_V46_REBUT.md').write_text(summary)
    shutil.copy2(report,dest/report.name)
    for name in ['A0_live_before.png','B1_Photoshop_real_lluna_1a1.png','B1_Photoshop_real_llenc_quart.png']+[f'B2_{x}_abans_despres_x3.png' for x in ['dalt','dreta','oest','baix']]:shutil.copy2(VIS46/name,dest/'vistes'/name)
    h=f'''# Traspàs V46 — Codex, 11-09-2026

Pere ha valorat molt positivament la millora V45 i ha demanat una V46 amb els últims píxels menys blancs, degradats i protecció de les protuberàncies de dalt i dreta, en treball desatès. La petició de la variant fotogràfica està completada.

{summary}

**Font crucial:** hi havia canvis sense desar a la capa lunar del document obert. S'han preservat a `{snapshot['snapshot']}` (SHA `{snapshot['sha256']}`), s'han conservat les24capes d'aquesta còpia i s'hi ha afegit una única capa Restar amb el pes de la màscara original ja aplicat als seus píxels. No reprendre la V46 des de la V45 de disc si es vol conservar l'estat acceptat per Pere.

Camp de to variant h: objectiu0,18 al contorn, transició8px; cua suau fins100px, amb només5% d'enfosquiment als60px i0,5% als80px. Interior més profund exactament igual. Cap remostreig ni cercle nou. No és una nova afirmació de correccióPSF ni de recuperació d'últim limbe: research163 conserva els límits científics.

Rebuts: `{REB46}`. Manifest: `{HERE46/'delivery_manifest.json'}`. Proves més negres descartades; primera serialitzacióPSB refusada i corregida abans de la porta real. Font V45 oberta no desada ni tancada; originalsSHA intactes. No hi ha cap procés propi ni escriptura pendent en acabar. SERIAL_WRITES s'allibera després de registrar RELEASED a CODEX_STATUS.

Següent acció opcional: Pere pot valorar la V46 i ajustar l'opacitat de la capa superior. Cap acció automàtica pendent; Capes Totals continuaV42.
'''
    handoff.write_text(h)
    heads=f'''**11-09-2026 — Earthshine V46, variant fotogràfica demanada per Pere.**
Pere valora positivament V45 i demana enfosquir el contorn amb degradats, preservant les protuberàncies de dalt i dreta. `{FINAL}` ·25capesRGB16 ·10551×7506 ·SHA `{pub['sha256']}`. Conserva les24capes de l'estat V45 obert amb canvis sense desar, preservat a `{snapshot['snapshot']}`, i afegeix una capa Restar d'opacitat regulable. Contorn/màscara/escala iguals. Photoshop i recomposicióPASS (màxim{px['max_full_DN16']}DN16); senyal cromàtic de protuberàncies preservat. És un ajust de to autoritzat, sense nova afirmació de recuperació científica del limbe. Originals i CapesTotalsV42 intactes.
Represa: `{handoff}`. Informe `research/{report.name}`. Manifest `research/tools/v46_earthshine_20260911/delivery_manifest.json`. Vistes `{dest/'vistes'}`. Tasca V46 completada; valoració visual de Pere oberta. Les notes anteriors són història.

'''
    auth=json.loads((REB46/'D0_authority_before.json').read_text())
    for a in auth:
        p=Path(a['path']);assert sha(p)==a['sha256'],str(p)
        old=p.read_text()
        if p==ROOT/'AGENTS.md':
            marker='**El traspàs vigent és';idx=old.index(marker);old=old[:idx]+f'**El traspàs vigent és `.coordination/{handoff.name}`** (V46 fotogràfica demanada perPere; contorn fosc gradual, estatV45obert preservat,25capes, PhotoshopPASS; research164). L\'anterior deia: '+old[idx:]
        elif p==ROOT/'CLAUDE.md':
            old=old.replace('Última actualització efectiva: 10 de setembre de 2026 (revisió V44 i fonts V45 de Codex).','Última actualització efectiva: 11 de setembre de 2026 (V46 fotogràfica de Codex).',1)
            old=old.replace('## 1. Punt de represa\n\n','## 1. Punt de represa\n\n'+heads,1)
        elif p==ROOT/'research/README.md':old=f'- [164 — Earthshine V46: contorn fosc gradual i protuberàncies protegides]({report.name})\n'+old
        elif p.name=='ACTIVE.json':
            j=json.loads(old);j['updated']=now;j['phase']='post-eclipse-V46-photographic-edge-grade-delivered';j['formal_worktree_handoff']=str(handoff)
            j['paths'].update(current_earthshine_editable=str(FINAL),current_earthshine_manifest=str(HERE46/'delivery_manifest.json'),current_earthshine_visual_output=str(dest/'vistes'))
            j['current_earthshine_product']=dict(path=str(FINAL),sha256=pub['sha256'],bytes=pub['bytes'],size=[W,H],depth=16,layers=25,PASS=True,PASS_scope='PHOTOGRAPHIC_TONE_REQUEST; PSB and actual Photoshop pixels and source/prominence invariants',artifact_free='not claimed',source=snapshot['snapshot'],report=str(report),manifest=str(HERE46/'delivery_manifest.json'),limitations='Photographic tone only; prior all-limb scientific recovery remains unproven',user_request='Less white lunar edge with gradients; preserve top/right prominences; unattended',user_V45_feedback='Very significant improvement',review_status='V46 prepared; user visual review optional')
            j['earthshine_task']=dict(status='V46_PHOTOGRAPHIC_REQUEST_COMPLETE',target='Dark lunar edge with gradual transition and protected prominences',completed_work='Live V45 source preserved; grade h; all24source layers exact;25layerPSB; actual Photoshop and chromatic-signal QA; originals intact',next_action='Optional user visual assessment or opacity adjustment; no unattended work pending',handoff=str(handoff))
            j['history']=dict(previous_active_snapshot=a['snapshot'],previous_active_sha256=a['sha256'],meaning='V45 source scientific review retained; V46 is a later explicit photographic request')
            old=json.dumps(j,ensure_ascii=False,indent=2)+'\n'
        elif p.name=='HANDOFF_VIGENT.md':old=h
        else:old=heads+'---\n\n'+old
        p.write_text(old);a['after_sha256']=sha(p)
    savejson(REB46/'D2_authority_update.json',auth)
    paths=[FINAL,HERE46/'V45_live_source.psd',report,handoff,CI/'Earthshine_V46_REBUT.md']
    paths+=list(HERE46.glob('*.py'))+list(REB46.glob('*.json'))+list((dest/'vistes').glob('*.png'))+[dest/'LLEGEIX_ME.md']+list(CAU46.glob('*.npy'))
    rows=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in paths]
    savejson(HERE46/'delivery_manifest.json',dict(created_utc=now,scope='USER_AUTHORIZED_PHOTOGRAPHIC_V46_COMPLETE',product=pub,report=str(report),handoff=str(handoff),authorities=auth,files=rows,source_snapshot=snapshot,scientific_limb_recovery='No new claim; limits from163 remain',rejected=['direct exponential broad black bands','e/f/g tone variants','first PSD-to-PSB header conversion','SUBTRACT with partial mask clips before interpolation'],photoshop_readback=px,protection=qa))
    print('DOCUMENTED',FINAL,flush=True)

if __name__=='__main__':main()
