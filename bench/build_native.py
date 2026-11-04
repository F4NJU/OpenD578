"""Compile the optional counter for the current host; no radio code is built."""
import argparse,hashlib,json,shlex,shutil,subprocess,sys,platform,os
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def build(compiler=None):
    cc=shlex.split(compiler or os.environ.get('CC','cc'))
    if not cc or not shutil.which(cc[0]):
        raise RuntimeError('C compiler unavailable; use --engine python, or install GCC/Clang')
    suffix='.dll' if sys.platform=='win32' else '.dylib' if sys.platform=='darwin' else '.so'
    destination=ROOT/(('native_gate' if sys.platform=='win32' else 'native_gate_host')+suffix)
    temporary=destination.with_name(destination.stem+'.building'+suffix)
    flags=['-dynamiclib','-fPIC'] if sys.platform=='darwin' else ['-shared'] if sys.platform=='win32' else ['-shared','-fPIC']
    command=[*cc,'-O2','-std=c11','-Wall','-Wextra',*flags,str(ROOT/'native_gate.c'),'-o',str(temporary)]
    subprocess.run(command,check=True)
    temporary.replace(destination)
    report=dict(platform=sys.platform,machine=platform.machine(),command=command,
        source_sha256=hashlib.sha256((ROOT/'native_gate.c').read_bytes()).hexdigest(),
        binary_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
    destination.with_suffix(destination.suffix+'.build.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cc')
    args=parser.parse_args()
    print(json.dumps(build(args.cc),indent=2))
