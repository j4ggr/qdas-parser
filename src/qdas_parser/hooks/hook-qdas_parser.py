# PyInstaller hook for qdas_parser.
#
# Ensures that the bundled ``qdas.toml`` data file is included in frozen
# applications.  This hook is discovered automatically by PyInstaller
# because the package advertises it via ``pyproject.toml``
# (``[tool.pyinstaller] hook-dirs``).
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('qdas_parser')
