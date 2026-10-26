# Build the macOS application

From the repository root, with `.venv` already created:

```bash
.venv/bin/python -m pip install -r requirements.txt -r requirements-build.txt
.venv/bin/python scripts/build_macos.py
```

To also create a drag-to-install disk image:

```bash
.venv/bin/python scripts/build_macos.py --dmg
```

The application is written to `dist/Eclipse Image Processor.app`. Open it from Finder or copy it to Applications. It bundles Python, dependencies and the icon, so no development environment is required to run it.

`dist/Eclipse Image Processor.dmg` contains the app and an Applications shortcut. Open the DMG and drag the app onto that shortcut to install it.

The build script derives both macOS bundle version fields from `config.APP_VERSION` (currently 0.6.0), then applies an ad-hoc signature. This is a local build, not an Apple-notarized public distribution; Developer ID signing and notarization require a separate release process.

The bundle uses the supplied `assets/Eclipse_Image_Processor.icns` directly for Finder and the Dock. The matching `assets/Eclipse_Image_Processor.png` is bundled for Qt windows and the menu-bar icon; it avoids dependence on a Qt ICNS decoder. In source runs, QApplication uses that PNG for the application icon. Intermediate files and PyInstaller configuration go into `build/macos`; both `build/` and `dist/` are ignored by Git.

The target architecture follows the build interpreter: use an arm64 Python and dependencies for Apple Silicon, or x86_64 for Intel. Rebuilding replaces previous build outputs. A version/source change requires a fresh build; existing app bundles are not updated automatically.

Use Python 3.14 or later with platform-compatible dependencies. Consult the [technical index](README.md) and [validation record](validation.md) for current scope. Packaging was not rerun during the 26 October documentation update.
