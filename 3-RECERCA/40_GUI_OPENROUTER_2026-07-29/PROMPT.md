You are reviewing a safety-critical, offline desktop command console for solar
eclipse photography. It is written in Python/PySide6 for macOS and Linux and
uses an existing gphoto2 controller. The current physical profile is a Sony
A7 III, but future profiles may include Canon.

Review the product direction and return a concise, implementation-ready answer
covering:

1. The simplest operator flow for C1, C2, C3 and C4 when the user enters only
   UTC time-of-day, not date.
2. How the GUI should discover cameras automatically and explain exact
   corrective actions when a required camera setting is wrong.
3. Three clearly different visual themes that remain legible outdoors in full
   daylight: give color hex values, contrast rationale and hierarchy.
4. A safe approach to audible alerts for C1-C4 that avoids false confidence.
5. The most important risks in making the app launch by double-click on macOS
   and Linux while gphoto2 remains an external dependency.
6. What should remain locked or read-only in the first prototype.

Assume that the controller remains the final authority, no network is available
during capture, the GUI must never silently fire the shutter, and remote camera
power-off is not a supported assumption. Prioritize usability under stress and
bright sunlight over decorative complexity.
