# Canon EOS R6 Mark III: candidat de triple RAW per totalitat

Data de decisio: 2026-08-04

Estat: `SOURCE CANDIDATE`, no promocionat. El programa operatiu continua sent
el fallback fisicament demostrat de 40 Single RAW totals, 35 dins C2-C3.

## Missio primer

- Una R6 exclosa o degradada no atura les altres cameres.
- Cap trigger ambigu es repeteix. Una accio amb resultat ambigu queda consumida.
- Identitat o propietari PTP divergent, write amb estat fisic desconegut,
  delta CR3 incorrecte o ledger no garantible aturen nomes el canal R6.
- ISO i bateria son telemetria advisory i no poden produir `FAILED` en missio.
- El candidat no escriu configuracio, no descarrega per USB, no fa drain, no
  recupera, no reintenta i no reprodueix cap trigger despres d'armar.

## Analisi del TEST RUN 0.7.7

Run:
`~/Library/Application Support/Eclipse Command/state/runs/20260804T232835_multi_camera_mission_run`

- Resultat global: `warning`, `exit_code=0`.
- Canon 6D: 93/93 imatges compromeses, zero misses, cleanup net i estat fisic
  conegut.
- Sony A7RIIIA: 75/75 imatges compromeses i 63/75 JPEG confirmats al Mac. Les
  tres accions de drain van quedar `drain_not_verified`; cleanup incomplet,
  pero estat fisic final conegut i cap captura omesa.
- Canon R6 III: seleccionada pero exclosa abans de launch amb
  `ptp_identity_unverified`. No va executar controlador ni cap trigger i va fer
  0 RAW. La resta de canals va continuar, com exigeix Mission First.

Aquest run no mesura rendiment de la R6. Mesura correctament el fail-closed
d'identitat i l'aillament entre canals. Quan es reconnecti, cal executar
`Check cameras` abans de `Start mission` per lligar model i serie PTP a la ruta
USB actual.

## DEMOSTRAT

| Ruta R6 | Evidencia fisica propia | Resultat |
|---|---|---|
| Single dens | `20260804T124524_lab_r6m3_dense_single_20x500ms_cfexpress_v1_run` i delta `20260804T124439_to_20260804T124548_exact_plus20.json` | 20/20 RAW, inicis cada 0,5 s, CFexpress +20, cleanup net, estat conegut |
| Timer 2 s | `20260804T224312_lab_r6m3_timer2_single_40x2p2s_cfexpress_20260804_run` i delta `20260804T224213_to_20260804T224458_exact_plus40.json` | 40/40 RAW, inicis cada 2,2 s, CFexpress +40, cleanup net, estat conegut |
| Capacitats PTP | `20260804T223711_lab_r6m3_readonly_preflight/gphoto_transcript.log` | Drive ofereix `Continuous high speed`; AEB ofereix `+/- 3`; shutter ofereix 1/320, 1/2500 i 1/40 |
| Setter Drive | `20260804T124807_lab_r6m3_drive_continuous_high_from_single_cfexpress_preflight_preflight` | canvi remot a Continuous rebutjat netament amb Busy 0x2019 / -110; no es pot posar al cami critic |

## Decisio candidata

Es prioritza AEB3 sobre 105 Single densos:

| Candidat | Ordres PTP C2-C3 | RAW C2-C3 | Exposicions | Risc principal |
|---|---:|---:|---|---|
| Single dens | 105 | 105 | 105 copies a 1/320 | 105 triggers i H90/buffer >20 no demostrat |
| AEB3 | 35 | 105 | 35 x [1/320, 1/2500, 1/40] | AEB3 i H90 encara sense gate fisic |

AEB3 triplica exactament el resultat actual de 35 RAW de totalitat amb el
mateix nombre de 35 pulsacions. Redueix ordres PTP i produeix tres exposicions
fisiques diferents. No es considera encara HDR cientific complet: la finestra
es limita a 6 EV totals i falten filtre retirat, VSD90SS, tracking, focus,
clipping, bits RAW i prova solar/optica.

## Programa materialitzat de referencia

Amb els contactes exactes del run 0.7.7 (C2-C3 = 98,8 s), la previsualitzacio
offline produeix:

