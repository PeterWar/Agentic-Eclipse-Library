# Independent GUI review via OpenRouter

Date: 2026-07-29  
Scope: research only; never part of the offline capture path.

## Selection matrix

| Voice | Provider / lineage | Why included | Result |
|---|---|---|---|
| `x-ai/grok-4.5` | xAI / Grok | Strong independent product and safety review | Complete and useful |
| `google/gemini-3.1-flash-lite` | Google / Gemini | Independent low-latency UX review | Complete; several recommendations rejected |
| `deepseek/deepseek-v4-flash` | DeepSeek / DeepSeek | Independent implementation review | Truncated; useful only as a dissenting partial view |

OpenAI was excluded because Codex already represents that provider. Anthropic
was excluded because Claude was already represented in the broader project
conversation. No router alias or duplicate provider was counted as an
independent voice.

## Context and privacy

- Authorized material sent: `PROMPT.md` only.
- Source files, controller evidence, camera serials and physical-test logs sent:
  none.
- `sent_files=[]` in every completed response.
- OpenRouter provider policy: `data_collection=deny`.
- ZDR: `false`; the prompt contained no sensitive project material.
- No OpenRouter response is used at capture time.

## Findings retained

The useful consensus was:

1. Keep C1–C4 as four explicit UTC time-of-day fields, validate ordering and
   show one timeline. The mission date belongs in one global field, not in each
   contact.
2. Discover cameras continuously, freeze arming on disconnect, and show
   `setting / current / required / exact correction`. Never silently choose a
   body when multiple cameras are present.
3. Encode state with words as well as color, use large type and strong borders,
   and keep a bright light theme as the outdoor default.
4. Audio is advisory. A tone must not imply that an exposure succeeded unless
   controller evidence confirms it. Missed contacts must never trigger a late
   catch-up burst.
5. Double-click launchers need explicit paths because Finder and desktop
   launchers provide a reduced environment. Missing `gphoto2`, USB permissions,
   stale PTP clients and working-directory assumptions need actionable errors.
6. Contact times, profile requirements and capture controls stay locked after
   arming. Remote power-off, destructive camera writes and silent shutter
   commands remain outside the prototype.

## Recommendations explicitly rejected

External models are advisory and sometimes contradicted the stated safety
contract:

- Gemini suggested deriving all contacts from one start time. The application
  keeps four explicit operator-supplied contact times.
- Gemini suggested a generic automatic-fix button and a “manual override.”
  Eclipse Command only exposes profile-declared qualified fixes, with explicit
  confirmation and readback; there is no override around a failed gate.
- DeepSeek suggested firing the shutter at each contact and pausing for
  acknowledgment. Contacts are phase boundaries, not a four-shot capture plan;
  the existing controller choreography remains authoritative.
- Dark themes were recommended for direct sun by two voices. The local visual
  review selected the light `Solar Paper` theme because it is easier to read
  on this display under bright ambient light. `Flight Deck` is retained as the
  night/totality option.
- Repeating unacknowledged audio every five seconds was rejected because it can
  mask other alerts and increase stress.

## Cost audit

Usage counter before this review: `$9.414911060`  
Usage counter after this review: `$9.479186021`  
Total charged by the complete review round: **`$0.064274961`**

Completed response metadata:

| Request | Prompt | Completion | Cost |
|---|---:|---:|---:|
| `x-ai/grok-4.5` final | 518 | 1,379 | `$0.00909240` |
| `google/gemini-3.1-flash-lite` | 311 | 872 | `$0.00138575` |
| `google/gemini-3.1-pro-preview` (output-starved) | 328 | 1,596 | `$0.01980800` |
| `deepseek/deepseek-v4-flash` (truncated) | 296 | 1,200 | `$0.00037744` |

Earlier completed attempts in the same round cost `$0.01476640`:
`google/gemini-3.6-flash` (`$0.00640200`) and
`x-ai/grok-4.5` (`$0.00836440`). Interrupted comparison and stalled
`deepseek-v4-pro` requests account for the remaining `$0.018844971`.

The total is about 1.29% of the authorized `$5` maximum.
