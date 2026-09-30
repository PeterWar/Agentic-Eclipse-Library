"""Measured report and scientific figure for the scatter candidate."""
from scatter_common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
model=json.loads((OUT/'B1_physical_mixture.json').read_text());injection=json.loads((OUT/'C0_native_injection.json').read_text());completion=json.loads((OUT/'D2_refined_validation.json').read_text());old=json.loads((OUT/'D1_completion_validation.json').read_text());witness=json.loads((OUT/'B0_temporal_witness_fit.json').read_text())
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False});fig,axs=plt.subplots(1,3,figsize=(15,5),layout='constrained')
epochs=model['new_epoch_summary'];names=['Primerenca','Abans de C3 · A','Abans de C3 · B','Abans de C3 · C'];x=np.arange(4);axs[0].bar(x,[r['reduction_percent'] for r in epochs],color='#197f8b');axs[0].set(xticks=x,xticklabels=names,ylabel='Reducció de l’error ponderat [%]',title='Prediccions en quatre èpoques reservades',ylim=(0,65));axs[0].tick_params(axis='x',rotation=22);axs[0].axhline(5,color='#888',ls=':',label='Llindar declarat');axs[0].legend(fontsize=8)
for stem,color,marker in [('572A2976','#197f8b','o'),('572A2994','#9653a0','s')]:
    rr=[r for r in injection['tests'] if r['stem']==stem and r['scene']!='baseline'];axs[1].plot([int(r['scene'][7:]) for r in rr],[r['relative_RMS_error'] for r in rr],marker=marker,color=color,label=stem)
axs[1].axhline(.01,color='#888',ls=':',label='Límit de la injecció');axs[1].set(xlabel='Longitud d’ona de la textura [píxels]',ylabel='Error relatiu de la textura recuperada',yscale='log',ylim=(1e-7,3e-2),xticks=[8,16,32],title='Conservació del detall del nucli òptic');axs[1].legend(fontsize=8)
rr=[r for r in completion['frames'] if r['mask_from_RAW']=='572A2983'];x=np.arange(len(rr))
for j,(radius,label,color) in enumerate([([415,435],'415–435 px','#197f8b'),([435,449],'435–449 px','#c1712c')]):
    vals=[next(a['p95_abs_G'] for a in r['regions'] if a['radius']==radius) for r in rr];axs[2].bar(x+(j-.5)*.3,vals,width=.29,label=label,color=color)
