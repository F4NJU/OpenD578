#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
.venv/bin/python ensure_environment.py
if [ ! -f native_gate_host.so ] && [ ! -f native_gate_host.dylib ]; then
    .venv/bin/python build_native.py || printf '%s\n' 'Compteur natif indisponible : choisir le moteur Référence dans la page.'
fi
if [ ! -f lcd_bridge_host.so ] && [ ! -f lcd_bridge_host.dylib ]; then
    .venv/bin/python build_lcd_bridge.py || printf '%s\n' 'Bus natif indisponible : le banc utilisera le modele Python.'
fi
exec .venv/bin/python web_launcher.py
