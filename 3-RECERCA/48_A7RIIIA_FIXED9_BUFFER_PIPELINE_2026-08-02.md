# A7RIIIA + 300 mm: fixed 9x1, buffer i midpoint

Data: 2 d’agost de 2026

## Decisió

Per totalitats de 90–100 s, la Sony A7RIIIA manté
`Bracketing C 1.0 Steps 9 Pictures` entre C2 i C3. Executa set brackets:
63 fotos, 18 obturacions diferents i una exposició de 3,2 s centrada al
midpoint. No canvia `capturemode` dins totalitat.

El programa usa el buffer en dos blocs físicament acotats:

1. 27 fotos ràpides; canvi de base `1/30 -> 1/5` sota deute JPEG; drenatge
   exacte 27/27 amb pressupost de 22 s.
2. bracket central llarg més 27 fotos ràpides; canvi `1/5 -> 1/30`; drenatge
   exacte 36/36 amb pressupost de 28 s, autoritzat a acabar fins C3+3,2 s.

Cada drenatge usa el contracte canònic
`capturemode_gate=deferred_to_next_config_target`: exigeix cua zero, ledger
exacte i tots els JPEG, i passa després a una lectura del mateix valor 9x1.
Les dues lectures van acabar en 8–12 ms amb `config_already_matches`: zero
escriptures i zero canvi de mode.

## Midpoint

El bracket llarg és:

`1/5, 1/10, 2/5, 1/20, 4/5, 1/40, 1,6 s, 1/80, 3,2 s`.

La presa de 3,2 s queda centrada 4,8 s després del press. Amb C2–C3 = 90 s,
el press és C2+40,2 s i el centre és C2+45,0 s.

## Gate físic complet

Run:
`controller/runs/codex_20260802_a7r3a_fixed9_optimization/physical_gate_v3_canonical/20260802T101914_candidate_a7r3a_300gm_short_checkpointed_1x5_3x9_run`

- 73/73 JPEG confirmats: 1 abans de C2, 63 dins totalitat i 9 a C4;
- 19/19 accions completades, zero skips, recovery o replay;
- drenatge 27: 27/27, 18,419158 s;
- drenatge 36: 36/36, 25,084274 s;
- dos handoffs de mode: `config_already_matches`, zero writes;
- `capt_DSC03018.JPG`: EXIF 3,2 s, SHA-256
  `d0a883bb964a4eae8ce9ba6a9bf6ae02bbe7b5fe7c2da85fa26766d4bba5a3fd`;
- `cleanup_ok=true`, `physical_state_unknown=false`;
- controlador Canon canònic preservat SHA-256
  `b9c4b28233350b225edaa4bbb09f3d6fb5d52fc7fc7c10ca5bf592e575f4421d`;
- resultat SHA-256
  `94f7d208fb29e629f88c0c34c3b2cb50648bfee3eb2b2c7dd7454acb659326d9`;
- manifest de descàrregues SHA-256
  `2c3c4b3c36eedd1b4e668569ae390a6475712327ed8c858c6d5929d68ce94cf6`;
- perfil congelat SHA-256
  `193e210d97edfef07c47f18e16c1bb0b633dd1d1d38fafb13e77783be3490860`.

La prova anterior, amb 18/24 s i gate `within_drain`, ja havia disparat les
63 fotos de totalitat però només havia descarregat 64/73 JPEG. No refutava la
captura: refutava el pressupost i intentar confirmar el mode dins del mateix
drenatge. No hi va haver replay.

## Demostrat, falta i ordre de gates

**DEMOSTRAT:** 63/63 fotos dins 90 s, 18 obturacions, 3,2 s al midpoint,
canvis de shutter amb deute JPEG, drenatges exactes 27/36, C4, cleanup i
identitat exacta del cos.

**FALTA:** delta SD ARW exclusiu; assaig solar/òptic amb 300/2,8, filtre i
focus; cable-pull i bateria; repetició de camp.

**ORDRE:** 1) delta SD ARW sense canviar el programa; 2) assaig solar/focus;
3) resiliència; 4) repeticions finals amb hashes; 5) promoció explícita. Els
temps 22/28 s, el deute 36 i 9x1 són exclusius d’aquest cos.