axs[2].axhline(25,color='#888',ls=':',label='Límit declarat');axs[2].set(xticks=x,xticklabels=[r['stem'][-4:] for r in rr],ylabel='Percentil95 de l’error de correcció [G]',xlabel='Preses curtes excloses del model de completat',title='Saturació: el llimb encara no passa');axs[2].legend(fontsize=8)
for ax in axs:ax.grid(axis='y',alpha=.18)
fig.suptitle('Dispersió ampla: candidat òptic positiu; completat de saturació pendent',fontsize=14);fig.savefig(OUT/'E0_scatter_review.png',dpi=140);plt.close(fig)
text=f'''# Earthshine — dispersió ampla i dades saturades

**Hi ha un candidat de correcció a l’origen amb evidència positiva, però encara no es pot aplicar de manera validada a totes les exposicions. V49 continua intacta; no s’ha creat V50.** El model explica part del vel proper al llimb mitjançant dispersió ampla, sense deconvolucionar el nucli òptic ni retocar màscares. La seva limitació actual és estimar aquesta llum en les preses amb corona saturada.

![Resultats de la dispersió i del completat](</Users/USUARI/Downloads/Eclipse 2026/output/earthshine_scatter_witness_20260911/E0_scatter_review.png>)

## Evidència nova

- Dos instants d’entrenament: Vixen2973–2976 i2991–2994. Dotze exposicions d’altres quatre èpoques queden reservades. Dades verdes natives, agregades en cel·les fixes de5px només com a estadístic; cap nou camp fotogràfic o remostreig de fonts. Les prediccions àmplies es calculen sense pesos de brillantor sobre radiància vàlida. Es rebutgen posicions amb més de0,5% de massa del nucli sense dada.
- A cada cel·la s’ajusta una radiància lunar comuna i, per captura, un pla de fons. En les preses reservades aquest pla només es calibra dins415–423px; la prova utilitza426–445px. Això separa els canvis globals de brillantor de la variació del vel amb la corona observada.
- El testimoni lineal amb predictors gaussians12/24px selecciona aproximadament0,0140/0. El control amb predictors girats90° selecciona zero i no millora. Les meitats angulars donen0,01459/0,01354 per al primer predictor. No són intervals de confiança ni fraccions físiques per si mateixos.
- La versió física proposa **Y=((1−p)I+pG12)X**, onX encara conté el nucli òptic estret real. Resultatp={model['p']:.9f}, és a dir, aproximadament1,406% en aquest model condicionat. No demostra una PSF única ni que el mecanisme sigui exclusivament instrumental. La gaussiana12px és l’eixamplament addicional respecte del nucli, no el sigma total d’una PSF mesurada.

| Època reservada | Error inicial | Error amb el model físic | Reducció |
|---|---:|---:|---:|
'''
for r in epochs:text+=f"| {r['epoch']} | {r['weighted_MSE']['zero']:.5f} | {r['weighted_MSE']['physical']:.5f} | {r['reduction_percent']:.2f}% |\n"
text+=f'''
47/48 combinacions d’època i sector no empitjoren més del2%. Es compleix el criteri declarat de millora a cadascuna de les quatre èpoques. És evidència de predicció temporal del vel, **no una mesura del percentatge de detall recuperat**. Els pesos incorporen el factor FPN històric; les dependències de calibració i covariàncies completes no estan modelades.

## Inversa i conservació del detall

La inversa es calcula amb quatre termes de la sèrie de Neumann. Per al p ajustat, la cota del terme omès és inferior a{model['neumann_remainder_max_G']:.6f}G en els camps observats; no és una cota de l’error del model físic. El terme principal continua sent la mostra nativa, i els termes correctors són suaus. No s’inverteix una PSF uniforme de1px ni s’augmenta arbitràriament l’enfocament.

Vuit proves de fantoma passen: dues fases reals de la graella verda, lluna650G/corona100.000G amb una protuberància de prova, i textures afegides de8,16,32px. S’integra la superfície del píxel natiu. L’error de recuperació del nucli conegut és0,539/0,545G RMS; GL4 versusGL6 canvia menys de0,042G. L’error relatiu de les textures és menor de0,001%. **Aquests fantomes només validen l’operador: no s’ha introduït cap textura sintètica a les imatges de l’eclipsi.**

## Per què no s’ha publicat una nova font encara

Per corregir una mostra lunar vàlida cal conèixer també la llum solar que el nucli ample hi dispersa. Si la corona del mateix fotograma està saturada, no és vàlid tractar els píxels censurats com si fossin negres ni donar per coneguda una radiància reconstruïda.

**D0/D1:** es construeixen camps auxiliars lunar i solar només amb55preses, excloent les12de prova. El Sol es registra separadament. En amagar regions de les preses de prova, el primer completat passa12/36comprovacions. La vora lunar observada contaminada no és una bona entrada de radiància lunar latent: tornar-la a convolucionar pot comptar de nou part del halo. A més, els marges estrictes de validesa deixen forats en el camp solar auxiliar. No s’aplica aquest completat.

**D2:** es refà el camp amb51preses, excloent també quatre targets nous(2967,2985,2997,3003). Per a la llum lunar que falta s’utilitza només un nivell mesurat dins350px, i una continuació suau de la corona es limita a8px de dades reals. Són supòsits auxiliars de llum no observada, mai textures mesurades. Les màscares provenen de preses llargues reals(2978,2980,2983), de manera que el retall no selecciona fluctuacions positives de soroll de les curtes.

Aquest segon completat dona100% de suport en les zones examinades i passa24/36comprovacions. Però **les12comprovacions435–449 fallen**: mediana absoluta entre5,7i11,9G i percentil95 entre38,5i134,5G. El criteri fixat era mediana≤5G iP95≤25G. No s’afluixa per obtenir una promoció. Els models de geometria/llum del llimb encara no prediuen prou bé les dades amagades. Els testsD1/D2 tenen targets i màscares diferents; no se’n poden comparar directament els recomptes com si fossin el mateix assaig.

## Pas següent

El candidat de dispersió sobre dades completes es conserva. El proper problema concret és el completat físic per fotograma: ajustar la geometria i la radiància solar local utilitzant observacions no saturades i, si s’incorporen, les desigualtats que aporten els píxels censurats. Elp de dispersió queda congelat; no tornar a buscar sigmes globals sobre aquests mateixos jutges. Cal reservar nous targets abans de qualsevol nou ajust.

No promoure una barreja de fonts llargues sense corregir i curtes corregides, ni introduir un degradat per amagar el problema. Les condicions de contorn del model auxiliar no són màscares de Photoshop. La porta de detall entre trens i la porta Photoshop continuen pendents per a qualsevol nova font/PSB.

Preservació i represa: `Z0_preservation.json`, `research/tools/earthshine_scatter_witness_20260911/REPRESA.md` i el manifest final de la ronda. No s’ha invocat Photoshop ni alterat originals, CameraRaw, capes, màscares o protuberàncies. No s’ha tornat a apilar capRAW; es llegeixen fonts natives congelades.
'''
(OUT/'RESULTAT.md').write_text(text)
save('E0_summary.json',dict(temporal_mixture_PASS=model['temporal_mixture_PASS'],native_injection_PASS=injection['all_pass'],physical_candidate_p=model['p'],completion_PASS=False,D1_pass=sum(r['PASS'] for r in old['summary']),D1_total=len(old['summary']),D2_pass=sum(a['PASS'] for r in completion['frames'] for a in r['regions']),D2_total=36,new_PSB=False,goal_complete=False))
print('REPORT AND FIGURE READY',flush=True)
