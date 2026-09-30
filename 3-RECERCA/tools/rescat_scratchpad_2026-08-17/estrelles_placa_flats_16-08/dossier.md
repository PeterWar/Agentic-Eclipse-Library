# Dossier científic de postprocessat — corona de l'eclipsi del 12 d'agost de 2026

**Versió 1.0 · 15 d'agost de 2026 · Equip assessor de postprocessat**

Aquest document és la referència de consulta per a totes les decisions de postprocessat de l'eclipsi de Lleó. És autosuficient: qui llegeixi només això ha de poder implementar-ho tot. Substitueix qualsevol resum anterior de la bibliografia de Druckmüller.

**Convenció de marcatge**, la mateixa que la resta del projecte:

- **DEMOSTRAT** — s'ha llegit al paper, al codi o s'ha mesurat sobre els fitxers de Pere. S'hi diu on.
- **INFERIT** — es dedueix del que hi ha, però la font no ho afirma.
- **NO VERIFICAT** — es diu perquè és útil, però no s'ha pogut comprovar en aquesta sessió.

**Tres regles que valen per a tot el document.** La primera: cap dels filtres de realçat que hi surten no conserva la fotometria, i tots van a l'última porta, sobre una còpia. La segona: el que està publicat no sempre és el que els autors fan de veritat, i en dos casos concrets el que està publicat és directament un mètode que ells mateixos van abandonar. La tercera: les dades de Pere tenen tres defectes de calibratge que s'han de reparar abans de tocar res del que hi ha aquí; són a §4.1 i no són negociables.

---

## 1. Qui és aquesta gent i què ha aportat cadascú

**Miloslav Druckmüller** (Institut de Matemàtiques, Facultat d'Enginyeria Mecànica, Universitat Tecnològica de Brno). És l'eix. Tres aportacions vives: l'alineació per correlació de fase modificada (2009), la convolució de nucli variable que la comunitat anomena ACHF (2006, amb Rušín i Minarovjech), i el NAFE (2013), l'equalització difusa adaptada al soroll. Amb Morgan signa el MGN (2014), que és l'únic dels seus mètodes amb implementació oberta i mantinguda. El seu programari central —**Corona**, **LDIC** i **PhaseCorr**— és intern del grup, és de Windows i no es distribueix (DEMOSTRAT: s'ha sondejat el seu web a `/Software/`, `/Corona/`, `/Programs/`, `/Download/`, `/SW/` i tots retornen 404). Contacte públic: `[adreça]`.

**Vojtech Rušín** i **Milan Minarovjech** (Observatori de Skalnaté Pleso, Eslovàquia). Coautors del paper de 2006. Hi aporten la banda observacional d'eclipsis i la publicació al butlletí de Skalnaté Pleso; el nucli matemàtic és de Druckmüller. (INFERIT a partir del repartiment del text; el paper no reparteix la feina.)

**Hana Druckmüllerová**. És, per a nosaltres, la font més important de totes. Signa el **FNRGF** (2011, amb Morgan i Habbal) i, sobretot, la **tesi doctoral de 2013** —versió completa, 128 pàgines, oberta— que fa tres coses que cap article no fa: (a) dona la **fórmula real del nucli de l'ACHF**, que el paper de 2006 no té; (b) **corregeix** la compensació de soroll del FNRGF publicada a l'ApJ, i la qualifica literalment de «misleading idea»; (c) descriu el **compositor HDR LDIC** amb la seva fórmula. Si només es pot llegir un document d'aquest grup, és aquest.

**Karel Martišek**. Tesi de 2008/2012 sobre filtres adaptatius en 2D i 3D: filtres freqüencials amb transformada discreta de Fourier i **equalització adaptativa d'histograma amb veïnat adaptatiu**, que és l'antecedent directe del NAFE. El capítol 11.2 aplica el mètode a la corona. Si algú ha citat mai un mètode de Druckmüller anomenat «ADF», probablement ve del títol d'aquesta tesi: **«ADF» no existeix com a mètode publicat en aquesta obra** (DEMOSTRAT per cerca expressa).

**Huw Morgan** (Aberystwyth). NRGF (2006, amb Habbal i Woo) i MGN (2014, amb Druckmüller). És qui va portar el FNRGF a IDL dins el paquet CORIMP del SolarSoft.

**Shadia Habbal** (Institute for Astronomy, Hawaii). Dirigeix els **Solar Wind Sherpas**, el programa d'expedicions d'eclipsi que ha generat gairebé totes les dades que Druckmüller processa. La seva aportació al postprocessat és indirecta però decisiva: fixa què s'ha de poder mesurar després.

**Benjamin Boe**. La generació següent i la més útil per a la part fotomètrica: separació K/F per color (2021), brillantor absoluta de línies (2022), topologia magnètica per transformada de Hough rotacional amb Druckmüller (2020), i el *benchmark* de llum blanca contra models PFSS (2024). És el pont entre «imatge bonica» i «número publicable».

**Els successors, i per què importen.** **Zdeněk Hrazdíra** (tesi 2021/2022) porta la correlació de fase a la versió **iterativa** subpíxel. **Petra Kalenská** (tesi 2024) separa la component dinàmica de la quasi estable amb *Principal Component Pursuit* i *Dynamic Mode Decomposition*, i de passada publica els paràmetres reals del NAFE que el grup fa servir en producció. I fora de Brno hi ha els dos mètodes que canvien el panorama: **Frédéric Auchère** amb el **WOW** (2023) i **Gilly & Cranmer** amb el **RHEF** (2025), tots dos amb codi obert i pensats explícitament per no dependre d'ajustos a ull.

---

## 2. La cadena de mètodes, per ordre històric i lògic

### 2.0 De què va tot això

La corona té una relació de brillantor de fins a **1:1.000.000** entre el que és més brillant i el que és més fosc en una foto d'eclipsi reeixida; la corona sola, sense protuberàncies, cromosfera ni perles de Baily, en tindria d'1:1.000 (DEMOSTRAT, Druckmüller et al. 2006, p. 132). Cap suport no ho pot mostrar: l'ull humà, amb el contrast d'una pantalla, distingeix **entre 150 i 250 nivells** de brillantor (id., p. 136). D'aquí que la conversió de 16 bits a 8 no pugui ser mai lineal ni una simple gamma: ha de passar per un filtre que amplifiqui el que l'ull veuria i atenuï el gradient radial que no aporta res a la vista.

Tots els mètodes d'aquesta secció fan exactament això i **cap no és una mesura**.

### 2.1 Unsharp radial (radial blur / spin) — el mètode que es va superar

**Què fa.** Es desenfoca la imatge girant-la al voltant del centre del Sol (el filtre *Blur / Radial Blur / Spin* de Photoshop) i es resta aquesta màscara de l'original. És la tècnica que Espenak va popularitzar el 2000 i que es fa servir des de llavors.

**Fórmula.** No n'hi ha cap de publicada. Druckmüller et al. (2006, p. 138) el descriuen amb paraules i n'expliquen el sentit: equival a **comparar cada píxel amb uns quants veïns situats sobre una circumferència centrada al Sol**.

**Què destrueix.** Dues coses, i totes dues són fatals:

1. **És cec a les estructures tangencials.** Literal del paper: *«it is blind to tangential structures»*. Per construcció, el veïnat de comparació és un arc; el que està alineat amb l'arc desapareix.
2. **Canvia la fase.** DEMOSTRAT a la tesi de Druckmüllerová (§5.1): l'espectre de fase d'aquest filtre pren valors de tot el rang 0–2π. Un filtre que mou la fase **desplaça estructures i n'inventa de noves**.

**Quan s'ha de fer servir.** Mai, per a ciència. La tesi hi dedica un argument fort: durant anys es va creure que els models de camp magnètic estaven equivocats perquè no mostraven el que sortia a les imatges filtrades així, i els equivocats eren les imatges.

### 2.2 ACHF — convolució de nucli variable (2006 + tesi 2013)

⚠️ **Primer, la nomenclatura.** L'expressió «ACHF» i «adaptive circular high-pass filter» **no apareix enlloc del paper de 2006** (DEMOSTRAT per cerca de text al PDF). Els termes dels autors són *«variable kernel convolution»* (§4.2) i *«adaptive kernel convolution»* (peu de la fig. 4). El nom popular és de fora.

**Què fa.** Un passa-alt amb un nucli **diferent a cada píxel**, que s'anul·la a través de les fronteres entre parts molt diferents de la imatge (Lluna contra corona, protuberància contra corona), de manera que no genera efecte de vora on el contrast salta.

**Les fórmules que el paper sí que dona.** Convolució clàssica (eq. 5) i convolució de nucli variable (eq. 7):

$$b_{k,l}=\sum_{i=-r}^{r}\sum_{j=-r}^{r} a_{k+i,\,l+j}\;c^{(k,l)}_{i,j}$$

amb quatre condicions sobre el nucli (p. 139, literals):

- **(a)** L'espectre $\mathcal{F}(C^{(k,l)})$ ha de ser real, o com a mínim $\arg\mathcal{F}(C^{(k,l)})\approx 0$. *«This ensures that the filter will not change the phase, i.e. it will not create artifacts in the image.»*
- **(b)** Passa-alt: amplifica les altes i atenua les baixes. *«The amplification is limited by the amount of the noise.»*
- **(c)** Espectre **centralment simètric**, almenys a alta freqüència, perquè el realçat no depengui de la direcció.
- **(d)** $c^{(k,l)}_{i,j}=0$ si els píxels comparats pertanyen a parts significativament diferents de la imatge, amb un llindar de diferència màxima *«estimated experimentally»*.

I la confessió immediata dels autors: *«These requirements, of course, do not define $C^{(k,l)}$ uniquely and several parameters must be set intuitively.»* Corona 3.0 té **38 paràmetres**.

