"""Check icon resolution and packaging commands without invoking native build tools."""
import ast
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch

from config import APP_VERSION
from scripts import build_macos, build_windows
from utils.helpers import application_icon_path


class ApplicationPackagingTests(unittest.TestCase):
    def test_runtime_icons_resolve_in_source_and_frozen_app(self):
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication
        app=QApplication.instance() or QApplication([])
        for platform,suffix in (('win32','.ico'),('darwin','.png')):
            with patch('utils.helpers.sys.platform',platform):
                path=Path(application_icon_path())
                self.assertEqual(path.name,'Eclipse_Image_Processor'+suffix)
                self.assertTrue(path.is_file())
                self.assertFalse(QIcon(str(path)).isNull())
        with tempfile.TemporaryDirectory() as tmp:
            assets=Path(tmp)/'assets';assets.mkdir()
            (assets/'Eclipse_Image_Processor.png').touch()
            with patch('utils.helpers.sys._MEIPASS',tmp,create=True),patch('utils.helpers.sys.platform','win32'):
                self.assertEqual(application_icon_path(),str(assets/'Eclipse_Image_Processor.png'))

    def test_build_commands_use_native_icons_and_generated_version(self):
        for module,platform,suffix in ((build_macos,'darwin','.icns'),(build_windows,'win32','.ico')):
            with self.subTest(platform=platform),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();(root/'assets').mkdir();(root/'scripts').mkdir()
                for ext in (suffix,'.png'):
                    (root/'assets'/('Eclipse_Image_Processor'+ext)).touch()
                commands=[]
                def run(command,**kwargs):
                    commands.append(command)
                    if 'PyInstaller' in command and platform=='darwin':
                        plist=root/'dist'/'Eclipse Image Processor.app'/'Contents'/'Info.plist'
                        plist.parent.mkdir(parents=True)
                        plist.write_bytes(plistlib.dumps({'CFBundleIconFile':'Eclipse_Image_Processor.icns'}))
                with patch.object(module,'__file__',str(root/'scripts'/'builder.py')), \
                     patch.object(module.sys,'platform',platform),patch.object(module.sys,'argv',['builder']), \
                     patch.object(module.subprocess,'run',side_effect=run):
                    module.main()
                command=commands[0]
                self.assertEqual(command[command.index('--icon')+1],str(root/'assets'/('Eclipse_Image_Processor'+suffix)))
                self.assertIn(f'{root / "assets" / "Eclipse_Image_Processor.png"}:assets',command)
                self.assertIn(f'{root / "docs" / "third-party"}:docs/third-party',command)
                if platform=='darwin':
                    data=plistlib.loads((root/'dist'/'Eclipse Image Processor.app'/'Contents'/'Info.plist').read_bytes())
                    self.assertEqual(data['CFBundleShortVersionString'],APP_VERSION)
                    self.assertEqual(data['CFBundleVersion'],APP_VERSION)
                else:
                    resource=Path(command[command.index('--version-file')+1]).read_text()
                    ast.parse(resource)
                    self.assertIn(f"StringStruct('FileVersion', '{APP_VERSION}')",resource)
                    self.assertIn(f'filevers={tuple(int(part) for part in APP_VERSION.split("."))+(0,)!r}',resource)
