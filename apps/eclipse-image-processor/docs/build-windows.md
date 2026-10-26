# Build the Windows application

Build on Windows using Python 3.14 or later and a matching set of binary dependencies. From the repository root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt
.venv\Scripts\python.exe scripts/build_windows.py
```

The output is `dist\Eclipse Image Processor\Eclipse Image Processor.exe`. Run the executable there. To distribute the app, copy or ZIP the entire `Eclipse Image Processor` folder, including `_internal`; copying the executable alone will not work. No installer or Start-menu shortcut is generated.

The build embeds `assets/Eclipse_Image_Processor.ico` in the executable for Explorer and shortcuts. Qt loads the bundled ICO for the window and taskbar, with a matching PNG fallback. The notification-area icon uses `assets/Eclipse_Image_Processor.png` when a system tray is available. The stable Windows AppUserModelID is set before QApplication starts.

`scripts/build_windows.py` generates `build/windows/version_info.txt` from `config.APP_VERSION`, including file/product versions and author metadata, and passes it to PyInstaller. There is no version file to maintain manually. The builder also bundles the runtime icons, attribution file and retained third-party licenses. Work files, generated spec, caches and version resource stay under `build/windows`; final output goes under `dist`.

This is a local unsigned build. Authenticode signing and an installer are separate release tasks. Build on Windows; the macOS script cannot produce a Windows executable. Target architecture follows the Windows Python interpreter and available dependencies.

Rebuilding replaces the previous output. Existing pinned shortcuts may retain a cached icon; recreate the shortcut if it still shows an older icon after replacing the application. Source runs use the same Qt icon resources but do not replace the Python executable's Explorer icon.

Use Python 3.14 or later with platform-compatible dependencies. Consult the [technical index](README.md) and [validation record](validation.md) for current scope. Packaging was not rerun during the 26 October documentation update.
