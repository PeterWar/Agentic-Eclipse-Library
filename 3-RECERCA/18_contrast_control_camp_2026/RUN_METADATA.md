# Metadades de la ronda Claude + OpenRouter

Data: 2026-07-26

## Context enviat

Només es va enviar el text de [PROMPT.md](PROMPT.md). No es van enviar RAW,
logs, directoris de Dropbox ni altres fitxers del projecte.

## Claude local

- El CLI `claude` era instal·lat, però va retornar `Not logged in`.
- Es va utilitzar com a fallback la sessió local ja autenticada de Claude.ai.
- Xat canònic del projecte:
  <https://claude.ai/chat/cf1fdb0a-acce-4875-9519-5cbb464a469c>
- Model visible a la interfície: `Fable 5 Extra`.
- Resposta conservada:
  [responses/claude_fable_5_extra.md](responses/claude_fable_5_extra.md).

## OpenRouter

Totes les consultes útils es van executar amb:

- Zero Data Retention exigit (`zdr=true`);
- recollida de dades denegada (`data_collection=deny`);
- temperatura final `0.1`;
- resposta final demanada sense cadena de raonament.

| Model final | Tokens entrada | Tokens sortida | Cost declarat |
|---|---:|---:|---:|
| `google/gemini-3.1-pro-preview` | 2.047 | 4.362 | 0,056438 USD |
| `x-ai/grok-4.5` | 2.124 | 2.198 | 0,0172184 USD |
| `nvidia/nemotron-3-ultra-550b-a55b` | 1.961 | 2.731 | 0,0110082 USD |
| **Total de les tres respostes conservades** | **6.132** | **9.291** | **0,0846646 USD** |

### Reintents i incidències

1. La primera crida `compare` va fallar perquè almenys un endpoint va retornar
   contingut no textual incompatible amb el parser.
2. `moonshotai/kimi-k3`, consultat individualment, va repetir el mateix error
   de contingut no textual. Es va substituir per NVIDIA Nemotron 3 Ultra.
3. El primer intent de Gemini va consumir 3.800 tokens i 0,02556 USD però va
   deixar només un fragment de resposta.
4. El primer intent de Grok va consumir 5.330 tokens i 0,0201704 USD però va
   acabar a mig document.
5. Gemini i Grok es van repetir amb més marge i instrucció de resposta concisa;
   només les segones respostes es conserven com a opinions finals.

### Cost total auditat de la ronda

- Ús acumulat OpenRouter abans: `0,13770109 USD`.
- Ús acumulat OpenRouter després: `0,37343889 USD`.
- **Increment real de compte: 0,23573780 USD.**

L'increment real inclou les tres respostes finals, els dos intents truncats i
les crides que van fallar abans que el CLI pogués emetre metadades. La part no
desglossada directament és `0,1053428 USD`; no s'atribueix artificialment a un
model concret.

## Limitació interpretativa

Les respostes dels models són opinions de revisió, no fonts tècniques. Les
afirmacions sobre compatibilitat, rellotges, cables, cadència i bràqueting
només es promocionen a fet després de:

1. font primària del fabricant; i
2. prova física amb A7III/A7RIIIA, targetes i configuració finals.