⚠️ **Amb això sol no es pot programar res.** Quatre condicions no són una recepta. I la condició (d), tal com està impresa, està **mal indexada**: diu que es comparin els píxels $a_{k,l}$ i $a_{i,j}$, o sigui el píxel actual amb el píxel absolut $(i,j)$ del cantó de la imatge. Els que s'han de comparar són $[x,y]$ i $[x+i,\,y+j]$ (DEMOSTRAT: la tesi ho escriu bé).

**La fórmula que falta, i que sí que està publicada.** Tesi de Druckmüllerová (2013), §5.2, eq. (5.1) — nucli gaussià en coordenades polars modificades, centrat al píxel $[r,\varphi]$ i avaluat al píxel $[\rho,\phi]$:

$$C_{r,\varphi}(\rho,\phi)=\exp\!\left(-\frac{(r-\rho)^2+\big(r(\varphi-\phi)\big)^2}{2\sigma^2}\right)$$

i eq. (5.2), la convolució **incompleta i normalitzada**, on $w$ és el pes de pertinença (1 si el píxel és de la mateixa part de la imatge, 0 si no):

$$g(r,\varphi)\;=\;f(r,\varphi)\;-\;\frac{\displaystyle\sum_{\rho,\phi} f(\rho,\phi)\,C_{r,\varphi}(\rho,\phi)\,w(\rho,\phi)}{\displaystyle\sum_{\rho,\phi} C_{r,\varphi}(\rho,\phi)\,w(\rho,\phi)}$$

Això respon d'un cop dues preguntes que quedaven obertes: **sí que es renormalitza** després d'anul·lar coeficients (el denominador és la suma de $C\cdot w$), i **és una màscara de desenfocament** (imatge menys mitjana local ponderada), no un passa-alt dissenyat en freqüència.

**Paràmetres.** $\sigma$ útil de **0,5 a 64**; límits d'integració de $-2\sigma$ a $+2\sigma$; el pes $w$ decideix l'adaptivitat (DEMOSTRAT, tesi §5.2).

⚠️ **Però això és el PREDECESSOR, no l'ACHF viu.** La mateixa tesi diu que aquest és *«the filter that was implemented in the first version of the Corona software»* i que l'ACHF actual (Corona 4.1) fa servir **un conjunt de filtres amb diversos $\sigma$ combinats** més *«nonlinearity in the use of filtered images»*, que no es descriu enlloc.

**Què conserva i què destrueix.** Conserva la **geometria**: amb fase zero, cap estructura no es mou de lloc, i per tant les mesures astromètriques (posicions de raigs, plomalls, alineació entre trens) són segures. Destrueix la **fotometria** deliberadament: la condició (b) elimina el gradient radial, que és justament la informació fotomètrica de gran escala. **Irreversible**: nucli dependent del contingut, coeficients anul·lats i compressió final a 8 bits.

**Quan s'ha de fer servir.** Quan es busca el **detall més fi** i es té mostreig per aprofitar-lo. Vegeu §2.8: no és el nostre cas.

### 2.3 NRGF — Normalizing Radial-Graded Filter (Morgan, Habbal i Woo 2006)

**Què fa.** Talla la corona en anells d'un píxel centrats al Sol i, a cada anell, resta la mitjana i divideix per la desviació típica de tot l'anell.

$$g(r,\varphi)=\frac{f(r,\varphi)-\mathrm{E}(r)}{S(r)},\qquad \mathrm{E}(r)=\frac{1}{N_r}\sum_{\rho=r} f,\qquad S(r)=\sqrt{\frac{1}{N_r-1}\sum_{\rho=r}\big(f-\mathrm{E}(r)\big)^2}$$

**Paràmetres.** Cap, llevat del centre del Sol i del rang de radis. És completament automàtic.

**Què conserva.** El **contrast azimutal**: un forat coronal continua fosc i un *streamer* continua brillant dins del mateix anell. Aquesta és la seva virtut i la raó per la qual és l'eina estàndard de coronògraf.

**Què destrueix.** El gradient radial (a propòsit) i la brillantor absoluta.

**Quan.** Com a **referència de control**. Si una estructura surt al NRGF i al filtre sofisticat, és real; si només surt al sofisticat, s'ha de justificar.

### 2.4 FNRGF — la versió de Fourier (Druckmüllerová, Morgan i Habbal 2011)

**Què fa.** El mateix que el NRGF, però la mitjana i la desviació que es resten i divideixen **depenen també de l'angle**. Es parteix cada anell en $n_s$ segments angulars, se'n treu mitjana i desviació, i les dues seqüències s'aproximen amb un polinomi trigonomètric d'ordre $\omega$.

