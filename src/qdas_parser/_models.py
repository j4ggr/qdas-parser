"""Pure Q-DAS data model: :class:`KField`, :class:`Feature`, and :class:`ProductionOrder`.

These classes have no I/O and no side-effects, making them ideal
candidates for a future Cython extension (``_fast.pyx``).
"""
import re

from typing import List
from typing import Dict
from typing import Tuple
from typing import Literal
from typing import KeysView
from typing import ItemsView
from typing import ValuesView

from ._constants import FIELD_CATEGORY
from ._constants import QDAS
from ._fields import CATALOG
from ._fields import DEFINED
from ._fields import REQUIRED
from ._fields import SUPPORTED


__all__ = [
    'field_type',
    'format_order',
    'KField',
    'Feature',
    'ProductionOrder',
]


def field_type(
        kfield_key: str
        ) -> Literal['other', 'required', 'defined', 'supported', 'catalog']:
    """Determine the field type from the configuration.

    Iterates over field sections in ``qdas.toml >> fields``, skipping
    ``'regex_pattern'`` and ``'category'`, and returns the name of the
    first section containing the current key. Defaults to ``'other'``.

    Parameters
    ----------
    kfield_key : str
        K-Field key string (e.g. ``'K0100'``).

    Returns
    -------
    field_type : Literal['other', 'required', 'defined', 'supported', 'catalog']
        The field type as defined in the configuration.
    """
    if kfield_key in REQUIRED:
        return 'required'
    if kfield_key in DEFINED:
        return 'defined'
    if kfield_key in SUPPORTED:
        return 'supported'
    if kfield_key in CATALOG:
        return 'catalog'
    return 'other'


def format_order(order: str | int) -> str:
    """Return *order* as a 12-digit zero-padded string, or ``''``.

    Parameters
    ----------
    order : str or int
        Production order number to normalise.  Accepts integers, numeric
        strings (with optional whitespace), or empty/``None``-like values.

    Returns
    -------
    str
        12-digit zero-padded string, e.g. ``'000001234567'``, or ``''``
        when *order* is empty, ``None``, or non-numeric.

    Examples
    --------
    >>> format_order('1234567')
    '000001234567'
    >>> format_order(1234567)
    '000001234567'
    >>> format_order('')
    ''
    """
    if not order and order != 0:
        return ''
    if isinstance(order, str):
        order = order.strip()
        if not order:
            return ''
    try:
        return f'{int(order):012}'
    except (ValueError, TypeError):
        return ''


