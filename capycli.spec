# SPDX-FileCopyrightText: (c) 2025 Siemens
# SPDX-License-Identifier: MIT
#
# PyInstaller .spec file
# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import copy_metadata
from os import path

site_packages = next(p for p in sys.path if 'site-packages' in p)
datas=[
        (path.join(site_packages,"cyclonedx/schema/_res/*.*"), 'cyclonedx/schema/_res'),
        (path.join(site_packages,"license_expression/data"), 'license_expression/data')
    ]
datas += copy_metadata('capycli')
hiddenimports = []
hiddenimports += collect_submodules('application')

a = Analysis(
    ['capycli/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='capycli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
