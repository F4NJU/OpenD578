"""Open qualification coverage and JUnit XML; missing models never become passes."""
import argparse,json,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent


def build_report(catalog,regressions=()):
    items=[]
    for f in catalog['features']:
        # Existing OEM oracles exercise a limited layer, not the full acceptance criterion.
        items.append(dict(id=f['id'],title=f['title'],scope=f['scope'],status='incomplete',
            reason='; '.join(f['blockers']),model=f['model'],acceptance=f['acceptance']))
    regressions=list(regressions)
    for case in regressions:
        if case.get('status') not in ('passed','failed','incomplete','not_supported'):
            raise ValueError('Unknown regression verdict')
    failed=any(r['status']=='failed' for r in regressions)
    return dict(schema_version=1,status='failed' if failed else 'incomplete',target=catalog['target'],
        inventory_completeness=catalog['completeness'],physical_radio_certified=False,
        features=items,regressions=regressions,counts=dict(Counter(v['status'] for v in items)),
        limitations=['Passing an OEM logical regression does not qualify an RF/audio waveform chain',
                     'New firmware requires hardware observations; no OEM RAM addresses are portable',
                     'No automatic completeness claim from strings, routine candidates or unit test count'])


def junit(report,path):
    rows=[dict(v,classname='requirements') for v in report['features']]+[
        dict(v,id=v.get('scenario','unknown'),classname='bounded_OEM_regressions') for v in report['regressions']]
    root=ET.Element('testsuite',name='OpenD578',tests=str(len(rows)),
        failures=str(sum(v['status']=='failed' for v in rows)),errors='0',
        skipped=str(sum(v['status'] in ('incomplete','not_supported') for v in rows)))
    props=ET.SubElement(root,'properties')
    for name,value in [('physical_radio_certified','false'),('inventory_completeness',report['inventory_completeness'])]:
        ET.SubElement(props,'property',name=name,value=value)
    for item in rows:
        case=ET.SubElement(root,'testcase',classname=item['classname'],name=item['id'])
        tag='failure' if item['status']=='failed' else 'skipped' if item['status']!='passed' else None
        if tag:ET.SubElement(case,tag,message=item.get('reason','No completed hardware test'),type=item['status'])
    path.parent.mkdir(parents=True,exist_ok=True);ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,default=ROOT/'qualification_data/catalog.json')
    p.add_argument('--regressions',type=Path,help='qualification.json produced by run_bench.py')
    p.add_argument('--out-dir',type=Path,default=ROOT/'results/selftest')
    a=p.parse_args();catalog=json.loads(a.catalog.read_text());cases=[]
    if a.regressions:
        data=json.loads(a.regressions.read_text());cases=data['cases']
        # run_bench explicitly marks incompatible observation profiles incomplete.
        if data.get('status')=='failed' and not any(c.get('status')=='failed' for c in cases):
            cases.append(dict(scenario='runner',status='failed',reason='Runner failed'))
    report=build_report(catalog,cases);a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/'selftest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    junit(report,a.out_dir/'junit.xml');print(json.dumps(dict(status=report['status'],requirements=report['counts'],regressions=len(cases)),ensure_ascii=False))
    return 1 if report['status']=='failed' else 2
if __name__=='__main__':raise SystemExit(main())
