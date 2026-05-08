"""
All downstream modules import from here so the TOML is only loaded once
and the compiled regex objects are shared across all parser instances.
"""

import re
from re import Pattern

from typing import Literal

from dataclasses import dataclass

__all__ = ['QDAS', 'FIELD_CATEGORY']

@dataclass(frozen=True)
class _Spec:
    """Container for package-level constants.

    This class is not intended to be instantiated; it serves as a
    namespace for related constants and their docstrings. The actual
    constant values are defined at the module level below for direct
    import.
    """

    SEP_F: str = chr(15)
    """Feature separator character (ASCII 15, i.e. ``0x0F``)."""

    SEP_E: str = chr(20)
    """Extension separator character (ASCII 20, i.e. ``0x14``)."""

    EXTENSIONS: tuple[str, ...] = (
        'Wert',
        'Attribut',
        'Datum/Zeit',
        'Ereignisse',
        'Chargennummer',
        'Nestnummer',
        'Prüfnummer',
        'Maschinennummer',
        'Prozessparameter',
        'Prüfmittelnummer',)
    """Ordered tuple of extension names corresponding to their numeric
    identifiers (1-10)."""

    TIMESTAMP: Literal['Zeitstempel'] = 'Zeitstempel'
    """Column name for the timestamp (``'Zeitstempel'``)."""

    PART_ID: Literal['Seriennummer'] = 'Seriennummer'
    """Column name for the part identity (``'Seriennummer'``)."""

    ORDER: Literal['Auftragsnummer'] = 'Auftragsnummer'
    """Column name for the production order number 
    (``'Auftragsnummer'``)."""

    RE_HEADER: Pattern = re.compile(r'(K\d+)/?(\d+)? (.+)?')
    """Compiled regex that parses a single ``.dfd`` line into 
    (key, feature_n, value).
    - ``key``: K-Field key string (e.g. ``'K0100'``, ``'K2002'``, ``'K10100'``).
    - ``feature_n``: Optional feature number for feature-specific 
      K-Fields (e.g. ``'1'`` from ``'K2002/1'``). None for 
      non-feature-specific K-Fields (e.g. ``'K0100'``).
    - ``value``: The rest of the line after the key and optional feature
      number, which may be empty or None.
    """

    RE_CLEAN_LINE: Pattern = re.compile(r'^K\d{4,}')
    """Compiled regex that matches K-Field lines embedded in value files.
    These lines start with a K-Field key 
    (e.g. ``'K0100'``, ``'K2002/1'``) and are not part of the
    measurement data. They should be handled separately.
    """

QDAS = _Spec()
"""Package-level constants.

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

@dataclass(frozen=True)
class _FieldCategory:
    """Category mapping for K-Field keys.

    Category is determined by the thousands-digit group of the K-Field
    number (e.g. ``'1'`` from ``'K1001'``, ``'10'`` from ``'K10100'``).

    Examples
    --------
    >>> FIELD_CATEGORY['K0100']
    'description'
    >>> FIELD_CATEGORY['K2002']
    'feature_data'
    >>> FIELD_CATEGORY['K10100']
    'extensions'
    """

    CATEGORIES: tuple[str, ...] = (
        'description',    # K0xxx
        'part_data',      # K1xxx
        'feature_data',   # K2xxx
        'ppap_data',      # K3xxx
        'catalog',        # K4xxx
        'group',          # K5xxx
        'other',          # K6xxx
        'other',          # K7xxx
        'control_chart',  # K8xxx
        'other',          # K9xxx
        'extensions',     # K10xxx and above
    )
    """Ordered tuple of category names indexed by the K-Field thousands
    group: ``('description', 'part_data', 'feature_data', …)``."""

    def __getitem__(self, key: str) -> str:
        """Return the category string for a K-Field key.

        Parameters
        ----------
        key : str
            K-Field key string (e.g. ``'K2002'``, ``'K10100'``).

        Returns
        -------
        str
            Category name. Returns the last defined category
            (``'extensions'``) for any thousands group beyond the
            defined range.
        """
        if not key.startswith('K') or not key[1:].isdigit():
            raise ValueError(
                f'Invalid K-Field key: {key}. '
                f'Must start with "K" followed by digits.')
        n = int(key[1:]) // 1000
        return self.CATEGORIES[min(n, len(self.CATEGORIES) - 1)]


FIELD_CATEGORY = _FieldCategory()
"""Singleton :class:`_FieldCategory` instance.

Look up the category of any K-Field key::

    FIELD_CATEGORY['K0100']  # 'description'
    FIELD_CATEGORY['K1001']  # 'part_data'
    FIELD_CATEGORY['K2002']  # 'feature_data'
"""