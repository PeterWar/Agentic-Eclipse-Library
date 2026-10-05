# Goal-first onboarding review — 1.2.1

This is a manual review of the written instructions and sample first replies, not a
model benchmark or a claim that three independent agents were run.

| Input | Required first action | Reviewed sample (Catalan) |
| --- | --- | --- |
| “Hola, acabo de descarregar la llibreria.” | Ask goal in the user's language with short choices; do not assume stacking | “Què vols fer: processar fotos d'un eclipsi, continuar una imatge, fer una animació o explorar la llibreria?” |
| “Tinc els RAW a aquesta carpeta; fes-me un PSB amb filtres.” | Use the explicit goal; begin inventory; no repeated goal question | “Revisaré les fotos, les exposicions i els calibradors per preparar l'apilat i el PSB amb capes.” |
| “No sé per on començar.” | Offer to inspect files the user identifies and recommend a starting point | “Puc mirar les fotos o la imatge que tinguis i proposar-te un primer pas. En quina carpeta són?” |

`AGENTS.md` and `skills/eclipse-first-steps/SKILL.md` were checked against all three cases.
The old instruction that the path is always RAW-to-Photoshop was removed. The ordered
calibration/stacking/layers path still applies when the user actually requests it.