class KField:
    """A K-Field key/value pair parsed from a Q-DAS description file.

    Prefer :meth:`from_line` to construct from a raw ``.dfd`` line.
    Direct construction is useful when key, value, and feature number
    are already known.

    Parameters
    ----------
    key : str
        K-Field key string (e.g. ``'K2002'``).
    value : str
        Raw field value string.
    feature_number : int or None
        Ordinal feature number (1-based) this K-Field belongs to,
        or ``0`` for header fields.

    Examples
    --------
    Parse from a raw description-file line:

    >>> kf = KField.from_line('K2002/1 Merkmalname\\n')
    >>> kf.key, kf.value, kf.feature_number
    ('K2002', 'Merkmalname', 1)

    Construct directly and check feature membership:

    >>> kf = KField('K2002', 'Durchmesser', 1)
    >>> bool(kf), kf.feature_index
    (True, 0)
    """

    __slots__ = (
        'key',
        'value',
        'feature_number',
        '_field_type',
        '_category',)

    key: str
    """Parsed K-Field number e.g. ``'K0100'``."""

    value: str
    """Parsed K-Field value."""

    feature_number: int | None
    """Ordinal number of the current feature."""

    _category: str
    """K-Field category looked up from the configuration."""

    @property
    def category(self) -> str:
        """K-Field category looked up from the configuration (read-only).

        Extracts the thousands-digit group from the K-Field key
        (e.g. ``'1'`` from ``'K1001'``) and returns the corresponding
        category string defined in ``qdas.toml >> fields >> category``.
        """
        if not self._category:
            self._category = FIELD_CATEGORY[self.key]
        return self._category

    _field_type: Literal['other', 'required', 'defined', 'supported', 'catalog', '']
    """Field type looked up from the configuration. Cached after first 
    lookup."""

    @property
    def field_type(
            self
            ) -> Literal['other', 'required', 'defined', 'supported', 'catalog']:
        """Field type looked up from the configuration (read-only).
        
        Uses :func:`field_type` to determine the field type based on the
        K-Field key and caches the result for subsequent accesses.
        """
        if not self._field_type:
            self._field_type = field_type(self.key)
        return self._field_type
    
    @property
    def feature_index(self) -> int:
        """Zero-based index of the feature this K-Field belongs to
        (read-only).

        Returns ``-1`` when the K-Field does not belong to any feature
        section (header field or ``feature_number == 0``).

        Examples
        --------
        >>> KField('K2002', 'Name', 1).feature_index
        0
        >>> KField('K2002', 'Name', 3).feature_index
        2
        >>> KField('K1001', '123', 0).feature_index
        -1
        """
        return self.feature_number - 1 if self.feature_number else -1

    def __init__(
            self,
            key: str,
            value: str,
            feature_number: int | None
            ) -> None:
        self.key = key
        self.value = value
        self.feature_number = feature_number
        self._field_type = ''
        self._category = ''

    @staticmethod
    def from_line(line: str) -> 'KField':
        """Parse a K-Field from a line in a Q-DAS description file.

        Parameters
        ----------
        line : str
            Single line from a Q-DAS description file (``.dfd`` file).

        Returns
        -------
        kfield : KField
            Parsed K-Field object.

        Raises
        ------
        ValueError
            When the line does not match the expected K-Field pattern.

        Examples
        --------
        Header field (no feature number):

        >>> kf = KField.from_line('K1001 1234567\\n')
        >>> kf.key, kf.value, kf.feature_number
        ('K1001', '1234567', 0)

        Feature-specific field:

        >>> kf = KField.from_line('K2002/1 Merkmalname\\n')
        >>> kf.key, kf.value, kf.feature_number
        ('K2002', 'Merkmalname', 1)
        """
        match = QDAS.RE_HEADER.match(line)
        if match:
            key, number, value = match.groups()
            return KField(key, value, int(number) if number else 0)
        else:
            raise ValueError(f'Line does not match K-Field pattern: {line}')

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

        Examples
        --------
        A ``'required'`` field — raw key mapped to a descriptive name:

        >>> KField('K1001', '1234567', 0).decode()
        ('Teilenummer', '1234567')

        A ``'defined'`` field — both name and value are translated:

        >>> KField('K2004', '0', 1).decode()
        ('Merkmalart', 'variabel')
        """
        name = self.key
        value = self.value

        match self.field_type:
            case 'required':
                name = REQUIRED[self.key]
            case 'defined':
                field = DEFINED[self.key]
                name = field.name
                value = field.values.get(int(self.value), self.value)
            case 'supported':
                name = SUPPORTED[self.key]
            case 'catalog':
                name = CATALOG[self.key]
            case _:
                pass

        return name, value

    def __str__(self) -> str:
        return (
            f'{self.key}: {self.value} '
            f'(type {self.field_type!r}, feature {self.feature_number})')

    def __eq__(self, key: object) -> bool:
        """Compare by K-Field key string (e.g. ``'K0100'``)."""
        return self.key == key

    def __bool__(self) -> bool:
        """``True`` when this K-Field belongs to a feature section."""
        return isinstance(self.feature_number, int) and self.feature_number > 0

    def __int__(self) -> int:
        """Numeric part of the K-Field key (e.g. ``100`` for ``'K0100'``)."""
        return int(self.key[1:])


class Feature:
    """Represented object of a Q-DAS feature with associated K-Fields.

    This class represents a single feature as defined in a Q-DAS 
    description file (``.dfd`` file) and holds the associated K-Fields 
    as well as metadata such as the feature label, unit, and column 
    names for the value file.

    Parameters
    ----------
    number : int
        Ordinal feature number to associate with the position in the 
        value file.

    Notes
    -----
    - This class behaves like a dictionary for the additional data
      fields, allowing easy access and manipulation of these fields.
      Special handling is implemented for certain K-Field keys in the 
      `add` method to update the label and unit attributes accordingly.
      This design allows for a flexible and extensible representation of 
      a Q-DAS feature.
    - The ``identity`` attribute is used to store the column name of the
      ``'Chargennummer'`` when more than three extensions are present,
      as specified in the configuration. This allows for easy access to
      the identity column in the value file.
    - The ``columns`` attribute holds the list of column names for this
      feature, including any extension columns. The first column is the
      base value column, and additional columns are added based on the
      extensions specified in the configuration.
    """

    __slots__ = (
        'identity',
        'unit',
        'columns',
        '_number',
        '_label',
        '_data')

    identity: str
    """Column name of ``'Chargenummer'`` used as data identity."""
    
    unit: str
    """Unit of measurement values."""

    columns: List[str]
    """Column names including any extension columns."""

    _number: int
    """Ordinal number to associate with the position in the value file."""

    @property
    def number(self) -> int:
        """Ordinal feature number to associate with the position in the
        value file (read-only)."""
        return self._number

    _label: str
    """Feature label ``'Merkmalname'``."""
    
    @property
    def label(self) -> str:
        """Get feature label ``'Merkmalname'``.

        The getter returns the current label without modification.

        The setter for this property also updates the column list with 
        the new label. The label is cleaned by replacing spaces with 
        underscores and collapsing multiple underscores to a single one.
        """
        return self._label

    @label.setter
    def label(self, label: str) -> None:
        self._label = re.sub('__', '_', re.sub(' ', '_', label))
        self.columns = [self._label]

    _data: Dict[str, str] | None
    """Additional data fields decoded from K-Fields with keys other than
    K2002 (label) and K2142 (unit)."""

    @property
    def data(self) -> Dict[str, str]:
        """Additional data fields decoded from K-Fields with keys other 
        than K2002 (label) and K2142 (unit) (read-only).
        
        Returns an empty dictionary when no additional data fields have
        been added."""
        if self._data is None:
            self._data = {}
        return self._data

    def __init__(self, number: int) -> None:
        self._label = ''
        self.identity = ''
        self.unit = ''
        self.columns = []
        self._number = number
        self._data: Dict[str, str] | None = None

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
            extensions = list(QDAS.EXTENSIONS)
            columns = [f'{self.label}_{e}' for e in extensions[1:amount]]
            if len(columns) > 3:
                self.identity = columns[3]
            self.columns += columns

    def keys(self) -> KeysView[str]:
        """Return the keys of the additional data fields."""
        return self.data.keys()
    
    def values(self) -> ValuesView[str]:
        """Return the values of the additional data fields."""
        return self.data.values()
    
    def items(self) -> ItemsView[str, str]:
        """Return the items of the additional data fields."""
        return self.data.items()
    
    def get(self, key: str, default: str | None = None) -> str | None:
        """Get the value of a data field by key, returning default if 
        not found."""
        return self.data.get(key, default)

    def add(self, kfield: KField) -> None:
        """Add a K-Field to this feature.

        Certain keys additionally update dedicated attributes:

        - ``K2002`` sets :attr:`label` and resets :attr:`columns`.
        - ``K2142`` sets :attr:`unit`.
        - ``K9004`` appends the value to the label for process disambiguation.

        All K-Fields are also stored in :attr:`data` via :meth:`KField.decode`.

        Parameters
        ----------
        kfield : KField
            A K-Field parsed from a ``.dfd`` file line.

        Examples
        --------
        >>> f = Feature(1)
        >>> f.add(KField('K2002', 'Durchmesser', 1))
        >>> f.add(KField('K2142', 'mm', 1))
        >>> f.label, f.unit, f.columns
        ('Durchmesser', 'mm', ['Durchmesser'])
        """
        match kfield.key:
            case 'K2002':
                self.label = kfield.value
            case 'K2142':
                self.unit = kfield.value
            case 'K9004':
                self.label = f'{self.label}_{kfield.value}'
                
        k, v = kfield.decode()
        self[k] = v

    def __contains__(self, item: str) -> bool:
        """Check if a K-Field key is present in the feature's data."""
        return item in self.data
    
    def __getitem__(self, key: str) -> str:
        """Get the value of a K-Field key from the feature's data."""
        return self.data[key]
    
    def __setitem__(self, key: str, value: str) -> None:
        """Set the value of a K-Field key in the feature's data."""
        self.data[key] = value

    def __eq__(self, num: object) -> bool:
        """Compare by ordinal feature number."""
        return self.number == num

    def __str__(self) -> str:
        return (
            f'Feature {self.number}: {self.label} ({self.unit}), '
            f'columns: {self.columns}')


