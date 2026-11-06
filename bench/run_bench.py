"""Reproducible software scenarios; never equates missing models with success."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
from qualification import assess
def main():
    p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path,default=Path.home()/'Downloads/D578');p.add_argument('--cache-dir',type=Path,default=ROOT/'work/inputs')
    p.add_argument('--out-dir',type=Path,default=ROOT/'results/bench');p.add_argument('--firmware',type=Path);p.add_argument('--engine',choices=('native','python'),default='python');p.add_argument('--cold',action='store_true')
    p.add_argument('--case',action='append',choices=('cold_boot','FM','GPS','PTT','LED_bus'))
    a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True);reports=[]
    cases=[('cold_boot',70000000,[])] if a.cold or a.firmware else []
    if not a.firmware:cases += [('FM',9000000,['--resume-ready','--scenario',str(ROOT/'scenarios/FM_carrier.json')]),('GPS',13000000,['--resume-ready','--gps','fix','--gps-rate','4','--scenario',str(ROOT/'scenarios/GPS_loss.json')]),('PTT',4000000,['--resume-ready','--microphone','--scenario',str(ROOT/'scenarios/micro_PTT.json')])]
    if not a.firmware:cases.append(('LED_bus',13000000,['--resume-ready','--microphone','--scenario',str(ROOT/'scenarios/LED_RX_TX.json')]))
    if a.case:cases=[c for c in cases if c[0] in a.case]
    if not cases:p.error('No runnable case for the selected firmware/boot options')
    for name,count,options in cases:
        destination=a.out_dir/name
        command=[sys.executable,str(ROOT/'run_lcd.py'),'--source-dir',str(a.source_dir),'--cache-dir',str(a.cache_dir),'--out-dir',str(destination),'--engine',a.engine,'--voltage','13.8','--instructions',str(count),*options]
        if a.firmware:command+=['--firmware',str(a.firmware)]
        process=subprocess.run(command,capture_output=True,text=True)
        if process.returncode:report=dict(status='failed',reason='simulator process error',detail=process.stderr[-3000:])
        else:
            result=json.loads((destination/'resultat.json').read_text(encoding='utf-8'));report=assess(name,result)
            if a.firmware:report=dict(status='incomplete',reason='different firmware: peripheral and observation profile not qualified',stop=result['stop'])
            report['executed_instructions']=result['steps']-result.get('session_origin',{}).get('recorded_steps',0)
        report['scenario']=name;reports.append(report);print(json.dumps(report,ensure_ascii=False),flush=True)
    overall='failed' if any(r['status']=='failed' for r in reports) else 'incomplete' if a.firmware or any(r['status']=='incomplete' for r in reports) else 'passed_for_executed_scenarios_only'
    report=dict(status=overall,cold_boot_requested=bool(a.cold or a.firmware),
                cold_boot_executed=any(r['scenario']=='cold_boot' and r.get('executed_instructions',0)>0 for r in reports),
                cold_boot_completed=any(r['scenario']=='cold_boot' and r['status']=='passed' for r in reports),
                firmware=str(a.firmware) if a.firmware else 'authenticated OEM V1.21',cases=reports,
                physical_radio_certified=False,not_covered=['RF waveform and PA power','DSP and AMBE','DMR reception','complete APRS modulation DMA','all memory corruption paths'])
    from selftest_report import build_report,junit
    coverage=build_report(json.loads((ROOT/'qualification_data/catalog.json').read_text()),reports)
    (a.out_dir/'selftest.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    junit(coverage,a.out_dir/'junit.xml')
    (a.out_dir/'qualification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    return 1 if overall=='failed' else 2 if overall=='incomplete' else 0
if __name__=='__main__':raise SystemExit(main())
