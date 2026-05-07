"""Core parser: :class:`ProductionOrder` and :class:`QDASFileParser`.

The two hot-path methods (:meth:`QDASFileParser.rows` and
:meth:`QDASFileParser._flatten_`) delegate to ``_fast`` if the compiled
Cython extension is available, otherwise fall back to the pure-Python
implementations in :mod:`._fast`.
"""

import re
import copy
import logging

import numpy as np
import pandas as pd
import dateutil.parser as dtp

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Generator
from pathlib import Path
from pandas.core.api import DataFrame

from ._constants import QDAS
from ._models import KField, Feature
from ._module import AssemblyLineModule

from ._fast import rows_fast as _rows_fast
from ._fast import flatten_fast as _flatten_fast

logger = logging.getLogger(__name__)


def ensure_path(filepath: str | Path) -> Path:
    """Return *filepath* as a :class:`~pathlib.Path`."""
    return filepath if isinstance(filepath, Path) else Path(filepath)


class ProductionOrder(str):
    """Production order identifier parsed from a QDAS description file.

    A thin :class:`str` subclass so that ``str(order)`` always works and
    the value can be used directly as a column value.
    """


class QDASFileParser:
    """Parser for QDAS Ascii Transferformat file pairs (``.dfd`` + ``.dfx``/``.dfb``).

    Parse a description file first, then a value file.

    Parameters
    ----------
    description_file : Path | str
        Path to the ``.dfd`` description file.
    product : Product
        Product identifier (e.g. ``'ACT1'``).
    tc_modules : TCModules, optional
        Test-cell module map injected into :class:`AssemblyLineModule`.
        Defaults to an empty dict (no test-cell detection).
    tc_shortcut : str, optional
        Prefix used in test-cell descriptions. Defaults to ``'TC'``.
    kind : str, optional
        Data kind: ``'bd'`` (batch) or ``'pc'`` (process). When omitted
        the second-to-last parent directory name is used as fallback.
    module_name : str, optional
        Module folder name (e.g. ``'m01'``). When omitted the immediate
        parent directory name is used as fallback.
    line : str, optional
        Assembly-line identifier (e.g. ``'as1'``). When omitted an empty
        string is used, disabling test-cell detection.

    Examples
    --------
    >>> from pathlib import Path
    >>> qdas = QDASFileParser(Path("path/to/2603160002.dfd"), 'ACT1')
    >>> qdas.parse_description()
    >>> qdas.parse_values()
    >>> df = qdas.dataframe()
    >>> dfm = qdas.metadata()
    """

    __slots__ = (
        'vfile',
        'dfile',
        'order',
        'module',
        'stem',
        'data',
        'head_data',
        'head_columns',
        'features',
        'index_columns',
        'product',
        '_description_parsed',
        '_fn_date',
        '_mtime',
        '_mtime_lstat',
        '_kind')

    dfile: Path
    """Description file path (``.dfd``)."""

    vfile: Path
    """Value file path (``.dfx`` for process data, ``.dfb`` for 
    batch data)."""

    order: ProductionOrder
    """Production order identifier parsed from the description file."""

    module: AssemblyLineModule
    """Assembly-line module inferred from the description file path and
    test-cell module map."""

    stem: str
    """Six-character date prefix of the description file stem 
    (``YYMMDD``)."""

    data: List[List[Any]]
    """Parsed measurement data as a list of rows, where each row is a
    list of values corresponding to the columns yielded by 
    :meth:`gen_columns`."""

    head_data: Dict[str, str]
    """Decoded header K-Field pairs from the description file, excluding
    K0100 and feature-specific K-Fields."""

    head_columns: List[str]
    """Column names corresponding to the header K-Fields in 
    :attr:`head_data`."""

    features: List[Feature]
    """List of features parsed from the description file."""

    index_columns: List[str]
    """Column names to use as DataFrame index (e.g. 
    ``'Chargennummer'``)."""

    product: str
    """Product identifier (e.g. ``'ACT1'``) passed at initialization."""

    _description_parsed: bool
    """Flag indicating whether the description file has been parsed yet."""

    @property
    def description_parsed(self) -> bool:
        """Flag indicating whether the description file has been parsed 
        yet (read-only).
        
        Parsing is required before parsing values or building 
        DataFrames."""
        return self._description_parsed

    _fn_date: str
    """Six-character date prefix of the description file stem 
    (``YYMMDD``)."""

    @property
    def fn_date(self) -> str:
        """Six-character date prefix of the description file stem 
        in ``YYMMDD`` format (read-only)."""
        return self._fn_date

    _mtime: float | None
    """POSIX timestamp derived from the description file's date prefix, 
    used for sorting and comparison purposes."""

    @property
    def mtime(self) -> float:
        """POSIX timestamp derived from the filename date prefix."""
        if self._mtime is None:
            self._mtime = dtp.parse(self.fn_date, yearfirst=True).timestamp()
        return self._mtime
    
    _mtime_lstat: float | None
    """POSIX timestamp of the description file's last modification time,
    derived from the filesystem. Used for comparison with :attr:`mtime`
    to determine if the file has been modified since it was last parsed."""

    @property
    def mtime_lstat(self) -> float:
        """POSIX timestamp of the description file's last modification time,
        derived from the filesystem (read-only).
        
        Used for comparison with :attr:`mtime` to determine if the file 
        has been modified since it was last parsed."""
        if self._mtime_lstat is None:
            self._mtime_lstat = self.dfile.lstat().st_mtime
        return self._mtime_lstat
    
    _kind: str | None
    """Data kind: ``'bd'`` for batch data, ``'pc'`` for process data. 
    When None, the kind is inferred from the file path."""

    @property
    def kind(self) -> str:
        """Data kind: ``'bd'`` for batch data, ``'pc'`` for process data."""
        if self._kind is not None:
            return self._kind
        return self.dfile.parents[1].name

    @staticmethod
    def ensure_path(filepath: str | Path) -> Path:
        """Return *filepath* as a :class:`~pathlib.Path`."""
        return filepath if isinstance(filepath, Path) else Path(filepath)

    def __init__(
            self,
            description_file: Path | str,
            product: str,
            tc_modules: Dict[str, Dict[str, List[str]]] | None = None,
            tc_shortcut: str = 'TC',
            kind: str | None = None,
            module_name: str | None = None,
            line: str | None = None,
        ) -> None:
        self.data = []
        self.head_data = {}
        self.head_columns = []
        self.features = []
        self.index_columns = QDAS.INDEX_COLUMNS
        self.product = product
        self.dfile = ensure_path(description_file)
        self._kind = kind
        self.vfile = self._get_vfile_()
        self.module = self._get_module_(tc_modules or {}, tc_shortcut, module_name, line)
        self.order = ProductionOrder('')
        self._mtime = None
        self._mtime_lstat = None
        self._description_parsed = False
        self._fn_date = self.dfile.stem[:6]

    @property
    def state(self) -> Dict[str, Any]:
        """Snapshot of parser identity (module name and order)."""
        return copy.deepcopy({
            'module_name': f'{self.module}',
            'order': f'{self.order}'})

    def gen_columns(self) -> Generator[str, Any, None]:
        """Yield all column names in data-layout order.

        Index columns → head-data columns → (cleaned) feature columns.
        """
        for idx_column in self.index_columns:
            yield idx_column
        for head_column in self.head_columns:
            yield head_column
        for feature in self.features:
            for column in feature.columns:
                yield self._clean_colname_(column)

    def kfields(self) -> Generator[KField, Any, None]:
        """Yield a :class:`KField` for every line in the description file."""
        try:
            with open(self.dfile, 'r') as description_data:
                for line in description_data:
                    yield KField.from_line(line)

        except FileNotFoundError as e:
            logger.error(f'Description file not found: {self.dfile}')
            raise e
        
        except ValueError as e:
            logger.error(f'Error parsing K-Field from line: {e}')
            raise e

    def rows(self) -> Generator[List[List[str]], Any, None]:
        """Yield measurement rows from the value file as nested lists.

        Delegates to the compiled ``_fast`` extension when available.
        """
        yield from _rows_fast(self.vfile, QDAS.SEP_F, QDAS.SEP_E)

    def parse_description(self) -> Tuple[Dict[str, str], List[Feature]]:
        """Parse the ``.dfd`` description file into header data and features.

        Returns
        -------
        head_data : Dict[str, str]
            Decoded header K-Field pairs.
        features : List[Feature]
            Feature objects sorted by feature number.
        """
        for kfield in self.kfields():
            if kfield == 'K0100':
                self.head_data = {}
                self.features = [Feature(i + 1) for i in range(int(kfield.value))]
            elif kfield:
                self.features[kfield.feature_index].add(kfield)
            else:
                self.head_data.update([kfield.decode()])
        self.order = ProductionOrder(self.head_data.get(QDAS.ORDER, ''))
        return self.head_data, self.features

    def parse_values(self) -> None:
        """Parse the value file into :attr:`data`.

        Consumes the first row to determine extension-column counts, then
        processes all remaining rows. :meth:`parse_description` must be
        called first.
        """
        rows = self.rows()
        row0 = next(rows)
        for feature, inner_array in zip(self.features, row0):
            feature.extend(len(inner_array))
        self.data = [self._flatten_(row0)] + [self._flatten_(r) for r in rows]

    def dataframe(self, add_head: bool = True) -> DataFrame:
        """Build a pandas MultiIndex DataFrame from parsed measurement data.

        Parameters
        ----------
        add_head : bool, optional
            Append header K-Field columns. Defaults to ``True``.

        Returns
        -------
        DataFrame
            MultiIndex DataFrame with ``('Modul', 'Merkmal')`` column levels.
        """
        columns = list(self.gen_columns())
        df = pd.DataFrame(self.data, columns=columns)
        df = self._index_data_(df)
        df = self._add_head_data_(df, skip=not add_head)
        df = self._remove_unusable_rows_(df)
        df = df[columns].set_index(self.index_columns)
        df = self._add_tc_number_(df)
        df = self._add_column_level_(df, len(self.head_columns))
        return df

    def metadata(self) -> DataFrame:
        """Build a pandas MultiIndex DataFrame of feature metadata.

        Returns
        -------
        DataFrame
            MultiIndex DataFrame with ``('Modul', 'Merkmal')`` column levels.
        """
        mdata = self._get_feature_metadata_()
        mdata = self._add_meta_index_columns_(mdata)
        mdata = mdata.set_index(self.index_columns[:2], append=True)
        mdata = mdata.reorder_levels([1, 2, 0], axis='index')
        mdata = self._add_column_level_(mdata, 0)
        return mdata

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _index_data_(self, df: DataFrame) -> DataFrame:
        for col in self.index_columns:
            if col == QDAS.ORDER:
                values = str(self.order)
            elif col == QDAS.PART_ID:
                id_column = self._clean_colname_(self.features[0].identity)
                values = df[id_column] if id_column in df.columns else ''
            else:
                values = self.head_data.get(col, np.nan)
            df[col] = values
        return df

    def _add_head_data_(self, df: DataFrame, skip: bool = False) -> DataFrame:
        if skip:
            return df
        self.head_columns = []
        for colname, value in self.head_data.items():
            if colname in self.index_columns:
                continue
            self.head_columns.append(colname)
            df[colname] = value
        return df

    def _get_feature_metadata_(self) -> DataFrame:
        mdata = pd.DataFrame()
        for f in self.features:
            index = pd.Series(list(f.keys()), name='Bezeichnung')
            fdata = pd.DataFrame(data={f.label: f.values()}, index=index)
            mdata = pd.concat([mdata, fdata], axis='columns')
        return mdata

    def _add_meta_index_columns_(self, df: DataFrame) -> DataFrame:
        for c in self.index_columns[:2]:
            df[c] = str(self.order) if c == QDAS.ORDER else self.head_data.get(c)
        return df

    def _clean_colname_(self, colname: str) -> str:
        pattern = self.module.name.upper() + '_'
        return re.sub(pattern, '', colname)

    def _add_column_level_(self, df: DataFrame, n_head: int) -> DataFrame:
        n_modules = len(df.columns) - n_head
        levels = [['Kopf'] * n_head + [f'{self.module}'] * n_modules, df.columns]
        names = ['Modul', 'Merkmal']
        mi_columns = pd.MultiIndex.from_arrays(levels, names=names)
        df.columns = mi_columns
        return df

    def _add_tc_number_(self, df: DataFrame) -> DataFrame:
        if not self.module:
            return df
        df['Prüfzelle'] = self.module.description
        return df

    def _remove_unusable_rows_(self, df: DataFrame) -> DataFrame:
        df = df.drop_duplicates(subset=self.index_columns, keep='last')
        df = df.dropna(axis=0, how='all')
        return df

    def _remove_unusable_cols_(self, df: DataFrame) -> DataFrame:
        return df.loc[:, (df.notna() & (df != '0')).any(axis=0)]

    def _get_vfile_(self) -> Path:
        """Determine the value file path based on the description file 
        path and data kind.
        
        Returns
        -------
        Path
            Value file path with the same stem as the description file 
            and a suffix determined by the data kind (``.dfx`` for
            process data, ``.dfb`` for batch data).
        """
        suffix = '.dfb' if self.kind == 'bd' else '.dfx'
        return self.dfile.with_suffix(suffix)

    def _get_module_(
            self,
            tc_modules: Dict[str, Dict[str, List[str]]],
            tc_shortcut: str,
            module_name: str | None,
            line: str | None,
            ) -> AssemblyLineModule:
        """Determine the assembly-line module based on the description 
        file path and other parameters.

        Parameters
        ----------
        tc_modules : Dict[str, Dict[str, List[str]]]
            Test-cell module map injected into :class:`AssemblyLineModule`.
        tc_shortcut : str
            Prefix used in test-cell descriptions.
        module_name : str | None
            Module folder name (e.g. ``'m01'``). When None, the
            immediate parent directory name is used as fallback.
        line : str | None
            Assembly-line identifier (e.g. ``'as1'``). When None, an 
            empty string is used as a placeholder.

        Returns
        -------
        AssemblyLineModule
            Assembly-line module inferred from the description file path 
            and test-cell module map.

        Notes
        -----
        The module name is determined in the following order of 
        precedence:
        1. Explicit `module_name` parameter.
        2. Immediate parent directory name of the description file.
        
        The line identifier is determined as follows:
        1. Explicit `line` parameter.
        2. If test-cell detection is enabled (i.e., `line` is not None), 
           an empty string is used as a placeholder.

        The module kind is determined as follows:
        1. Explicit `kind` parameter.
        2. Inferred from the second-to-last parent directory name of the 
        description file."""
        return AssemblyLineModule(
            name=module_name if module_name is not None else self.dfile.parent.name,
            product=self.product,
            line=line if line is not None else '',
            kind=self.kind,  # type: ignore[arg-type]
            tc_modules=tc_modules,
            tc_shortcut=tc_shortcut,)

    def _flatten_(self, nested_row: List[List[Any]]) -> List[Any]:
        """Flatten a nested measurement row, delegating to ``_fast`` 
        when available.
        
        Parameters
        ----------
        nested_row : List[List[Any]]
            Nested list of measurement values corresponding to the 
            current row, as yielded by :meth:`rows`.
            
        Returns
        -------
        List[Any]
            Flattened list of measurement values corresponding to the 
            current row, in the same order as the columns yielded by 
            :meth:`gen_columns`.
        """
        return _flatten_fast(len(self.index_columns), nested_row)
