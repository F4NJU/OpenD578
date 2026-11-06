#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
    printf '%s\n' "Lancer d'abord OUVRIR_BANC_WEB pour preparer le banc."
    exit 1
fi
exec .venv/bin/python cps_bridge.py --pty "$@"
