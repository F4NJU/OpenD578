"""Avoid a network/pip check on every launch when exact dependencies exist."""
import importlib.metadata
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent


def ready(requirements):
    for line in requirements.splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        name,separator,version=line.partition('==')
        if not separator:return False
        try:
            if importlib.metadata.version(name)!=version:return False
        except importlib.metadata.PackageNotFoundError:return False
    return True


def main():
    requirements=(ROOT/'requirements.txt').read_text()
    if ready(requirements):return
    print('Installation des dependances du banc...',flush=True)
    subprocess.run([sys.executable,'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)

if __name__=='__main__':main()
