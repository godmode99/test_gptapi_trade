"""Test package setup.

This module checks that optional third-party dependencies are available. If any
are missing a helpful message is raised so developers remember to install them
before running the tests.
"""

REQUIRED = ["pandas", "MetaTrader5", "openai", "yfinance"]

for mod in REQUIRED:
    try:
        __import__(mod)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f"Required package '{mod}' is missing. Run './scripts/install_deps.sh' before executing the tests."
        ) from exc

