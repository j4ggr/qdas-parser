"""Package-level constants derived from the bundled ``qdas.toml`` config.

All downstream modules import from here so the TOML is only loaded once
and the compiled regex objects are shared across all parser instances.
"""

import re

from re import Pattern
from typing import Literal
from dataclasses import dataclass

from ._config import QDAS_CONFIG

__all__ = ['QDAS']

@dataclass(frozen=True)
class _QDASConstants:
    """Container for package-level constants derived from the bundled 
    config.

    This class is not intended to be instantiated; it serves as a 
    namespace for related constants and their docstrings. The actual
    constant values are defined at the module level below for direct 
    import.
    """

    SEP_F: str = chr(QDAS_CONFIG['features']['sep']['dec'])
    """Feature separator character (ASCII 15, i.e. ``0x0F``)."""

    SEP_E: str = chr(QDAS_CONFIG['extensions']['sep']['dec'])
    """Extension separator character (ASCII 20, i.e. ``0x14``)."""

    TIMESTAMP: Literal['Zeitstempel'] = 'Zeitstempel'
    """Column name for the timestamp (``'Zeitstempel'``)."""

    PART_ID: Literal['Seriennummer'] = 'Seriennummer'
    """Column name for the part identity (``'Seriennummer'``)."""

    ORDER: Literal['Auftragsnummer'] = 'Auftragsnummer'
    """Column name for the production order number 
    (``'Auftragsnummer'``)."""

    RE_HEADER: Pattern = re.compile(
        QDAS_CONFIG['fields']['regex_pattern']['header_file'])
    """Compiled regex that parses a single ``.dfd`` line into 
    (key, feature_n, value)."""

    RE_CLEAN_LINE: Pattern = re.compile(
        QDAS_CONFIG['fields']['regex_pattern']['clean_line'])
    """Compiled regex that matches K-Field lines embedded in value files."""

QDAS = _QDASConstants()
"""Package-level constants derived from the bundled ``qdas.toml`` config.

Access individual constants as attributes, e.g. ``QDAS.SEP_F``.

The constants include:
- ``SEP_F``: Feature separator character (ASCII 15, i.e. ``0x0F``).
- ``SEP_E``: Extension separator character (ASCII 20, i.e. ``0x14``).
- ``TIMESTAMP``: Column name for the timestamp (``'Zeitstempel'``).
- ``PART_ID``: Column name for the part identity (``'Seriennummer'``).
- ``ORDER``: Column name for the production order number (``'Auftragsnummer'``).
- ``RE_HEADER``: Compiled regex that parses a single ``.dfd`` line into
    (key, feature_n, value).
- ``RE_CLEAN_LINE``: Compiled regex that matches K-Field lines embedded
    in value files.
"""
