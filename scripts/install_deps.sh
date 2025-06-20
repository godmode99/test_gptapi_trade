#!/usr/bin/env sh
# Install pinned dependencies for development and testing
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install APScheduler==3.10.4
pip install -e .

