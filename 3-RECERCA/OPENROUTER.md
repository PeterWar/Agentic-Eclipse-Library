# OpenRouter per a la recerca

OpenRouter és una eina auxiliar de contrast i no forma part del controlador
de captura. `controller/` conserva el seu contracte sense Internet, API ni
dependències externes.

## Secret

La clau no es desa al projecte. L'eina la busca, per aquest ordre:

1. la variable temporal `OPENROUTER_API_KEY`;
2. una contrasenya genèrica del clauer `login` amb servei
   `OPENROUTER_API_KEY`;
3. les variants de compatibilitat `openrouter.ai`.

Es pot indicar un servei diferent amb `--keychain-service NOM` o amb la
variable `OPENROUTER_KEYCHAIN_SERVICE`.

Per crear o corregir l'entrada compatible des del Terminal, sense deixar la
clau a l'historial:

```bash
/usr/bin/security add-generic-password -U \
  -a "$USER" \
  -s "OPENROUTER_API_KEY" \
  -w
```

`security` demana la contrasenya de manera oculta perquè `-w` és l'última
opció. Cal enganxar-hi la clau d'OpenRouter i prémer Retorn.

## Validació sense consum

```bash
/usr/bin/python3 research/tools/openrouter_client.py check
```

Aquesta ordre consulta l'estat de la clau i mostra l'ús i els límits, però
no envia cap prompt ni consumeix tokens de model.

## Consulta simple

```bash
/usr/bin/python3 research/tools/openrouter_client.py ask \
  "Resumeix els riscos principals de la captura de corona solar."
```

El model per defecte és `openrouter/auto`. OpenRouter tria el model i cobra
la tarifa del model seleccionat. Per fixar-ne un:

```bash
/usr/bin/python3 research/tools/openrouter_client.py ask \
  --model AUTOR/MODEL \
  "Consulta"
```

La resposta informa a `stderr` del model efectivament utilitzat i dels
tokens d'entrada i sortida.

## Fitxers i privacitat

Cap document del projecte s'envia automàticament. `--context` és una acció
explícita: llegeix el fitxer indicat i n'envia el contingut a OpenRouter i
al proveïdor que serveixi el model.

```bash
/usr/bin/python3 research/tools/openrouter_client.py ask \
  "Contrasta aquest document i separa fets, inferències i dubtes." \
  --context research/06_APLICACIO_2026.md
```

No s'han d'enviar credencials, dades personals ni material que no estigui
autoritzat per a un proveïdor extern.

## Proves locals

```bash
/usr/bin/python3 -m unittest research/tools/test_openrouter_client.py -v
```

Les proves simulen el Clauer i la xarxa: no llegeixen la clau real, no fan
peticions i no gasten crèdit.