**Coeficients** (eqs. 3.2–3.4 de la tesi curta; eqs. 2–4 de l'ApJ), amb $\mathrm{E}_s(r)$ la mitjana del segment $s$ a l'alçada $r$:

$$a_{r,0}=\frac{2}{n_s}\sum_{s=0}^{n_s-1}\mathrm{E}_s(r),\qquad
a_{r,k}=\frac{2}{n_s}\sum_{s=0}^{n_s-1}\mathrm{E}_s(r)\cos\frac{2\pi k\left(s+\tfrac12\right)}{n_s},\qquad
b_{r,k}=\frac{2}{n_s}\sum_{s=0}^{n_s-1}\mathrm{E}_s(r)\sin\frac{2\pi k\left(s+\tfrac12\right)}{n_s}$$

i els $c_{r,k}$, $d_{r,k}$ igual però sobre $\sqrt{S^2_s(r)}$, la **desviació** del segment (no la variància). ⚠️ L'ApJ no escriu aquestes tres últimes fórmules: només diu *«in a similar way»*. La tesi sí.

**Variància per segment**, en la forma computacional que convé programar:

$$S^2_s(r)=\frac{1}{N_{r,s}(N_{r,s}-1)}\left(N_{r,s}\sum f^2-\Big(\sum f\Big)^{2}\right)$$

**Reconstrucció amb atenuacions** (eqs. 3.8–3.9 amb els coeficients $A_k$, $C_k$ del §3.2.2 de la tesi):

$$F_{\bar f}(r,\varphi)=A_0\frac{a_{r,0}}{2}+\sum_{k=1}^{\omega}A_k\big(a_{r,k}\cos k\varphi+b_{r,k}\sin k\varphi\big)$$
$$F_{S(f)}(r,\varphi)=C_0\frac{c_{r,0}}{2}+\sum_{k=1}^{\omega}C_k\big(c_{r,k}\cos k\varphi+d_{r,k}\sin k\varphi\big)$$
$$g(r,\varphi)=\frac{f(r,\varphi)-F_{\bar f}(r,\varphi)}{F_{S(f)}(r,\varphi)},\qquad h=K_1 f+K_2\,g$$

⚠️ **Atenció a un detall que sembla una errada i no ho és**: els arguments dels sinus i cosinus dels **coeficients** van amb $2\pi k(s+\tfrac12)/n_s$ (índex de segment, punt mig), i els de la **reconstrucció** van amb $k\varphi$ (angle real del píxel). El paper avisa expressament.

**La correcció més important de tot el document.** L'ApJ de 2011 proposa compensar el soroll additiu **restant** la desviació del soroll al denominador: $F_\sigma - m\sqrt{D_N}$. **La mateixa autora ho repudia** a la tesi: *«a misleading idea»*, perquè a les zones que només tenen soroll porta a **amplificació infinita**. El que s'ha d'implementar és exactament el contrari — **sumar** una variància artificial $V_n$ a les variàncies locals, dins del càlcul dels $c$ i $d$ i **enlloc més**:

$$c_{r,k}=\frac{2}{n_s}\sum_{s=0}^{n_s-1}\sqrt{S^2_s(r)+V_n}\;\cos\frac{2\pi k\left(s+\tfrac12\right)}{n_s}$$

Amb $\sqrt{V_n}$ **del 10 % al 15 %** de la desviació del soroll de la imatge, estimada com la **mediana** de les desviacions dels segments dels **10 anells més exteriors** processats. No cal generador aleatori ni segona matriu: només se suma un escalar.

**Paràmetres i restriccions dures.**

| Paràmetre | Valor | Regla |
|---|---|---|
| $n_s$ | 50–150 | $n_s\ge 2\omega+1$ **i** $n_s\approx 2\pi r_o/10$ (deu píxels per segment al radi mínim) |
| $\omega$ | 10 a l'exemple; «el més alt possible» als resultats | limitat per $n_s$ |
| $A_k$ | rampa lineal des d'1, pas 0,01–0,05 | no creixent |
| $C_k$ | rampa lineal des d'1, pas 0,02–0,06 | no creixent, i **$A_k$ ha de decréixer una mica més lent que $C_k$** |
| $\sqrt{V_n}$ | 10–15 % del soroll | — |
| $K_1{:}K_2$ | 1:7 sobre imatges normalitzades a [0,1] | — |

Valors reals de producció (DEMOSTRAT, tesi §3.3.1): llum blanca del TSE 2010, $n_s=150$, $A_k=(1;0{,}99;0{,}98;\dots)$, $C_k=(1;0{,}98;0{,}96;\dots)$.

**Modes de fallada.** $A_k$ massa alts → ondulacions falses de Gibbs (*«false glimmers»*). $C_k$ massa alts → **el denominador s'acosta a zero i la imatge explota localment**; entre una imatge bona i una destrossada hi ha 0,1 en cada coeficient. El paper afirma que el denominador és sempre estrictament positiu; **no ho demostra i no és cert en general** per a una sèrie truncada i atenuada: cal posar-hi un pis numèric.

⚠️ **No facis servir la prova unitària que proposa l'ApJ.** El paper diu que amb $A_0=S_0=1$ i tota la resta a zero es recupera el NRGF. **És fals** (DEMOSTRAT numèricament: corona sintètica de 801×801, $n_s=50$; la mitjana coincideix dins el 0,2 % però el denominador surt **un 89 % més petit**, perquè la mitjana de les desviacions dels segments no conté la variància *entre* segments). La reducció exacta al NRGF és la que dona la tesi: **$n_s=1$**.

⚠️ **Errates de l'apèndix del centre del Sol**, a resoldre abans de programar-lo: la normal al moviment de la Lluna ha de ser $(M_{dy},-M_{dx})$ i no $(M_{dx},-M_{dy})$; l'eq. (A4) ha de dir $n_{\delta,y}=\delta n_y/v$; i la $N$ de la definició de $h$ és $B$.

**Quan.** Escala gran, alçades altes, i **dades sorolloses**. La tesi diu que NRGF i FNRGF *«were proposed especially for images in spectral lines and from coronagraphs, which contain much more noise»*. Això **no** vol dir que no serveixin per a llum blanca: la mateixa tesi processa amb FNRGF una imatge de llum blanca del TSE 2010, i la pràctica publicada del grup és combinar-los, **0,4 de FNRGF i 0,6 d'ACHF**.

### 2.5 MGN — Multiscale Gaussian Normalization (Morgan i Druckmüller 2014)

**Què fa.** El mateix principi de normalització local, però a **moltes escales alhora** i sense geometria radial: no cal centre del Sol, no cal màscara d'anell, funciona sobre la imatge sencera.

**Fórmules** (DEMOSTRAT, llegides al PDF). Amb $B$ la imatge original **normalitzada pel temps d'exposició** i $k_w$ un nucli gaussià de sigma $w$ píxels:

$$C=\frac{B-B\otimes k_w}{\sigma_w},\qquad \sigma_w=\sqrt{\big[(B-B\otimes k_w)^2\big]\otimes k_w}$$
$$C'=\arctan(kC)$$
$$C'_g=\left(\frac{B-a_0}{a_1-a_0}\right)^{1/\gamma}$$
$$I=h\,C'_g+\frac{(1-h)}{n}\sum_{i=1}^{n} g_i\,C'_i$$

**Paràmetres verificats al paper**: $w=\{1{,}25;\,2{,}5;\,5;\,10;\,20;\,40\}$, $k=0{,}7$, $\gamma=3{,}2$ (útil de 2,5 a 4), $h=0{,}7$, $a_0$ i $a_1$ el mínim i el màxim d'entrada. Els $g_i$ són més petits per a nuclis estrets i s'acosten a 1 quan $w\gtrsim 3$.

**Pseudocodi**, literal del paper: (1) substituir píxels negatius espuris per zero o per la mediana local; (2) nucli gaussià que sumi 1; (3) mitjana local; (4) desviació local; (5) $C$; (6) arctan; (7) repetir per a cada $w$; (8) mitjana dels $C'_i$; (9) $C'_g$; (10) suma amb pes $h$.

**Què destrueix.** El mateix de sempre: gradient radial i brillantor relativa. L'arctan garanteix que la sortida no saturi.

**Quan.** És el camí curt i implementat. `sunkit_image.enhance.mgn`.

### 2.6 WOW — Wavelet-Optimized Whitening (Auchère et al. 2023)

**Què fa.** Descompon la imatge amb la transformada d'ondetes *à trous* i **blanqueja** la potència: normalitza cada coeficient per l'arrel de la potència local, de manera que la variància queda equalitzada a totes les escales **i a totes les posicions**. El resultat és la suma dels coeficients blanquejats.

**Fórmules** (DEMOSTRAT, eqs. 8 i 9):

$$w_s(k)\;\longrightarrow\;\frac{w_s(k)}{\sqrt{P_s(k)}},\qquad P_s(k)=w_s(k)^2 * h_s(k)$$
$$c'_0(k)=c_S(k)+\sum_{s=1}^{S} w_s(k)$$

**Desbrollament integrat** (eqs. 10 i 12): els coeficients significatius són els que compleixen $|w_s(k)|>n_s\sigma_s$ amb $\sigma_s=\sigma\,\sigma_{1s}$, i s'atenuen suaument amb

$$\alpha\big(n_s\sigma_s, w_s(k)\big)=\mathrm{erf}\!\left(\frac{|w_s(k)|}{n_s\sigma_s}\right)$$

**La part que ens interessa de debò** (eqs. 16–18): la convolució de l'*à trous* genera **halos** al voltant de vores i pics forts, i el blanqueig els reforça com si fossin estructura real. La versió *edge-aware* substitueix la convolució per un filtre **bilateral**, amb el pes de rang gaussià i amplada donada per la **variància local a cada escala**:

$$c_{s+1}(k)=\frac{\sum_{l\in\Omega} c_s(k+2^s l)\,h(l)\,b(k,k+2^s l)}{\sum_{l\in\Omega} h(l)\,b(k,k+2^s l)},\qquad
b(k,k+2^s l)=\exp\!\left(-\tfrac12\left(\frac{c_s(k)-c_s(k+2^s l)}{\nu_s}\right)^{\!2}\right)$$
$$\nu_s(k)^2=h_s(k)*c_s(k)^2-\big(h_s(k)*c_s(k)\big)^2$$

**Paràmetres.** L'autor ho declara explícitament: *«The only free parameters are the denoising significance levels»* $n_s$. I: la versió estàndard és **unes dues vegades més ràpida que el MGN**.

**Quan.** És la nostra **primera opció** (raonament complet a §2.8): criteri objectiu en lloc d'ajust subjectiu, codi obert, i el mecanisme *edge-avoiding* existeix **precisament per suprimir els halos que generen les discontinuïtats**, que és el front G3.

### 2.7 RHEF — Radial Histogram Equalizing Filter (Gilly i Cranmer 2025)

**Què fa.** Substitueix la resta de la mitjana i la divisió per la desviació per un **remapatge per percentils** dins de cada anell concèntric: cada píxel passa a valer el seu rang dins l'anell, dividit pel nombre de píxels.

$$I_\mathrm{out}[A_i]=\frac{\mathrm{rank}\big(I_\mathrm{in}[A_i]\big)}{N_{A_i}}$$

Opcionalment s'hi aplica la redistribució **Υ**, una família de corbes de dos paràmetres ($\Upsilon_L$ per sota de la mediana i $\Upsilon_H$ per damunt) que preserva el rang mitjà millor que una gamma clàssica; el valor de referència és $\Upsilon=0{,}35$. (La forma exacta de la corba surt garbullada a l'extracció de text: **PARCIALMENT VERIFICAT**.)

**Virtuts declarades.** *«Works out of the box—without requiring careful parameter tuning»*, i implementació doble en `sunkit_image.radial.rhef` i en IDL.

**Advertència que els autors mateixos fan.** *«It is unsuitable for photometric applications.»*

⚠️ **Una imprecisió del seu propi article**: la taula 1 classifica l'ACHF dins la família d'*histogram equalization* i el descriu com a *«histogram manipulation heuristics»*. Això és fals — l'ACHF és convolució adaptativa incompleta — o sigui que **el seu banc de comparació tampoc no és net**.

### 2.8 Quin s'ha de fer servir aquí, i per què

**No hi ha cap comparació publicada entre ACHF, MGN, WOW i RHEF sobre un compost HDR real d'eclipsi total en llum blanca** (DEMOSTRAT per absència: els bancs de prova de WOW i RHEF són EUV d'AIA, EUI/FSI, HRI, LASCO C2/C3, K-Cor i dades sintètiques). Qualsevol afirmació de «el millor» és, avui, una preferència heretada.

L'única font que declara l'ACHF el millor per a llum blanca és la tesi de Druckmüllerová (2013): *«This makes ACHF the best nowadays used structure enhancement technique for images of the solar corona from total solar eclipses in white light»*. És una **autoavaluació del grup que fa el programa**, ancorada a l'any 2013.

I el criteri pel qual l'ACHF guanya és el detall més fi — **el que aquests dos trens no poden cobrar**:

| | Mostreig | Resolució efectiva (2 px) | Difracció |
|---|---:|---:|---:|
| R6 III + VSD90SS | 2,158 ″/px | **≈ 4,3 ″** | 1,26 ″ (D=90 mm) |
| A7RIIIA + 300/2,8 | 3,234 ″/px | **≈ 6,5 ″** | 0,46 ″ (D=107 mm) |
| Druckmüller (2014, ApJ 785) | — | **2–3 ″** | — |

Estem submostrejats per un factor 1,5–2 respecte del terreny on l'ACHF és superior. Dir «amb 2,158 ″/px la R6 hi és just» confon mostreig amb resolució: **hi és curt**.

**Recomanació operativa.**

1. **WOW** (versió *edge-aware*, amb desbrollament). Primera opció.
2. **MGN**. Segona, i la més fàcil de justificar davant de tercers perquè és la més usada.
3. **RHEF**. Tercera, sense paràmetres, per a una lectura ràpida i reproduïble.
4. **FNRGF** per a l'escala gran i alçades altes, si es vol seguir la pràctica del grup de Brno.
5. **ACHF** com a **referència**, reimplementat amb les eqs. (5.1)+(5.2) de la tesi i un joc de $\sigma$, i declarant sempre que això és el **predecessor** de l'ACHF viu.

**Cap dels cinc no toca mai el producte científic.**

---

## 3. L'alineació

### 3.1 Per què és el pas més crític

*«The first and the most critical step»* (Druckmüller et al. 2006). No hi ha punts de referència: les estrelles no surten a les exposicions curtes, la vora lunar està saturada a les llargues, i **totes dues es mouen respecte de la corona durant la totalitat**. Les estructures coronals, que són l'única referència fixa, tenen un contrast tan baix que a les imatges originals són gairebé invisibles.

### 3.2 La correlació de fase (Druckmüller 2009)

**Base.** Amb $b(x,y)=a(x-x_0,y-y_0)$ i $A$, $B$ les transformades de Fourier:

