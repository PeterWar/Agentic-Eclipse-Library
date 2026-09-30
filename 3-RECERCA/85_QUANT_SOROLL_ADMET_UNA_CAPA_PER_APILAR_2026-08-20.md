# 85 — Quant soroll admet una capa per entrar a un apilat? (20-08-2026)

⚠️ **Aquest document només fa preguntes.** Pere les va plantejar el 20 d'agost i va
demanar explícitament que quedessin anotades com a **fil d'investigació canònic**, sense
resposta. Res del que hi ha aquí no és una decisió, una recomanació ni una mesura nova:
és el plantejament, i el context del projecte que fa que les preguntes siguin bones.

## 1. Les dues preguntes, tal com les va fer

1. **Quant de soroll pot tenir una capa per considerar-la vàlida per apilar?**
2. **El criteri pot ser una mica més flexible si es fa una reducció de soroll poc
   agressiva?**

## 2. Per què són bones preguntes

Perquè el projecte ha apilat molt i **aquest criteri no s'ha escrit mai**. El que hi ha
avui és això:

- **Tot el que s'ha exclòs d'un apilat s'ha exclòs per geometria, no per soroll.** La
  06990 (8 s) i la 06988 (1 s) van quedar fora de l'apilat Sony pels **salts de la
  muntura i uns traços d'estrelles de ~25 px**; la 06991 hi és a dins amb **11 px de
  trailat** i un 4 % de pes (`83` §9.2). Una capa amb la geometria bona no l'ha refusada
  mai ningú, sigui quin sigui el seu soroll.
- **Què entra a l'apilat s'ha decidit pel guany, no per un llindar.** L'apilat Sony v2 va
  afegir els curts i el guany va ser **+1,5 %** de SNR —«els curts no porten fotons»—; la
  v3 els va treure i es va quedar amb els deu fotogrames > 1/8 s (`83` §7.1 i §9.2). Això
  diu què **aporta** una capa; no diu a partir d'on una capa **fa mal**.
- **El pes és sempre l'exposició.** Als apilats Sony el pes és el temps d'exposició, cosa
  que és òptima si el soroll és de fotons i totes les capes són igual de bones. Un
  fotograma més sorollós del que li tocaria —cel, calima, moguda parcial, temperatura del
  sensor— hi entra amb un pes que no s'ha guanyat, i cap comprovació d'avui no ho detecta.
- **La porta de soroll ja existeix, però decideix una altra cosa.** Els filtres de la
  corona externa en tenen, **per banda i per anell** i entre trens (`82`; `83` §8, §9.6):
  allà es decideix quina **estructura** és real. La pregunta d'aquest fil és quin
  **fotograma** és admissible. Són dos llindars diferents i avui no es parlen.
- **La reducció de soroll ja s'aplica, i sense criteri escrit.** La norma canònica de
  `84` diu **«denoise suau a les fraccions de segon»**, i al projecte hi ha capes de
  NoiseXTerminator. O sigui que la pregunta 2 no és hipotètica: el criteri d'admissió que
  s'estigui fent servir de facto **ja és un criteri post-denoise**, i no consta enlloc.
- **Hi ha eina per contestar-ho amb números.** Les **meitats A/B** de l'apilat Sony donen
  σ real per píxel, validada al 96–99 % contra el passa-alt del total (`83` §9.2). En
  canvi el mapa de variància de l'HDR del Vixen **sobreestima σ ×2,7**, perquè és un pes i
  no una variància calibrada. La pregunta es pot atacar mesurant, no mirant.

## 3. Què caldria definir abans de respondre

1. **Soroll de què, i mesurat on.** La corona abasta quatre ordres de magnitud: una capa
   pot ser excel·lent a 1,1 R☉ i soroll pur a 8 R☉. ¿El criteri és per fotograma, o per
   fotograma **i anell**?
2. **Vàlida per a què.** Admissible per a l'HDR fotomètric —que ha de conservar la
   fotometria— no és el mateix que admissible per a una capa de detall —on només compta
   l'estructura relativa— ni per al camp d'estrelles, on mana l'astrometria.
3. **¿És un llindar, la pregunta bona, o és el pes?** Amb σ ben mesurada, «afegir aquesta
   capa millora o empitjora l'apilat» té resposta exacta amb pes per variància inversa.
   Cal decidir si el que es busca és una porta de sí/no o una regla de pes —i si el pes
   d'avui, l'exposició, és el bo.
4. **Què vol dir «poc agressiva».** Fa falta una definició comprovable: que conservi la
   fotometria per anell i que no inventi ni aplani estructura. La prova ja existeix en una
   altra forma —el pendent del log-ratio contra la capa sola que `84` §2 va fer servir per
   destapar que les màscares de V3 aplanaven l'estructura a 0,34–0,82.
5. **De quin costat de la porta va el denoise.** Si el criteri s'aplica **després**,
   qualsevol capa dolenta passa, perquè el denoise abaixa σ sense afegir fotons; si
   s'aplica **abans**, el denoise no compta per a res. Aquesta tria *és* la pregunta 2.
6. **La correlació que introdueix el denoise.** Un denoise per fotograma correlaciona el
   soroll dins del fotograma; llavors apilar N capes ja no baixa σ com √N a les escales
   suavitzades. Això s'ha de quantificar abans de relaxar res, o la flexibilitat és
   comptable i no real.
7. **Què hi ha del soroll que no és soroll.** Cel, calima, PRNU i residu de fosc no
   promitgen a la baixa. Si el que limita una capa és el cel i no el soroll de fotons, ni
   més fotogrames ni cap denoise no compren res, i el criteri ha de ser un altre.

## 4. Estat

**Obert.** Cap resposta, cap mesura nova, cap decisió. No canvia cap producte viu ni cap
norma de `84`.
