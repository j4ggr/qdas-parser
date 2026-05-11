# qdas-parser

A Python parser for the **Q-DAS ASCII Transfer Format (V12)**.  
Reads `.dfd` description files paired with `.dfx` (process) or `.dfb` (batch) value files,
decodes K-Field metadata, and returns structured **pandas DataFrames** ready for downstream
quality analysis.

---

## Features

- Parse Q-DAS `.dfd` + `.dfx`/`.dfb` file pairs into tidy pandas DataFrames
- Full K-Field decoding — field names and coded values translated via typed Python registries (`REQUIRED`, `DEFINED`, `SUPPORTED`, `CATALOG`)
- MultiIndex columns `(module, feature)` for easy slicing across assembly lines
- Production order normalisation via `format_order()` / `ProductionOrder`
- Optional test-cell detection through an injected module map
- Pure Python — no compiled extensions required
- Typed API with `__slots__` throughout for low-memory footprint

---

## Requirements

| Dependency | Version |
|---|---|
| Python | ≥ 3.13 |
| pandas | ≥ 3.0 |
| numpy | ≥ 2.4 |
| python-dateutil | ≥ 2.8 |

---

## Installation

```bash
pip install qdas-parser
```

---

## Quick start

```python
from pathlib import Path
from qdas_parser import QDASFileParser

qdas = QDASFileParser(
    Path("data/bd/m01/2603160002.dfd"),
    product="ACT1",
)
qdas.parse_description()
qdas.parse_values()

df  = qdas.dataframe()   # measurement data as MultiIndex DataFrame
dfm = qdas.metadata()    # feature metadata as MultiIndex DataFrame
```

The DataFrame index is `['Auftragsnummer', 'Seriennummer']`.  
Columns are a two-level `MultiIndex`: `(module_name, feature_label)`.

---

## File format overview

A Q-DAS measurement set consists of two files sharing the same stem:

| File | Role |
|---|---|
| `<stem>.dfd` | Description file — K-Field header and feature metadata |
| `<stem>.dfx` | Value file for **process** data (`.dfx`) |
| `<stem>.dfb` | Value file for **batch** data (`.dfb`) |

Each line in the `.dfd` file is a K-Field:

```
K0100 3               ← number of features
K1001 1234567         ← part number (Teilenummer)
K2002/1 Diameter      ← feature 1 label
K2142/1 mm            ← feature 1 unit
```

---

## Public API

### `QDASFileParser`

Main entry point.

```python
from qdas_parser import QDASFileParser

parser = QDASFileParser(
    description_file="2603160002.dfd",
    product="ACT1",
    kind="bd",                          # 'bd' | 'pc' — inferred from path if omitted
    tc_modules={"ACT1": {"as1": ["tc1_bd", "tc2_bd"]}},
    tc_shortcut="TC",
    index_columns=["Auftragsnummer", "Seriennummer"],  # default; customise as needed
)
parser.parse_description()
parser.parse_values()

df  = parser.dataframe()
dfm = parser.metadata()
```

### `format_order`

Normalise raw order numbers from any source to a 12-digit zero-padded string:

```python
from qdas_parser import format_order

df["order"] = df["order"].map(format_order)
# '1234567'  →  '000001234567'
# 1234567    →  '000001234567'
# ''         →  ''
```

### `ProductionOrder`

A lightweight value object wrapping a formatted order number:

```python
from qdas_parser import ProductionOrder

po = ProductionOrder("1234567")
str(po)       # '000001234567'
int(po)       # 1234567
bool(po)      # True
po == 1234567 # True  — comparison normalises both sides
```

### `KField`

Low-level K-Field model, useful for custom description-file processing:

```python
from qdas_parser import KField

kf = KField.from_line("K2002/1 Diameter\n")
kf.key            # 'K2002'
kf.value          # 'Diameter'
kf.feature_number # 1
kf.feature_index  # 0  (zero-based)

name, value = kf.decode()
```

### `QDAS` constants

```python
from qdas_parser import QDAS

QDAS.SEP_F          # feature separator character (ASCII 15)
QDAS.SEP_E          # extension separator character (ASCII 20)
QDAS.TIMESTAMP      # 'Zeitstempel'
QDAS.ORDER          # 'Auftragsnummer'
QDAS.PART_ID        # 'Seriennummer'
```

---

## Running the tests

```bash
pip install pytest pytest-benchmark
pytest tests/
```

Benchmarks only:

```bash
pytest tests/bench_fast.py --benchmark-only -v
```

---

## License

MIT — see [LICENSE](LICENSE).
