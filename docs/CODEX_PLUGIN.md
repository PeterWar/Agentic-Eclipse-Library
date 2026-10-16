# AEL for Codex

Agentic Eclipse Library is available as a desktop plugin with six guided workflows and the bundled
AEL 1.3.2 numerical engine. Plugin version 1.0.0 is independently versioned from the Python library.
The repository marketplace works independently of OpenAI's public directory review.

![AEL synthetic workflow demonstration](../plugins/codex-ael/assets/synthetic-workflow.png)

*Synthetic test data: a full linear input, a structure display and a polar view. This is a software
demonstration, not an astronomical observation. The logarithmic view of the linear input is for display.*

## Install

With a recent Codex CLI:

```
codex plugin marketplace add PeterWar/Agentic-Eclipse-Library
codex plugin add agentic-eclipse-library@pere-guerra-eclipse
```

In the desktop app, add the repository marketplace, open the Plugins Directory, select
**Pere Guerra · Eclipse** and install **Agentic Eclipse Library**. After installation, start a new local
chat so that the skills can be discovered. If an older client does not have `codex plugin add`, use
the desktop directory or update the client through its normal update flow.

The plugin requires local execution and Python 3.10+. It checks dependencies before processing.
Installing the plugin does not install Python packages silently. See the bundled
[setup instructions](../plugins/codex-ael/docs/USAGE.md). Photoshop is optional; it is needed only to
open/edit Photoshop deliverables, not for AEL's numerical processing.

## Ask in your language

- “Help me process these eclipse RAWs and preserve the originals.”
- “Inspect this ring and find where it first appears in the processing.”
- “Make a polar view with the solar geometry I measured.”
- “Show me a clearly labelled synthetic demonstration.”

The six workflows cover onboarding, calibration/stacking, filter layers, artefact diagnosis,
structure/polar/motion views and coronagraph comparisons. An agent must measure inputs and explain
uncertainties; the plugin is not a one-click reconstruction of a finished photograph.

## Validation and limitations

The first ZIP was extracted into a separate directory and exercised using Python 3.12 on macOS.
All 84 bundled AEL tests passed with zero skips. Seventeen integration checks covered dependency
reporting without installed packages, missing-dependency messages, refusal to overwrite existing output,
the synthetic motion demonstration, full-canvas structure output, preservation of input hashes and
rejection of unsupported colour input and output-name path escapes.

The bundled runtime was checked byte for byte against the maintained AEL source. The six skills passed
structural validation and their entrypoint links resolved inside the package. Native Codex marketplace
installation was also tested. These checks do not prove usability on every platform or validate new
astronomical data. Windows and Linux have not been exercised for this plugin release.

AEL 1.3.2 retains documented ACHF/WOW boundary bands and possible fine-detail sign inversion in WOW
bilateral. See [field lessons](FIELD_LESSONS.md). The plugin's structure launcher preserves the full
canvas and defaults to mono; the underlying historical CLI has different display defaults.

## Privacy, licence and support

The plugin has no MCP server, lifecycle hooks, telemetry, credential reader, paid-model client or uploader.
Numerical processing runs locally. Dependency installation may download from PyPI. Public reference data
is obtained only when needed and authorized. The AI host's policies still govern prompts and tool outputs
in the chat; local processing does not mean the entire chat is offline.

The historical research archive is kept in the repository, outside the plugin package. Source code and
plugin are MIT licensed. Credit is welcome, not a licence condition. Report reproducible problems through
[GitHub Issues](https://github.com/PeterWar/Agentic-Eclipse-Library/issues), without private photographs or
personal information unless you intentionally choose to publish them.

## Maintainers

The plugin lives in `plugins/codex-ael/`. Its runtime and reference snapshots come from the maintained
root package. Use `tools/build_codex_plugin_20261016.py --sync --out NEW.zip` to refresh and package them,
then `tools/test_codex_plugin.py NEW.zip NEW_VALIDATION_DIR` with the supported Python environment.
The output ZIP is never overwritten. `BUNDLE_CONTENTS.json` records the file hashes and runtime source commit.
Update the snapshot and the package version deliberately when the maintained AEL engine changes.
