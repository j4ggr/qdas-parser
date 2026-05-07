# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2026-05-07

Initial public release.

### Added

#### Core parser

- `QDASFileParser` — parse `.dfd` + `.dfx`/`.dfb` file pairs into pandas DataFrames
- `QDASFileParser.parse_description()` — decode header K-Fields and build `Feature` list
- `QDASFileParser.parse_values()` — read value file and flatten measurement rows
- `QDASFileParser.dataframe()` — return MultiIndex DataFrame `(module, feature)`
- `QDASFileParser.metadata()` — return MultiIndex DataFrame of feature metadata
- `QDASFileParser.gen_columns()` — yield ordered column names
- `QDASFileParser.kfields()` — yield `KField` objects from the description file
- `QDASFileParser.rows()` — yield nested measurement rows from the value file
- `QDASFileParser.kind`, `mtime`, `mtime_lstat`, `fn_date` — lazy read-only properties
- `QDASFileParser.ensure_path()` — static helper to coerce `str` to `Path`

#### Data models

- `KField` — explicit 3-argument constructor (`key`, `value`, `feature_number`)
- `KField.from_line()` — static factory; parses a raw `.dfd` line; raises `ValueError` on mismatch
- `KField.decode()` — translates raw key/value to human-readable name/value via `qdas.toml`
- `KField.field_type` — cached property (`'required'`, `'defined'`, `'supported'`, `'catalog'`, `'other'`)
- `KField.category` — cached property derived from the thousands-digit of the key
- `KField.feature_index` — zero-based feature index; `-1` for header fields
- `Feature` — pure `__slots__` class (not a `dict` subclass); lazy `_data` allocation
- `Feature.add()` — add a `KField`; special-cases `K2002` (label), `K2142` (unit), `K9004` (disambiguation)
- `Feature.extend()` — populate extension columns from `qdas.toml` extension order
- `Feature` dict-like interface — `__contains__`, `__getitem__`, `__setitem__`, `keys()`, `values()`, `items()`, `get()`
- `ProductionOrder` — value object; normalises any order input to a 12-digit zero-padded string
- `ProductionOrder.__eq__` — normalises both sides before comparison
- `format_order()` — module-level function; normalise `int | str` to a 12-digit string; suitable for `df.map()`

#### Module detection

- `AssemblyLineModule` — infer module name and test-cell membership from file path and injected map
- `AssemblyLineModule.description` — returns `'TC1'` style for test cells, plain name otherwise

#### Utilities

- `QDAS` — frozen dataclass of package-level constants derived from `qdas.toml`
- `ensure_path()` — module-level helper in `_parser.py`
- `field_type()` — module-level helper in `_models.py`

### Architecture

- `_models.py` — pure data model with no I/O (`KField`, `Feature`, `ProductionOrder`, `format_order`)
- `_parser.py` — file I/O and DataFrame construction (`QDASFileParser`)
- `_fast.py` — hot-path string parsing (`rows_fast`, `flatten_fast`) with single-allocation `chain` pattern
- `_module.py` — assembly-line module abstraction (`AssemblyLineModule`)
- `_constants.py` — shared constants loaded once from `qdas.toml`
- `_config.py` — TOML config loader

### Build

- PDM backend (`pdm-backend`); no compiled extensions
- `src/` layout; `package-dir = "src"` in `pyproject.toml`
- Dev dependencies: `pytest ≥ 8.0`, `pytest-benchmark ≥ 5.0`

[Unreleased]: https://github.com/j4ggr/qdas-parser/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/j4ggr/qdas-parser/releases/tag/v0.1.0