- 40 grups i 120 RAW totals.
- 3 grups / 9 RAW abans de C2.
- 35 grups / 105 RAW dins C2-C3.
- 2 grups / 6 RAW despres de C3.
- Separacio dels grups de totalitat: 2,788235 s.
- Ordre esperat per grup: 1/320, 1/2500, 1/40; biaixos 0, -3, +3 EV.
- Zero setters, drains, recovery, retry o replay despres d'armar.

La geometria minima de 88 s conserva 35 grups amb separacio >=2,47 s. Aquesta
previsualitzacio esta implementada a
`gui/eclipse_command/adaptive_profiles.py` pero declara
`promotion_ready=false` i no es seleccionada pel materialitzador operatiu.

## FALTA

- G1 real a 1/320: un press AEB i delta CFexpress exacte +3.
- G5 real: cinc grups a 2,2 s i delta exacte +15.
- G40/H90 real: 40 grups a 2,2 s, 120 commits i delta exacte +120.
- Reobrir i inspeccionar els CR3: ordre d'obturacio repetit, hashes unics,
  cos/serie correctes, mida valida i correspondencia 1:1 amb ledger.
- Repetir tres histories completes, inclosos cold start, canvi de bateria i
  permutacio de ports.
- Assaig solar/optic amb Baader ASSF100, VSD90SS natiu, tracking i focus real.
- Integrar el candidat al materialitzador i al validador immutable, reconstruir
  l'app i fer un TEST RUN complet des del bundle.

## ORDRE DE GATES

1. Bateria carregada, reconnectar i executar preflight read-only. Confirmar
   model `Canon EOS R6 Mark III`, serie PTP exacta, firmware, CFexpress
   `00010001`, RAW card-only i propietari PTP unic.
2. Configuracio manual al cos abans de connectar: M, Electronic, Continuous
   high speed, AEB +/-3, 1/320, RAW CFexpress, Memory card, autoapagada off.
   No intentar reparar Drive/AEB amb setters gphoto.
3. Snapshot CFexpress previ i G1 amb
   `lab_r6m3_native_aeb3_1_320_g1_cfexpress_v1.json`. Aturar al primer Busy,
   timeout, trigger ambigu, delta diferent de +3 o estat desconegut.
4. Snapshot nou i G5 amb
   `lab_r6m3_native_aeb3_1_320_g5_cfexpress_v1.json`. PASS nomes amb +15.
5. Snapshot nou i G40 amb
   `lab_r6m3_native_aeb3_1_320_g40_cfexpress_v1.json`. PASS nomes amb 40
   commits, 120 CR3 nous, zero skips/recovery/replay i estat conegut.
6. Gate CR3 i inspeccio de la sequencia completa; cap recompte PTP substitueix
   el delta exclusiu de la targeta.
7. Nomes despres, promocionar el materialitzador de 35 a 105 RAW de totalitat,
   mantenint el perfil 40/35 actual com a fallback reversible.

## Artefactes offline

- Template G1 SHA-256:
  `0aee53038a3cad697b83d41c3494404789b3b6ab9f498cbef2b1203ab9c0d9dc`.
- G5 SHA-256:
  `099fd52ea575c795e3f37cc638cead8cd7308f4c39d431c13c6177229546ee01`.
- G40 SHA-256:
  `161f7a186e2dda58996fc45790bf743b02e4d5917926c5356bad124af774d55e`.
- Compilador: `controller/tools/compile_r6m3_aeb3_gate_profile.py`.
- Proves: `controller/tests/test_compile_r6m3_aeb3_gate_profile.py`.
- Validacio offline: G1 3, G5 15 i G40 120 imatges esperades; dry-run G40
  `complete`, `exit_code=0`, 120 imatges.

## Decisio actual

No canviar l'app 0.7.7 ni el perfil operatiu mentre la camera es carrega. El
fallback 40/35 es l'unic programa R6 materialitzat que te gate fisic complet.
El candidat AEB3 esta preparat per ser qualificat tan aviat com la R6 torni a
estar disponible; cap afirmacio offline substitueix aquest gate.
