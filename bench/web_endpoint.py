"""Remember the actual loopback port of this copy of the bench."""
import hashlib,json
from pathlib import Path
from urllib.parse import urlparse
from bench_version import APPLICATION


def root_id(root):return hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()[:16]


def loopback_url(url):
    parsed=urlparse(url)
    if (parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1')
            or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment):
        raise ValueError('Utiliser l’adresse HTTP locale du banc, sans chemin ni paramètres')
    # Force validation of an invalid/non-numeric port before any network call.
    parsed.port
    return url.rstrip('/')


def read_endpoint(root):
    path=Path(root)/'work/web_endpoint.json'
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value,dict) or value.get('root_id')!=root_id(root):raise ValueError('Dossier différent')
        return loopback_url(value['url'])
    except (OSError,ValueError,KeyError,TypeError) as error:
        raise ValueError('Serveur de ce dossier introuvable. Lancer OUVRIR_BANC_WEB, ou fournir --url avec l’adresse du navigateur.') from error


def record_endpoint(root,url,build):
    path=Path(root)/'work/web_endpoint.json';path.parent.mkdir(parents=True,exist_ok=True)
    value=dict(url=loopback_url(url),root_id=root_id(root),application=APPLICATION,build_id=build)
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value),encoding='utf-8');temporary.replace(path)
