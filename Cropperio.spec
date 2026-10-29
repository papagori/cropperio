# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct,
    VSVersionInfo,
)

from cropper.version import __version__
from importlib.metadata import distribution


# The Windows wheel stores libheif/libde265/libx265 beside its Python package.
# Collect precisely the wheel's native libraries, plus their bundled licenses.
heif_wheel = distribution('pillow-heif')
heif_binaries = [(str(heif_wheel.locate_file(path)), '.')
                 for path in heif_wheel.files if path.suffix.lower() == '.dll']
heif_licenses = [(str(heif_wheel.locate_file(path)), 'licenses/pillow-heif')
                for path in heif_wheel.files if 'licenses' in path.parts]


version_numbers = tuple(int(part) for part in __version__.split('.')) + (0,)
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=version_numbers,
        prodvers=version_numbers,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable('040904B0', [
                StringStruct('CompanyName', 'Cropperio'),
                StringStruct('FileDescription', 'Cropperio photo crop and resize utility'),
                StringStruct('FileVersion', __version__),
                StringStruct('InternalName', 'Cropperio'),
                StringStruct('LegalCopyright', 'GNU General Public License v3.0'),
                StringStruct('OriginalFilename', 'Cropperio.exe'),
                StringStruct('ProductName', 'Cropperio'),
                StringStruct('ProductVersion', __version__),
            ]),
        ]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])]),
    ],
)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=heif_binaries,
    datas=[('assets/cropperio.ico', 'assets'),
           ('tests/fixtures/input_formats', 'validation-inputs')] + heif_licenses,
    hiddenimports=['_pillow_heif'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Cropperio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/cropperio.ico',
    version=version_info,
)