$$C(\xi,\eta)=A(\xi,\eta)\,B^{\star}(\xi,\eta),\qquad N(\xi,\eta)=\frac{C(\xi,\eta)}{|A(\xi,\eta)B(\xi,\eta)|},\qquad n(x,y)=\mathcal{F}^{-1}\big(N\big)$$

Idealment $n$ val zero a tot arreu llevat de $(x_0,y_0)$. Com que només es conserva la **fase**, un canvi d'exposició en règim lineal no l'afecta: per això alinea entre 1/6400 i 8 s.

**Modificació 1 — regularització.** Amb dades reals hi ha freqüències d'amplitud molt baixa i el quocient explota:

$$N_{p,q}(\xi,\eta)=\frac{C(\xi,\eta)}{\big(|A(\xi,\eta)|+p\big)\big(|B(\xi,\eta)|+q\big)}$$

**Modificació 2 — filtratge del soroll**, amb una gaussiana de pas baix al domini de la freqüència:

$$G_\sigma(\xi,\eta)=\exp\!\left(-\frac{\xi^2+\eta^2}{2\sigma^2}\right),\qquad n_{p,q,\sigma}=\mathcal{F}^{-1}\big(N_{p,q}\,G_\sigma\big)$$

**Modificació 3 — el filtre tangencial $H_\varrho$.** Aquesta és la peça conceptual. Un filtre de banda al domini de la freqüència **no funciona**, i el paper diu per què: *«The problem is caused by the extreme radial gradient of the coronal brightness. Any nonlinearity in brightness scale (chip saturation, non-homogeneous diffuse light, film properties, etc.) highly influences spatial frequencies in the radial direction and makes them unreliable for image alignment.»* La solució és eliminar les freqüències baixes **només en direcció tangencial**, i això obliga a fer-ho a l'espai:

$$H_\varrho\big(a(x,y)\big)=a(x,y)-\int_{\omega_1}^{\omega_2} a\big(r\cos(\varphi+\omega),\,r\sin(\varphi+\omega)\big)\,e^{-\frac{\omega^2}{2\varrho^2}}\,d\omega$$

⚠️ **Dues esmenes obligatòries.** (i) El paper imprimeix l'argument com $a(r+\cos(\varphi+\omega),\,r+\sin(\varphi+\omega))$, amb **signe més**: no té sentit dimensional i és una errata. (ii) **No hi ha constant de normalització**: tal com està escrit, $H_\varrho(\text{constant})\neq 0$. Cal dividir pel pes gaussià integrat. Límits: $\omega_{1,2}=\pm 2\varrho$.

⚠️ Les **unitats** de $\omega$ i $\varrho$ no es defineixen enlloc. Si $\omega$ fos radians, $\pm 2\varrho=\pm 16$ serien més de dues voltes. Ha de ser graus o longitud d'arc en píxels. **NO VERIFICAT**, i afecta directament l'escala espacial del filtre.

**Modificació 4 — la màscara anular.** Tot el que es mou respecte de la corona (la Lluna, les estrelles brillants, la pols del sensor, els píxels morts) i la vora del quadre s'ha de **treure**, no tractar:

$$\overline m_a(x,y)=\begin{cases}1 & \text{si } (x,y)\in C_a \wedge r_1<r_{x,y}<r_2\\ 0 & \text{altrament}\end{cases}$$

amb $r_1>$ radi lunar i $r_2<$ radi del cercle inscrit al quadre. La màscara es suavitza amb una gaussiana i les imatges finals de correlació són $a_\varrho=H_\varrho(a)\,m_a$ i $b_\varrho=H_\varrho(b)\,m_b$.

**Aquesta és la resposta al problema del disc lunar saturat: no es tracta, s'exclou.**

### 3.3 Rotació i escala: els sis passos

1. Amplituds $|A|$, $|B|$ de les transformades.
2. Passar-les a coordenades polars amb **escala logarítmica al radi**.
3. Correlació de fase → $k$ (escala) i $\alpha$ (rotació).
4. Aplicar $k^{-1}$ i $-\alpha$ a $b$ → $b_1$.
5. Correlació de fase entre $a$ i $b_1$ → $(x_0,y_0)$.
6. Aplicar $(-x_0,-y_0)$ → $b_2$.

El truc: sobre les **amplituds**, el centre de rotació és conegut per construcció, és el punt $(0,0)$. Total: **vuit transformades de Fourier (sis directes i dues inverses) i dues transformacions a log-polar**.

### 3.4 Precisió subpíxel: centre de gravetat, no interpolació

El paper tria explícitament els moments per damunt de la interpolació del pic (*«more robust and more suitable»*):

$$(\overline x_0,\overline y_0)=\left(x_0+\frac{M_{1,0}}{M_{0,0}},\;y_0+\frac{M_{0,1}}{M_{0,0}}\right),\qquad
M_{r,s}=\!\!\sum_{k^2+l^2\le\varepsilon^2}\!\! k^r l^s\, n_{p,q,\sigma,\varrho}(x_0+k,\,y_0+l)$$

⚠️ L'eq. (7) del paper **no suma $(x_0,y_0)$**; els moments van sobre índexs relatius. INFERIT que és notació abreujada.

⚠️ El camp de correlació té valors positius i negatius; un centre de gravetat sobre valors de signe mixt pot donar $M_{0,0}$ petit i explotar. El paper no en diu res: **decisió d'implementació**.

### 3.5 Paràmetres i sensibilitat

| | Rang típic | Valor usat al paper | Sensibilitat |
|---|---|---|---|
| $p$, $q$ | 0,01–0,1 % de l'amplitud màxima | 0,01 % | **baixa** |
| $\sigma$ | $0{,}01n$ a $n$ ($n$ = amplada en píxels) | $0{,}1n$ | **alta i crítica** |
| $\varrho$ | 8–16 | 8 | baixa |
| $\varepsilon$ | 3–5 | 3 | no quantificada |

**El mode de fallada de $\sigma$ no és gradual.** Massa alt: *«incorrect maximum identification and incorrect alignment»* — s'agafa el pic equivocat. Massa baix: es perd precisió. I d'aquí ve l'única limitació que l'autor declara: *«The only disadvantage of the method, at present, is that it is not possible to automate it.»* Cal escombrar $\sigma$ i triar a mà; **el paper no proposa cap mètrica de qualitat del pic**.

### 3.6 Precisió assolida i com validar-la

**Amb dades sintètiques** ($k\in[0{,}9;1{,}1]$, $\alpha\in[0,2\pi]$, desplaçaments de ±100 px, 50 assajos, matrius de 4096×4096): error **< 0,01 px** prop de la vora lunar, **< 0,1 px** prop de les cantonades, **< 0,002 px** per a translació pura.

**Amb dades reals** només es pot contrastar amb el centroide lunar, i només amb exposicions molt curtes. La taula 1 dona diferències de 0,00 a **0,40 px** sobre deu imatges — i aquesta discrepància **inclou l'error del centroide lunar**, no només el de la correlació.

**Protocol a reproduir per validar una implementació pròpia**: agafar un fotograma real, aplicar-li $k$, $\alpha$ i desplaçament coneguts, i comprovar que es recuperen.

### 3.7 Alternatives modernes

- **Correlació de fase iterativa** (Hrazdíra, tesi 2021/2022, i dos articles a ApJS del 2020): finestrat de la imatge, filtratge de l'espectre creuat, subregions de correlació i sobremostreig. És l'estat de l'art del mateix grup i posterior al paper de 2009. **La tesi és oberta i la tenim; els dos articles no** (mur de bots d'IOP).
- **`skimage.registration.phase_cross_correlation`**: correlació de fase amb refinament subpíxel per sobremostreig matricial. Existeix i és estàndard. ⚠️ **No** implementa cap de les quatre modificacions de Druckmüller: cal aplicar $H_\varrho$ i la màscara **abans** de cridar-la. (INFERIT: és la via pràctica per no reescriure les FFT.)
- **`astroalign`** i els mètodes basats en detecció de fonts: **inservibles aquí**, perquè no hi ha fonts puntuals fiables.
- **ECC d'OpenCV** (`findTransformECC`): maximitza la correlació normalitzada i és invariant a canvis lineals de brillantor. **NO VERIFICAT** per a corona; candidat de segona.

### 3.8 El doble registre corona/Lluna — el que cap paper no cobreix

**DEMOSTRAT per absència**: cap dels documents consultats no descriu com alinear la Lluna. Druckmüller la treu amb la màscara i la fa servir només com a referència de verificació.

Per a nosaltres això és un gate propi (G4), i les peces les tenim:

