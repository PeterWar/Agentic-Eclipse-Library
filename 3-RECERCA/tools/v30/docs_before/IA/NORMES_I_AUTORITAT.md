# Normes i autoritat

Última actualització: 22-08-2026.

## Ordre d'autoritat

1. La instrucció més recent i explícita de Pere.
2. L'`AGENTS.md` de l'arrel on es treballa i aquest document.
3. `ESTAT_ACTUAL.md`, `DECISIONS.md` i `ACTIVE.json` per a l'estat i les rutes
   posteriors a la reorganització.
4. L'`AGENTS.md`, el bloc inicial de `CLAUDE.md`, el lock i els diaris del
   worktree de codi.
5. Handoffs, manifests, rebuts i documents datats com a evidència històrica.

Un rebut històric conserva la seva ruta original. No es modifica per adaptar-lo
a la nova estructura; s'hi afegeix un mapa de rutes separat.

## Separació d'arrels

- Desktop és l'arbre canònic de dades, Photoshop i memòria d'IA.
- Downloads és l'únic worktree Git canònic i manté codi, recerca, outputs
  traçables i coordinació formal.
- El disc `4TB` és el backup de comparació del 22-08-2026. No s'hi escriu ni
  se'n restaura res sense ordre de Pere.
- `/Users/USUARI/Desktop/Altres` conté 6D, meteorologia, ubicacions i vídeo;
  no és part de la composició Vixen+Sony tret que Pere ho demani.

## Seguretat i escriptura

- Abans de qualsevol mutació, llegeix els fitxers obligatoris, executa
  `git status --short` al worktree i preserva tots els canvis preexistents.
- Adquireix `SERIAL_WRITES` al worktree de Downloads, fins i tot si l'escriptura
  documental és a `IA`.
- No facis `reset`, `checkout`, `clean`, `stash`, commits massius ni
  sobreescriptures globals.
- RAW, darks, flats, PSB/TIFF existents, backups i rebuts són immutables per
  defecte. Tot producte nou ha de ser no-clobber i portar procedència.
- Cap càmera, PTP, `gphoto2`, captura, GUI física o Photoshop automatitzat sense
  autorització concreta.

## Regla de JPEG nous

**Estat: ACTIU.** Qualsevol JPEG/JPG nou generat per una IA per a aquest
projecte ha d'anar a:

`/Users/USUARI/Desktop/Eclipse 2026/IA/output/`

Quan una tasca produeixi més d'un fitxer, crea-hi una subcarpeta amb un nom
traçable per tasca o data. No generis JPEG/JPG nous en cap altra carpeta del
Desktop ni del worktree, tret que Pere ho ordeni explícitament per a una tasca
concreta. `IA/Skills/` queda reservada a l'índex i les instruccions de les
skills: `IA/Skills/output/` no és una ruta vàlida i no s'ha de crear.

La regla és prospectiva. No es mouen automàticament els JPEG històrics perquè
alguns formen part de rebuts, QA o captures. A l'auditoria inicial hi havia 15
JPEG al nou arbre de Desktop i 261 al worktree de Downloads, excloent `.git`.

## Política visual vigent

- Aspecte natural i contrast moderat; preservar marge per als retocs finals de
  Pere.
- No crear estructura, relleu o extensió de corona mitjançant màscares lliures.
- Les dues Sony útils de 8 s (`DSC06987` i `DSC06993`) són contribucions
  obligatòries i independents en marc solar. `DSC06990` queda exclosa per
  moviment real.
- El residual d'estrelles és diagnòstic i no pot vetar per si sol una
  contribució coronal en seguiment solar.
- Earthshine queda fora de l'abast fins que Pere el reprengui explícitament.
