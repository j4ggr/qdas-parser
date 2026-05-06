"""Pure Q-DAS data model: :class:`KField` and :class:`Feature`.

These classes have no I/O and no side-effects, making them ideal
candidates for a future Cython extension (``_fast.pyx``).
"""

import re

from typing import List
from typing import Literal
from typing import Tuple

from ._config import QDAS_CONFIG
from ._constants import QDAS


class KField:
    """Represented object of a key number and field content pair.

    Parameters
    ----------
    dfd_line : str
        Single line from a QDAS description file (``.dfd`` file).
    """

    __slots__ = ('line', 'type', 'key', 'value', 'feature_number')

    line: str
    """A single line from a ``*.dfd`` file."""
    type: str
    """Field type. Literal['other', 'required', 'defined', 'supported', 'catalog']"""
    key: str
    """Parsed K-Field number e.g. ``'K0100'``."""
    value: str
    """Parsed K-Field value."""
    feature_number: int
    """Ordinal number of the current feature."""

    def __init__(self, dfd_line: str) -> None:
        self.line = dfd_line
        self.key, n, self.value = QDAS.RE_HEADER.match(self.line).groups()
        self.feature_number = int(n) if n else 0
        self.type = self._get_type_()

    @property
    def category(self) -> str:
        """K-Field category looked up from the configuration.

        Extracts the thousands-digit group from the K-Field key
        (e.g. ``'1'`` from ``'K1001'``) and returns the corresponding
        category string defined in ``qdas.toml >> fields >> category``.
        """
        field_range = self.key[1:-3]
        return QDAS_CONFIG['fields']['category'][field_range]

    def decode(self) -> Tuple[str, str]:
        """Decode this K-Field into a human-readable name-value pair.

        Uses the field definitions from ``qdas.toml`` to map the raw
        K-Field key to a descriptive name and, for ``'defined'`` field
        types, to translate the raw value to its label as well. Unknown
        fields (type ``'other'``) are returned as-is.

        Returns
        -------
        name : str
            Human-readable field name. Falls back to the raw K-Field key
            when the field is not described in the configuration.
        value : str
            Translated field value for ``'defined'`` types; raw value
            for all other types.
        """
        name: str = self.key
        value: str = self.value

        if self.type != 'other':
            try:
                kfield = QDAS_CONFIG['fields'][self.type][self.key]

                if self.type == 'required':
                    name = kfield
                    value = self.value

                elif self.type == 'defined':
                    name = kfield['name']
                    value = kfield['values'][self.value]

                elif self.type in ['supported', 'catalog']:
                    name = kfield['name']
                    value = self.value

            except KeyError:
                value = self.value

        return name, value

    def _get_type_(
            self
    ) -> Literal['other', 'required', 'defined', 'supported', 'catalog']:
        """Determine the field type from the configuration.

        Iterates over field sections in ``qdas.toml >> fields``, skipping
        ``'regex_pattern'`` and ``'category'``, and returns the name of the
        first section containing the current key. Defaults to ``'other'``.
        """
        field_type = 'other'
        for _type, kfields in QDAS_CONFIG['fields'].items():
            if _type in ['regex_pattern', 'category']:
                continue
            if self.key in kfields.keys():
                field_type = _type
                break
        return field_type

    def __str__(self) -> str:
        return (
            f'{self.line}:\n'
            f'KFeld: {self.key},\tTyp: {self.type},\tWert: {self.value}')

    def __eq__(self, key: object) -> bool:
        """Compare by K-Field key string (e.g. ``'K0100'``)."""
        return self.key == key

    def __bool__(self) -> bool:
        """``True`` when this K-Field belongs to a feature section."""
        return bool(self.feature_number)

    def __int__(self) -> int:
        """Numeric part of the K-Field key (e.g. ``100`` for ``'K0100'``)."""
        return int(self.key[1:])


class Feature(dict):
    """A feature including its measurements and ordered extensions.

    The possible extensions are defined in ``qdas.toml``. The number of
    extension columns depends on what is found in the value file.

    Parameters
    ----------
    number : int
        Feature number matching the ordinal position in the value file.
    """

    __slots__ = ('id', 'number', '_label', 'unit', 'columns')

    id: str
    """Column name of ``'Chargenummer'`` used as data identity."""
    number: int
    """Ordinal number to associate with the position in the value file."""
    _label: str
    """Feature label ``'Merkmalname'``."""
    unit: str
    """Unit of measurement values."""
    columns: List[str]
    """Column names including any extension columns."""

    def __init__(self, number: int) -> None:
        self._label = ''
        self.id = ''
        self.unit = ''
        self.columns = []
        self.number = number

    @property
    def label(self) -> str:
        """Feature label used as the primary column name.

        Spaces are normalised to underscores; double underscores are
        collapsed. Setting the label resets :attr:`columns` to a
        single-element list containing the new label.
        """
        return self._label

    @label.setter
    def label(self, label: str) -> None:
        self._label = self._spaces_to_underscores_(label)
        self.columns = [self._label]

    def extend(self, amount: int) -> None:
        """Extend the column list with additional extension columns.

        The first slot (the base value) is already in :attr:`columns`
        and is skipped. When more than three extensions are present the
        fourth column is stored as the data identity (:attr:`id`).

        Parameters
        ----------
        amount : int
            Total number of extensions including the base value column.
        """
        if amount > 1:
            extensions = list(QDAS_CONFIG['extensions']['order'].values())
            columns = [f'{self.label}_{e}' for e in extensions[1:amount]]
            if len(columns) > 3:
                self.id = columns[3]
            self.columns += columns

    @staticmethod
    def _spaces_to_underscores_(label: str) -> str:
        """Replace spaces with underscores and collapse double underscores."""
        return re.sub('__', '_', re.sub(' ', '_', label))

    def __eq__(self, num: object) -> bool:
        """Compare by ordinal feature number."""
        return self.number == num

    def add(self, kfield: KField) -> None:
        """Add a K-Field to this feature.

        Certain keys additionally update dedicated attributes:

        - ``K2002`` sets :attr:`label` and resets :attr:`columns`.
        - ``K2142`` sets :attr:`unit`.
        - ``K9004`` appends the value to the label for process disambiguation.

        Parameters
        ----------
        kfield : KField
            A K-Field parsed from a ``.dfd`` file line.
        """
        if kfield == 'K2002':
            self.label = kfield.value
        elif kfield == 'K2142':
            self.unit = kfield.value
        elif kfield == 'K9004':
            self.label = f'{self.label}_{kfield.value}'
        k, v = kfield.decode()
        self[k] = v
