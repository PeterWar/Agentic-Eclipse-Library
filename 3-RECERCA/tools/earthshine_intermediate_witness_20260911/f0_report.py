"""Summarize intermediate-response evidence and native-operator qualification."""
from intermediate_common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
linear=json.loads((OUT/'B0_intermediate_witness.json').read_text());physical=json.loads((OUT/'B1_physical_cascade.json').read_text());cross=json.loads((OUT/'E0_physical_cascade.json').read_text());numeric=json.loads((OUT/'C0_native_lattice_check.json').read_text());numeric_cross=json.loads((OUT/'C1_native_lattice_check.json').read_text());native=json.loads((OUT/'D0_native_fields.json').read_text());assert len(native['frames'])==28 and all(all(r['exact_identity'].values()) for r in native['frames']);order=['vixen_0','vixen_1','vixen_4','vixen_6','vixen_7','vixen_8'];labels=['C2 nou','època1','època4','època6','època7','C3 nou']
fig,ax=plt.subplots(2,2,figsize=(14,9),layout='constrained');x=np.arange(6)
for i,(name,z) in enumerate([('Aproximació',linear),('Cascada',physical),('Verds separats',cross)]):
    lookup={r['epoch']:r['reduction_percent'] for r in z['epochs']};ax[0,0].bar(x+(i-1)*.24,[lookup[e] for e in order],.24,label=name)
ax[0,0].axhline(5,color='black',ls='--');ax[0,0].set(xticks=x,xticklabels=labels,ylabel='Reducció de l’error de predicció (%)',title='Comparació temporal · mínim predeclarat: 5% per grup');ax[0,0].legend(fontsize=8)
for i,(name,z) in enumerate([('Cascada',physical),('Verds separats',cross)]):
    vals=[z['p4']]+[r['p'] for r in z['angular_halves']];ax[0,1].plot([0,1,2],np.array(vals)*100,'o-',label=name)
ax[0,1].set(xticks=[0,1,2],xticklabels=['Tots els sectors','Meitat angular A','Meitat angular B'],ylabel='Fracció p4 del model (%)',title='Component de 4 px · p12 es manté congelat');ax[0,1].legend(fontsize=8)
ops=['world_predictors','native_lattice','cross_green'];names=['Predictor interpolat','Graella nativa','Verd oposat'];alltests=numeric['tests']+numeric_cross['tests']
for j,stem in enumerate(['572A2976','572A2994']):
    vals=[next(r['rms_G'] for r in alltests if r['stem']==stem and r['scene']=='baseline' and r['operator']==op) for op in ops];ax[1,0].bar(np.arange(3)+(j-.5)*.32,vals,.32,label=stem)
ax[1,0].axhline(2,color='black',ls='--');ax[1,0].set(yscale='log',xticks=np.arange(3),xticklabels=names,ylabel='RMS al contorn conegut (G)',title='Prova sintètica de l’operador · límit: 2 G');ax[1,0].legend(fontsize=8)
rows=[]
for ep,label in zip(order,labels):
    r=next(r for r in cross['epochs'] if r['epoch']==ep);rows.append([label,f"{r['reduction_percent']:.2f}%",'sí' if r['reduction_percent']>=5 else 'no'])
ax[1,1].axis('off');table=ax[1,1].table(cellText=rows,colLabels=['Test entre verds','Millora','Supera 5%'],loc='center',cellLoc='center');table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,1.7);ax[1,1].set_title('Resultat als RAW · encara no és recuperació de textura')
fig.suptitle('Earthshine: resposta intermèdia i càlcul sobre píxels nadius',fontsize=15);fig.savefig(OUT/'F0_intermediate_review.png',dpi=170);plt.close(fig)
summary=[]
for ep,label in zip(order,labels):
    a=next(r for r in physical['epochs'] if r['epoch']==ep);b=next(r for r in cross['epochs'] if r['epoch']==ep);summary.append(f"|{label}|{a['reduction_percent']:.2f}%|{b['reduction_percent']:.2f}%|{b['rotated_reduction_percent']:.2f}%|")
