"""Measured report and scientific plots; no eclipse-image edit."""
from geometry_common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates
phase=json.loads((OUT/'B1_reference_comparison.json').read_text());solar=json.loads((OUT/'A1_solar_registration.json').read_text());completion=json.loads((OUT/'C0_geometry_completion.json').read_text());variants=['baseline','solar_only','measured_lunar_phase','measured_phase_width'];labels=['Base anterior','Registre solar','Fase lunar mesurada','Fase i amplada'];test=[r for r in phase['frames'] if r['heldout']]
fig,axes=plt.subplots(2,2,figsize=(15,10),layout='constrained');ax=axes[0,0]
for r in test:
    ax.plot([p['angle'] for p in r['pairs']],[p['residual'] for p in r['pairs']],'o',markersize=4,label=r['stem'])
ax.axhspan(-.25,.25,color='grey',alpha=.15);ax.axhline(0,color='grey',lw=.7);ax.set(xlabel='Angle lunar (graus)',ylabel='Fase observada − predita (px)',title='La referència solar no prediu prou bé el llimb');ax.legend(fontsize=8)
ax=axes[0,1];x=np.arange(4);width=.18
for k,(v,label) in enumerate(zip(variants,labels)):
    vals=[]
    for stem in TEST:
        r=next(r for r in completion['results'] if r['stem']==stem and r['variant']==v and r['mask_from_RAW']=='572A2983');vals.append(r['regions'][2]['p95_abs_G'])
    ax.bar(x+(k-1.5)*width,vals,width,label=label)
ax.axhline(25,color='black',ls='--',label='Límit: 25 G');ax.set(xticks=x,xticklabels=[s[-4:] for s in TEST],ylabel='P95 de l’error absolut (G)',title='Completat a 435–449 px · màscara real de 10 s');ax.legend(fontsize=8)
theta=np.linspace(0,2*np.pi,720);radius=np.linspace(435,449,120);xx=CX+radius[:,None]*np.cos(theta);yy=CY+radius[:,None]*np.sin(theta)
for ax,stem in zip(axes[1],['572A2967','572A3003']):
    panels=[]
    for variant in ['baseline','measured_lunar_phase']:
        z=np.load(OUT/f'C0_map_{stem}_{variant}.npz');panels.append(map_coordinates(z['error'],[yy,xx],order=1))
    im=ax.imshow(np.concatenate(panels),origin='lower',aspect='auto',extent=[0,360,0,2],cmap='RdBu_r',vmin=-200,vmax=200);ax.axhline(1,color='black');ax.set(xlabel='Angle lunar (graus)',yticks=[.5,1.5],yticklabels=['Base 435→449','Fase 435→449'],title=f'{stem}: error signat del completat')
fig.colorbar(im,ax=axes[1,:],label='Error en la correcció ampla (G)',shrink=.8);fig.suptitle('Diagnòstic de geometria · no és una nova versió fotogràfica',fontsize=15);fig.savefig(OUT/'D0_geometry_review.png',dpi=170);plt.close(fig)
baseline=[]
for stem in ['572A2967','572A3003']:
    x=np.load(OUT/f'C0_map_{stem}_baseline.npz');y=np.load(PREV/f'E1_completion_map_{stem}.npz');q=x['qualified']&y['qualified'];baseline.append(dict(stem=stem,model_max_difference=float(np.nanmax(abs(x['model']-y['auxiliary_observed_field']))),broad_correction_max_difference=float(np.max(abs(x['error'][q]-y['correction_error'][q])))))
save('D0_baseline_reproduction.json',dict(results=baseline,reason='Full-precision bilinear scipy sampler replaces quantized OpenCV interpolation in the auxiliary model; broad correction difference below0.008G. All prior pass/fail conclusions unchanged.',PASS=all(r['broad_correction_max_difference']<.01 for r in baseline)))
table='\n'.join('|'+r['stem']+'|'+str(r['sectors'])+'|'+f"{r['predicted_phase_rms']:.3f}"+'|'+('sí' if r['solar_eligible'] else 'no')+'|' for r in test)
comparison=[]
for stem in TEST:
    row=[stem]
    for variant in variants:
        r=next(r for r in completion['results'] if r['stem']==stem and r['variant']==variant and r['mask_from_RAW']=='572A2983')['regions'][2];row.append(f"{r['median_abs_G']:.2f} / {r['p95_abs_G']:.2f}")
    comparison.append('|'+ '|'.join(row)+'|')
