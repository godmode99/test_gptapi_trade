# AI Trading System

This project implements an automated trading workflow that uses data from MT5 and generates trading signals using the GPT API. The main steps are documented in `Work_flow.md`.

## Installation

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Directory Structure

- `data/` – stores fetched data and processed CSV/JSON files
  - `raw/` – original data exported from MT5
  - `processed/` – cleaned data and generated datasets
- `scripts/` – Python scripts for data fetching, GPT communication and parsing
- `ea/` – Expert Advisor or trading automation code
- `signals/` – stored trading signals in JSON format
- `logs/` – log files for debugging and monitoring

## Configuration

The script `scripts/fetch_mt5_data.py` reads its parameters from
`config/fetch_mt5.json` by default and you can pass an alternative JSON file
using `--config`. The configuration defines:

- `symbol` – trading pair (e.g., `XAUUSD`).
- `fetch_bars` – number of historical bars requested for indicator calculation.
- `timeframes` – list of timeframes, each with `tf` (timeframe code) and `keep`
  (how many bars of that timeframe to retain).

If you do not specify an output path, `fetch_mt5_data.py` automatically
saves to `data/raw/` with a unique filename in the form
`<symbol>_<ddmmyy>_<HH>H.csv` (e.g. `xauusd_250616_16H.csv`).

Example `config/fetch_mt5.json`:

```json
{
  "symbol": "XAUUSD",
  "fetch_bars": 20,
  "timeframes": [
    {"tf": "M5", "keep": 10},
    {"tf": "M15", "keep": 6},
    {"tf": "H1", "keep": 4}
  ]
}
```

## CustomIndicator

The `ea/CustomIndicator.mq5` file is a simple MT5 indicator that can be compiled
with **MetaEditor**. The indicator calculates RSI‑14, SMA‑20 and ATR‑14 for the
current chart timeframe. If the `DisplaySignals` parameter is enabled it reads
the latest JSON file from the `signals/` directory and shows the parsed values
on the chart.

### Compile & Attach

1. Copy `CustomIndicator.mq5` to your MT5 **MQL5/Indicators** folder or open it
   directly in MetaEditor. A minimal `stdlib.mqh` stub is also provided in the
   `ea/` directory in case the standard library is missing.
2. Press **Compile**. The compiled indicator (`CustomIndicator.ex5`) will appear
   in the Navigator under *Indicators*.
3. Drag the indicator onto a chart. Set `DisplaySignals` to `false` to plot
   RSI/SMA/ATR or set it to `true` to display parsed signals.

Refer to `Work_flow.md` for the full workflow description.
