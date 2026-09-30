"""Summarize every candidate, including negative stress tests and real profiles."""
from diffraction_common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def read(name):return json.loads((OUT/name).read_text())
a0=read('A0_diffraction_prediction.json');a2=read('A2_actual_phase_stack.json');a4=read('A4_joint_phase_reconstruction.json');a5=read('A5_joint_sensitivity.json');b0=read('B0_profile_witness.json');b1=read('B1_spectral_witness.json')
fig,axs=plt.subplots(2,2,figsize=(13,9),layout='constrained')
ax=axs[0,0]
for row in a0['pupil_rows']:ax.loglog(row['radii_world_px'],row['energy_outside'],'o-',label=f"Airy {row['wavelength_nm']:.0f} nm")
old=a0['previous_cascade_energy_outside'];ax.loglog(old['radii_world_px'][:7],old['energy'][:7],'k--',label='Cascada anterior 4/12 px')
ax.set(xlabel='Radi (píxels físics)',ylabel='Fracció d’energia fora del radi',title='Predicció òptica; no és una PSF mesurada',ylim=(3e-4,.2));ax.legend(fontsize=8);ax.grid(alpha=.2)
ax=axs[0,1];parts=['all','early','late'];labels=['Totes','Inici','Final'];xx=np.arange(3)
for offset,(name,rows,key) in enumerate([('Inversió per presa',a2['tests'],'full'),('Reconstrucció conjunta',a4['tests'],None)]):
    vals=[next(r['rms_G'] for r in rows if r['wavelength_nm']==550 and r['scene']=='baseline' and r['part']==p and (key is None or r['operator']==key)) for p in parts]
    ax.bar(xx+(offset-1)*.24,vals,width=.23,label=name)
case=next(r for r in a5['cases'] if r['case']=='phase01');ax.bar(xx+.24,[next(r['rms_G'] for r in case['tests'] if r['part']==p) for p in parts],width=.23,label='Conjunta + error simulat 0,01 px')
ax.axhline(2,color='k',ls='--',lw=1,label='Límit numèric 2 G');ax.set(yscale='log',xticks=xx,xticklabels=labels,ylabel='RMS G del fantoma',title='La solució exacta és sensible a l’alineació');ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
ax=axs[1,0];epochs=[r['epoch'] for r in b0['comparisons']];x=np.arange(6)
for lam,color,source in [(500,'#4d8ac0',b1['endpoints'][0]),(550,'#253b56',b0),(600,'#d1813c',b1['endpoints'][1])]:
    vals=[100*next(r['reduction_fraction'] for r in source['comparisons'] if r['epoch']==e) for e in epochs];ax.plot(x,vals,'o-',color=color,label=f'{lam} nm')
