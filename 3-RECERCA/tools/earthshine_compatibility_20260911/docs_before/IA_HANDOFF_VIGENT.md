# Handoff — estratègies Earthshine, 11-09-2026

**Autorització viva de Pere:** buscar alternatives i continuar operant sense demanar confirmació entre assaigs. Fer proves acotades per cost, però no acabar cada prova amb una espera d'un altre «ok». Preservar originals i el Camera Raw de Pere. No hi ha permís nou per a maquinari, PTP o accions destructives.

Llegir `output/earthshine_strategies_20260911/ESTRATEGIES_I_RESULTATS.md` i la recomanació canònica de no forçar retocs manuals. Codi i manifest del mateix experiment. Els pilots anteriors es conserven com a evidència.

Troballes:

- Registre solar `f2.refina` viu = congelat del run019. La màscara comuna multiplicada abans de correlacionar pot dominar el pic. Control observat, llenç complet decimat×4: moviments imposats amb errors antics2,22–18,43px i confiança0,968–0,995; NCC amb màscares0,069–0,129px. Això prova fallada de l'estimador, no l'error real històric de les fotos. No citar la precisió antiga0,095px com a establerta.
- Ajust conjunt de regions coronals natives amb informació direccional: component inicial2976–2979 passa meitats0,093–0,282px, tancament0,164px, control0,0082px. El graf sencer NO passa: dos enllaços a fases tardanes fallen. No estendre la validació.
- Solució relativa ancorada a2976: 2978 sortida(+0,591,−0,0748)px, davant de(+1,439,−1,558) antic. Geometria de la corona; falta validació lunar absoluta i científica entre trens.
- Pilot de tres preses dominants dins de l'epoch: salt90,56%→69,70%, encara insuficient. No PSB. Braç `plain_same_weights` invàlid per suport antic + radiància nova, qualificat i exclòs; usar només `source_confidence`, que recalcula tot a la font.
- Model descriptiu de resposta nucli+ala entrenat fora del sector superior: 1s empitjora1,597× al sector reservat; molts guanys topen0,8. Rebutjat com a cura; no PSF identificada ni resta absoluta de vel.

Continuar autònomament, per ordre: ampliar el graf amb exposicions intermèdies i comprovar escala/rotació/marc lunar amb l'altre tren; separar incompatibilitats temporals de resposta abans de fusionar; després una zona verda. Un model temporal de formació d'imatge ha de predir dades reservades abans de qualsevol resta/deconvolució. No repetir pesos sols ni el vel uniforme refusat. No inventar textures ni usar Brno com a font de píxels.

Font estètica: `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V46_Detall.psb`, SHA `0af484cb7f1919900a51267f053467974c57902414258e67f54fe98638d2eb3a`, verificada intacta. Cap nova recuperació de l'últim llimb ni de les zones verdes proclamada. Cap PSB nou. Figura de síntesi i llenç complet inspeccionats. Estat final i alliberament al diari CODEX_STATUS; zero processos propis pendents al tancament.
