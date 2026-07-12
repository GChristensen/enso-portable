#!/bin/sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$SCRIPT_DIR" exec ~/.enso/venv/bin/python3 "$SCRIPT_DIR/scripts/run_enso.py" "$@" --debug -l DEBUG
