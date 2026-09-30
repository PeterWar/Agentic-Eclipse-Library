# Represa — resposta intermèdia i operador natiu

V49 vigent. Informe `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_intermediate_witness_20260911/RESULTAT.md`. Manifest `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_intermediate_witness_20260911/delivery_manifest.json`. Goal global actiu.

Resultats que no cal repetir: p12 congelat; component4px amb p4 interpolat=0.02572829, p4 entre verds=0.02714296. Control temporal entre verds: 4/6 grups superen5%, 71/72 sectors no empitjoren2%; PASS global=False. Detalls exactes aE0. No és una nova font qualificada.

Descobriment numèric: predictors interpolats fallen l’escena coneguda (RMS≈5,7G); convolució nativa≈0,00093G; verd oposat0,113/0,142G. Els senyals coneguts passen. Conservar l’operador sobre la graella u,v de pas√2; no interpolar la radiància abans de calcular la correcció.28camps natius D0, amb 3202063 mostres congelades exactes i28SHA deRAW comprovats, disponibles per evitar una nova lectura/calibració.

D1manté verds com a files separades percel·la, predictor de l’altre verd; no fer la mitjana abans del score. Calibració/FPNcompartits continuen com a límit; no és el jutge entre telescopis. Nova prova abans de qualsevol font/PSB: resposta òptica completa i llum oculta dels llargs, amb criteris independents i sense perdre detall de les protuberàncies. No reprendre màscares manuals, el·lipses lliures o ajustos triats pels mateixos errors.

Runtime `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1. Llegir autoritat viva i adquirir un claim nou abans de mutar. Codi aDownloads i actius aDesktop. No Git, maquinari, agents nous o generació d’imatges.


## Pista física per a la represa

L’autoritat local identifica el telescopi com a Vixen VSD90SS (`CLAUDE.md`, apartat de muntures). El fabricant declara 90 mm d’obertura i 495 mm de focal nominal: [fitxa oficial VSD90SS](https://www.vixen.co.jp/product/26131_4/). Abans de seguir afegint gaussianes lliures, té sentit provar la difracció del pupil·la del telescopi amb l’escala angular real de la cadena i un interval de longituds d’ona declarat. Aquesta és una hipòtesi nova, no una equivalència ja demostrada amb les components de 4/12 px. Cal verificar l’escala i la configuració òptica efectiva; no deduir-les de la imatge de referència DHS ni ajustar la longitud d’ona per fer desaparèixer el halo. No s’ha calculat ni aplicat cap correcció Airy en aquesta ronda.


Comprovació final C2: repetida al p4 final entre verds (0,02714295880522035), 8/8 PASS; RMS del contorn conegut 0.119520/0.149805 G. Els rebuts C0/C1 anteriors corresponen al p4 de l’ajust interpolat. Aquesta nova comprovació només valida l’operador numèric, no canvia el FAIL temporal ni publica cap font.
