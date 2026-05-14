# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for AE Analyzer (Windows build)
# Run with: pyinstaller AE_Analyzer.spec

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # tkinter
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        # matplotlib backends
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends._backend_tk',
        'matplotlib.backends.backend_agg',
        'matplotlib.figure',
        'matplotlib.gridspec',
        'matplotlib.mlab',
        # mpl_toolkits
        'mpl_toolkits',
        'mpl_toolkits.axes_grid1',
        'mpl_toolkits.axes_grid1.axes_divider',
        # numpy
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AE_Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no black console window on launch
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # add an .ico path here if you have one
)
