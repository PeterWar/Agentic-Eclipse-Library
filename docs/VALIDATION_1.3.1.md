# Validation of version 1.3.1 — 2026-10-13

Version 1.3.1 adds documentation and two tests; no function of the package changes its output.

- Built-in tests: 69/69 passed with no skips, in the source tree and from the built wheel imported outside
  the repository (Python 3.12, NumPy 2.5).
- `test_no_filter_makes_rings_on_a_ring_free_input`, on one scene: a ring-free corona with angular structure and
  no noise, the Moon on the Sun's centre, a straight coverage edge. The ring metric is a filtered RMS of the
  azimuthal-mean profile in the 2–16 px band (display units), with a threshold of 0.005. Its three zones lie
  inside the largest Sun-centred circle clear of the frame and of the coverage edge (269 px):
  - over whole rings, at the limb (70–110 px), in the middle (110–220 px) and outside (220–268 px), the sixteen
    filters reach at most 0.0030;
  - in all eight 45° sectors of the middle and outer zones, fifteen filters reach at most 0.0040; WOW bilateral
    reaches 0.0144 and is reported, not checked;
  - the positive controls exceed the threshold: in every zone the old stepped NRGF at 10 px (0.014 or more) and
    rings of 8–10 px added to a layer with amplitude 0.1 (0.024 or more); at the limb and in the middle the same
    rings at 0.02 (0.006 or more);
  - two-pixel grooves stay below 0.15 of the old NRGF's with the 1.2.1 measure;
  - every filter keeps at least 99 % of its support in each 1 px band from the lunar limb and from the straight
    edge (the angular ACHF from 2 px, where its angular kernel has neighbours) and in every sector, which the
    input fixes; layers that lose a band at the limb or a whole sector are caught.
- `test_filters_keep_injected_fine_detail_with_its_sign_and_strength`: with 0.3 % noise, fifteen filters return
  the faint injected pattern with a correlation of 0.68–0.98 and within ±25 % of their 1.3.0 transfer; a layer
  with 99.9 % less contrast would fail. WOW bilateral gives −0.23 and is reported, not checked.
- Not covered by these tests, and reported instead (`docs/FIELD_LESSONS.md` and the two issues): the bands
  along data edges in ACHF and WOW, and the behaviour of WOW bilateral.
- Before release, the plan, the changes and the issue texts were contrasted with Codex (GPT-6 Astra, xhigh) in
  three rounds. Its objections changed the tests (rings at several scales and in sectors fixed by the input,
  support by band, the strength of the detail) and the wording of these documents.

The contribution's own measurements were made on the contributor's data and producer, which are not
distributed; they are quoted as reported. These checks test the package as it is today, on one synthetic
scene; they do not certify the filters on real data.
