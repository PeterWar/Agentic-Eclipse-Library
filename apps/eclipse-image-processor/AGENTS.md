# Repository Guidelines

## Project Structure & Module Organization

Eclipse Image Processor is a Python/PySide6 desktop application for enhancing solar eclipse images. `main.py` initializes CPU threading and launches `gui.app.EclipseProcessorApp`. `core/filters.py` contains the active numerical filters and Qt `FilterWorker`; `gui/` contains the window, canvas, controls, and factories. The GUI coordinates asynchronous loading, geometry, background preparation, presentation and export. `core/pipeline.py` dispatches independent branches through `core/layer_engine.py`; `core/presentation.py` separates TIFF composition from PSB presentation. See `docs/architecture.md` for module responsibilities.

`config.py` holds styling and application constants; `utils/helpers.py` resolves resource paths. Synthetic filter tests live in `tests/`, development utilities in `scripts/`, and application icons in `assets/`. Bundled AEL ports have separate modules; preserve their attribution notices.

## Build, Test, and Development Commands

Run from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
python -m unittest discover -s tests -v
```

These commands create and activate an environment, install dependencies, launch the desktop UI, and run the test suite. On Windows, activate with `.venv\Scripts\Activate.ps1`. Python metadata declares version 3.14 or later; verify dependency compatibility. Platform builders are `scripts/build_macos.py` (optional `--dmg`) and `scripts/build_windows.py`; install `requirements-build.txt` and build on the target operating system. Keep dependencies in `requirements.txt` and the inline metadata in `main.py` synchronized.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` functions and variables, `PascalCase` classes, and `UPPER_SNAKE_CASE` constants. Follow surrounding code and document array shapes, units, masks, and normalization behavior for numerical changes. Preserve CPU environment initialization before NumPy imports in `main.py`. No formatter or linter configuration is provided.

## Testing Guidelines

Use standard-library `unittest` with NumPy assertions. Name files `tests/test_*.py` and methods `test_*`. Add deterministic synthetic cases for changed filter behavior, including boundaries, nonfinite inputs, masks, and bypass settings. No coverage threshold is configured. Manually verify GUI changes and preview/export behavior with real images; inspect TIFF dimensions/bit depth and the companion JPEG.

## Commit & Pull Request Guidelines

Use concise imperative subjects describing the affected behavior. Pull requests should explain the change, link relevant issues, report automated and manual checks, and include screenshots for UI changes. Keep virtual environments, caches, local image data, and generated code dumps out of commits.
