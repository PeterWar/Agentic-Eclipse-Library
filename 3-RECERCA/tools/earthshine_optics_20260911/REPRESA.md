# Represa acotada després de la prova òptica

Producte vigent al disc: V48, SHA `48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5`. **El document V48 obert1297 té canvis no desats al final de la ronda; s'ha preservat sense desar o tocar. Inspeccionar i preservar aquest estat abans de fer cap producte nou; el PSB al disc no prova l'estat dels píxels vius.** No hi ha V49. El model gaussià invertit sobre un HDR estàtic està rebutjat, tant al principi com al final de la totalitat. No tornar-lo a promoure ajustant força o retallant negatius.

## Evidència que canvia el següent pas

- A0/A1: nucli de les preses curtes estable de manera aproximada, però A2 mostra que l'error absolut del perfil és comparable a la llum interior. Un RMS del1% sobre la corona és massa gran per deduir que la textura lunar queda ben recuperada.
- B0: mínims −36.098/−14.799 en la franja final, anells evidents. B1 només 1 guany i1 pèrdua puntual, cap suport de recuperació global. B2 no executat: la fidelitat ja falla i injectar amb el mateix nucli no validaria el model físic.
- B3: el residu entre preses és ~0,06–0,07 a l'interior, però8,5–9,4 al llimb. La translació solar millora la corona exterior respecte d'un control contrari de la mateixa magnitud, però no explica tota la vora. El problema no es resol invertint una mitjana estàtica.

## Hipòtesi nova, encara no implementada

Model directe separat per captura, conceptualment:

`d_i = H_i [ P M + (1-P) W_i C ] + b_i + soroll`

`M` és la textura lunar comuna, `C` la corona en coordenades solars, `W_i` la transformació solar de la captura, `P` l'ocultació física observada i `H_i` la resposta òptica i d'integració. `b_i` representa només calibració/fons justificables. És una hipòtesi, no un resultat ni un codi ja fet. No imposar M=0 ni confondre P intern amb un retoc de la màscara del PSB. Un model natiu ha de respectar CFA, píxel, saturació i variància; la fase inicial sobre arrays remapats tindrà abast limitat declarat.

Començar amb les dues èpoques de6 captures, sense els10s: la complexitat ha de resoldre el desacord a la font abans d'ampliar a88. Baseline: HDR estàtic dels mateixos inputs i mateixos pesos. Validació mínima: predicció de preses separades, residus per cobertura física, prova de control de moviment, injecció de textura abans de la composició i corroboració amb Sony. No triar paràmetres amb les marques verdes ni provar sense límit contra els mateixos jutges. Si els paràmetres queden degenerats, declarar-ho abans de produir un PSB.

## Rutes i trampes

Arrel `/Users/USUARI/Downloads/Eclipse 2026`. Llegir autoritats i adquirir un claim nou. Codi d'aquesta ronda `research/tools/earthshine_optics_20260911`; sortides `output/earthshine_optics_20260911`. Python `/Users/USUARI/.venvs/eines-ia-py312/bin/python`; `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1`.

Fonts88: `output/earthshine_detail_20260911/native/*.npz`. Matrius Vixen67 exactes: `compositor_cache/G.npy`, `W.npy` al mateix directori; els noms/èpoques són a `B1_full_native_ensemble.json`. Conservar els pesos físics, no el mapa de variància com si fos radiància. Nou rebut B3 associa noms, temps i centres solars en la graella lunar.

Per Vixen, la posició solar local és `centre_lluna - A*[lluna_dx,lluna_dy] + native_shift`, on `A=COMMON_TO_FINAL[:2,:2] @ [[ca,-sa],[sa,ca]] / ctx.k`. B3 conté el codi executat. Aquesta posició inclou els ajustos de registre heretats i no és una mesura pura de moviment ni de jitter. No reaplicar com a translació global a la Lluna: aquesta trampa ja perjudicava les textures en rondes anteriors.

Registre original per textura de V45; no recuperar els desplaçaments globals ajustats a la vora aparent. La màscara física i geometria de V48 continuen intactes. Cap textura LROC/DHS s'introdueix a les fonts; la capa LROC antiga de Pere és una altra cosa i es preserva.

Escriptura de B0 només al directori propi; el precondicionador final és de dos nivells. `solver_cache` guarda solucions convergents per lambda, sigma i època; no reutilitzar-les per a un model nou o altres pesos. Logs de fallada preservats. `b1_inverse_judge.py` va escriure totes les mètriques abans de l'error de Matplotlib; la figura s'ha reparat a part i les puntuacions no han canviat. `b2_transfer.py` no executat, no és un gate verd.

No llegir el primer `E1b_psf_apilada.json` de V41 com a mesura estel·lar vàlida: la posició de la capa estel·lar estava mal registrada, corregida posteriorment. El `fitpsf.py` de `astrometria/vixen` correspon a altres captures de calibració del16-08, no mesura la PSF de les exposicions llargues del12-08. No importar aquests valors com si fossin contemporanis.
