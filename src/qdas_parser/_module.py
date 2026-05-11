"""Assembly-line module abstraction: :class:`AssemblyLineModule`.

Decoupled from any application config — all external knowledge
(test-cell map, shortcut string) is injected via constructor parameters.
"""

from typing import Dict
from typing import List
from typing import Literal

from ._config import logger


class AssemblyLineModule:
    """Handle module name and test-cell membership for one assembly-line slot.

    Parameters
    ----------
    name : str
        Raw module folder name as found in the file path (e.g. ``'tc1_bd'``).
    product : Product
        Upper-cased product identifier used to look up test-cell modules
    line : str
        Assembly-line name
    kind : Literal['bd', 'pc']
        Data kind: batch data (``'bd'``) or process data (``'pc'``).
    tc_modules : TCModules, optional
        Mapping of ``product → line → [module_names]`` used to detect
        test-cell slots. Defaults to an empty dict (no test cells).
    tc_shortcut : str, optional
        Short prefix used in human-readable test-cell descriptions
        (e.g. ``'TC'``). Defaults to ``'TC'``.

    Examples
    --------
    Regular module (no test-cell map)::

        mod = AssemblyLineModule('m01_bd', 'ACT1', 'as1', 'bd')
        mod.name          # 'm01_bd'
        bool(mod)         # False — not a test cell
        mod.description   # 'm01_bd'

    Test-cell detection via *tc_modules*::

        tc_map = {'ACT1': {'as1': ['tc1_bd', 'tc2_bd', 'tc3_bd']}}
        mod = AssemblyLineModule('tc1_bd', 'ACT1', 'as1', 'bd',
                                 tc_modules=tc_map)
        bool(mod)         # True
        mod.tc_number     # 1
        mod.description   # 'TC1'
    """

    __slots__ = (
        'TC', 'is_test_cell', 'tc_number', 'product', 'line', '_name',
        '_tc_modules', 'kind')

    TC: str
    """Short prefix for test-cell descriptions (e.g. ``'TC'``)."""
    is_test_cell: bool
    """``True`` when this module is a test-cell slot."""
    tc_number: None | int
    """1-based test-cell index, or ``None`` for regular modules."""
    product: str
    """Upper-cased product identifier."""
    line: str
    """Assembly-line folder name."""
    _name: str
    kind: str
    _tc_modules: List[str]

    def __init__(
            self,
            name: str,
            product: str,
            line: str,
            kind: Literal['bd', 'pc'],
            tc_modules: Dict[str, Dict[str, List[str]]] | None = None,
            tc_shortcut: str = 'TC',
    ) -> None:
        self.TC = tc_shortcut
        self.is_test_cell = False
        self.tc_number = None
        self.product = product.upper()
        self.line = line
        self._name = ''
        self._tc_modules = []
        self.kind = kind
        self.tc_modules = tc_modules or {}
        self.name = name

    @property
    def name(self) -> str:
        """Normalised module name including the data-kind suffix."""
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name.split('_')[0] + f'_{self.kind}'
        if name in self.tc_modules:
            self.is_test_cell = True
            self.tc_number = self.tc_modules.index(name) + 1
        logger.debug('Name changed %s', self._name)

    @property
    def description(self) -> str:
        """Human-readable identifier: ``'TC1'`` for test cells, plain name otherwise."""
        return f'{self.TC}{self.tc_number}' if self else self.name

    @property
    def tc_modules(self) -> List[str]:
        """Ordered list of test-cell module folder names for this product/line."""
        return self._tc_modules

    @tc_modules.setter
    def tc_modules(self, tc_modules: Dict[str, Dict[str, List[str]]]) -> None:
        modules: List[str] = []
        try:
            modules = tc_modules[self.product][self.line]
        except KeyError:
            logger.debug(
                'No test cell configured for product=%r, line=%r',
                self.product, self.line)
        self._tc_modules = modules
        logger.debug('Test cell modules changed %s', modules)

    def __str__(self) -> str:
        return self.TC if self.is_test_cell else self.name

    def __bool__(self) -> bool:
        """``True`` when this module is a test cell."""
        return self.is_test_cell
