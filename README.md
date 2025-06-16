# AI Trading System

This project implements an automated trading workflow that uses data from MT5 and generates trading signals using the GPT API. The main steps are documented in `Work_flow.md`.

## Directory Structure

- `data/` – stores fetched data and processed CSV/JSON files
  - `raw/` – original data exported from MT5
  - `processed/` – cleaned data and generated datasets
- `scripts/` – Python scripts for data fetching, GPT communication and parsing
- `ea/` – Expert Advisor or trading automation code
- `signals/` – stored trading signals in JSON format
- `logs/` – log files for debugging and monitoring

Refer to `Work_flow.md` for the full workflow description.