ax.axhline(5,color='k',ls='--',lw=1,label='Criteri 5% a cada grup');ax.axhline(0,color='gray',lw=.6);ax.set(xticks=x,xticklabels=['C2','1','4','6','7','C3'],ylabel='Reducció d’error respecte del model gaussià (%)',title='Perfils reals: resultat no qualificat; model inadequat');ax.legend(fontsize=8);ax.grid(alpha=.2)
ax=axs[1,1];profiles=read('B0_native_profiles.json');d=np.array(profiles['distance']);frame=next(r for r in profiles['frames'] if r['stem']=='572A2960');p=frame['profiles'][6];valid=np.array(p['valid'])
ax.plot(d[valid],np.array(p['mean'])[valid],'.',ms=3,label='Mostres natives agregades')
for name,label in [('gaussian','Nucli gaussià'),('airy550','Nucli + pupil·la 550 nm')]:ax.plot(d,p['fits'][name]['prediction'],label=label)
ax.axvspan(-25,-6,color='#52ab8b',alpha=.16,label='Franja exclosa de l’ajust');ax.set(xlim=(-34,5),ylim=(0,60000),xlabel='Distància al contorn heretat (px)',ylabel='Radiància G',title='Exemple C2: 572A2960, sector 6 (no representa tot el llimb)');ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.suptitle('Earthshine · diagnòstic de difracció i mostreig · V49 sense canvis',fontsize=15);fig.savefig(OUT/'F0_diffraction_review.png',dpi=160);plt.close(fig)
summary=dict(profile_model_adequacy_FAIL=True,numerical_joint_PASS=all(r['PASS'] for r in a4['tests']),numerical_joint_tests=len(a4['tests']),numerical_joint_max_baseline_rms=max(r['rms_G'] for r in a4['tests'] if r['scene']=='baseline'),sensitivity_no_candidate_qualified=True,real_profile_PASS=b0['PASS'],real_profile_epochs_PASS=sum(r['PASS'] for r in b0['comparisons']),real_profile_epochs=6,real_profile_sectors_no_worse=sum(r['no_worse'] for r in b0['sectors']),real_profile_sectors=72,all_spectral_endpoints_FAIL=all(not r['PASS'] for r in b1['endpoints']),new_source=False,new_PSB=False)
save('F0_summary.json',summary)
table='\n'.join('|'+r['epoch']+'|'+f"{100*r['reduction_fraction']:.2f}%"+'|'+('PASS' if r['PASS'] else 'FAIL')+'|' for r in b0['comparisons'])
text=f'''# Difracció, mostreig i perfils natius — 12-09-2026

**V49 preservada. Cap font fotogràfica ni PSB nou. El contorn complet continua pendent.** Aquesta ronda discrimina una hipòtesi física i una via de reconstrucció; els resultats numèrics favorables no es presenten com a detall lunar recuperat. Camera Raw i documents vius no s’han tocat.

## Predicció independent

La fitxa oficial del [Vixen VSD90SS](https://www.vixen.co.jp/product/26131_4/) declara una obertura nominal de 90 mm. S’utilitza l’escala **mesurada** 2,1494813525884373 arcsec/píxel del rebut F1.2 de la cadena, no la focal nominal per deduir-la. La pupil·la ideal és circular i sense obstrucció; el nucli atmosfèric/desconegut es conserva. 500/550/600 nm són una banda de sensibilitat declarada, no la resposta espectral mesurada del verd Canon. No s’escull longitud d’ona segons el millor halo.

A 550 nm, l’energia teòrica fora de 4/12 px és 2,9425%/0,9978%. La cascada anterior de dues gaussianes donava 2,9537%/0,8839%. La semblança justifica contrastar la difracció, però no identifica la PSF real. A grans radis les cues són diferents. **No sumar automàticament Airy i la cascada 4/12:** podrien comptar dues vegades la mateixa llum dispersada.

## Prova numèrica i sensibilitat

El fantoma conegut té un disc de radi 120 px, fons solar de 100000 G, protuberància sintètica local i injeccions sinusoidals de 8/16/32 px. La integració del píxel és un sinc físic, el nucli fix té sigma 0,97 px i la frontera és periòdica. No és cap font astronòmica ni simulació completa dels moviments reals.

A1: la inversió directa sobre una presa mostrejada falla el límit de 2 G al contorn (RMS 4,17–5,28 G). La variant suavitzada supera una prova contra un **objectiu també suavitzat**, però no recupera tota la imatge objectiu. A2 ho comprova amb el mateix objectiu complet per a tothom: el seu RMS és de centenars de G. Aquell PASS limitat no autoritza la variant suavitzada.

A2/A3 utilitzen les fases subpíxel reals i pesos congelats de 21 camps natius íntegrament vàlids. Exclouen els set camps D0 amb algun píxel censurat, només per qualificar l’aritmètica. No és una selecció acceptable per reemplaçar totes les exposicions de l’earthshine. La inversió per presa seguida d’apilat baixa el RMS a 1,92 G a 550 nm en el conjunt, però la meitat inicial queda a 2,60 G. La fórmula amb prior blanc de potència no resol el conjunt de criteris.

A4 resol conjuntament quatre components de freqüència que el mostreig havia barrejat, amb les fases reals i sense prior d’espectre lunar. **36/36 proves numèriques PASS**, RMS màxim {summary['numerical_joint_max_baseline_rms']:.6f} G; conserva les injeccions. És una graella interna de qualificació, no un canvi de FOV ni resolució del producte. El condicionament ponderat és 4,92/15,11/6,91 per conjunt/inici/final. L’amplificació de variància d’alguns coeficients arriba a 24 vegades el cas d’una única mitjana ideal; no és una mesura de soroll del PSB final.

**A5 impedeix aplicar-la directament.** Amb només 0,01 píxel u/v d’error simulat RMS, la reconstrucció conjunta deixa RMS 28,38/54,99/37,35 G. Variar sigma amb RMS 0,05 px dona 38,99/80,59/30,64 G; variar un 1% la brillantor de la protuberància sintètica dona 5,29/28,03/7,03 G. Totes aquestes variants fallen el mateix criteri de 2 G. No són mesures d’error de les captures: són proves de sensibilitat que refuten una aplicació ingènua sobre una escena assumida constant.

## Contrast amb les captures reals

B0 forma perfils de 12 sectors, amb bins de 0,5 px, directament des de mostres verdes natives vàlides. No interpola radiància ni crea textures. Ajusta cada presa/sector només a distàncies <=−27 px i >=−3 px respecte del contorn heretat. La franja −25..−6 px queda fora de l’ajust. Es comparen dos models amb els mateixos sis paràmetres de resposta i intensitat: nucli gaussià i nucli amb pupil·la fixa. El píxel quadrat es projecta segons la normal del sector.

Les cinc preses vàlides de les èpoques 2/5 entrenen un residu lunar comú; les altres setze comproven sis èpoques. Cada model té el seu propi residu lunar de referència i es puntua en les mateixes observacions. Els perfils agrupen textura i brillantor tangencial; la simplificació unidimensional no és una reconstrucció del terreny. Les dades són reservades per aquest ajust, però reutilitzades respecte de rondes anteriors, no completament verges.

Reducció d’error quadràtic ponderat del model 550 nm respecte del gaussià:

|Època|Reducció|Criteri >=5%|
|---|---:|---|
{table}

**4/6 èpoques PASS i 50/72 sectors no empitjoren més del 2%; criteri global FAIL.** Els extrems espectrals 500/600 nm també fallen les mateixes dues èpoques. No es tria el millor valor. Tretze dels 252 ajustos Airy i cinc gaussianes arriben a un límit de sigma/desplaçament; els rebuts els identifiquen. El sigma gaussià és un paràmetre condicionat a la geometria i al model, no una mesura pura del seeing.

La prova no cobreix els últims sis píxels, ni les exposicions llargues censurades, ni la corroboració entre telescopis. Aquesta reducció d’error no s’accepta com a evidència física: l’auditoria B2, motivada per la figura, detecta inadequació del model exterior lineal. 103/252 ajustos Airy tenen chi2 mitjà d’entrenament >5, i 71/252 forcen un pendent lunar discrepant >3 sigmes condicionals respecte de les dades profundes. Són indicadors retrospectius, no nous gates predeclarats. A C2, sector6 de 572A2960, el model arriba a desenes de milers de G dins la Lluna on la mitjana observada és de pocs milers. La corona exterior té un pic i una caiguda que la recta no pot representar. No usar els percentatges B0/B1 per identificar la PSF o promoure una resta. No s’han promogut els desplaçaments dels ajustos a la geometria ni restat aquests perfils de cap fotografia.

## Continuació acotada

Conservar D0 i l’operador natiu. Eliminar de les candidates la inversió conjunta que pressuposa escena/seeing constants i la variant suavitzada presentada com a recuperació completa. No repetir A0–A5 ni B0/B1. B2 refusa el model exterior lineal; no corregir-lo simplement restringint a mà el pendent lunar. La següent prova ha d’incloure resposta i llum solar **pròpies de cada presa** abans d’apilar la radiància lunar comuna, amb una comprovació que reservi els píxels del llimb; no ajustar un radi o un vel perquè desaparegui l’error sobre els mateixos targets.

Un model 2D amb pupil·la fixada i llum solar temporal mesurada és una possible continuació, encara no implementada ni qualificada. Ha de superar primer un fantoma amb moviments i variació de nucli, després els targets reals i la censura dels llargs. Si no supera aquests passos, no crear una V50 ni reemplaçar la font conservant només les curtes. No reduir llindars, no aplicar Airy damunt d’una correcció equivalent de 4/12 px, no alterar Camera Raw ni afegir màscares cosmètiques.

Rebuts: PLAN, A0–A5, B0/B1, F0_summary i F0_diffraction_review.png. Les figures de fantomes serveixen exclusivament per verificar aritmètica. El producte continua Earthshine_V49.psb. Per petició posterior de Pere, es prepara un punt de revisió visible amb còpies byte a byte V48/V49, sense correcció nova. Els rebuts R0/R1/R2 documenten la porta Photoshop i els documents vius preservats. Aturar la recerca quan la revisió quedi oberta; l’objectiu fotogràfic global continua incomplet.
'''
(OUT/'RESULTAT.md').write_text(text)
(HERE/'REPRESA.md').write_text('# Represa acotada\n\nLlegir RESULTAT.md i delivery_manifest.json d’aquesta ronda. V49 intacta; goal actiu.\n\n'+text.split('## Continuació acotada\n\n')[1])
print('REPORT',summary,flush=True)
