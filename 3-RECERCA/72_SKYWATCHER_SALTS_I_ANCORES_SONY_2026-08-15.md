# El tren Sony/Skywatcher durant la totalitat: dos salts de muntura, i el misteri de l'àncora moguda resolt

Data: 15 d'agost de 2026, matinada. Mateix mètode que `research/71` (limbe
lunar subpíxel + tancament amb efemèrides), aplicat als 18 fotogrames de mig
eclipsi de l'A7RIIIA + 300 GM. Validació visual dels ajustos inclosa (lliçó
de la trampa 0 del 71).

## 1. La muntura va fer DOS SALTS en ple mig de la totalitat

| Tram | Posició de la Lluna | Estat |
|---|---|---|
| C2+12 → C2+29 | (3670, 3483) ± 0,5 px | **estable** (tríada 1 + àncora 1) |
| ~C2+30 → +42 | **SALT 1: +223 px en x** (~12′) | |
| ~C2+42 → +57 | **SALT 2: −715 px en y** (~39′) | |
| C2+57 → C2+83 | (3894, 2768) ± 1,0 px | **estable** (àncora 3 + tríades 2-3) |

✅ **CAUSA, per testimoni de Pere (15-08): en treure el filtre solar va moure
la lent de 300 mm.** L'evidència hi encaixa i hi afegeix la cronologia fina:
els contactes de C2 (DSC06973-75) surten ben exposats → **el filtre ja era
fora abans de C2−3,35**; els salts, però, es materialitzen a C2+30 i C2+50.
O sigui: la manipulació va deixar la muntura destensada i **la pertorbació es
va alliberar amb retard i en dos temps d'un sol eix cadascun** — fricció
cedint sota càrrega (3,6 kg de tren amb braç de palanca a 9° d'altura), no
vent ni seeing.

✅ **El misteri de la DSC06990 (àncora 2 de 8 s, «motion-smeared» al consens
de postprocessat) queda resolt**: el seu punt mitjà (C2+46) cau exactament
entre els dos salts — **la muntura va cedir durant aquella exposició**, com a
conseqüència diferida del contacte amb la lent. El consens ja parlava dels
«Sony field jumps» com a pseudo-dither: són aquests dos salts.

📌 **Lliçó per al 2027**: el gest de treure el filtre és una manipulació de
càrrega en el pitjor moment; després de treure'l cal re-tensar/verificar
embragatges o preveure un filtre d'extracció sense contacte. Candidata a la
checklist física (canviar-la toca el SHA dels perfils: decisió a part).

## 2. Entre salts, la deriva és petita — i juga A FAVOR de les àncores

Ritme aparent de la Lluna al sensor: 0,203″/s (tram 1) i 0,302″/s (tram 2),
contra els 0,5905″/s del relatiu pur: la deriva de la muntura (0,4-0,8″/s
segons direcció, mateix ordre que la iOptron) **cancel·la parcialment el
moviment lunar**. Conseqüència d'or per a l'earthshine:

- **àncora 1 (DSC06987, 8 s): ~0,5 px de moguda interna**;
- **àncora 3 (DSC06993, 8 s): ~0,75 px**.

Contra els 3,5 px del 10,3 s del Vixen. Les dues àncores supervivents són
**nítides**.

## 3. Escala de placa i implicació per a l'earthshine

- **Escala mesurada: 3,234″/px** (radi lunar 302,8-304,5 px a les exposicions
  curtes; les de 8 s donen R ~292: mateix encongiment per glow que al Vixen —
  mai mesurar radis amb fotogrames profunds). Focal efectiva ≈ 288 mm.
- Fotons per píxel i per àncora contra el 10,3 s del Vixen: àrea de cel per
  píxel ×2,25, obertura ×1,43, temps ×0,78 → **×2,5 més senyal per píxel**,
  amb moguda interna 5 vegades més petita. **La intuïció de Pere és correcta:
  l'earthshine bo ha de sortir de les àncores Sony** (2 de netes de 3), amb
  el Vixen com a segona veu i control.
- L'apilat Sony ha de ser **conscient de segments**: àncora 1 i àncora 3 són a
  segments diferents (separats 750 px); l'alineació per limbe ho absorbeix,
  però màscares i halo s'han de calcular per fotograma, no compartits.

Pendent: el rastre de correccions de l'operador a les 122 parcials Sony
(l'ajust RANSAC només va passar 9/122; afinar-lo si es vol el sawtooth
complet del Skywatcher com el del 71 §1).

## 4. EARTHSHINE DETECTAT: les mars lunars, als dos cossos, amb dues proves d'independència

15-08, tarda. Pila de les dues àncores Sony bones (DSC06987 + DSC06993,
calibrades per Pere amb masters de 44 darks a 8 s), alineada al limbe lunar
(desplaçament entre membres +222,8/−717,9 px, coincidència després d'alinear
**0,08 px**), a `~/Desktop/Eclipse 2026/300mm/Earthshine_Claude/`.

**El disc no és fosc: seu sobre un pedestal de halo de ~44.500 ADU16
(68 % de l'escala), gairebé pla al centre (+4 % a r=250) i que puja
bruscament cap al limbe** — la corona saturada ×800 hi projecta les ales de
la PSF i el limbe queda menjat ~10 px cap a dins (R aparent 292 contra 302
reals). Els 12-14 px d'«amplada de vora» dels 8 s són aquesta rampa, isòtropa
als quatre azimuts: **no és moguda ni desenfocament** (els fotogrames curts
del mateix instant donen 1,5-2 px). La nitidesa intrínseca del disc és
intacta.

**Restant una superfície polinòmica de grau 4 dins r<267 px, apareix el patró
de mars i terres altes.** Amplitud ±3σ = 729 ADU16 al canal G sobre soroll
d'alta freqüència de 175. Les dues proves de la porta G2 («dues suports
independents»):

1. **Fotograma contra fotograma** (DSC06987 i DSC06993, cadascun detrendat al
   seu propi centre, 750 px separats al sensor): **r = 0,899**; controls
   nuls (un dels dos girat 90/180/270°): 0,14-0,21. Un patró fix al sensor
   —PRNU, pols, sense flats— no pot donar això.
2. **Sony contra Vixen** (òptica, sensor, exposicions i escala diferents; el
   Vixen és la fusió 2 s + 10,3 s de `research/71`, reescalada ×0,667):
   escombrada de rotació 0-360° i mirall: **pic únic r = 0,886 a 327,25°,
   sense mirall**; distribució sobre tots els angles: mediana 0,32, p95 0,54.
   **La rotació relativa entre els dos sensors queda mesurada: 327,25°.**

Límits honestos: el detrend polinòmic no és el model físic de halo (G3);
s'endú la component d'albedo de gran escala i **no dona fotometria** — dona
el mapa d'estructura a escales intermèdies. L'anell brillant a la vora de la
màscara és efecte del polinomi/rampa, no lunar.

✅ **IDENTIFICACIÓ CONFIRMADA CONTRA EL MAPA D'ALBEDO LROC (15-08, vespre).**
Codex (contrast xhigh, §5) va assenyalar amb raó que les dues proves anteriors
exclouen un patró fix al sensor **però no un residu comú lligat a la geometria
Sol-Lluna** (estructura de la corona projectada pel halo, igual per als dos
trens). El gate d'identificació és el registre contra un mapa real: LROC WAC
(NASA SVS 4720, `lroc_color_poles_4k.tif`, cilíndric 4096×2048, autoritzat
per Pere), projectat ortogràficament amb libració lliure i **el mateix
tractament** que el nostre residu (mateix polinomi grau 4 dins r<267, mateix
suavitzat, mateixa màscara r<240):

| Parella | r | nul (mediana / p95 sobre 0-360°) | rotació |
|---|---|---|---|
| Sony 2×8 s ↔ LROC | **0,684** | −0,03 / 0,14 | 71,5° |
| Vixen 2 s+10,3 s ↔ LROC | **0,511** | −0,07 / 0,25 | 38,5° |
| Sony ↔ Vixen (§4, directa) | 0,886 | 0,32 / 0,54 | 327,25° ≡ −32,75° |

**El triangle de rotacions tanca a 0,25°** (71,5 − 38,5 = 33,0 contra 32,75).
Libració ajustada: lon +4°, lat −1° (graella d'1°). Cap artefacte de halo o
de corona pot reproduir el mapa d'albedo lunar mar per mar en dos trens
independents: **l'earthshine queda identificat.** La fotometria continua
pendent del model físic de halo (G3). Figura:
`Earthshine_Claude/identificacio_LROC_sony_vixen.png`; mapa de referència
desat al costat.

Fitxers: `stack_8s_x2_lluna{,_16bit_lineal,_sRGB_visible}.tif`,
`earthshine_residu_2x8s_G_float.tif` (mapa científic),
`earthshine_residu_2x8s_{G,RGB}_visible.tif`.

## 5. PROPOSTA (Claude, 15-08) — què fer amb la foto final d'earthshine — CONTRASTADA AMB CODEX (sol·xhigh)

**Veredicte de Codex: APPROVE WITH CHANGES.** «L'arquitectura de dos productes
independents és bona; la fusió al 2 % encara no és defensable.» Correccions
adoptades (el text original de la proposta es conserva a sota tal com es va
contrastar; on discrepa, mana aquest bloc):

1. **Aritmètica de la taula, errònia**: 2×8 s + 3×2 s = √2,75 = 1,66 (no
   1,73); + 2×1 s = √3 = 1,73 (no 1,80). Guany total sobre les dues àncores:
   **+22,5 %**, no «+22 % pels 2 s».
2. **Física dels pesos del Vixen, errònia per doble compte de la focal**
   (escala de placa × nombre f). Per font extensa els fotons per unitat de cel
   són ∝ D²·t: Vixen 10,3 s / Sony 8 s = 90²×10,3 / 107²×8 = **0,91** → en
   graella lunar comuna un 10,3 s del Vixen val **~0,95 àncores**, no 0,58, i
   un 2 s ~0,42: **el Vixen és un soci gairebé igual en soroll fotònic** (1,8
   contra 1,7 unitats). Codex ho expressa per píxel natiu (0,64/0,28); totes
   dues xifres són priors: **els pesos finals surten de la variància residual
   empírica en graella comuna**, no del pressupost.
3. **Piles niades amb porta fora de mostra per capa**: 2×8 s = producte de
   control científic → +2 s → +1 s (**dues**, 06985 i 06991; la 06988 cau
   durant el primer salt de muntura i el limbe la rebutja) → Vixen. Cada capa
   entra només si redueix la variància sense residu estructurat; fins llavors
   el Vixen és control, no ingredient. Halo per tren, exposició, segment i
   geometria de cada fotograma.
4. **La porta fixa del 2 % es retira**: exigiria conèixer el halo de 44.500
   ADU16 al 0,3-0,5 % i el detrend actual s'ha menjat la magnitud que
   compararia. Substituïda per una **porta d'incertesa predefinida**: màscara i
   bandes espacials congelades, registre LROC, només guany+offset entre trens,
   bootstrap/leave-one-out, residu inter-tren compatible amb la incertesa i
   sense estructura.
5. **Risc irreductible (Codex)**: sense calibració independent del PSF/halo en
   aquella geometria, albedo de gran escala i llum difosa són parcialment no
   identificables; la morfologia intermèdia és creïble, la fotometria al 2 %
   no s'hi podrà atribuir honestament. I la refutació que ha canviat el pla:
   les proves d'independència de §4 no excloïen un residu comú Sol-Lluna →
   el registre LROC ha passat de «pas següent» a **gate d'identificació**
   (superat el mateix vespre, vegeu §4).

**Ordre operatiu acordat**: Sony 2×8 s referència → capes Sony condicionals
→ Vixen independent i multiescala → validació externa → només llavors fusió
i compost HDR.

## 6. EXECUTAT (15-08, vespre): model físic de halo, portes per capa i pila única

**Model de halo (per tren, ajustat sense LROC per no ser circular)**: dins del
disc, `obs = A1·(Font ⊛ K1) + A2·(Font ⊛ K2) + pla de cel + c`, amb Font =
HDR de la corona real del grup del fotograma (cascada per saturació dels
1/100 → 8 s, disc lunar a zero), K = Moffat `1/(1+(d/s)²)^β` unitaris,
graella (s, β) per a un nucli proper i un d'ample, amplituds i pla lineals.
Un sol nucli **no** funciona (residu 730 ADU16, coeficient d'albedo negatiu):
calen ales properes (pujada al limbe) i dispersió ampla (pedestal pla).

| | Sony 2×8 s | Vixen 3×10,3 s |
|---|---|---|
| nucli proper (s px binat, β) · A1 | (6, 1,5) · 0,016 | (1,5, 1,5) · 0,058 |
| nucli ample · A2 | (320, 1,5) · 0,027 | (160, 2,5) · 0,001 |
| residu de l'ajust | 326 ADU16 | 182 ADU16 |
| pedestal de halo al centre | ~8.000 ADU16 (+ constant ~34.000 degenerada amb cel/vel) | |

**Validació fora de mostra contra LROC** (mètrica amb vora farcida, r<105
binat), i **portes per capa** (una capa entra només si no empitjora):

| pila | r escala completa | r mitja escala | soroll (ADU16/s) |
|---|---|---|---|
| **Sony 2×8 s** | **0,679** | **0,731** | 14,9 |
| Sony +3×2 s | 0,579 ↓ | 0,687 ↓ | 13,7 |
| Sony +2×1 s | 0,575 ↓ | 0,613 ↓ | 13,3 |
| Vixen 3×10,3 s | 0,650 | 0,401 | 9,1 (escalat) |
| Vixen +3×2 s | 0,493 ↓ | — | |
| Fusió Sony8+Vixen (guany+offset, variància inversa) | 0,684 (=) | 0,509 ↓ | 8,1 |
| (referència) polinomi grau 4 de §4 | 0,443 | 0,756 | |

Sony↔Vixen a mitja escala: 0,68; residu Sony−Vixen amb estructura d'albedo
(r=0,25) → els dos trens **no** coincideixen prou per fusionar. **Cap capa
curta ni el Vixen no passa la porta: la pila única final és la Sony 2×8 s amb
halo modelat.** El model físic recupera l'estructura de **gran escala** (0,68
contra 0,44 del polinomi) conservant la de mitja escala.

⚠️ **Color no fiable**: l'ajust per canal RGB deixa el canal R amb residu
919 ADU16 (×3) i pedestals diferents per canal → dominants falses de gran
escala. El producte és **luminància (canal G)**; els fitxers RGB queden com
a `EXPERIMENTAL_color_no_fiable_*`. Fotometria absoluta: no (constant
degenerada). Zona vàlida: r < 267 px (plena) — l'anell exterior el menja el
halo saturat.

**Lliurable**: `~/Desktop/Eclipse 2026/Earthshine_FINAL/`
(`earthshine_FINAL_Sony2x8s_LUM_fullres_*` a 3,234″/px, R=302, orientació
del sensor Sony; versions binades ×2 amb més senyal/soroll; controls Sony i
Vixen; `LLEGEIX-ME.txt`; paràmetres del halo en JSON). Eines:
`research/tools/` (`halo_sony2_full.py`, `halo_vixen_full.py`,
`final_rgb_full.py`, copiats des de la sessió).

### Text original de la proposta (tal com es va contrastar)

Pregunta de Pere: per a la foto final, sumar tots els fotogrames de llarga
exposició de la Sony i del Vixen, o limitar-se a la Sony?

**Proposta: ni suma cega ni Sony sola. Dos productes separats, cadascun amb
tots els seus fotogrames llargs ponderats, i fusió només al final i només si
passa la porta del consens.**

Pressupost de senyal/soroll a l'escala de les mars, per fotons per unitat de
cel (unitat = una àncora Sony de 8 s; SNR ∝ √(temps × obertura² × àrea de
píxel al cel), fons dominat pel halo, que també escala amb l'exposició):

| Conjunt | n | contribució/fotograma | acumulat |
|---|---|---|---|
| Sony 8 s | 2 | 1,00 | 1,41 |
| Sony 2 s (tríades) | 3 | 0,50 | 1,73 (+22 %) |
| Sony 1 s | 2 (06985, 06991) | 0,35 | 1,80 |
| Vixen 10,3 s | 3 | 0,58 | Vixen sol 1,10 |
| Vixen 2 s | 3 | 0,26 | |
| Tot junt | | | ~2,1 (+18 % sobre la Sony sencera) |

Arguments:

1. La Sony aporta ~75 % de la informació; els seus 2 s i 1 s valen més
   (+22 %) que tot el Vixen (+18 %). Apilat **ponderat per variància inversa
   en unitats lineals dividides per l'exposició** (G4), mai suma en cru.
2. El coll d'ampolla no és el soroll sinó el **halo**: pedestal de ~44.500
   ADU16 (Sony) per un senyal d'earthshine de potser 6-12.000: sistemàtica
   4-7× el senyal, amb pendent. Cap nombre de fotogrames la redueix; només un
   **model físic del halo per tren i per grup d'exposició** (G3; la rampa de
   ~10 px dins del limbe és la PSF mesurable).
3. **Cada tren té el seu halo** (PSF pròpia): fusionar cossos abans de treure'l
   barreja dues sistemàtiques; separar-los conserva l'acord entre cossos com a
   validació (r=0,89 a §4).
4. Porta de fusió del consens: si després del halo els dos coincideixen a
   ≤2 % en la component de gran escala, es fusionen amb els pesos de la taula
   (+18 %); si no, el Vixen és control i la Sony el producte.
5. La foto final és un **compost**, no una suma: capa d'earthshine (alineada a
   la Lluna) inserida dins l'HDR de corona (alineat al Sol) a la posició de la
   Lluna a l'instant de referència de la corona (0,59″/s de moviment relatiu).

Ordre d'execució proposat: producte Sony sencer amb halo modelat → producte
Vixen → porta de fusió → compost.
