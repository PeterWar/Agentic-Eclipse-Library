"""Build an Apple Silicon or Intel .app using the current Python architecture.

Run from the repository root: .venv/bin/python scripts/build_macos.py
"""

from pathlib import Path
import argparse
import os
import plistlib
import subprocess
import sys
import tempfile



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dmg", action="store_true", help="Also create the drag-to-install disk image")
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("Build the macOS application on macOS.")
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root))
    from config import APP_VERSION
    build = root / "build" / "macos"
    build.mkdir(parents=True,exist_ok=True)
    assets=root/'assets'
    icon=assets/'Eclipse_Image_Processor.icns'
    for resource in (icon,assets/'Eclipse_Image_Processor.png'):
        if not resource.is_file():
            raise FileNotFoundError(resource)

    # Keep caches and generated spec files inside the ignored build directory.
    environment = os.environ.copy()
    environment["PYINSTALLER_CONFIG_DIR"] = str(build / "cache")
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--windowed", "--onedir", "--name", "Eclipse Image Processor",
        "--icon", str(icon), "--osx-bundle-identifier", "com.fbitto.realcecoronal",
        "--specpath", str(build), "--workpath", str(build / "work"),
        "--distpath", str(root / "dist"),
        "--add-data", f"{assets / 'Eclipse_Image_Processor.png'}:assets",
        "--add-data", f"{root / 'docs' / 'third-party'}:docs/third-party",
        "--add-data", f"{root / 'ATTRIBUTIONS.md'}:.",
        "--add-data", f"{root / 'LICENSE'}:.",
        "--collect-all", "watroo",
        "--collect-all", "psd_tools",
        "--hidden-import", "PIL.TiffImagePlugin",
        str(root / "main.py"),
    ], cwd=root, env=environment, check=True)
    plist_path=root/'dist'/'Eclipse Image Processor.app'/'Contents'/'Info.plist'
    with plist_path.open('rb') as stream:
        metadata=plistlib.load(stream)
    metadata.update(CFBundleShortVersionString=APP_VERSION,CFBundleVersion=APP_VERSION)
    with plist_path.open('wb') as stream:
        plistlib.dump(metadata,stream)
    subprocess.run(["/usr/bin/codesign","--force","--deep","--sign","-",str(plist_path.parents[1])],check=True)
    print(f"Application ready: {root / 'dist' / 'Eclipse Image Processor.app'}")
    if args.dmg:
        app = root / "dist" / "Eclipse Image Processor.app"
        subprocess.run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)], check=True)
        with tempfile.TemporaryDirectory(prefix="dmg-", dir=build) as staging:
            destination = Path(staging)
            subprocess.run(["/usr/bin/ditto", str(app), str(destination / app.name)], check=True)
            (destination / "Applications").symlink_to("/Applications", target_is_directory=True)
            dmg = root / "dist" / "Eclipse Image Processor.dmg"
            subprocess.run([
                "/usr/bin/hdiutil", "create", "-volname", "Eclipse Image Processor",
                "-srcfolder", str(destination), "-format", "UDZO", "-ov", str(dmg),
            ], check=True)
            subprocess.run(["/usr/bin/hdiutil", "verify", str(dmg)], check=True)
        print(f"Installer ready: {dmg}")


if __name__ == "__main__":
    main()
