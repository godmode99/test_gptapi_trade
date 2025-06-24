# AI Trading System

This project implements an automated trading workflow that uses data from MT5 and generates trading signals using the GPT API. The main steps are documented in `Work_flow.md`.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Running the workflow](#running-the-complete-workflow)
- [Backtesting](#backtesting)
- [Troubleshooting](#troubleshooting)

## Installation

Install the pinned Python dependencies using the helper script:

```bash
./scripts/install_deps.sh
```

This project requires specific versions of `pandas`, `MetaTrader5`, `openai` and
`yfinance` which are defined in `requirements.txt`.
`APScheduler` is also needed if you plan to use
`src/gpt_trader/cli/scheduler_liveTrade.py`. The helper script above installs it
automatically.

### Installing MetaTrader5

1. Download the **MetaTrader 5** desktop terminal from the official website and
   install it.
2. Ensure the terminal architecture matches your Python interpreter
   (typically 64‑bit).
3. Keep the path to `terminal64.exe` handy. If `mt5.initialize()` cannot find
   the terminal automatically, pass the path manually:

   ```python
   mt5.initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe")
   ```

   On Linux under Wine the path might look like
   `~/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe`.

### Setting the OpenAI API key

Copy the example configuration and insert your API key:

```bash
cp src/gpt_trader/send/config/gpt.example.json src/gpt_trader/send/config/gpt.json
```

Edit `gpt.json` and replace `YOUR_API_KEY` with your OpenAI key. You can also
set the `OPENAI_API_KEY` environment variable which takes precedence over the
value in the JSON file.

## Directory Structure

- `data/live_trade/` – stores all CSV and JSON output
  - `fetch/` – fetched OHLC data
  - `signals/signals_json/` – stored trading signals in JSON format
  - `signals/signals_csv/` – CSV log of parsed signals
- `src/gpt_trader/` – package containing the workflow code
- `ea/` – Expert Advisor or trading automation code
- `logs/` – log files for debugging and monitoring

## Coding Standards

The scripts in this repository aim to keep input/output operations separate from
business logic. See [CODE_STANDARD.md](CODE_STANDARD.md) for details.

## Configuration

The script `src/gpt_trader/fetch/fetch_mt5_data.py` reads its parameters from
`src/gpt_trader/fetch/config/fetch_mt5.json` by default and you can pass an alternative JSON file
using `--config`. The configuration defines:

- `symbol` – trading pair (e.g., `XAUUSD`).
- `fetch_bars` – number of historical bars requested for indicator calculation.
- `indicators` – enable or disable calculation of `atr14`, `rsi14`, `sma20`,
  `ema50` and `sma200`.
  Indicators disabled here will not appear as columns in the resulting CSV or
  JSON files.
- `time_fetch` – optional timestamp in the form `YYYY-MM-DD HH:MM:SS` to
  retrieve bars ending at that time. Leave empty to fetch the most recent data.
- `timeframes` – list of timeframes, each with `tf` (timeframe code) and `keep`
  (how many bars of that timeframe to retain).
- `tz_shift` – hours to shift timestamps. If omitted the default is `0`.

If the specified `time_fetch` has no matching bars, the script will exit with an error.

You can adjust timestamps with the `--tz-shift` option. For example, if the
server time is GMT+3 and you need GMT+7 data, pass `--tz-shift 4`. The shift is
always applied *after* the raw data has been fetched so the CSV and JSON output
use the same timezone regardless of whether the source is MT5 or Yahoo Finance.

If you do not specify an output path, `fetch_mt5_data.py` saves the CSV
and an equivalent JSON file in the directory specified by `save_as_path`
(defaults to `data/live_trade/fetch`). The file name now uses a UNIX
timestamp for uniqueness. It has the form
`<symbol_signal><unixtime>.csv` (e.g. `xauusd1750424400.csv`). The
`symbol_signal` value can be set in the configuration and defaults to the
fetch `symbol` in lower case.

Each row in the output also includes a `session` field that labels the
bar as belonging to the **asia**, **london** or **newyork** trading
session based on the shifted timestamp.

Example `src/gpt_trader/fetch/config/fetch_mt5.json`:

```json
{
  "tz_shift": 4,
  "symbol": "XAUUSD",
  "symbol_signal": "xauusd",
  "fetch_bars": 20,
  "time_fetch": "",
  "timeframes": [
    {"tf": "M5", "keep": 10},
    {"tf": "M15", "keep": 6},
    {"tf": "H1", "keep": 4}
  ]
}
```

The `fetch` section inside `config/setting_live_trade.json` accepts the same keys as the
individual fetcher configuration files, so you can provide `time_fetch` there as
well when running the combined workflow with `main_liveTrade.py`.

The script `src/gpt_trader/fetch/fetch_yf_data.py` provides similar functionality using yfinance.
It loads `src/gpt_trader/fetch/config/fetch_yf.json` and accepts the same command-line options.
When fetching currency pairs from Yahoo Finance use the `=X` suffix (e.g. `EURUSD=X`).
To download gold prices for `XAUUSD` configure the symbol as `GC=F`. Like the MT5 fetcher,
the yfinance version shifts timestamps only after the data has been downloaded.

The `src/gpt_trader/send/send_to_gpt.py` script reads its API key and other settings from
`src/gpt_trader/send/config/gpt.json`. Copy `src/gpt_trader/send/config/gpt.example.json`
to `src/gpt_trader/send/config/gpt.json` and fill in your API key. The prompt is
generated automatically from the JSON file name unless you override it on the
command line. The script loads `src/gpt_trader/send/config/gpt.json` unless you pass
an alternative path with `--config`.
Example `src/gpt_trader/send/config/gpt.json`:

```json
{
  "openai_api_key": "YOUR_API_KEY",
  "model": "gpt-4o",
  "json_file": "",
  "json_path": "data/live_trade/fetch",
  "save_prompt_dir": "data/live_trade/save_prompt_api"
}
```

Values provided on the command line override those in the config file.
For the API key the `OPENAI_API_KEY` environment variable takes precedence over
the `openai_api_key` value in the JSON config.

If `json_file` is empty, the script picks the newest `*.json` file from
`json_path`. When a file name is specified it is loaded from that directory
unless an absolute path is given.

If you omit the positional `json` argument, `send_to_gpt.py` uses the config
values described above. The `--data-dir` option defaults to `json_path` and can
be used to override the search directory. The script also saves a JSON file
containing the input data and final prompt to `data/live_trade/save_prompt_api`
by default. Use
`--save-dir` or the `save_prompt_dir` config value to change this location.

The parser `src/gpt_trader/parse/parse_gpt_response.py` reads a raw GPT reply and writes the structured result to a JSON file. Default paths are loaded from `src/gpt_trader/parse/config/parse.json` which defines where to store the CSV log, JSON signals and the latest response file. Use `--csv-log`, `--json-dir`, `--latest-response` or `--tz-shift` to override these values. Each run appends a row to the CSV log and saves the parsed data in a uniquely named file like `250616_153045.json` inside the configured directory. A copy of the parsed data is also written to `latest_response.json` alongside the text file for easy access.

### Creating configuration files

The combined workflow expects configuration files named
`config/setting_live_trade.json` and `config/setting_backtest.json`.
Templates are provided as
`config/setting_live_trade.example.json` and
`config/setting_backtest.example.json`. Copy them before editing:

```bash
cp config/setting_live_trade.example.json config/setting_live_trade.json
cp config/setting_backtest.example.json config/setting_backtest.json
```

See [`live_trade/docs/config_main_th.md`](live_trade/docs/config_main_th.md) for
an explanation of each key.

The live trade config also accepts the keys `risk_per_trade` and
`max_risk_per_trade` (percentages of account balance).  When
`risk_per_trade` is set it overrides any value found in the signal JSON.
If `max_risk_per_trade` is provided the actual risk is calculated as
`(confidence / 100) * max_risk_per_trade` and will never exceed this
limit.

For Thai users: สำหรับภาษาไทย ดูเอกสารที่ `live_trade/docs/usage_th.md`.

## Running the complete workflow

Once the individual scripts are configured you can execute the whole process in
a single command:

```bash
python main_liveTrade.py
```

`main_liveTrade.py` reads default settings from `config/setting_live_trade.json` (the
file you created in the previous step). Pass `--config` with a different path to
use custom values. Command-line options override the config entries. The
configuration is divided into `workflow`, `fetch`, `send` and `parse` sections so
all parameters can be managed in one place.

The `main_liveTrade.py` helper runs the fetch step, sends the result to the GPT API and
parses the raw response into a JSON signal. Use `--fetch-script`, `--send-script`
and `--parse-script` to override the default script locations. You can also
select a built-in fetcher with `--fetch-type mt5|yf` (default is `mt5`) or skip
individual stages with `--skip-fetch`, `--skip-send` and `--skip-parse`.

Example fetching from MT5 and only parsing a previous response:

```bash
python main_liveTrade.py --fetch-type mt5 --skip-fetch --skip-send
```

### Automated execution

Run `src/gpt_trader/cli/scheduler_liveTrade.py` to execute the workflow on a
schedule. The script uses APScheduler to call `main_liveTrade.py` repeatedly
(version 3.x is expected but the code attempts to handle version 4.x as well).
`main_liveTrade.py` prepends the repository root to `sys.path` so the scheduler
can be executed directly from the project root. The workflow is executed once
immediately and then the next run is aligned to the next ``:10`` or ``:40`` slot
based on the configured start time (08:10 by default). Subsequent runs follow
this 30 minute cycle. You can override the interval, start and stop times:

```bash
python src/gpt_trader/cli/scheduler_liveTrade.py \
  --start-day mon --start-time 08:10 \
  --stop-day fri --stop-time 23:35 \
  --interval 30 --start-in 15
```

The command above waits 15 minutes before the first run and then repeats every
30 minutes. The script prints a countdown showing how long remains until the next
scheduled execution. Press **Ctrl+C** to stop the scheduler.

After each run the file `latest_response.json` is generated and passed to
`TradeSignalSender` which submits the pending order to MT5 automatically.
If your broker uses different symbol names, adjust the `SYMBOL_MAP` dictionary
inside `src/gpt_trader/cli/latest_signal_to_mt5.py` to map between the signal
prefix and the actual MT5 symbol.
If a signal sets `pending_order_type` to `skip`, the script prints the reason and
does not send any order to MT5.
The file was previously named `lastest_signal_to_mt5.py`; a stub remains for
backward compatibility.
The sender uses the `risk_per_trade` value from the config when provided.

## Backtesting

The `back_test` directory contains a helper script for running an offline
simulation. Configuration values are loaded from a JSON file and must specify
at least:

- `symbol` – instrument to download historical data for
- `timeframe` – timeframe of the bars
- `start_time` and `end_time` – begin and end timestamps for the loop
- `loop_every_minutes` – step size between iterations
- `fetch_bars` – number of bars to retrieve per step
- `gpt_model` – OpenAI model to call
- `prompt_template` – path to the prompt used for each request
- `signal_table` – output CSV file for generated signals
- [`back_test/backtest_flow.md`](back_test/backtest_flow.md) – overview of the backtest workflow

Execute a backtest with the provided example config:

```bash
python src/gpt_trader/cli/main_backtest.py --config back_test/backtest.json
```

The resulting CSV defined by `signal_table` (default
`data/back_test/signals/backtest_signals.csv`) can be imported into MT5 for evaluation
inside the strategy tester.

## CustomIndicator

The `ea/CustomIndicator.mq5` file is a simple MT5 indicator that can be compiled
with **MetaEditor**. The indicator calculates RSI‑14, SMA‑20 and ATR‑14 for the
current chart timeframe. If the `DisplaySignals` parameter is enabled it reads
the latest JSON file from the `data/live_trade/signals/signals_json/` directory and shows the parsed values
on the chart. Each JSON signal must include the fields `signal_id`, `entry`, `sl`,
`tp`, `pending_order_type`, `confidence`, `regime_type` and `short_reason`.

### Compile & Attach

1. Copy `CustomIndicator.mq5` to your MT5 **MQL5/Indicators** folder or open it
   directly in MetaEditor. A minimal `stdlib.mqh` stub is also provided in the
   `ea/` directory in case the standard library is missing.
2. Press **Compile**. The compiled indicator (`CustomIndicator.ex5`) will appear
   in the Navigator under *Indicators*.
3. Drag the indicator onto a chart. Set `DisplaySignals` to `false` to plot
   RSI/SMA/ATR or set it to `true` to display parsed signals.

Refer to `Work_flow.md` for the full workflow description.

## Running tests

Install the pinned dependencies *before* executing the test suite. The tests
import optional packages that will be missing in a fresh clone unless you run
the helper script:

```bash
./scripts/install_deps.sh
```

You can also install the packages listed in `requirements.txt` manually. The
tests rely on optional modules such as `MetaTrader5`, `openai` and `yfinance`.
If these modules are missing the test discovery step will raise a clear error
from `tests/__init__.py`.

Run the tests with:

```bash
pytest
```

## Troubleshooting

- **`MetaTrader5.initialize()` fails** – ensure the desktop terminal is installed
  and that the path passed to `mt5.initialize()` is correct. The Python package
  must match the terminal architecture.
- **Missing modules** – run `./scripts/install_deps.sh` to install all
  dependencies from `requirements.txt`.
- **Authentication errors from OpenAI** – verify that `OPENAI_API_KEY` is set or
  that your `gpt.json` contains the correct key.
## Additional documentation

- [การใช้งานระบบภาษาไทย](live_trade/docs/usage_th.md)
- [คู่มือใช้งาน Live Trade และ Backtest](docs/usage_overall_th.md)
- [สรุปรายการไฟล์ในโครงการ](docs/files_overview_th.md)
- [ภาพรวม flow การทำงาน](docs/flow_overview_th.md)
- [การติดตั้งบน Linux/Wine และใช้งาน scheduler](docs/usage_linux_th.md)


## License

This project is licensed under the [MIT License](LICENSE).
