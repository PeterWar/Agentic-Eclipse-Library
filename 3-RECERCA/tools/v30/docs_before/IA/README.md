# IA — punt d'entrada del projecte Eclipse 2026

Última actualització: 22-08-2026.

Aquesta carpeta és la memòria operativa i de coordinació entre LLM. Una IA nova
ha de començar aquí i no ha d'intentar reconstruir l'estat només a partir de
noms de fitxer, dates o handoffs antics.

## En una frase

Estem construint una fotografia final de l'eclipsi natural, editable i sense
anells artificials, combinant de manera traçable el tren Vixen/R6 III i el Sony
300 mm/A7RIIIA. La branca visual està aturada per decisió de Pere: el darrer
resultat no és un final estèticament acceptat i encara no incorpora com cal les
dues contribucions Sony útils de 8 s.

La troballa visual prioritària és ara la branca Python Druckmüller preservada
de Gemini: Pere n'ha provat els resultats i diu que **«pinten molt, molt bé»**.
Continua sent experimental fins que es reprodueixi sobre S6 i passi els gates.

## Les dues arrels vives

- **Actius fotogràfics i Photoshop:**
  `/Users/USUARI/Desktop/Eclipse 2026`
- **Git, codi, eines, rebuts i diaris d'agents:**
  `/Users/USUARI/Downloads/Eclipse 2026`

No són dues còpies competidores. Tenen funcions diferents. El backup de
referència anterior a la reorganització és
`/Volumes/4TB/Eclipse 2026-22Agost/Eclipse 2026` i no és una arrel de treball.

## Ordre de lectura obligatori

1. `NORMES_I_AUTORITAT.md` — què mana i què no es pot tocar.
2. `ESTAT_ACTUAL.md` — DEMOSTRAT, FALTA i SEGÜENT GATE.
3. `DECISIONS.md` — decisions expresses de Pere.
4. `MAPA_RUTES_I_OUTPUTS.md` — on és ara cada família de dades.
5. `Coordinació/HANDOFF_VIGENT.md` — traspàs curt i agent-neutral per reprendre.
6. `Coordinació/DELTA_CODEX_a_CLAUDE_22-08-26_BRANCA_DRUCKMULLER_GEMINI_KIMI.md`
   — prioritat visual de Pere, preservació, correccions i ordre de gates.
7. `Coordinació/AUDITORIA_RECUPERACIO_KIMI_GEMINI_DRUCKMULLER_2026-08-22.md`
   — evidència, hashes, entorn Python i reparació fail-closed de V4/V4b.
   Rebut final executablement verificat:
   `/Users/USUARI/Downloads/Eclipse 2026/output/auditoria_kimi_gemini_20260822/FINAL_VALIDATION_2026-08-22.md`.
8. `Coordinació/DELTA_CODEX_a_CLAUDE_22-08-26_FLATS_POSTERIORS.md` —
   handoff verificable dels calibradors posteriors encara no aplicats.
9. `Coordinació/AUDITORIA_FLATS_POSTERIORS_2026-08-22.md` — què és
   transferible, què queda en quarantena i per què flat i warp no commuten.
10. `Coordinació/DELTA_CODEX_a_CLAUDE_22-08-26_ECLIPSE_POSTPROCESSAT.md` —
   handoff verificable específic de Codex a Claude.
11. `Coordinació/AUDITORIA_REPRESA_VIXEN_SONY_2026-08-22.md` — autoritats S6,
   Sony de 8 s, origen dels arcs, FOV i gates exactes de represa.
12. `Coordinació/CRONOLOGIA_POSTECLIPSI_2026-08-22.md` — seqüència de decisions,
   auditories, neteja i traspàs.
13. `Coordinació/AUDITORIA_NETEJA_DEPRECAT_NOSE_2026-08-22.md` — neteja,
   reubicació, Paperera i gates finals.
14. `Coordinació/AUDITORIA_REESTRUCTURACIO_2026-08-22.md` — fotografia anterior
   a la neteja i comparació amb el backup.
15. `/Users/USUARI/Downloads/Eclipse 2026/AGENTS.md`, el bloc inicial de
   `CLAUDE.md` i
   `.coordination/HANDOFF_2026-08-22_ALTERNANCA_CODEX_CLAUDE.md` abans
   d'actuar al repositori.

`ACTIVE.json` conté les mateixes rutes principals en format llegible per
programes.

## Disciplina d'actualització

- `ESTAT_ACTUAL.md` es reescriu només quan canvia l'estat efectiu.
- `DECISIONS.md` és append-only: no s'esborren decisions; es marquen com a
  supersedides amb data i autoritat.
- Cada auditoria o handoff datat va a `Coordinació/`.
- `Skills/README.md` indexa les skills canòniques; no es creen còpies silencioses.
- Qualsevol JPEG/JPG nou generat per una IA va a `IA/output/`, preferentment dins
  una subcarpeta identificable per tasca o data.
- Fora d'`IA/output/`, cap original ni derivat fotogràfic forma part de la
  memòria d'IA.
