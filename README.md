# AI Trading System

This project implements an automated trading workflow that uses data from MT5 and generates trading signals using the GPT API. The main steps are documented in `Work_flow.md`.

## Installation

Install the pinned Python dependencies using the helper script:

```bash
./scripts/install_deps.sh
```

This project requires specific versions of `pandas`, `MetaTrader5`, `openai` and
`yfinance` which are defined in `requirements.txt`.

## Directory Structure

- `live_trade/data/` – stores all CSV and JSON output
  - `fetch/` – fetched OHLC data
  - `signals/signals_json/` – stored trading signals in JSON format
  - `signals/signals_csv/` – CSV log of parsed signals
- `scripts/` – Python scripts for data fetching, GPT communication and parsing
- `ea/` – Expert Advisor or trading automation code
- `logs/` – log files for debugging and monitoring

## Coding Standards

The scripts in this repository aim to keep input/output operations separate from
business logic. See [CODE_STANDARD.md](CODE_STANDARD.md) for details.

## Configuration

The script `scripts/fetch/fetch_mt5_data.py` reads its parameters from
`scripts/fetch/config/fetch_mt5.json` by default and you can pass an alternative JSON file
using `--config`. The configuration defines:

- `symbol` – trading pair (e.g., `XAUUSD`).
- `fetch_bars` – number of historical bars requested for indicator calculation.
- `time_fetch` – optional timestamp in the form `YYYY-MM-DD HH:MM:SS` to
  retrieve bars ending at that time. Leave empty to fetch the most recent data.
- `timeframes` – list of timeframes, each with `tf` (timeframe code) and `keep`
  (how many bars of that timeframe to retain).
- `tz_shift` – hours to shift timestamps. If omitted the default is `0`.

If the specified `time_fetch` has no matching bars, the script will exit with an error.

You can adjust timestamps with the `--tz-shift` option. For example, if the
server time is GMT+3 and you need GMT+7 data, pass `--tz-shift 4`. The shift is
always applied *after* the raw data has been fetched so the CSV output uses the
same timezone regardless of whether the source is MT5 or Yahoo Finance.

If you do not specify an output path, `fetch_mt5_data.py` automatically
saves to `live_trade/data/fetch/` with a unique filename in the form
`<symbol>_<ddmmyy>_<HH>H.csv` (e.g. `xauusd_250616_16H.csv`).

Example `scripts/fetch/config/fetch_mt5.json`:

```json
{
  "tz_shift": 4,
  "symbol": "XAUUSD",
  "fetch_bars": 20,
  "time_fetch": "",
  "timeframes": [
    {"tf": "M5", "keep": 10},
    {"tf": "M15", "keep": 6},
    {"tf": "H1", "keep": 4}
  ]
}
```

The `fetch` section inside `live_trade/config/setting_main.json` accepts the same keys as the
individual fetcher configuration files, so you can provide `time_fetch` there as
well when running the combined workflow with `main.py`.

The script `scripts/fetch/fetch_yf_data.py` provides similar functionality using yfinance.
It loads `scripts/fetch/config/fetch_yf.json` and accepts the same command-line options.
When fetching currency pairs from Yahoo Finance use the `=X` suffix (e.g. `EURUSD=X`).
To download gold prices for `XAUUSD` configure the symbol as `GC=F`. Like the MT5 fetcher,
the yfinance version shifts timestamps only after the data has been downloaded.

The `scripts/send_api/send_to_gpt.py` script reads its API key and other settings from
`scripts/send_api/config/gpt.json`. Copy `scripts/send_api/config/gpt.example.json`
to `scripts/send_api/config/gpt.json` and fill in your API key. The prompt is
generated automatically from the CSV file name unless you override it on the
command line. The script loads `scripts/send_api/config/gpt.json` unless you pass
an alternative path with `--config`.
Example `scripts/send_api/config/gpt.json`:

```json
{
  "openai_api_key": "YOUR_API_KEY",
  "model": "gpt-4o",
  "csv_file": "",
  "csv_path": "live_trade/data/fetch",
  "save_prompt_dir": "live_trade/data/save_prompt_api"
}
```

Values provided on the command line override those in the config file.
For the API key the `OPENAI_API_KEY` environment variable takes precedence over
the `openai_api_key` value in the JSON config.

If `csv_file` is empty, the script picks the newest `*.csv` file from
`csv_path`. When a file name is specified it is loaded from that directory
unless an absolute path is given.

If you omit the positional `csv` argument, `send_to_gpt.py` uses the config
values described above. The `--data-dir` option defaults to `csv_path` and can
be used to override the search directory. The script also saves a copy of the
CSV data and the final prompt to `live_trade/data/save_prompt_api` by default. Use
`--save-dir` or the `save_prompt_dir` config value to change this location.

The parser `scripts/parse_response/parse_gpt_response.py` reads a raw GPT reply and writes the structured result to a JSON file. Default paths are loaded from `scripts/parse_response/config/parse.json` which defines where to store the CSV log, JSON signals and the latest response file. Use `--csv-log`, `--json-dir`, `--latest-response` or `--tz-shift` to override these values. Each run appends a row to the CSV log and saves the parsed data in a uniquely named file like `250616_153045.json` inside the configured directory.

### Creating `setting_main.json`

The combined workflow expects a configuration file named
`live_trade/config/setting_main.json`. A template is provided as
`live_trade/config/setting_main.example.json`. Copy it and edit the values
before running `main.py`:

```bash
cp live_trade/config/setting_main.example.json \
   live_trade/config/setting_main.json
```

See [`live_trade/docs/config_main_th.md`](live_trade/docs/config_main_th.md) for
an explanation of each key.

## Running the complete workflow

Once the individual scripts are configured you can execute the whole process in
a single command:

```bash
python main.py
```

`main.py` reads default settings from `live_trade/config/setting_main.json` (the
file you created in the previous step). Pass `--config` with a different path to
use custom values. Command-line options override the config entries. The
configuration is divided into `workflow`, `fetch`, `send` and `parse` sections so
all parameters can be managed in one place.

The `main.py` helper runs the fetch step, sends the result to the GPT API and
parses the raw response into a JSON signal. Use `--fetch-script`, `--send-script`
and `--parse-script` to override the default script locations. You can also
select a built-in fetcher with `--fetch-type mt5|yf` (default is `mt5`) or skip
individual stages with `--skip-fetch`, `--skip-send` and `--skip-parse`.

Example fetching from MT5 and only parsing a previous response:

```bash
python main.py --fetch-type mt5 --skip-fetch --skip-send
```

## CustomIndicator

The `ea/CustomIndicator.mq5` file is a simple MT5 indicator that can be compiled
with **MetaEditor**. The indicator calculates RSI‑14, SMA‑20 and ATR‑14 for the
current chart timeframe. If the `DisplaySignals` parameter is enabled it reads
the latest JSON file from the `live_trade/data/signals/signals_json/` directory and shows the parsed values
on the chart. Each JSON signal must include the fields `signal_id`, `entry`, `sl`,
`tp`, `pending_order_type` and `confidence`.

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
