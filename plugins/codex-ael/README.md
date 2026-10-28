# Agentic Eclipse Library for Codex

Process total solar eclipse photographs with seven guided workflows: get started, calibrate and stack,
create corona filter layers, investigate artefacts, make polar views and motion analyses, compare
observations with coronagraphs, and take a whole case to an editable master the photographer accepts
(contributed by Raúl Hussein). Created by Pere Guerra Serra. MIT licensed.

This desktop plugin bundles the AEL 1.3.4 Python processing engine, its known-truth tests, recipe
templates and practical documentation. It runs on the user's computer with Python 3.10 or later.
The host AI plans the work and explains the results; AEL performs the numerical processing.

## Start

Install this plugin from the configured Codex marketplace or the OpenAI directory once approved.
Then ask, in your language:

- Help me process my total solar eclipse photos while preserving the original files.
- Inspect the rings in my corona image and find which processing stage caused them.
- Show me a clearly labelled synthetic demonstration before I use my own photos.

Follow [setup and operating instructions](docs/USAGE.md). Installing the plugin does not install Python
or Python dependencies automatically. The setup checks what is available before proposing a change.

## Outputs and limits

AEL can write linear stacks, validity and coverage maps, filter layers, 16-bit layered Photoshop files,
polar views, motion check sheets and animations. A photograph is not an absolute brightness measurement.
Calibration, registration, geometry and any spatial cloud correction require measured inputs; AEL does
not infer all of these from a folder of RAWs. Photoshop itself is optional.

Known limitations in 1.3.4 include bands near data boundaries in ACHF/WOW, rings of the default WOW next
to a lunar limb that the data reach, and some fine-detail sign inversion in the worst sectors of WOW bilateral. See [field lessons](docs/FIELD_LESSONS.md). Passing the bundled tests does
not validate a new astronomical observation. Missing data stays missing. Synthetic examples are labelled
and must never be used as pixels in an observed image.

## Data and execution

- The bundled Python source runs locally. It reads the files selected for the task and writes new outputs.
- Dependency installation uses pip and normally downloads packages from PyPI. Basic processing needs
  NumPy, SciPy, OpenCV, Pillow, tifffile and imageio. RAW/FITS and Photoshop support have extra dependencies.
- This plugin has no MCP server, lifecycle hooks, telemetry, paid model calls, credential reader or uploader.
- Public coronagraph or ephemeris data can be downloaded when needed and authorized. State the source,
  purpose and approximate size first. Astropy may access Earth-orientation tables if network access is enabled.
- The AI host has its own data-handling policy: filenames, prompts, previews and tool outputs used in a chat
  may enter that chat's context. Local numerical processing does not imply that the entire AI session is offline.
- Publishing photographs, uploading data, creating contributions or contacting third parties requires the
  user's authorization for that action.

The original project's historical research archive remains available in the
[source repository](https://github.com/PeterWar/Agentic-Eclipse-Library). It is not installed by this plugin.
The bundled runtime is an exact snapshot of the maintained package, checked by the packaging script.

Support: [GitHub Issues](https://github.com/PeterWar/Agentic-Eclipse-Library/issues).
See the [privacy policy](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/main/docs/CODEX_PLUGIN_PRIVACY.md)
and [licence and terms](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/main/docs/CODEX_PLUGIN_TERMS.md).
Optional credit: Processed with Agentic Eclipse Library by Pere Guerra.
