# Decisió ISO 100 per a cel net — A7III + AP130GTX + QUADCC

Data: 27 de juliol de 2026  
Estat: **decisió operativa incorporada al candidat, pendent de qualificació**

## Fet nou aportat per Pere

L'ISO 200 del run day-of de 2024 no era la calibració base del sistema.
Pere el va seleccionar a última hora perquè hi havia una capa fina de
núvols. El pla inicial per a cel net era ISO 100.

## Decisió 2026

- ISO 100 fix durant tota la seqüència principal.
- Es conserven els temps d'obturació calculats per l'AP130GTX + QUADCC.
- No s'introdueixen canvis d'ISO dins de la totalitat.
- Qualsevol perfil alternatiu per transparència atmosfèrica reduïda s'haurà
  de preparar i qualificar abans; no s'improvisarà un canvi després d'armar.

## Conseqüències de control

El generador, els dos perfils curts, el preflight, el checklist i el gate de
drenatge han de requerir ISO 100. Els resultats físics anteriors lligats per
hash a un perfil ISO 200 no promocionen el perfil nou: cal repetir el
cribratge i la qualificació.

L'A7III no publica `Toma silenciosa` entre les propietats PTP exposades per
gphoto2/libgphoto2 en aquest estat. Silent Shooting continua sent un gate
manual verificat visualment abans de connectar l'USB.
