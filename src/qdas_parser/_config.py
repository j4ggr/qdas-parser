"""Load the bundled ``qdas.toml`` configuration at import time.

Uses :mod:`tomllib` (stdlib ≥ 3.11) and :mod:`importlib.resources` so
the TOML file is read directly from the installed package without
relying on the filesystem path of the source tree.
"""

import tomllib
import importlib.resources


__all__ = ['QDAS_CONFIG']


def _load() -> dict:
    data = importlib.resources.files(__package__).joinpath('qdas.toml').read_bytes()
    return tomllib.loads(data.decode())


QDAS_CONFIG: dict = _load()
"""Package-level configuration loaded from the bundled ``qdas.toml`` 
file."""