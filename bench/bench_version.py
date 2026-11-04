"""Identify the running web bench before reusing its local server."""
import hashlib
from pathlib import Path

VERSION = 'V11.1'
APPLICATION = 'D578 local bench ' + VERSION
BUILD_FILES = ('bench_version.py', 'web_launcher.py', 'web_server.py',
               'prepare_inputs.py', 'run_lcd.py', 'web/index.html',
               'web/app.js', 'web/style.css')


def build_id(root):
    digest = hashlib.sha256()
    for name in BUILD_FILES:
        digest.update(name.encode('utf-8') + b'\0')
        digest.update((Path(root) / name).read_bytes())
    return digest.hexdigest()


def server_matches(config, root_id, expected_build):
    return (isinstance(config, dict) and config.get('root_id') == root_id
            and config.get('application') == APPLICATION
            and config.get('build_id') == expected_build)
