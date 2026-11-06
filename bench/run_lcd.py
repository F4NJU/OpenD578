#!/usr/bin/env python3
"""Prepare authenticated inputs and run the LCD-enabled D578 simulator."""
import argparse
import contextlib
import json
import sys
from pathlib import Path
from adc_dma import validate_profile
from bench_runner import BenchRunner as LcdRunner
from emulate_nand_v121 import CapturedNand
from nand_overlay import OverlayNand
from prepare_inputs import prepare, resolve_input, prepare_sct_reference, check_inputs, OEM_ARCHIVE
from uart_serial import BT_SHA
from PIL import Image
from full_flash import load_full_flash
from firmware_input import load_selected
from ready_session import load_ready

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=Path.home()/'Downloads'/'D578')
    parser.add_argument('--cache-dir', type=Path, default=ROOT/'work'/'inputs')
    parser.add_argument('--out-dir', type=Path, default=ROOT/'results'/'local')
    parser.add_argument('--bluetooth', choices=('absent','et12'), default='absent')
    parser.add_argument('--poison', type=lambda x:int(x,0), choices=(0xA5,0x5A), default=0xA5)
    parser.add_argument('--instructions', type=int, default=200_000_000)
    parser.add_argument('--idle-clock-scale',type=int,choices=(1,64,4096,65536),default=4096)
    parser.add_argument('--audit',action='store_true')
    parser.add_argument('--interactive',action='store_true')
    parser.add_argument('--control-stdin',action='store_true')
    parser.add_argument('--cdc-stdio',action='store_true',help='Send CDC status through stdout instead of a live JSON file')
    parser.add_argument('--no-native-lcd',action='store_true')
    parser.add_argument('--engine',choices=('native','python'),default='native')
    parser.add_argument('--trace',choices=('full','minimal'),default='minimal')
    parser.add_argument('--nand-read-only',action='store_true')
    parser.add_argument('--nand-state',type=Path,help='Persist virtual NAND pages separately from original captures')
    parser.add_argument('--without-power', action='store_true')
    parser.add_argument('--rtc-mode',choices=('retained','empty'),default='retained')
    parser.add_argument('--rtc-date',default='2026-11-04T12:00:00')
    parser.add_argument('--full-flash',type=Path)
    parser.add_argument('--resume-ready',action='store_true')
    parser.add_argument('--firmware',type=Path,help='Selected raw application CDD/bin or full 3MiB Flash; V1.21-compatible model')
    parser.add_argument('--entry',choices=('application','bootloader'),default='application')
    parser.add_argument('--gps',choices=('absent','fix','no_fix'),default='absent')
    parser.add_argument('--latitude',type=float,default=48)
    parser.add_argument('--longitude',type=float,default=2)
    parser.add_argument('--gps-utc',default='2026-11-04T12:00:00')
    parser.add_argument('--gps-rate',type=int,choices=(1,2,4),default=1)
    parser.add_argument('--microphone',action='store_true')
    parser.add_argument('--mic-lock',action='store_true')
    parser.add_argument('--initial-keys',default='')
    parser.add_argument('--scenario',type=Path)
    parser.add_argument('--voltage',type=float)
    parser.add_argument('--diagnostic-snapshot',action='store_true',help='Export a diagnostic state; not loaded automatically')
    parser.add_argument('--watch-ram',action='append',default=[],metavar='START:SIZE',
                        help='Record CPU and model writes/CPU reads within a SRAM range; repeatable')
    args = parser.parse_args()
    if args.instructions < 1:
        parser.error('--instructions must be positive')
    if args.resume_ready and args.rtc_mode=='empty':parser.error('Ready session requires retained RTC mode')
    if args.nand_state and args.nand_read_only:parser.error('NAND persistence requires an overlay')
    if args.nand_state and args.nand_state.exists() and args.resume_ready:parser.error('A persisted NAND requires application reset, not an old RAM recording')
    if args.resume_ready and (args.firmware or args.entry!='application'):parser.error('La reprise OEM ne peut pas valider un firmware sélectionné ni un reset bootloader')
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir/'hardware_events.jsonl').write_text('',encoding='utf-8')
    args.out_dir.joinpath('status.json').write_text(json.dumps(dict(running=True, steps=0,
        phase='Vérification des archives et des empreintes', pixels=0)), encoding='utf-8')
    check_inputs(args.source_dir, args.cache_dir, args.full_flash, args.bluetooth)
    firmware, nand_directory = prepare(args.source_dir, args.cache_dir, args.full_flash)
    sct_reference = prepare_sct_reference(args.source_dir, args.cache_dir)
    if args.bluetooth == 'et12':
        resolve_input(args.source_dir, args.cache_dir,
                      'B707_Audio_AGHF_ET12_QX-V10043.bin', 96170, BT_SHA, OEM_ARCHIVE)
    profile = validate_profile(json.loads((ROOT/'profiles'/'front_panel.json').read_text(encoding='utf-8')))
    runner = LcdRunner(firmware.read_bytes(), (CapturedNand if args.nand_read_only else OverlayNand)(nand_directory), args.poison,
        profile=profile, wake_once=not args.without_power, idle_clock_scale=args.idle_clock_scale,
        bluetooth=args.bluetooth, live_directory=args.out_dir,
        rtc_mode=args.rtc_mode,rtc_date=args.rtc_date,fast_mode=not args.audit)
    flash_path=args.full_flash or args.source_dir/'full_flash_pass1.bin'
    if not flash_path.is_file():
        raise ValueError('Full physical Flash capture missing: '+str(flash_path))
    load_selected(runner,flash_path,args.firmware,args.entry)
    runner.sct_hpi.load_reference(sct_reference)
    battery_file=args.out_dir/'pile_simulee.json'
    if args.rtc_mode=='retained' and battery_file.exists():
        saved=json.loads(battery_file.read_text(encoding='utf-8'))
        if saved.get('kind')!='synthetic_backup_domain':
            raise ValueError('Invalid simulated battery file')
        for name,registers in (('rtc',runner.backup.regs),('backup',runner.backup.backup)):
            values={int(k):v for k,v in saved[name].items()}
            if values.keys()!=registers.keys() or any(not isinstance(v,int) or not 0<=v<=65535 for v in values.values()):
                raise ValueError('Invalid simulated backup registers')
            registers.update(values)
    if args.resume_ready:load_ready(runner)
    if args.cdc_stdio:
        from cdc_channel import Publisher
        runner.cdc_sink=Publisher(sys.__stdout__)
    if args.nand_state and args.nand_state.exists():
        from nand_state import load
        runner.nand_checkpoint=load(runner.nand,args.nand_state)
    runner.interactive_mode=args.interactive and not args.audit
    if runner.interactive_mode:runner.enable_serial_time()
    runner.disable_native_lcd=args.no_native_lcd
    runner.last_control_id=None
    if args.control_stdin:
        from interactive_runtime import ControlInbox
        runner.control_inbox=ControlInbox(sys.stdin)
    runner.fast_mode=not args.audit
    runner.idle_clock_scale=args.idle_clock_scale
    runner.arm_lab()
    runner.trace_enabled=args.trace=='full'
    if args.initial_keys:runner.input_command(dict(control='KEY_SET',keys=args.initial_keys.split(',')))
    if args.microphone:runner.input_command(dict(control='MIC_CONNECT',connected=True))
    if args.mic_lock:runner.input_command(dict(control='MIC_LOCK',locked=True))
    if args.gps!='absent':runner.input_command(dict(control='GPS',mode=args.gps,latitude=args.latitude,longitude=args.longitude,utc=args.gps_utc,hertz=args.gps_rate))
    if args.voltage is not None:runner.voltage_sample(args.voltage)
    if args.scenario:runner.load_scenario(args.scenario)
    if args.watch_ram:
        from memory_watch import MemoryWatch,parse_range
        runner.memory_watch=MemoryWatch(runner,[parse_range(value) for value in args.watch_ram])
    if args.engine=='native' and not args.audit:
        from native_gate import NativeGate
        NativeGate(runner)
    with (args.out_dir/'execution.log').open('w', encoding='utf-8') as log:
        with contextlib.redirect_stdout(log):
            result, state = runner.run_chunks(runner.steps+args.instructions)
    from bench_version import VERSION
    from usb_cdc_runtime import final_snapshot
    final_snapshot(runner)
    result['simulator_version']=VERSION
    result['interactive_mode']=runner.interactive_mode
    result['observation_profile']=runner.observation_profile
    result['remaining_scenario_events']=len(runner.scenario)
    result['application_running']=bytes(runner.cpu.mem_read(0x20001542,1))==b'\x01'
    from unicorn import arm_const
    names=['R'+str(i) for i in range(13)]+['SP','LR','PC','XPSR','MSP','PSP','CONTROL','PRIMASK','BASEPRI','FAULTMASK']
    result['cpu_registers']={name:hex(runner.cpu.reg_read(getattr(arm_const,'UC_ARM_REG_'+name))) for name in names}
    if getattr(runner,'memory_watch',None):result['memory_watch']=runner.memory_watch.describe()
    result['qualification']=dict(status='incomplete' if getattr(runner,'firmware_selection',{}).get('experimental',False) or result['stop']['kind'] not in ('instruction_budget','stopped by simulator user') else 'observed scenario only',
        firmware_observation_profile_qualified=not getattr(runner,'firmware_selection',{}).get('experimental',False),
        physical_radio_certified=False,trace_mode=args.trace,
        missing_models=['RF waveforms and calibrated PA power','DSP/AMBE and DMR reception','APRS modulation DMA'])
    if getattr(runner,'native_gate',None):result['execution_engine']=runner.native_gate.describe()
    if args.nand_state:
        from nand_state import save
        result['NAND_persistence']=save(runner.nand,args.nand_state)
    (args.out_dir/'resultat.json').write_text(json.dumps(result, indent=None if runner.interactive_mode else 2, ensure_ascii=False),encoding='utf-8')
    (args.out_dir/'resultat.sram.bin').write_bytes(state)
    battery_file.write_text(json.dumps(dict(kind='synthetic_backup_domain',
        rtc=runner.backup.regs,backup=runner.backup.backup),indent=2),encoding='utf-8')
    runner.lcd.frame().transpose(Image.Transpose.TRANSPOSE).save(args.out_dir/'lcd_paysage.png')
    if args.diagnostic_snapshot:
        from ready_session import export_ready
        digest=export_ready(runner,args.out_dir/'diagnostic_state.pkl.gz')
        (args.out_dir/'diagnostic_state.sha256').write_text(digest,encoding='ascii')
    print(json.dumps(dict(stop=result['stop'], pixels=result['lcd']['total_pixel_writes'],
                         NAND_buffers=len(result['verified_RAM_reads'])), ensure_ascii=False))


if __name__ == '__main__':
    main()
