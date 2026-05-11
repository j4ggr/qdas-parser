# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.2.0] — 2026-05-08

### Added

- `src/qdas_parser/_fields.py` — Python-native K-Field registry replacing
  `qdas.toml` field data with typed structures and four `MappingProxyType`
  exports:
  - `FieldDef` — `NamedTuple` with `name`, `values`, and `comments` fields
  - `REQUIRED` — five mandatory header fields (`K0100`, `K1001`, `K1002`,
    `K2001`, `K2002`)
  - `DEFINED` — ~80 K-Fields with integer-coded value/comment maps
  - `SUPPORTED` — ~250 documented non-coded fields
  - `CATALOG` — ~100 catalog fields (`K4xxx`)
- `QDASFileParser` accepts an `index_columns` parameter
  (`List[str]`, default `['Auftragsnummer', 'Seriennummer']`) so callers can
  customise the DataFrame row index without subclassing

### Changed

- `_models.py` — `field_type()`, `KField.decode()`, and `Feature.extend()` now
  use the `_fields` registries directly; `QDAS_CONFIG` import removed
- `_constants.py` — `_FieldCategory.CATEGORIES` tuple hardcoded; `QDAS_CONFIG`
  import removed

### Fixed

- `SUPPORTED` key `K0099` corrected to `K0999` (`'Anzahl Merkmale pro Teil = 0'`)
- `CATALOG` entries `K4791` and `K4792` were missing; added
- `_DOKUMENTATIONSPFLICHT` codes 17–20 were bare integers; corrected to
  string literals so `FieldDef.values: Mapping[int, str]` holds

---

## [0.1.2] — 2026-05-07

### Added

- `src/qdas_parser/hooks/hook-qdas_parser.py` — PyInstaller hook that calls
  `collect_data_files('qdas_parser')` so `qdas.toml` is automatically included
  in frozen applications without requiring `--collect-data` or a custom `.spec`
- `[tool.pyinstaller] hook-dirs` entry in `pyproject.toml` so PyInstaller
  discovers the hook from the installed package

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

[Unreleased]: https://github.com/j4ggr/qdas-parser/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/j4ggr/qdas-parser/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/j4ggr/qdas-parser/releases/tag/v0.1.0