class ProductionOrder:
    """Object to handle production orders (FA).

    It ensures the correct format so that comparisons can be made.
    The order is either a 12-digit number, padded on the left with ``0``,
    or an empty string.

    Use :func:`format_order` when you only need the normalised string
    without constructing a full object (e.g. ``df['order'].map(format_order)``).

    Parameters
    ----------
    order : int or str, optional
        Production order number, by default ``''``.

    Examples
    --------
    >>> po = ProductionOrder('1234567')
    >>> str(po)
    '000001234567'
    >>> po == 1234567        # comparison normalises both sides
    True
    >>> bool(ProductionOrder(''))
    False
    >>> int(po)
    1234567
    >>> repr(ProductionOrder(''))
    'order:\\tall'
    """

    __slots__ = ('_order',)

    _order: str
    """Internal storage of the production order number as a 12-digit 
    string or an empty string."""

    def __init__(self, order: int | str = '') -> None:
        self._order = format_order(order)

    @property
    def order(self) -> str:
        """Production order number as a 12-digit string (read-only).

        Gets the production order number in a consistent format,
        ensuring that comparisons can be made.
        """
        return self._order

    @order.setter
    def order(self, order: str | int) -> None:
        self._order = format_order(order)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ProductionOrder):
            return self._order == other._order

        elif isinstance(other, (str, int)):
            return self._order == format_order(other)
        
        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self._order)

    def __str__(self) -> str:
        return self._order

    def __repr__(self) -> str:
        return f'order:\t{self._order or "all"}'

    def __int__(self) -> int:
        return int(self._order) if self._order else 0

    def __hash__(self) -> int:
        return hash(self._order)

