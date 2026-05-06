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

:data:`QDAS`
    Package-level constants (``QDAS.SEP_F``, ``QDAS.SEP_E``,
    ``QDAS.RE_HEADER``, ``QDAS.RE_CLEAN_LINE``, ``QDAS.INDEX_COLUMNS``,
    ``QDAS.PART_ID``, ``QDAS.ORDER``).
"""

from ._constants import QDAS
from ._models import Feature
from ._models import KField
from ._module import AssemblyLineModule
from ._parser import ProductionOrder
from ._parser import QDASFileParser

__all__ = [
    'QDAS',
    'KField',
    'Feature',
    'AssemblyLineModule',
    'ProductionOrder',
    'QDASFileParser',
]
