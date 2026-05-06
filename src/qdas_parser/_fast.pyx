# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
"""Cython-compiled hot paths for the qdas_parser package.

Provides the same public interface as ``_fast.py`` so that ``_parser.py``
can import either transparently. When this extension is built and installed
the ``.pyd`` / ``.so`` takes precedence over the pure-Python fallback.

Build (in-place for development)::

    python setup.py build_ext --inplace

"""

from itertools import chain
from pathlib import Path

from qdas_parser._constants import QDAS as _QDAS

cdef object _RE_CLEAN = _QDAS.RE_CLEAN_LINE


def rows_fast(
        vfile,
        str sep_f,
        str sep_e,
):
    """Yield measurement rows from a QDAS value file.

    Parameters
    ----------
    vfile : Path | str
        Path to the ``.dfx`` or ``.dfb`` value file.
    sep_f : str
        Feature separator character.
    sep_e : str
        Extension separator character.

    Yields
    ------
    list[list[str]]
        Nested list where ``row[i]`` is the value + extensions for
        feature ``i + 1``.
    """
    cdef str line
    cdef list row

    with open(vfile, 'r') as fh:
        for line in fh:
            if not _RE_CLEAN.match(line):
                row = [fs.split(sep_e) for fs in line[:-1].split(sep_f)]
                yield row


def flatten_fast(int n_ids, list nested_row):
    """Flatten a nested measurement row and prepend index placeholders.

    Parameters
    ----------
    n_ids : int
        Number of index-column placeholder slots to prepend.
    nested_row : list[list]
        Nested row as yielded by :func:`rows_fast`.

    Returns
    -------
    list
        Flat list: ``n_ids`` empty strings + all measurement values.
    """
    return [''] * n_ids + list(chain.from_iterable(nested_row))
