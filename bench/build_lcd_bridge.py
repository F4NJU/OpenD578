"""Build the host GPIO dispatcher; no radio firmware is compiled."""
import argparse,hashlib,json,os,shlex,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def build(compiler=None,target=None,output=None):
    cc=shlex.split(compiler or os.environ.get('CC','cc'))
    if not cc or not shutil.which(cc[0]):raise RuntimeError('C compiler unavailable')
    suffix='.dll' if sys.platform=='win32' else '.dylib' if sys.platform=='darwin' else '.so'
    destination=Path(output) if output else ROOT/(('lcd_bridge' if sys.platform=='win32' else 'lcd_bridge_host')+suffix)
    flags=['-dynamiclib','-fPIC'] if sys.platform=='darwin' and not target else ['-shared'] if target or sys.platform=='win32' else ['-shared','-fPIC']
    command=[*cc,*(['-target',target] if target else []),'-O3','-std=c11','-Wall','-Wextra',*flags,str(ROOT/'lcd_bridge.c'),'-o',str(destination)]
    subprocess.run(command,check=True)
    report=dict(command=command,target=target or sys.platform,source_sha256=hashlib.sha256((ROOT/'lcd_bridge.c').read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
    destination.with_suffix(destination.suffix+'.build.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--cc');parser.add_argument('--target');parser.add_argument('--output')
    args=parser.parse_args();print(json.dumps(build(args.cc,args.target,args.output),indent=2))
