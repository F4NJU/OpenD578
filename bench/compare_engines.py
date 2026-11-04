"""Replay one OEM scenario with both engines and compare execution evidence."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def compare(reference,native):
    # Timings and paths are intentionally excluded; CPU/device state is not.
    fields=['firmware_sha256','steps','stop','ram_sha256','cpu_registers',
        'systick','systick_wraps','hardware_configuration','virtual_core_units',
        'remaining_scenario_events','application_running','delivered_exceptions',
        'timers','rtc','RF_control_spi','SCT3258_HPI','usart0','usart1','uart3','flash_cache']
    checks={key:key in reference and key in native and reference[key]==native[key] for key in fields}
    for key in ('raw_rgb_sha256','display_on','sleeping','command_crosscheck_mismatches','total_pixel_writes','write_edges','commands'):
        checks['LCD.'+key]=(key in reference.get('lcd',{}) and key in native.get('lcd',{}) and
            reference['lcd'][key]==native['lcd'][key])
    for key in ('NAND','Flash','gps_OEM','RX','FAN','power_observation'):
        checks['hardware.'+key]=(key in reference.get('hardware',{}) and key in native.get('hardware',{}) and
            reference['hardware'][key]==native['hardware'][key])
    differences=[key for key,value in checks.items() if not value]
    missing=[key for key in fields if key not in reference or key not in native]
    differences_in_irq=[]
    for index,(a,b) in enumerate(zip(reference.get('delivered_exceptions',[]),native.get('delivered_exceptions',[]))):
        if a!=b and len(differences_in_irq)<8:differences_in_irq.append(dict(index=index,reference=a,native=b))
    valid_stops=all(r.get('stop',{}).get('kind')=='instruction_budget' for r in (reference,native))
    verdict='incomplete' if missing or not valid_stops else 'identical_for_executed_scenario' if not differences else 'different'
    return dict(status=verdict,checks=checks,differences=differences,missing_fields=missing,
        first_IRQ_differences=differences_in_irq,
        physical_radio_certified=False,cycle_accuracy_established=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,default=Path.home()/'Downloads/D578')
    parser.add_argument('--cache-dir',type=Path,default=ROOT/'work/inputs')
    parser.add_argument('--out-dir',type=Path,default=ROOT/'results/engine_comparison')
    parser.add_argument('--instructions',type=int,default=500000)
    parser.add_argument('--scenario',type=Path);parser.add_argument('--gps',choices=('absent','fix','no_fix'),default='absent')
    parser.add_argument('--gps-rate',type=int,choices=(1,2,4),default=1)
    parser.add_argument('--microphone',action='store_true');parser.add_argument('--cold',action='store_true')
    args=parser.parse_args()
    if args.instructions<1:parser.error('instructions must be positive')
    args.out_dir.mkdir(parents=True,exist_ok=True);reports=[]
    for engine in ('python','native'):
        output=args.out_dir/engine
        command=[sys.executable,str(ROOT/'run_lcd.py'),'--engine',engine,'--source-dir',str(args.source_dir),
            '--cache-dir',str(args.cache_dir),'--out-dir',str(output),'--instructions',str(args.instructions),
            '--voltage','13.8','--gps',args.gps,'--gps-rate',str(args.gps_rate)]
        if not args.cold:command.append('--resume-ready')
        if args.scenario:command+=['--scenario',str(args.scenario)]
        if args.microphone:command.append('--microphone')
        process=subprocess.run(command,capture_output=True,text=True)
        if process.returncode:
            report=dict(status='incomplete',engine=engine,error=process.stderr[-3000:])
            (args.out_dir/'comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));return 2
        reports.append(json.loads((output/'resultat.json').read_text()))
    report=compare(*reports)
    (args.out_dir/'comparison.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='identical_for_executed_scenario' else 2 if report['status']=='incomplete' else 1

if __name__=='__main__':raise SystemExit(main())
