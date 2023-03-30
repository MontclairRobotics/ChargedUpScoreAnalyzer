import cx_Freeze
import sys
import zipfile

base = "Win32GUI" if sys.platform == "win32" else None

executables = [cx_Freeze.Executable('Cusa 555.py', base=base, icon='icon.ico')]

cx_Freeze.setup(
    name="Cusa 555",
    options={
        "build_exe": {"packages": ['pygame', 'easygui'], 'include_files': ['icon.png', 'icon.ico', 'help.txt']}
    },
    executables=executables
)