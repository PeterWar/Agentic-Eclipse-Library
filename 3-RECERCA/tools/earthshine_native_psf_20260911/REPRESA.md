# Represa — V49 i mostreig verd natiu

V49 publicada com a correcció modesta de mostreig, no com a llimb resolt. Producte i límits: `output/earthshine_native_psf_20260911/RESULTAT.md`. El goal global continua actiu. No demanar confirmacions intermèdies; Pere ha autoritzat continuar. No crear agents nous.

## Allò ja fet: no repetir-ho

- Les 67 captures Vixen tenen `A0_quincunx_{stem}.npz` i `A0_native_samples_{stem}.npz` sota `output/earthshine_native_psf_20260911`; inventari complet `A2_all_native.json`. Els punts natius cobreixen l’anell 415–495 en coordenades lunars locals, amb radiància, variància, confiança, fracció bruta, validesa i identificador de verd.
- Renderer `a0_native_and_quincunx.py`, interpolador `quincunx.py`; la primera execució limitada és A0 i `--all-vixen` amplia als67. No executar-los sobre les sortides existents: els asserts eviten sobreescriptures. La mateixa arrel de codi, calibració i registre que V48.
- `B0_old_all/early/late.npz` i `B0_new_all/early/late.npz`; compositor actual congelat, antic reproduït. Les meitats25/42 són disjuntes. `compositor_cache/G.npy,W.npy` són les noves fonts i pesos; Sony es conserva a `output/earthshine_detail_20260911/B2_sony_reference.npz`.
- A1 mesura sense interpolació radiomètrica dels punts natius. El sigma natiu1,0121 és descriptiu de17 sectors de2976; NO és una PSF que es pugui posar automàticament a tota la totalitat. El sigma antic1,4275 procedia d’un altre mostreig i d’un fantoma; tampoc no s’ha de traslladar al nou renderer.
- Primera transferència només8–16px: diagnòstic C0–C5, no publicada. V49: subdirectori `full_sampler_delta`, scripts d0–d5 i e0–e3; diferència completa dels dos apilats abans de la mateixa recepta de CameraRaw. Màscara V48 exacta i25capes anteriors preservades; nova capa26.
- Les 50 condicions de retenció fotogràfica anteriors es conserven, però el jutge independent de fonts B1 continua mixt. No hi ha descoberta general de nou detall fi ni eliminació completa de l’halo.

## Pas següent acotat

El mostreig de les fonts ha millorat, però resta separar la llum solar dispersada de la radiància lunar a l’últim llimb. Continuar amb una prova de resposta **per captura al CFA natiu**, que predigui mostres vàlides d’una altra exposició/època abans de promoure cap inversió. Ja hi ha totes les coordenades i mostres natives; no cal tornar a llegir88RAW per començar.

Primer limitar el model a un sector amb dades completes primerenques/tardanes i a les captures2973–2978,2991–2996. Mantenir separats els moviments solar i lunar, la integració del píxel, el suport de saturació i les incerteses de calibració. La nova interpolació no és una inversa de la PSF; un ajust a una vora remapada no demostra una PSF òptica.

El model conjunt anterior és `research/tools/earthshine_joint_20260911/forward_model.py`; B6 no estava qualificat. La quadratura d’ocultació convergent és `output/earthshine_joint_20260911/A2_occlusion_polygon.npz` (P64). El default històric del model és P4: no reutilitzar-lo inadvertidament. La vora observada i les translacions de textura tenen incerteses diferents; no tornar a moure totes les fonts amb translacions globals estimades de la vora aparent.

Una nova hipòtesi de PSF/model necessita prediccions separades i control de resposta a senyal afegit al mateix operador. No repetir una inversió estàtica del HDR ni decidir-ne la força pel seu aspecte. Una solució restringida a radiància no negativa pot estudiar-se com a model físic explícit, però no convertir el retall de valors negatius en validació. No hi ha autorització per inventar textura amb IA o LROC.

Si la discrepància queda al muntatge, consultar abans `output/earthshine_joint_20260911/C1_composition_review.json`: la màscara és l’encaix fotogràfic heretat i hi ha fonts originals alternatives visibles. El retall geomètric C2 produïa un anell negre; no és una correcció reutilitzable. Pere prioritza curar l’origen i mantenir l’estètica de CameraRaw.

## Operació

Runtime: `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1`. Codi Downloads, actius Desktop. Llegir autoritat viva i adquirir un nou claim abans d’escriure. Les claus del mòdul d’aquesta ronda continuen fixades al claim `CODEX_EARTHSHINE_NATIVE_PSF_20260911`; no executar constructors antics sota un claim diferent.

Documents anteriors79/140/1297 continuen sense desar;1275desat. V49 publicada queda oberta i desada per a Pere. Les còpies natives pròpies es tanquen. No guardar ni tancar els originals.
