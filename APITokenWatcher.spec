# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None
ROOT = os.path.abspath('.')

a = Analysis(
    ['run.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('backend/static', 'backend/static'),
    ],
    hiddenimports=[
        # pywebview
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'webview.platforms.mshtml',
        # APScheduler
        'apscheduler.schedulers.background',
        'apscheduler.executors.pool',
        # pydantic settings
        'pydantic_settings',
        # httpx
        'httpx._transports.default',
        # SQLModel / SQLAlchemy
        'sqlmodel',
        'sqlalchemy.dialects.sqlite',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='APITokenWatcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 无控制台窗口
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='APITokenWatcher',
)
