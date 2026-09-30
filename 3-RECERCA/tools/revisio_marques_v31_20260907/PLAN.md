# Revisió visual autoritzada per Pere — 07-09-2026

Pausa de la recerca causal general per revisar V31_FiltresPurs_Artefactes.psb capa a capa. Groc, blau i lila: artefactes confirmats per Pere. Verd: dubtós, possiblement corona. No corregir ni sobreescriure el PSB; preservar l’original i la còpia anotada.

Flux executat: inventari de les 19 capes; còpia clone APFS de lectura; extracció a coordenades originals i vistes completes; segmentació de pintura semitransparent; comparació per nom amb les capes sense pintar de V31_FiltresPurs; revisió visual de totes les capes; comprovació local entre trens a les verdes; catàleg i informe. Tots els lliurables passen per comu.Run. Root únic escriptor, dos revisors només lectura.

Rectificacions durant la ingestió: el primer llindar de color era massa alt per al pinzell semitransparent i confonia el groc natural de la base amb pintura. Passada descartada, recàlcul complet amb llindar S>25,V>20; base exclosa de classificació cromàtica i revisada visualment. ModeH109=blau, H119–123=lila, tall116; IDsneutres per no heretar el primer nom del color. Cap d’aquests masks toca les fotografies. Vistes antigues i finestres espúries de la base conservades a provisional_SUPERSEDED.

La descodificació ZIP16 predictiva original de psd_tools usa un bucle per píxel i feia lenta la lectura. S’ha substituït només al lector local per suma acumulada uint16 per fila, verificada contra bytes originals i lector oficial amb valors de wrap, amplada10551 i diverses formes. Cap canvi al paquet instal·lat ni als fitxersPSB.

Executables: extract.py, reference.py, refine_inventory.py, green_check.py, write_review.py, close_review.py. Les vistes són de diagnosi8bits i inclouen el llenç complet; no són nova radiància ni una versió del producte. Els radis del catàleg sónp05/mediana/p95dels traços, no centres de circumferències.
