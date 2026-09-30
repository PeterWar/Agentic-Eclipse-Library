# Diagnòstic complementari del genoll V112

`knee_guard.py` observa la funció històrica vinculada per SHA sense modificar
les seves quatre sortides. Requereix configuració, domini, GATE i descripció
de l'escala explícits. Separa capacitat, terra assolit, residu i referència
governant SEC/HQ, inclosos els empats. Amb GATE parcial calcula el sostre
corresponent; un terra inferior al nivell actual ja està satisfet.

La coincidència amb una funció facilitada pel cridador es limita a tipus,
forma i bytes dels quatre retorns d'aquella invocació. No autentica tota la
preparació dels inputs. El sidecar declara configuració, n i els SHA de les
dues fonts. No retorna un PASS global ni modifica paràmetres o ràsters.

Ús i API detallats preservats a
`4-RESULTATS/v112_20260928/KNEE_DIAGNOSTIC_GUARD/README.md`.
Les 20 proves escalars i de vectors petits s'han repetit des d'aquesta
instal·lació: `KNEE_DIAGNOSTIC_GUARD/ROOT_TEST_RECEIPT.json`.
Les fonts històriques són exactes abans i després de les proves.

Per executar només les proves, sense generar un rebut a la carpeta de codi:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 /Users/USUARI/.venvs/eines-ia-py312/bin/python -m unittest discover -s '3-RECERCA/tools/v112_20260928/knee_diagnostic' -p 'test_knee_guard.py'
```

No s'ha executat aquest helper sobre la imatge completa ni s'ha connectat
com si fos una porta ja superada per la candidata. El model puntual no
certifica el suavitzat, el clip final, el cel físic, la retenció de senyal
o la recomposició nativa. Les portes de lliurament vigents continuen
rebutjant la candidata V112.