- **La deriva relativa Lluna–Sol és 0,5905 ″/s** (valor viu de `research/71`; el 0,585 de `CLAUDE.md` és previ a l'eclipsi i està caducat). Entre la primera i la quarta àncora d'earthshine, 48 s, són **28 ″ ≈ 9 px** a l'escala de la Sony: **la pila de corona i la pila de Lluna no poden compartir alineació**.
- **La deriva d'apuntat del R6** és de 0,71–0,75 ″/s, mesurada per correlació de fase sobre quatre parelles de fotogrames de la mateixa exposició (contra els ~0,61 ″/s de `research/71`: mateix ordre, 18 % més alt).
- **Els dos salts de la Skywatcher**: +228 px en $x$ entre C2+25,6 i C2+42,6, i −710 px en $y$ entre C2+42,6 i C2+58,6, compatibles amb els +223 i −715 px de `research/72`. **L'àncora d'earthshine DSC06990 cau dins del segon salt.**
- **El centre del Sol a partir del moviment de la Lluna**: la recepta tancada és al §4.1.4 de la tesi completa de Druckmüllerová i a l'apèndix de l'ApJ de 2011 (amb les tres errates de §2.4). Es mesuren la posició del centre lunar a C2, el vector de desplaçament per segon i el radi lunar en píxels; amb la raó Lluna:Sol i la profunditat umbral en surt el centre del Sol.

$$H_R=\frac{M_E}{R_{MS}},\qquad \delta=2h\,(M_E-H_R),\qquad
H_x=M_{x,0}+\tfrac{l}{2}M_{dx}+\frac{\delta\,n_x}{v},\qquad H_y=M_{y,0}+\tfrac{l}{2}M_{dy}+\frac{\delta\,n_y}{v}$$

amb $\vec n\perp(M_{dx},M_{dy})$ i $v=|\vec n|$.

**Recepta operativa (INFERIT, no publicada):** dues piles independents. La de **corona** s'alinea amb correlació de fase sobre $H_\varrho$ + màscara anular, com diu el paper. La de **Lluna** s'alinea pel **limbe lunar** dels fotogrames curts (1/6400 i 1/3200), on la vora és neta i no saturada, ajustant-hi una circumferència. Els dos registres es guarden com a paràmetres explícits, mai barrejats. El pont entre les dues és la deriva de 0,5905 ″/s, que serveix de comprovació creuada: si el registre lunar no la reprodueix, hi ha un error.

---

## 4. El que va abans del realçat i que tothom es salta

### 4.1 Linealitat — i els tres defectes de les nostres dades

Els papers ho donen per fet. La tesi de Druckmüllerová és l'única que hi entra i dona el número útil: **la resposta del sensor deixa de ser prou lineal a partir d'un ~85 % del rang dinàmic**, i aquells píxels s'han de rebutjar igual que els del terra de soroll.

**Però aquell 85 % no descriu res del que hi ha als nostres TIFF actuals.** Tres defectes mesurats:

**(a) Retall d'altes llums pel balanç de blancs.** Els dos scripts de calibratge fan `raw.postprocess(use_camera_wb=True, ...)` amb el mode de retall per defecte de LibRaw. Els guanys de càmera són R=1,943 i B=1,659 al R6, i R=2,504 i B=1,629 a la Sony. Conseqüència: **el canal vermell es retalla a 8.430 ADU crus al R6** (1,00 EV per sota del pou) **i a 6.543 a la Sony** (1,32 EV). Verificat al fotograma de 10 s del R6: el RAW té 0,068 % de fotolocalitats R al blanc i el TIFF en té **5,55 %** — vuitanta-una vegades més, i la predicció del mecanisme (5,698 %) coincideix amb la mesura. **65535 al TIFF no vol dir sensor saturat.**

**(b) El terra està censurat.** El `np.clip` al domini cru més la resta de negre de LibRaw deixen el fons retallat a zero: **44,0 % dels píxels exactament a 0 a 1/2000**, 41,2 % a 1/1000, 34,9 % a 1/500 al R6; i 40,8/52,5/38,8 % (RGB) al fotograma de contacte Sony de 1/6400, que és un dels que porta el limbe net per registrar. La prova de linealitat ho tanca: a 5 R☉ la raó 1/500→1/125 surt **9,0** en comptes de 4,0 (les curtes són al terra), mentre que 1/30→1/8 surt 4,28 contra 4,167 esperat. **La mediana d'una distribució truncada no és un nivell de fons.**

**(c) L'exposició més profunda està mal anotada.** El manifest diu 10,000 s; el programa declara **10,3 s** i l'EXIF en diu 10,4. El manifest la llegeix de Spotlight, no de l'EXIF. Són 0,04–0,06 EV d'error sistemàtic **justament a l'esglaó que porta l'earthshine**. I el R6 té **16 exposicions diferents**, no 12: l'escala de 12 esglaons existeix però està mostrejada desigualment (4 fotogrames a sis esglaons, 2 als altres sis).

**Recepta de recalibratge (INFERIT, però obligada).** Tornar a desbayerar els RAW amb `user_wb=[1,1,1,1]`, `output_color=rawpy.ColorSpace.raw`, `no_auto_bright=True`, `gamma=(1,1)`, `output_bps=16`, i **sense cap `clip` a zero**; conservar el pedestal; treballar en `float64` en ADU crus; aplicar el balanç de blancs i la matriu de color **després** de tota la fotometria, o no aplicar-los mai al producte científic. Llegir el temps d'exposició de l'EXIF.

**I l'inventari s'ha de refer.** Els «124 fotogrames de totalitat» del R6 abasten 207,65 s d'EXIF: només **~68 cauen dins [C2, C3]**, 23 són abans de C2, 30 després de C3 i 3 són parcials documentals a 1/320. Dels 194 de la Sony, el **nucli de totalitat són 33**; 122 són parcials filtrades a 1/400 i 34 més no pertanyen a cap bloc del programa i no tenen dark propi. Als fotogrames de fora de totalitat la referència d'alineació no és la corona sinó un creixent fotosfèric, i una correlació de fase s'hi enganxarà.

### 4.2 Foscos

La tesi (§4.1.2) dona la cadena completa: bias, master dark i flat, amb els flats al mateix ISO, obertura i focus, i sense moure ni apagar la càmera entremig.

**El nostre banc té dos defectes no declarats** (DEMOSTRAT, `proces.log` del R6): el master de **0,5 s** conté fotogrames amb desviació típica de 4,3 a 55,1 ADU quan tots els altres van de 2,7 a 2,9 — com a mínim un d'aquells setze «darks» **no és fosc**; i el master de **10 s** té pedestal 511,0 quan tota la resta té 512,0, precisament l'esglaó de l'earthshine. A la Sony, 34 fotogrames es van calibrar amb el master de 1/6400 com a bias perquè no tenien dark propi.

I la trampa ja documentada a `research/71`: **el negre de metadata de libraw és fals; el pedestal real és 511–512 pla.**

### 4.3 Camp pla

**No en tenim.** Conseqüència directa: el vinyetatge de cada tren queda dins de les dades i és **indistingible d'un gradient de fons**. Bemporad (2020) corregeix el vinyetatge explícitament al seu flux de DSLR. Sense flat, el model de halo del G3 haurà d'absorbir també el vinyetatge, i llavors deixa de ser un model físic i passa a ser un model empíric del sistema sencer. **S'ha de dir així al document final.**

### 4.4 La composició HDR lineal

Dues receptes publicades, i totes dues serveixen.

**(1) Els pesos de Druckmüller et al. (2006).** Per a cada imatge $A_i$ i cada píxel es fixa un pes $w_{i,k,l}$ amb cinc condicions: 1 on l'exposició és correcta, 0 on està cremat o negat, entre 0 i 1 a la transició, **−1 a la part coberta per la Lluna**, i almenys un pes no nul per píxel entre totes les imatges. Amb $A^*_j$ la imatge de referència (la que té la corona interior ben exposada):

$$f(w_{i,k,l})=\begin{cases}
w_{i,k,l} & i\neq j \ \wedge\ (w_{j,k,l}\neq-1 \ \wedge\ w_{i,k,l}\neq-1)\\
0 & i\neq j \ \wedge\ (w_{j,k,l}=-1 \ \vee\ w_{i,k,l}=-1)\\
|w_{i,k,l}| & i=j
\end{cases}$$

$$b_{k,l}=\frac{\displaystyle\sum_{i=1}^{n} a^*_{i,k,l}\,f(w_{i,k,l})}{\displaystyle\sum_{i=1}^{n} f(w_{i,k,l})}$$

**El pes −1 és la peça clau i és tan simple com decisiva**: diu que aquell píxel no és «sense senyal» sinó «un altre objecte». Si la Lluna el tapa a la imatge de referència **o** a la imatge $i$, la imatge $i$ no hi contribueix. Així el moviment de la Lluna no barreja les dues piles. El resultat representa el Sol tal com era **a l'instant de la imatge de referència**.

És una **mitjana ponderada**, no una suma, i opera sobre valors **calibrats**. ⚠️ El paper **no diu mai com es calibra**: és el forat més gros que té. Per a un flux lineal com el nostre, la resposta òbvia és normalitzar per (temps × ISO × obertura), però **això és una millora sobre el paper, no una lectura del paper**.

**(2) El LDIC** (tesi §4.1.4, programa de Druckmüller de 2006):

$$g(r,\varphi)=\sum_i w(f_i)\,\big(k_i(\varphi)\,f_i(r,\varphi)+q_i(\varphi)\big)$$

Els pesos depenen del valor del píxel i de l'exposició; la transformació lineal $(k,q)$ es calcula **per separat en 60 segments angulars**; i la composició comença per l'exposició **més llarga**. El motiu declarat és exactament el nostre: així es poden compondre imatges amb **distribucions diferents de llum difusa a l'òptica** —per exemple just després de C2 contra just abans de C3— i fins i tot a través de núvols prims.

**Això és molt important i canvia com hem de llegir el G3: el grup de Brno no resol la llum difusa amb un model físic, la resol amb adaptivitat per segments dins la composició.**

**(3) Bemporad (2020)**, per a DSLR: identifica **a cada píxel l'interval de linealitat** entre les 15 exposicions (de 1/4000 a 4 s) i hi fa un ajust lineal. És la variant més disciplinada de les tres i la més propera al nostre cas.

**Pressupost de referència.** Druckmüller (2014): *«at least 10 or more exposures»* i un temps efectiu total de **20 a 50 s** per imatge composta. Els nostres 68 fotogrames útils del R6 i 33 de la Sony estan **per damunt** del que ell fa servir; els nostres 24 s d'integració d'earthshine cauen just dins la seva finestra. **El coll d'ampolla no serà el nombre de fotogrames sinó el registre i el model de fons.**

### 4.5 El model de halo (G3) — el front obert

**DEMOSTRAT per absència:** en tot el corpus de Druckmüller **no hi ha cap model de halo, de llum difusa instrumental ni de PSF**. La llum difusa hi apareix només com a cosa que la composició per segments absorbeix. Si volem un model, l'hem d'anar a buscar fora.

**Els tres components que se sumen al fons**, i que s'han de separar conceptualment abans de modelar res:

1. **PSF instrumental i *veiling glare*.** Llum de la fotosfera i de la corona interior escampada dins l'òptica i el cos de la càmera. Talvala et al. (2007) el quantifiquen per a càmeres digitals i en donen dues vies: **deconvolució per una funció d'escampament mesurada** i **separació directa/indirecta amb una màscara d'oclusió estructurada**, que dona molt millor senyal/soroll. La segona no la podem fer *a posteriori*; la primera sí.
2. **Cel circumsolar atmosfèric.** Schad et al. (2026) mesuren la radiància a **1,54° ± 0,77°** del centre del disc i la lliguen a l'inversió d'aerosols d'AERONET. Durant la totalitat el disc és tapat, però el **cel de fora de l'ombra** continua il·luminant l'atmosfera sobre l'observador; Emde i Mayer (2007) i Ockenfuss et al. (2020) en fan el transport radiatiu 3D.
3. **Corona F real.** No és fons: és senyal. Boe et al. (2021) la separen de la K pel **color** (cinc bandes de 0,5 nm entre 529,5 i 788,4 nm) i troben que la F és **més brillant del que s'esperava a la corona baixa**, cosa que suggereix que està lleugerament polaritzada — contra la hipòtesi habitual.

**Mesura de la PSF, tres vies publicades.**

- **Ocultació d'un cos**: Wedemeyer-Böhm (2008) amb el trànsit de Mercuri sobre Hinode/SOT, ajustant un perfil de Voigt; Yeo et al. (2014) amb el trànsit de Venus sobre SDO/HMI.
- **Estrelles brillants**: Liu et al. (2022), programa **`elderflower`**. Ajusta simultàniament la llum escampada de diverses estrelles brillants **i** un model de fons, píxel a píxel i amb marc bayesià, per caracteritzar l'ala de la PSF fins a **20–25 minuts d'arc**. És el mètode conceptualment més transferible al nostre cas.
- **La Lluna mateixa**: durant la totalitat el disc lunar és un ocultador perfecte, de mida i posició conegudes. **INFERIT**: la seva vora és un esglaó gairebé ideal, o sigui que el perfil de brillantor cap endins del disc és una mesura directa de l'ala de la PSF.

⚠️ **Precaució decisiva i pròpia d'aquesta missió: el disc lunar NO és negre.** Hi ha earthshine real, que és l'objectiu científic número u de l'A7RIIIA, i és el que fan les tres àncores de 1/8 · 1 s · 8 s. **INFERIT** que la separació és possible perquè les dues components tenen forma diferent: l'earthshine és **pla i uniforme** sobre el disc, i el halo de PSF té un **gradient fort cap al limbe** i decau amb la distància a la vora. Un ajust de dos termes —constant més perfil decreixent des del limbe— hauria de separar-los. **Aquesta és la peça central del G3 i no està feta.**

**Deconvolució.** L'estat de l'art és Richardson-Lucy, però té dos defectes: és lent i **conserva el flux dins la imatge**, o sigui que no compta els fotons escampats fora del camp. Hofmeister (2024) reinstaura el **BID** (*Basic Iterative Deconvolution*), que sí que els compta, és **1,8 a 7,1 vegades més ràpid** per a imatges de 4096×4096 (i fins a 150 vegades més per a subregions de 250×250), i coincideix amb Richardson-Lucy **dins l'1 %**. Els set passos, verificats al paper:

1. (Si és subregió) retallar la regió d'interès i un retall de PSF del doble de mida, centrat.
2. (Si és subregió) estimar la llum que entra de fora: posar la regió a zero, convolucionar amb la PSF, i restar-ho de l'observada.
3. $I_o \Rightarrow I_t$ (la imatge observada com a primera aproximació de la vertadera).
4. $I_t * \mathrm{PSF} \Rightarrow I_{o,\mathrm{sim}}$.
5. $I_{o,\mathrm{sim}} - I_o \Rightarrow I_{\mathrm{dev}}$.
6. $I_t - I_{\mathrm{dev}} \Rightarrow I_t$.
7. Repetir des de (4) fins que la desviació sigui negligible.

Amb dues notes d'implementació del paper: fer la convolució al domini de la freqüència per eficiència, i **farcir amb zeros la meitat de la dimensió** per trencar les condicions de contorn periòdiques.

**Proposta operativa per al G3 (INFERIT, cap paper no la dona sencera):**

1. Recalibrar els RAW sense retall (§4.1) i mesurar el fons **en coordenades heliocèntriques**, per fotograma, mai amb un rectangle fix.
2. Mesurar l'ala de la PSF per dues vies independents: perfil cap endins del disc lunar, i estrelles si n'hi ha alguna de prou brillant als fotogrames llargs.
3. Ajustar un model paramètric de PSF (nucli difractiu més ales de potència) i deconvolucionar amb BID sobre el compost HDR lineal.
4. Validar amb el criteri de Talvala: després de la correcció, el disc lunar ha de quedar **pla**, amb un residu que és l'earthshine.
5. Documentar que el que s'ha tret és PSF **més** vinyetatge **més** cel, perquè sense flat no es poden separar.

⚠️ **Tres coses que invaliden qualsevol ajust fet sobre els TIFF actuals**: el terra retallat, la caixa de «cel» que al R6 és a **4,2–5,1 R☉** del Sol (o sigui dins del domini de corona F i de halo), i el fet que el fons **no és estacionari** — a la mateixa exposició de 1/8 s, el camp difús del R6 cau de −7 % a 1,5 R☉ a **−23 % a 6 R☉** entre C2+9 i C2+71.

---

## 5. Fotometria: com es valida que un processat no s'ha inventat estructura

### 5.1 La regla de les dues imatges

Literal de la introducció del FNRGF: *«it is necessary to use at least two images for analysis: the calibrated image with high dynamic range suitable for a quantitative photometric analysis and a processed image with the reduced dynamic range necessary for revealing the underlying coronal structure»*. **El producte científic és el compost lineal de 16+ bits; el filtre n'és una representació per mirar.**

### 5.2 K + F + E

- **K** (*Kontinuierlich*): llum de la fotosfera dispersada per **electrons lliures** (Thomson). És **fortament polaritzada** i les línies de Fraunhofer hi queden esborrades per l'eixamplament Doppler tèrmic.
- **F** (*Fraunhofer*): llum dispersada per la **pols** interplanetària. Conserva les línies de Fraunhofer i **s'ha assumit sempre no polaritzada** — assumpció que Boe et al. (2021) posen en dubte.
- **E**: **línies d'emissió** dels ions coronals (Fe X 637,4 nm, Fe XI 789,2 nm, Fe XIII 1074,7 nm, Fe XIV 530,3 nm…). Amb llum blanca sense filtre hi contribueixen poc.

En llum blanca mesurem $K+F$ i la separació és el problema. Les dues vies publicades: per **polarització** (la clàssica, Lamy 2020 sobre LASCO C2) i per **color** (Boe 2021, cinc bandes estretes). **Nosaltres no tenim ni l'una ni l'altra**: ni polarímetre ni bandes. Per tant **no podem separar K de F amb les nostres dades** i qualsevol densitat electrònica que en surti serà un límit superior. (INFERIT, però directe.)

### 5.3 Baumbach

**DEMOSTRAT** (Çakmak 2023, eq. 1, citant Baumbach 1937/1938): la primera fórmula general de densitat electrònica de la corona a partir de fotometria,

$$N(r)=10^{8}\left(\frac{0{,}036}{r^{1{,}5}}+\frac{1{,}55}{r^{6}}+\frac{2{,}99}{r^{16}}\right)\ \ [\mathrm{cm^{-3}}]$$

amb $r$ en radis solars.

**DEMOSTRAT** (Bazin i Koutchmy 2015): per a **perfils de brillantor** ajusten la llei polinòmica

$$B(\rho)=P_1\rho^{-17}+P_2\rho^{-7}+P_3\rho^{-3}$$

i declaren que ajusta millor que una caiguda exponencial més enllà de 2 R☉. Fan servir una estrella de magnitud 5,6 mostrejada a 80 ADU en verd com a **referència fotomètrica**, i resten fons i cel abans.

⚠️ Els coeficients clàssics de Baumbach per a la brillantor —$0{,}0532\,r^{-2,5}+1{,}425\,r^{-7}+2{,}565\,r^{-17}$ en unitats de $10^{-6}B_\odot$— **són coneguts però NO VERIFICATS** en cap document llegit en aquesta sessió. Si s'han de citar, s'ha d'anar a Baumbach 1937 (*Astron. Nachrichten* 263, 121).

### 5.4 Van de Hulst

**DEMOSTRAT** (Çakmak 2023, §2, resumint van de Hulst 1950). La intensitat dispersada per una columna, amb $x$ la distància projectada i $A(r)$, $B(r)$ els semieixos de l'el·lipsoide de vibració:

$$K(x)=C\int_x^{\infty} N(r)\left[\left(2-\frac{x^2}{r^2}\right)A(r)+\frac{x^2}{r^2}B(r)\right]\frac{r\,dr}{\sqrt{r^2-x^2}}$$
$$K_t(x)=C\int_x^{\infty} N(r)\,A(r)\,\frac{r\,dr}{\sqrt{r^2-x^2}},\qquad
K_t(x)-K_r(x)=C\int_x^{\infty} N(r)\big(A(r)-B(r)\big)\frac{x^2\,dr}{r\sqrt{r^2-x^2}}$$

amb $C=\tfrac{3}{4}R_\odot\sigma=3{,}44\times10^{-14}\ \mathrm{cm^3}$, $R_\odot=6{,}96\times10^{10}$ cm i $\sigma=0{,}66\times10^{-24}\ \mathrm{cm^2}$.

Les components es lliguen al grau de polarització $p(x)$:

$$K_t(x)=\tfrac12\big[1+p(x)\big]K(x),\qquad K_t(x)-K_r(x)=p(x)\,K(x)$$

i s'expandeixen en sèries de potències $K_t(x)=\sum_s h_s x^{-s}$, $K_t-K_r=\sum_s k_s x^{-s}$, amb tres termes cadascuna. La inversió és analítica sobre els coeficients.

**Conseqüència per a nosaltres**: sense polarímetre no tenim $p(x)$ mesurat i hem de fer servir el $p(x)$ **de model**, que és el que van de Hulst mateix va fer. Això és acceptable i és el que fan els papers, però s'ha de declarar.

### 5.5 Calibratge absolut a la manera Bemporad

És la referència directa per al nostre cas (DSLR, 15 exposicions de 1/4000 a 4 s, 3,7 ″/px, resolució efectiva de 10,2 ″ mesurada amb estrelles). El seu procediment:

1. Interval de linealitat **per píxel** entre les exposicions, amb ajust lineal.
2. Correcció de vinyetatge.
3. Estrelles com a **verificació**: α-Leo (m=1,35) i ν-Leo (m=5,15) donen $\Delta m_{G,\mathrm{obs}}=-2{,}5\log_{10}(I_{G,\nu}/I_{G,\alpha})=3{,}80$, que coincideix **exactament** amb $\Delta m=5{,}15-1{,}35=3{,}80$. Aquesta coincidència és la que autoritza a fer servir magnituds visuals.
4. **Calibratge absolut** a partir de la magnitud aparent del Sol, $m_\odot=-26{,}75$, i de la imatge del Sol sencer.
5. Intercalibratge amb K-Cor de Mauna Loa: factor $K_G=1{,}54\times10^{11}\ B_\odot\,\mathrm{DN/s}$.

**I la conclusió que hem de tenir present**: el seu calibratge absolut discrepa **d'un factor ~2** respecte de MLSO — i és el mateix factor que s'ha trobat entre prediccions MHD i observacions. **Un factor 2 és l'estat de l'art en aquest terreny.** No ens hem d'exigir més.

**Per a nosaltres** (INFERIT): el pont podria ser la parcial filtrada de 1/400 amb l'ASSF100 OD 5,0, però **la densitat òptica real del filtre no està mesurada** (NO VERIFICAT), i una OD nominal de 5,0 pot desviar-se fàcilment 0,2–0,3 dex. Si es vol calibratge absolut, s'ha de mesurar el filtre.

### 5.6 Set proves per no inventar estructura

Aquestes són les proves que s'han d'aplicar a **tota** imatge processada abans de publicar-la.

**Prova 1 — perfil radial en lineal (INFERIT).** Traçar el perfil radial mitjà sobre el compost lineal i sobre la sortida del filtre. El filtre pot canviar-ne l'escala i el pendent, però **no pot canviar l'ordre relatiu** de dos punts a la mateixa alçada si l'estructura és real.

**Prova 2 — coherència entre trens (INFERIT, i és la nostra millor arma).** Tenim dos telescopis independents, amb escales de placa diferents (2,158 i 3,234 ″/px), òptiques diferents i sensors diferents. **Una estructura coronal real ha de sortir als dos; un artefacte de nucli, no.** És l'equivalent barat de les dues expedicions que Druckmüller combinava.

**Prova 3 — invariància a la rotació (INFERIT).** Girar la imatge d'entrada un angle arbitrari, filtrar, i desgirar. Si l'estructura canvia, és del filtre. Detecta immediatament qualsevol filtre anisòtrop, i és la manera de comprovar la condició (c) de l'ACHF sense mirar l'espectre.

**Prova 4 — espectre de fase del nucli (DEMOSTRAT com a criteri, Druckmüllerová §5.1).** Calcular $\arg\mathcal{F}(C)$ del nucli emprat. Si no és pràcticament zero, el filtre desplaça estructures. Amb això es va desqualificar el desenfocament radial de Photoshop.

**Prova 5 — composició de colors (DEMOSTRAT, Druckmüller et al. 2006, fig. 5).** Compondre dos processats diferents del mateix compost, un en blau i l'altre en taronja. **On coincideixen surt gris; on divergeixen surt color saturat.** És una eina de diagnòstic qualitativa però immediata, i és la que els autors mateixos van fer servir per demostrar que el radial blur és cec a les tangencials.

**Prova 6 — injecció sintètica (INFERIT).** Afegir al compost lineal una estructura sintètica de contrast conegut i comprovar que surt amb el mateix contrast relatiu al processat. És l'única prova quantitativa de la llista.

**Prova 7 — contrast amb model (DEMOSTRAT com a pràctica, Boe 2024).** Comparar la topologia amb la predicció PFSS o MHD (Predictive Science). ⚠️ Amb la precaució històrica de la tesi: durant anys es va creure que els models estaven equivocats i **els equivocats eren les imatges**. El model és un contrast, no un àrbitre.

---

## 6. Programari

### 6.1 El que existeix i funciona

**`sunkit-image` 0.7.0** (DEMOSTRAT: instal·lat en un entorn nou al Mac de Pere, inspeccionat i executat, i esborrat després). ⚠️ **Ara mateix no està instal·lat** a cap dels tres intèrprets del Mac; cal `pip install sunkit-image` a `~/.venvs/eines-ia-py312`.

Conté **cinc** dels filtres d'aquest dossier, no un:

| Funció | Mètode | Entrada |
|---|---|---|
| `sunkit_image.enhance.mgn` | MGN | `ndarray` **o** `Map` |
| `sunkit_image.enhance.wow` | WOW | `ndarray` o `Map` |
| `sunkit_image.radial.nrgf` | NRGF | **`sunpy.map.GenericMap`** |
| `sunkit_image.radial.fnrgf` | FNRGF | **`GenericMap`** |
| `sunkit_image.radial.rhef` | RHEF | **`GenericMap`** |

Signatura real i verificada:

```
mgn(data, *, sigma=None, k=0.7, gamma=3.2, h=0.7, weights=None,
    truncate=3, clip=True, gamma_min=None, gamma_max=None)
```

**Trampes verificades, totes quatre:**

1. **Tots els paràmetres després de `data` són només per nom.** `mgn(imatge, [1.25, 2.5])` peta amb `TypeError: too many positional arguments`.
2. **Vol `dtype` float i dades normalitzades pel temps d'exposició.** Amb `uint16`, la protecció interna `data[data <= 0] = 1e-15` es converteix silenciosament en no fer res i **`clip=True` deixa de protegir sense avisar**.
3. **Modifica l'array del cridant en el lloc** i **retorna `float32`**, no `float64`. Xoca amb el nostre gate G5: cal passar-li una còpia i tornar a `float64`.
4. **Els filtres radials no accepten arrays.** `fnrgf(array)` peta amb `AttributeError: 'numpy.ndarray' object has no attribute 'wcs'`. Volen un `GenericMap` amb metadades WCS (radi solar, píxel de referència). Per a TIFF d'eclipsi sense capçalera solar, **s'ha de fabricar el `Map` a mà**, i això és feina.

⚠️ Els paràmetres per defecte del `fnrgf` de `sunkit-image` **no són els del paper**: `order=3` contra ordre 10, i `number_angular_segments=130` contra $n_s=50$. **NO VERIFICAT** si la implementació segueix les fórmules de §2.4 o una variant.

**`wavelets`** d'Auchère: `github.com/frederic-auchere/wavelets`. Codi de referència del WOW.

**FNRGF a SolarSoft IDL**, dins CORIMP (DEMOSTRAT per cerca; no és una promesa pendent).

### 6.2 El que existeix i no podem fer servir

**Corona, LDIC i PhaseCorr**: programari intern del grup de Brno, **Windows**, sense pàgina de descàrrega ni dipòsit. El LDIC és el que ens faria més falta i és el que no hi ha. **NAFE Image Analyzer 1.0**: descarregable però Windows.

### 6.3 El que s'ha de programar aquí

Per ordre de dependència:

1. **Recalibratge RAW sense retall** (§4.1). És el bloquejador de tot.
2. **Mesura de fons en coordenades heliocèntriques**, per fotograma.
3. **Correlació de fase modificada**: $H_\varrho$ + màscara anular + $N_{p,q}G_\sigma$ + moments. Es pot recolzar en `skimage.registration.phase_cross_correlation` per al nucli, però el pretractament és nostre.
4. **Registre lunar independent** per ajust de circumferència al limbe dels fotogrames curts.
5. **Compositor HDR ponderat** amb el pes **−1** al disc lunar i l'interval de linealitat per píxel.
6. **Model de halo i deconvolució BID** (§4.5). El front obert.
7. **ACHF reimplementat** amb les eqs. (5.1)+(5.2), joc de $\sigma$, com a referència.

**Notes d'entorn** (regles globals de Pere): l'únic entorn viu és `~/.venvs/eines-ia-py312`; **cap script no ha d'anomenar un intèrpret concret**, ha de detectar-ne un i fallar amb un missatge útil.

---

## 7. Bibliografia

### A la carpeta `/Users/USUARI/Desktop/Eclipse 2026/Papers Druckmuller`

**Nucli metodològic de Brno**

- Druckmüller, M.; Rušín, V.; Minarovjech, M. (2006). *A new numerical method of total solar eclipse photography processing*. **Contrib. Astron. Obs. Skalnaté Pleso** 36, 131–148. → `ta3.sk/caosp/Eedition/FullTexts/vol36no3/pp131-148.pdf` · ⚠️ el PDF **no porta DOI imprès**; el codi ADS habitual, `2006CoSka..36..131D`, **no s'ha verificat al document**.
- Druckmüller, M. (2009). *Phase correlation method for the alignment of total solar eclipse images*. **ApJ** 706, 1605–1608. DOI 10.1088/0004-637X/706/2/1605.
- Druckmüllerová, H.; Morgan, H.; Habbal, S. R. (2011). *Enhancing coronal structures with the FNRGF*. **ApJ** 737, 88. DOI 10.1088/0004-637X/737/2/88.
- Druckmüllerová, H. (2013). **Tesi doctoral completa**, 128 p., VUT Brno. → **el document més útil de tots**: fórmula de l'ACHF (§5.2), LDIC (§4.1.4), calibratge (§4.1.2), correcció del FNRGF-N (cap. 6).
- Druckmüllerová, H. (2014). *Versió curta de la tesi*, 36 p., ISSN 1213-4198.
- Druckmüller, M.; Habbal, S. R.; Morgan, H. (2014). *Discovery of a new class of coronal structures in white light eclipse images*. **ApJ** 785, 14.
- Morgan, H.; Druckmüller, M. (2014). *Multi-scale Gaussian normalization for solar image processing*. **Solar Phys.** 289, 2945–2955. → `arxiv.org/pdf/1403.6613`.
- Morgan, H.; Habbal, S. R.; Woo, R. (2006). *The depiction of coronal structure in white-light images* (NRGF). **Solar Phys.** 236, 263–272. DOI 10.1007/s11207-006-0113-6.
- Martišek, K. (2008/2012). *Adaptive filters for 2-D and 3-D digital images processing*. Tesi, VUT Brno.
- Hrazdíra, Z. (2021/2022). *High precision sub-pixel image registration methods and their applications in astrophysics*. Tesi, VUT Brno.
- Kalenská, P. (2024). *Separation of the dynamic image component for the solar corona plasma research*. Tesi, VUT Brno. → paràmetres reals del NAFE: $\gamma=2{,}6$, $w=0{,}2$, $\sigma=15$.
- Kalenská, P.; Rajmic, P.; Gebrtová, K.; Druckmüller, M. (2024). *A novel technique for the extraction of dynamic events in EUV solar images*. **ApJS** 275, 15.

**Filtres posteriors**

- Auchère, F. et al. (2023). *Image enhancement with wavelet-optimized whitening* (WOW). **A&A** 670, A66.
- Gilly, C.; Cranmer, S. (2025). *RHEF*. **Solar Phys.** → `arXiv:2511.02798`.
- Patel, R. et al. (2022). *SiRGraF*. **Solar Phys.** 297, 27.
- Seaton, D. et al. (2023). *SWAP azimuthally varying radial filter*. **Solar Phys.**
- Liu, Y. et al. (2025). *Self-supervised denoising TDR*. **Nature Astronomy**.

**PSF, llum difusa i cel (el material del G3)**

- Hofmeister, S. J. (2024). *The Basic Iterative Deconvolution*. **Solar Phys.** → `arXiv:2312.11784v3`.
- Talvala, E.-V.; Adams, A.; Horowitz, M.; Levoy, M. (2007). *Veiling glare in high dynamic range imaging*. **SIGGRAPH**.
- Liu, Q. et al. (2022). *A method to characterize the wide-angle PSF of astronomical images* (`elderflower`). **ApJ** 925, 219 → `arXiv:2110.11598v2`.
- Yeo, K. L. et al. (2014). *PSF of SDO/HMI from the Venus transit*. **A&A** 561, A22.
- Wedemeyer-Böhm, S. (2008). *PSF of Hinode/SOT from the Mercury transit*. **A&A** 487, 399.
- Schad, T. A. et al. (2026). *Joint diagnostics of circumsolar sky brightness at Mauna Loa*. **ApJ** → `arXiv:2603.09196`.
- Emde, C.; Mayer, B. (2007). *3D radiative transfer during a total eclipse*. **ACP** 7, 2259.
- Ockenfuss, P. et al. (2020). **ACP** 20, 1961.
- *Dust-induced stray light in ground coronagraphs* (2026) → `arXiv:2605.12979`; *Lijiang coronagraph dust scattering background correction* → `arXiv:2311.14784`.

**Fotometria i ciència**

- Bemporad, A. (2020). *Coronal electron densities derived with images acquired during the 21 August 2017 TSE*. **ApJ** → `arXiv:2010.15005v2`. **La referència directa per a DSLR.**
- Boe, B. et al. (2021). *F-corona color and brightness, K-Cor calibration*. **ApJ** 912, 44.
- Lamy, P. et al. (2020). *LASCO C2 photopolarimetry, K–F separation*.
- Çakmak, H. (2023). *Simplified van de Hulst electron density* → `arXiv:2310.14903`.
- Bazin, C.; Koutchmy, S. (2015). *Photometric analysis of the solar corona*. **SF2A**.
- Boe, B. et al. (2024). *TSE white-light benchmark of PFSS models*.
- Boe, B.; Habbal, S. R.; Druckmüller, M. (2020). *Coronal magnetic field topology via RHT*. **ApJ** 895, 123.
- Hanaoka, Y. (2021, 2024); Shaik & Habbal (2023); Takeda (2020); Vorobiev (2020) — polarimetria de corona; **NO LLEGITS** en aquesta sessió.

### No obtinguts

- **Druckmüller, M. (2013). *A noise adaptive fuzzy equalization method…* ApJS 207, 25.** DOI 10.1088/0067-0049/207/2/25. Unpaywall el marca lliure de llegir, però IOPscience el protegeix amb captcha. **Pere el pot baixar a mà en deu segons.** La formulació sencera, però, ja la tenim per la tesi de Kalenská §3.3.2: $f_B=(1-w)\varphi_\gamma(f_A)+w\,E_{N,\sigma}(f_A)$, amb $w$ entre 0,05 i 0,3.
- **Druckmüller, M.; Druckmüllerová, H. (2014). *NAFE with variable neighborhood…* LNCS 8466, ~280–289.** DOI 10.1007/978-3-319-07148-0_23. **Tancat.** És, sobre el paper, la versió del NAFE pensada per a corona d'eclipsi. Substitut: §5.4 de la tesi de Druckmüllerová.
- **Habbal, Druckmüller i Morgan (2014). *Role of image processing in solar coronal research*. LNCS 8466, ~27–38.** DOI 10.1007/978-3-319-07148-0_3. **Tancat.**
- **Els dos articles de 2020 a ApJS sobre correlació de fase iterativa.** Bloquejats per IOP. Substitut: la tesi de Hrazdíra, que sí que tenim.
- **Rušín, Druckmüller et al. (2010). A&A 513, A45.** Obert a aanda.org però el servidor retorna 403.
- **Baumbach, S. (1937). *Astron. Nachrichten* 263, 121.** No consultat; els coeficients de brillantor citats habitualment no s'han verificat contra l'original.
- **NASA ADS**: no escombrat (cal testimoni d'API). S'ha substituït per OpenAlex, que dona 105 obres de Druckmüller.

---

## 8. El que encara no sabem

Honestament, i per ordre de risc.

**1. No sabem quin filtre és el millor per a aquestes dades, i ningú no ho sap.** No existeix cap comparació publicada entre ACHF, MGN, WOW i RHEF sobre un compost HDR real d'eclipsi total en llum blanca. La manera de resoldre-ho no és citar autoritat: és passar el mateix compost lineal pels quatre i mirar-los al costat.

**2. No tenim el model de halo, i el corpus de Brno no ens el donarà.** La seva solució és adaptivitat per segments dins la composició, no un model físic. Les peces per fer-ne un les tenim (Talvala, Liu, Yeo, Wedemeyer-Böhm, Hofmeister), però la separació entre **halo de PSF** i **earthshine real** sobre el disc lunar no està feta i és específica d'aquesta missió.

**3. No sabem quant val la densitat òptica real del filtre solar.** Sense això, no hi ha calibratge absolut per la via de les parcials filtrades.

**4. No podem separar K de F.** Ni polarímetre ni bandes estretes. Qualsevol densitat electrònica derivada d'aquestes dades serà un límit superior, amb un $p(x)$ de model.

**5. L'ACHF viu no està publicat.** El que és reimplementable és el predecessor. La combinació multi-$\sigma$ i la «no-linearity in the use of filtered images» de Corona 4.1 no es descriuen enlloc. Qualsevol reimplementació dona un filtre de la mateixa família, no una reproducció.

**6. No sabem les unitats de $\varrho$ i $\omega$** al filtre tangencial de la correlació de fase, i això canvia l'escala espacial del filtre. S'ha de calibrar per assaig.

**7. No sabem si el `fnrgf` de sunkit-image implementa el paper.** Els seus valors per defecte ($\omega=3$, $n_s=130$) no coincideixen amb els publicats, i no s'ha verificat el codi.

**8. Cap dels papers no dona un criteri quantitatiu de qualitat.** Els coeficients d'atenuació, el $\sigma$ de l'ACHF, els pesos $K_1/K_2$ i la barreja 0,4/0,6 es fixen a ull. Les set proves de §5.6 són el nostre substitut, i sis de les set són invenció nostra, no de la bibliografia.

**9. No sabem la magnitud real de l'error de registre entre els dos trens.** Tenim la deriva d'apuntat del R6 mesurada dues vegades amb un 18 % de discrepància (0,71–0,75 ″/s per correlació de fase contra ~0,61 ″/s de `research/71`), i no s'ha resolt d'on ve.

**10. El banc de darks té defectes no explicats**: un fotograma no fosc dins el master de 0,5 s del R6, i un pedestal de 511,0 al master de 10 s quan la resta és 512,0. Cap dels dos s'ha diagnosticat.

**11. I la incògnita que no es pot tancar amb dades**: **no tenim camp pla.** Sense flat, el vinyetatge, la PSF i el cel queden barrejats en un sol terme empíric. Es pot modelar, però no es podrà dir que s'ha mesurat la PSF de l'instrument. S'ha de dir així, sempre.