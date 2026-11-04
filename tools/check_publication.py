"""Check the tracked source package for excluded firmware/capture artifacts."""
import subprocess,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bad=[]
process=subprocess.run(['git','ls-files','-z'],cwd=ROOT,capture_output=True)
paths=[ROOT/p.decode() for p in process.stdout.split(b'\0') if p] if process.returncode==0 else [
    p for p in ROOT.rglob('*') if p.is_file() and not any(v in ('work','results','__pycache__','.git','.venv') for v in p.relative_to(ROOT).parts)]
for path in paths:
    name=path.name.lower()
    if any(name.endswith(ext) for ext in ('.bin','.cdd','.cdi','.spi','.hex','.pkl','.pkl.gz','.dll','.so','.dylib','.elf','.o','.zip')):
        bad.append(str(path.relative_to(ROOT))+': binary/capture excluded')
    data=path.read_bytes()
    if b'\0' in data:bad.append(str(path.relative_to(ROOT))+': unexpected binary content')
    if re.search(rb'gh[pousr]_[A-Za-z0-9]{30,}',data):bad.append(str(path.relative_to(ROOT))+': credential-shaped value')
print('Publication check:',len(paths),'files,',len(bad),'violations')
for issue in bad:print(issue)
raise SystemExit(bool(bad))
