"""qdas_parser — Q-DAS ASCII Transfer Format parser.

Public API
----------
:class:`QDASFileParser`
    Main entry point. Parse a ``.dfd`` + ``.dfx``/``.dfb`` file pair
    into pandas DataFrames.

:class:`KField`
    Low-level K-Field model. Useful for custom description-file
    processing.

:class:`Feature`
    Feature model including measurement columns and extension metadata.

:class:`AssemblyLineModule`
    Assembly-line module abstraction with optional test-cell detection.

:class:`ProductionOrder`
    Thin ``str`` subclass representing a production order number.

:func:`format_order`
    Normalise any order value (``int`` or ``str``) to a 12-digit
    zero-padded string.  Useful when reading order numbers from raw
    data files that may be inconsistently formatted.

:data:`QDAS`
    Package-level constants (``QDAS.SEP_F``, ``QDAS.SEP_E``,
    ``QDAS.RE_HEADER``, ``QDAS.RE_CLEAN_LINE``,
    ``QDAS.PART_ID``, ``QDAS.ORDER``).

:data:`FIELD_CATEGORY`
    Singleton :class:`_FieldCategory` instance. Maps any K-Field key
    string to its category (e.g. ``FIELD_CATEGORY['K2002']`` →
    ``'feature_data'``).
"""

from ._constants import QDAS
from ._constants import FIELD_CATEGORY
from ._models import Feature
from ._models import KField
from ._models import ProductionOrder
from ._models import format_order
from ._module import AssemblyLineModule
from ._parser import QDASFileParser

__all__ = [
    'QDAS',
    'FIELD_CATEGORY',
    'KField',
    'Feature',
    'AssemblyLineModule',
    'ProductionOrder',
    'format_order',
    'QDASFileParser',
]