report=f'''# Referències solar i lunar: assaig de geometria

**V49 continua vigent. No hi ha nova font fotogràfica ni PSB; la correcció geomètrica assajada no passa la prova del llimb.** Originals, CameraRaw i documents vius no s’han editat. El goal global continua actiu.

S’ha separat el registre de la corona del contorn lunar per comprovar la discrepància de llum prop de les protuberàncies. El candidat ample anterior queda congelat: p={P_WIDE}, gaussiana addicional12px, nucli estret retingut. No s’ha tornat a buscar aquest coeficient.

## Mesura externa al llimb a recuperar

Referència solar:33RAW curts, excloent les16preses objectiu. Cada registre es calcula només a470–650px, amb comprovació entre meitats angulars.15/16curts passen el criteri de coherència;2985falla amb0,419px entre meitats. Dels3llargs, només2980passa;2978falla amb0,489px.2983no té prou suport no censurat en aquesta obertura i queda **sense estimació**, no amb un desplaçamentzero validat. El registrador explicita aquesta absència i exigeix1000mostres per ajust.

Fase lunar: mostres verdes natives, integració de l’àrea de píxel3×3, perfil amb mescla òptica ampla congelada i fons local acotat. Només r≥450px.435–449queda reservat. L’amplada descriu aquest perfil, no unaPSF única.12preses calibren una fase angular comuna;4preses reservades proven si el registre solar en prediu la fase lunar. La fase comuna és empírica i **no** s’ha convertit en màscara de Photoshop.

|RAW reservat|Sectors qualificats|RMS de fase predita(px)|Registre solar qualificat|
|---|---:|---:|---|
{table}

**0/4passen** el límit predeclarat0,25px. Per tant, un sol lligam entre les referències solar i lunar no basta per assignar geometria precisa als llargs censurats. Els desplaçaments residuals de les preses són diagnòstics, no una correcció aplicada a les fonts.

## Predicció de llum oculta, amb comprovació espacial reservada

Quatre variants aniuades: base anterior; registre/guany solar; fase lunar mesurada independentment a r≥450; fase més amplada mediana del perfil. Cada variant es comprova amb les mateixes4preses i les mateixes3màscares de saturació reals. El model només estima llum auxiliar dins de l’operador ample; cap píxel completat és textura recuperada.

Errors mediana absoluta/P95absolut, enG, a435–449px amb la màscara real de2983(10s):

|RAW|Base|Solar|Fase lunar|Fase i amplada|
|---|---:|---:|---:|---:|
{chr(10).join(comparison)}

Totes4variants passen24/36comprovacions; **cap passa les12comprovacions435–449**. A3003, mesurar la fase baixaP95de133,31a53,12G, però a2967l’empitjora de40,38a94,54G. Variar l’amplada no resol aquesta discrepància. Els límits5G de mediana,25G deP95i80%suport es mantenen. El suport és complet en aquests casos: ara el problema és de predicció, no manca de cobertura del càlcul.

El canvi d’interpolador de la base, d’OpenCV quantitzat a bilineal de precisió completa, altera la correcció ampla menys de0,008G; les conclusions anteriors es reprodueixen. Rebut `D0_baseline_reproduction.json`.

## Què queda après i quin pas té sentit

La corona exterior està registrada amb coherència en les preses qualificades, però aquesta dada no fixa prou bé la transició lunar. Tampoc una fase lunar global mesurada i una amplada de perfil arreglen el completat. **No atribuir-ho exclusivament a un desplaçament ni reprendre traslacions/elispses lliures.** Els perfils locals poden confondre fase, corona pròxima i ales intermèdies de la resposta òptica; les protuberàncies fan especialment feble la hipòtesi de fons exterior pla. Això és una limitació del model, no una causa única demostrada.

El pas següent ha de comprovar una resposta òptica intermèdia entre el nucli≈1px i la component ampla12px, amb predicció temporal reservada i control angular. La component ampla sola es va qualificar sobretot a426–445; no prova tota la resposta a450px. Cal declarar la nova hipòtesi i els jutges abans d’ajustar, sense tornar a utilitzar les mateixes proves com si fossin dades verges. Alternativament, el model solar local necessita una dada de suport addicional real; no una continuació més flexible seleccionada pels errors dels targets.

**Límits:** calibres i metadades compartits; els4RAW ja havien participat en el diagnòstic anterior. La prova de fase usa RAWexclosos de la referència, però el completat amb fase mesurada és withholding espacial dins de cada presa. No qualifica automàticament els llargs. No hi ha detall nou acreditat, equivalència ambDHS, resta de vel promoguda ni nova porta Photoshop.

Figura `D0_geometry_review.png`. Plans `PLAN.json`, `B0_plan.json`, `C0_plan.json`; mesures `A1_solar_registration.json`, `B0_lunar_profiles.json`, `B1_reference_comparison.json`; comprovació `C0_geometry_completion.json`. Tots els scripts són reproduïbles en aquest directori de recerca sotaSERIAL_WRITES.
'''
(OUT/'RESULTAT.md').write_text(report)
(HERE/'REPRESA.md').write_text(f'''# Represa — geometria de completat

V49 vigent. Informe `{OUT/'RESULTAT.md'}`; manifest `{HERE/'delivery_manifest.json'}`.

No repetir A0–C0:33curts fan referència solar;15/16curts qualificats,2985no. Llargs:2980sí,2978no,2983sense suport. La fase lunar nativa r≥450 no queda predita per la corona:0/4targets passen0,25px. Correcció auxiliar amb fase mesurada:24/36comprovacions; totes12de435–449fallen. A3003 milloraP95de133a53G, a2967empitjora40a95G. Amplada mediana no ho arregla. Cap font/PSB canviat.

Nou assaig justificable: resposta intermèdia entre nucli≈1px i ala12px, comprovada entre epochs i angles, amb nova hipòtesi/gates i límits explícits de reutilització de dades. Congelar pample={P_WIDE}; no reprendre desplaçaments globals/elispses o completats flexibles seleccionats pels mateixos errors. Conservar CameraRaw i V49. Consultar l’informe abans de triar una nova parametrizació.

Runtime `/Users/USUARI/.venvs/eines-ia-py312/bin/python`; envPYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1. Root canònicDownloads; actiusDesktop. Llegir autoritat viva, comprovarlock, adquirir un claim nou per mutar. No Git, dispositius, agents nous ni imatges generatives.
''')
print('REPORT WRITTEN; geometry/width rejected; V49 preserved',flush=True)
