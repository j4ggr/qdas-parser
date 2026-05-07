"""Pure-Python fallback implementations of the two parsing bottlenecks.

These functions are imported by :mod:`._parser` unconditionally. When a
compiled Cython extension (``_fast.pyx``) is built and installed, the
extension's symbols shadow these at the call sites in ``_parser.py``.

To add a Cython version:

1. Create ``src/qdas_parser/_fast.pyx`` with identical signatures.
2. Add a ``build`` hook to ``pyproject.toml`` that compiles the ``.pyx``
   file (e.g. via ``cython`` + ``setuptools`` or ``meson-python``).
3. The ``try/except ImportError`` guard in ``_parser.py`` will prefer the
   compiled extension automatically once it is on the path.

Bottleneck hot paths
--------------------
* ``rows_fast`` — called for every measurement line; two ``str.split``
  calls per line dominate the file-read loop.
* ``flatten_fast`` — list-of-lists flattening; called once per row
  after ``rows_fast`` yields it.
"""

from __future__ import annotations

from typing import Any
from typing import Generator
from typing import List
from pathlib import Path
from itertools import chain, repeat

from ._constants import QDAS

_RE_CLEAN = QDAS.RE_CLEAN_LINE


def rows_fast(
        vfile: Path,
        sep_f: str,
        sep_e: str,
        ) -> Generator[List[List[str]], Any, None]:
    """Yield measurement rows from a QDAS value file.

    This function is a generator that lazily yields one measurement row 
    at a time. Each row is represented as a nested list of strings, 
    where the outer list corresponds to features and the inner lists
    contain the value and extension data for each feature. The caller 
    can then flatten this structure as needed (e.g. via 
    :func:`flatten_fast`).

    Parameters
    ----------
    vfile : Path
        Path to the ``.dfx`` or ``.dfb`` value file.
    sep_f : str
        Feature separator character (``SEP_F``).
    sep_e : str
        Extension separator character (``SEP_E``).

    Yields
    ------
    List[List[str]]
        Nested list where ``row[i]`` contains the value and extension
        data for feature ``i + 1``.

    Notes
    -----
    This function is optimized for speed by minimizing intermediate
    data structures and using efficient string splitting. The caller is
    responsible for any necessary cleanup (e.g. stripping newlines) and
    for handling the index columns separately, as this function focuses
    solely on parsing the measurement data. The index columns are 
    expected to be handled by the caller, as they are not included in
    the yielded rows. The caller can prepend index placeholders as 
    needed (e.g. via :func:`flatten_fast`).

    K-Field lines embedded in the value file are ignored by this 
    function, as they are not part of the measurement data and should be 
    handled separately by the caller.
    """
    with open(vfile, 'r') as fh:
        for line in fh:
            if not _RE_CLEAN.match(line):
                yield [fs.split(sep_e) for fs in line[:-1].split(sep_f)]


def flatten_fast(n_ids: int, nested_row: List[List[Any]]) -> List[Any]:
    """Flatten a nested measurement row and prepend index placeholders.

    Parameters
    ----------
    n_ids : int
        Number of index-column placeholder slots to prepend.
    nested_row : List[List[Any]]
        Nested row as yielded by :func:`rows_fast`.

    Returns
    -------
    List[Any]
        Flat list starting with *n_ids* empty strings followed by all
        measurement values in feature order.

    Examples
    --------
    Two features, three index columns, one extension on feature 2:

    >>> flatten_fast(3, [['1.23'], ['4.56', 'batch-01']])
    ['', '', '', '1.23', '4.56', 'batch-01']
    """
    return list(chain(repeat('', n_ids), chain.from_iterable(nested_row)))
