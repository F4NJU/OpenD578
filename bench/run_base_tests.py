"""Run bounded OEM regressions and export incomplete full-coverage JUnit report."""
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path);a=p.parse_args()
    source=a.source_dir
    if source is None:
        source=Path(input('Dossier des captures du poste : ').strip().strip('"'))
    if not source.is_dir():p.error('Dossier source introuvable')
    print('Quatre scénarios OEM limités ; la couverture matérielle complète reste incomplète.',flush=True)
    destination=ROOT/'results/bench'/str(time.time_ns());destination.mkdir(parents=True)
    run=subprocess.run([sys.executable,str(ROOT/'run_bench.py'),'--source-dir',str(source),'--engine','native','--out-dir',str(destination)])
    target=destination/'qualification.json'
    if not target.exists():return run.returncode or 1
    return subprocess.run([sys.executable,str(ROOT/'selftest_report.py'),'--regressions',str(target),'--out-dir',str(destination)]).returncode
if __name__=='__main__':raise SystemExit(main())
