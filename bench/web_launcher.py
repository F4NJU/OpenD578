"""Open this version of the local D578 web bench, without reusing stale code."""
import hashlib
import json
import socket
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path
from bench_version import build_id, server_matches
from web_endpoint import read_endpoint

ROOT = Path(__file__).resolve().parent


def reusable_server(url, root_id, expected_build):
    try:
        with urllib.request.urlopen(url + '/api/config', timeout=1) as response:
            config = json.load(response)
        return server_matches(config, root_id, expected_build)
    except (OSError, ValueError):
        return False


def main():
    root_id = hashlib.sha256(str(ROOT.resolve()).encode()).hexdigest()[:16]
    try:remembered=read_endpoint(ROOT)
    except ValueError:remembered=None
    if remembered and reusable_server(remembered,root_id,build_id(ROOT)):
        webbrowser.open(remembered);return
    url = 'http://127.0.0.1:8765'
    if reusable_server(url, root_id, build_id(ROOT)):
        webbrowser.open(url)
        return
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', 8765))
            port = 8765
        except OSError:
            # Let the new server bind its own free port. The old server may
            # still be in use; leave it alone and open the new server's URL.
            port = 0
    (ROOT / 'results').mkdir(exist_ok=True)
    with (ROOT / 'results/serveur_web.log').open('a', encoding='utf-8') as log:
        subprocess.Popen([sys.executable, str(ROOT / 'web_server.py'),
                          '--port', str(port), '--open-browser'],
                         stdout=log, stderr=subprocess.STDOUT,
                         creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)


if __name__ == '__main__':
    main()