passes=sum(r['reduction_percent']>=5 for r in cross['epochs']);nsectors=len(cross['sectors']);goodsectors=sum(r['no_worse'] for r in cross['sectors']);count=sum(r['native_annulus_samples'] for r in native['frames']);p4=cross['p4'];limits=json.loads((OUT/'PLAN.json').read_text())['limitations'];decision='La cascada passa el criteri temporal predeclarat en aquest control.' if cross['temporal_cascade_PASS'] else 'La cascada encara no passa el criteri temporal predeclarat en tots els grups.'
report=f'''# Resposta intermèdia i operador sobre la graella nativa

**V49 vigent i preservada. Cap nova font fotogràfica ni PSB.** El goal global continua actiu. Aquest assaig ha identificat una limitació numèrica corregible i ha contrastat una component òptica intermèdia amb mesures entre verds separats.

## Què s’ha mesurat

La component ampla anterior queda congelada: p12={P12}, sigma addicional de 12 px. S’ha declarat una única component intermèdia de 4 px abans de mirar els seus resultats. El nucli estret no es deconvoluciona. Vuit preses entrenen, dotze tornen a actuar com a comprovació retrospectiva, i vuit preses de prop de C2/C3 són noves per a aquest ajust temporal. Cap d’aquestes dades és completament verge respecte de tot el projecte.

S’utilitzen mostres verdes natives a 415–449 px, amb guarda de 6 px respecte del contorn heretat. S’agreguen en cel·les de 5 px només per a l’estadística. Cada cel·la conserva una radiància lunar desconeguda; no es força la Lluna a zero. Els plans de les preses reservades es calibren només a 415–423 px i es comprova 426–449 px. El control gira el predictor 90 graus mantenint l’època.

El testimoni aproximat dona coeficient 0,02483. La cascada física H12(H4(X)) dona p4={physical['p4']:.8f}; X reté el nucli estret. Les meitats angulars donen {physical['angular_halves'][0]['p']:.8f}/{physical['angular_halves'][1]['p']:.8f}. És un model condicionat, no una PSF única ni percentatge de detall recuperat. La resta de la sèrie inversa queda acotada a {physical['neumann_bound_G']:.6f} G; això és error de truncament, no error del model físic.

## Error d’interpolació identificat amb una escena coneguda

La mateixa escena de validació, la mateixa obertura del píxel i dues fases natives permeten separar l’error de càlcul de l’error físic. Calcular la correcció amb predictors interpolats al llenç deixa RMS 5,67/5,74 G prop del contorn conegut i falla el límit de 2 G. Convolucionar directament sobre la graella verda nativa baixa el RMS a aproximadament 0,00093 G. La graella verda és quadrada, girada i de pas √2; per això el sigma natiu és el sigma físic dividit per √2. Cap radiància observada s’interpola en aquest operador.

La comprovació amb només el verd oposat dona RMS 0,113/0,142 G, també per sota del límit. Els senyals de prova de 8/16/32 px conserven el guany i passen les toleràncies declarades en les dues fases. **Són fantomes numèrics, mai fonts lunars ni prova de detall astronòmic recuperat.** Els rebuts C0/C1 inclouen totes les xifres i el control d’integració GL4/GL6.

S’han reconstruït camps natius complets de 28 RAW amb exactament la calibració existent. Els {count:,} valors de l’anell congelat coincideixen en g, variància, validesa, qualitat i coordenades; els 28 SHA dels RAW també coincideixen. Només són nous caches diagnòstics. Originals, màscares, filtres Camera Raw i projectes de Photoshop intactes.

## Control del soroll entre els dos verds

Un predictor suavitzat que incorpora el mateix píxel objectiu pot predir una part del seu soroll. Per comprovar-ho, cada verd es prediu amb l’altre verd. Es mantenen dues observacions separades per cel·la; no s’agrupen abans de mesurar l’error, perquè això reintroduiria el mateix soroll. Són fotons/píxels diferents, però encara comparteixen calibració i possibles residus FPN. No equival a un segon telescopi.

Amb aquest control, p4={p4:.8f}; meitats angulars {cross['angular_halves'][0]['p']:.8f}/{cross['angular_halves'][1]['p']:.8f}. Reducció de l’error respecte de la base amb només H12, dins del suport vàlid de cada assaig:

|Grup temporal|Cascada amb predictors interpolats|Verd oposat natiu|Control girat del verd oposat|
|---|---:|---:|---:|
{chr(10).join(summary)}

El control entre verds supera el 5% en {passes}/6 grups; {goodsectors}/{nsectors} sectors no empitjoren més d’un 2%. {decision} Els llindars no s’han rebaixat. La comparació entre columnes canvia mostreig, suport i tractament del soroll: no és una mesura aparellada de millora fotogràfica. Cada percentatge correspon al seu propi control zero.

## Decisió i continuació

Conservar l’operador natiu qualificat i els camps RAW exactes: no repetir la correcció intermèdia amb predictors interpolats. Conservar també els resultats negatius o incomplets del criteri temporal. Abans de promoure una correcció cal resoldre la variació que queda entre èpoques i el model de llum oculta dels llargs; no barrejar curts corregits amb llargs sense qualificar. La dispersió intermèdia ha de continuar sent una hipòtesi física condicionada, amb comprovació independent, no un retoc manual del contorn.

El següent pas ha d’utilitzar aquesta aritmètica nativa per discriminar resposta del nucli, ales òptiques i llum solar temporal. No tornar a ampliar una màscara perquè el llimb sembli més fosc. No declarar recuperat tot el llimb, equivalència amb DHS, ni preservació de textures noves sense el jutge entre telescopis i la porta Photoshop. No hi ha una V50 en aquest assaig.

Fonts metodològiques consultades: els treballs de [Norton et al. sobre HMI](https://arxiv.org/abs/2511.13348) i de [Courrier et al. sobre IRIS](https://link.springer.com/article/10.1007/s11207-018-1347-9) utilitzen dades d’ocultacions o trànsits per estimar/comprovar la resposta instrumental. No se n’importen paràmetres, models de telescopi ni la hipòtesi d’una Lluna sense earthshine.

Rebuts: `PLAN.json`, `B0_intermediate_witness.json`, `B1_physical_cascade.json`, `C0_native_lattice_check.json`, `C1_native_lattice_check.json`, `D0_native_fields.json`, `D1_crossgreen_plan.json`, `E0_physical_cascade.json`. Figura `F0_intermediate_review.png`.
'''
(OUT/'RESULTAT.md').write_text(report)
(HERE/'REPRESA.md').write_text(f'''# Represa — resposta intermèdia i operador natiu

V49 vigent. Informe `{OUT/'RESULTAT.md'}`. Manifest `{HERE/'delivery_manifest.json'}`. Goal global actiu.

Resultats que no cal repetir: p12 congelat; component4px amb p4 interpolat={physical['p4']:.8f}, p4 entre verds={p4:.8f}. Control temporal entre verds: {passes}/6 grups superen5%, {goodsectors}/{nsectors} sectors no empitjoren2%; PASS global={cross['temporal_cascade_PASS']}. Detalls exactes aE0. No és una nova font qualificada.

Descobriment numèric: predictors interpolats fallen l’escena coneguda (RMS≈5,7G); convolució nativa≈0,00093G; verd oposat0,113/0,142G. Els senyals coneguts passen. Conservar l’operador sobre la graella u,v de pas√2; no interpolar la radiància abans de calcular la correcció.28camps natius D0, amb {count} mostres congelades exactes i28SHA deRAW comprovats, disponibles per evitar una nova lectura/calibració.

D1manté verds com a files separades percel·la, predictor de l’altre verd; no fer la mitjana abans del score. Calibració/FPNcompartits continuen com a límit; no és el jutge entre telescopis. Nova prova abans de qualsevol font/PSB: resposta òptica completa i llum oculta dels llargs, amb criteris independents i sense perdre detall de les protuberàncies. No reprendre màscares manuals, el·lipses lliures o ajustos triats pels mateixos errors.

Runtime `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1. Llegir autoritat viva i adquirir un claim nou abans de mutar. Codi aDownloads i actius aDesktop. No Git, maquinari, agents nous o generació d’imatges.
''')
save('F0_summary.json',dict(p12=P12,p4_interpolated=physical['p4'],p4_crossgreen=p4,temporal_crossgreen_PASS=cross['temporal_cascade_PASS'],epoch_passes=passes,epochs=6,no_worse_sectors=goodsectors,sectors=nsectors,native_fields=28,exact_native_samples=count,native_operator_PASS=all(r['PASS'] for r in numeric['tests'] if r['operator']=='native_lattice'),crossgreen_operator_PASS=all(r['PASS'] for r in numeric_cross['tests']),source_or_PSB_changed=False))
print('REPORT WRITTEN',passes,'of6 epochs;',goodsectors,'of',nsectors,'sectors;V49 preserved',flush=True)
