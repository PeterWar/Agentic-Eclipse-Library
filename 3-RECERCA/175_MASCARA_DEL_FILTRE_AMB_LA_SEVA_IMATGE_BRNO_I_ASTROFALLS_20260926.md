# 175 · La màscara d'un filtre amb la seva pròpia imatge: ho fa Brno? Què guanya i què perd (26-09-2026)

- Consulta de Pere a partir de la V105.
- Resposta completa, amb fonts, xifres i imatges del llenç sencer: `4-RESULTATS/v106_inversio_20260926/consulta_mascares/LLEGEIX-ME.md`. La van fer quatre agents: Astrofalls, Brno, mesura i un verificador adversari.

## Què s'ha après
1. **Brno no ho fa, almenys en res del que ha publicat.** Ni a la tesi del 2014, ni al CAOSP 2006, ni a l'ApJ 2011, ni a l'MGN 2014, ni a 657 pàgines del seu web.
   - Per a ells, «mask» és la imatge suavitzada que es resta en un passa-alt.
   - El soroll el combaten a la captura i amb portes que depenen de la variància o de l'entrada, mai del signe del detall.
   - Exigeixen que la resposta mantingui l'ordre de clar a fosc.
   - Reserva: la no-linealitat de l'ACHF modern i el programa ACC 6.1 no estan publicats.
2. **Astrofalls tampoc no ho fa exactament així.**
   - La pròpia imatge a la màscara només la posa a la barreja HDR d'exposicions, amb un trapezi de Nivells/Corbes i un desenfocament de 10 a 400 px.
   - A les capes de detall hi posa la lluminositat de l'original (vídeo 51:02) o màscares pintades a mà.
3. **Matemàtica** (verificada):
   - **Multiplicar**, amb la màscara igual a la pròpia imatge F: factor 1 − o·F·(1−F), cec al signe. Un buit de la NRGF passa de ser un 18 % més fosc que un plomall a ser un 3 % més clar; l'ordre queda invertit al 74 % dels píxels de la 41 a 1–3 R☉.
   - **Superposar**, amb la mateixa màscara: el detall queda a la meitat, hi apareix un biaix clar proporcional a la variància (soroll inclòs) i per sota de F = 0,25 el detall s'inverteix.
4. **D'on surten les zones negres** (1,3–4,5 R☉ més fosc que el cel): de la NRGF 41/42 i de la WOW bilateral 56 juntes.
   - Sense la 41 i la 42 en desapareix el 61 %; sense la 56, el 33 %; sense totes tres en queda el 12 %. La base sola no en té cap.
   - La màscara pròpia les amaga (V105: 11–12 % dels píxels; amb la màscara: 0–2 %), però alhora:
     - s'emporta la meitat del detall;
     - el contrast entre plomall i buit cau un 55 %;
     - les perles del limbe queden a ×0,6;
     - s'allunya una mica de Brno.
   - Si la 56 també porta la pròpia imatge com a màscara, el gra del cel es multiplica per 2,5–3,9.
5. **Cura de causa arrel** (proposta, la decisió és de Pere): corregir-ho a la NRGF (41/42) i a la 56, amb un guany que segueixi el S/N, un terra a l'enfosquiment dels buits o una opacitat que baixi amb el radi. No passa per la màscara.
