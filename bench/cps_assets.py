"""Serve only built CPS assets on the bench's existing authenticated origin."""
from pathlib import Path
from urllib.parse import unquote

TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
}


def read_cps_asset(root, url_path):
    if not url_path.startswith('/cps/'):
        raise ValueError('Not a CPS route')
    directory = Path(root).resolve()
    relative = unquote(url_path[len('/cps/'):]) or 'index.html'
    if '\\' in relative or '\x00' in relative or ':' in relative:
        raise ValueError('Invalid asset path')
    target = (directory / relative).resolve()
    if not target.is_relative_to(directory) or target.suffix not in TYPES:
        raise ValueError('Asset outside CPS output')
    return target.read_bytes(), TYPES[target.suffix]
