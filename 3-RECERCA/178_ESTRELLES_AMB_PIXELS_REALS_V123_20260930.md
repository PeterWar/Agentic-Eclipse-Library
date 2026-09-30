# 178 · Les estrelles amb píxels reals: apilats alineats sobre les estrelles (V123, 30-09-2026)

**Encàrrec de Pere:** abans d'enviar l'APOD, substituir les estrelles re-renderitzades (perfils gaussians de la capa 202) per píxels reals.
- Rebut i detalls: `1-PHOTOSHOP/V123_REBUT.md`.
- Codi: `IA/output/estrelles_reals_20260930/`.

## Què s'ha après
1. **El mapa llenç→natiu de la V65 (`S11_vixen_manifest`, files «catalog») dona coordenades de l'àrea VISIBLE del sensor.** Per retallar del raw complet cal sumar-hi el marge: (172, 108) a la R6 III. Sense el marge, cap estrella cau on es preveu.
   - Les files «rotated_null» del manifest són controls nuls i no s'han de fer servir per ajustar.
2. **El Vixen, sol, veu 30 de les 36 estrelles del retall** (S/N de 6 a 190 en 38 s). Cal el fons PLA local: amb la mediana de l'anell, les estrelles dins de gradients (corona, vora de la Lluna) sortien amb S/N < 3.
   - La Sony completa les altres 6. Una estrella de V 9,4 (S54) queda a S/N 3,7.
3. **Convertir el color píxel a píxel amb la matriu de la càmera, i amplificar el blau de les estrelles vermelles, fa soroll de color** (taques blaves i verdes).
   - La solució: la forma surt de la lluminància registrada i el color, del color integrat mesurat.
4. **Després de l'acabat (BlurX, llums retallades), una estrella dibuixada ja no és gaussiana.**
   - Restar-li una gaussiana ajustada hi deixa marca.
   - Per retirar-la: disc de 5 px al nivell del cel del voltant, amb transició de 2 px.
5. **psd-tools, en 16 bits:** en llegir mana el bloc «Lr16», però en escriure les capes van a la secció principal. Una capa afegida a un PSB de 16 bits no la veu ningú si no es mou al bloc Lr16 (`psd16.a_lr16`).
