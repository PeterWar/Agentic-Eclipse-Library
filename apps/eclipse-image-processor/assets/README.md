# Application icons

The active artwork is provided in three matching formats:

- `Eclipse_Image_Processor.icns`: native macOS application-bundle icon (Finder/Dock).
- `Eclipse_Image_Processor.ico`: Windows executable, shortcut and Qt window icon, with 16–256 px sizes.
- `Eclipse_Image_Processor.png`: 1024 px Qt application icon on macOS and the menu-bar/notification-area icon on both systems; Windows fallback if the ICO is unavailable.

These resources are used in source runs and by `scripts/build_macos.py` / `scripts/build_windows.py`. Keep all three formats synchronized when replacing the artwork. Builders consume the supplied files directly and generate only packaging metadata. The older `icon-options/` artwork is retained as alternatives and is not used by the application or builds.
