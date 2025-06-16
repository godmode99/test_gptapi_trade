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

The script `scripts/fetch/fetch_mt5_data.py` reads its parameters from
`config/fetch_mt5.json` by default and you can pass an alternative JSON file
using `--config`. The configuration defines:

- `symbol` – trading pair (e.g., `XAUUSD`).
- `fetch_bars` – number of historical bars requested for indicator calculation.
- `timeframes` – list of timeframes, each with `tf` (timeframe code) and `keep`
  (how many bars of that timeframe to retain).
- `tz_shift` – hours to shift timestamps. If omitted the default is `0`.

You can adjust timestamps with the `--tz-shift` option. For example, if the
server time is GMT+3 and you need GMT+7 data, pass `--tz-shift 4`.

If you do not specify an output path, `fetch_mt5_data.py` automatically
saves to `data/raw/` with a unique filename in the form
`<symbol>_<ddmmyy>_<HH>H.csv` (e.g. `xauusd_250616_16H.csv`).

Example `config/fetch_mt5.json`:

```json
{
  "tz_shift": 4,
  "symbol": "XAUUSD",
  "fetch_bars": 20,
  "timeframes": [
    {"tf": "M5", "keep": 10},
    {"tf": "M15", "keep": 6},
    {"tf": "H1", "keep": 4}
  ]
}
```

The script `scripts/fetch/fetch_yf_data.py` provides similar functionality using yfinance.
It loads `config/fetch_yf.json` and accepts the same command-line options.
When fetching currency pairs from Yahoo Finance use the `=X` suffix (e.g. `EURUSD=X`).
To download gold prices for `XAUUSD` configure the symbol as `GC=F`.

The `scripts/send_api/send_to_gpt.py` script also reads default values from a JSON file.
It loads `config/gpt.json` unless you pass an alternative path with `--config`.
Example `config/gpt.json`:

```json
{
  "openai_api_key": "YOUR_API_KEY",
  "prompt": "Generate a trading signal and reply only with a JSON object like {\"signal_id\": \"xauusd-20250616_14hr\", \"entry\": 12, \"sl\": 10, \"tp\": 20, \"position_type\": \"buy limit\", \"confidence\": 77 }",
  "model": "gpt-4o",
  "csv": "path/to/file.csv"
}
```

Values provided on the command line override those in the config file.
For the API key the `OPENAI_API_KEY` environment variable takes precedence over
the `openai_api_key` value in the JSON config.
If a `csv` path exists in the provided config file it is used directly and
skips the automatic search for the newest CSV.

If you omit the positional `csv` argument, `send_to_gpt.py` first checks
`config["csv"]`. If that setting is missing it scans the directory specified by
`--data-dir` (default `data/raw`) and uses the newest `*.csv` file it finds. The
selected file path is reported in the logs and the script exits with an error if
no CSV files are available.

The parser `scripts/parse_gpt_response.py` reads a raw GPT reply and writes the
structured result to a JSON file. Use `--csv-log` to set the path for logging
every response (default `logs/responses.csv`) and `--json-dir` to choose the
directory for generated JSON signals (default `signals`). Each run appends a row
to the CSV log with the key values from the signal and saves the parsed data in
a uniquely named file like `250616_153045.json` inside the configured
directory.

## Running the complete workflow

Once the individual scripts are configured you can execute the whole process in
a single command:

```bash
python main.py
```

The `main.py` helper runs the fetch step, sends the result to the GPT API and
parses the raw response into a JSON signal. Use `--fetch-script`, `--send-script`
and `--parse-script` to override the default script locations.

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

## License

This project is licensed under the [MIT License](LICENSE).
