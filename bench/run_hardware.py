#!/usr/bin/env python3
"""Run any compatible raw Cortex-M4 image against the known D578 board model."""
import argparse,json
from pathlib import Path
from hardware_runner import HardwareRunner
from adc_dma import validate_profile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware',type=Path)
    parser.add_argument('--load-address',type=lambda n:int(n,0))
    parser.add_argument('--vector-address',type=lambda n:int(n,0))
    parser.add_argument('--instructions',type=int,default=100000)
    parser.add_argument('--out-dir',type=Path,default=Path('results/hardware'))
    parser.add_argument('--nand-dir',type=Path,help='Optional authenticated physical capture; default is synthetic erased NAND')
    parser.add_argument('--nand-state',type=Path)
    parser.add_argument('--sct-boot',type=Path,help='Explicit DSP bootstrap expected by this hardware profile; no OEM code address')
    parser.add_argument('--watch-ram',action='append',default=[],metavar='START:SIZE')
    parser.add_argument('--carrier',choices=('absent','match','mismatch','no_tone'),default='absent')
    parser.add_argument('--engine',choices=('native','python'),default='native')
    parser.add_argument('--control-stdin',action='store_true')
    parser.add_argument('--cdc-stdio',action='store_true')
    parser.add_argument('--initial-keys',default='')
    parser.add_argument('--trace',action='store_true')
    parser.add_argument('--coverage',action='store_true')
    args=parser.parse_args()
    if args.instructions<1:parser.error('instructions must be positive')
    profile=validate_profile(json.loads(Path(__file__).with_name('profiles').joinpath('front_panel.json').read_text()))
    nand=None
    if args.nand_dir:
        from nand_overlay import OverlayNand
        nand=OverlayNand(args.nand_dir)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    from board_image import inspect_board_image,inspect_upload
    if args.load_address is None and args.vector_address is None:
        meta=inspect_upload(args.firmware);image=args.firmware.read_bytes()
    else:image,meta=inspect_board_image(args.firmware,args.load_address,args.vector_address)
    runner=HardwareRunner(image,load_address=meta['load_address'],vector_address=meta['vector_address'],nand=nand,profile=profile,
        live_directory=args.out_dir,sct_boot=args.sct_boot.read_bytes() if args.sct_boot else None)
    runner.trace_enabled=args.trace
    if args.cdc_stdio:
        import sys
        from cdc_channel import Publisher
        runner.cdc_sink=Publisher(sys.__stdout__)
    if args.nand_state and args.nand_state.exists():
        from nand_state import load
        runner.nand_checkpoint=load(runner.nand,args.nand_state)
    if args.control_stdin:
        import sys
        from interactive_runtime import ControlInbox
        runner.control_inbox=ControlInbox(sys.stdin)
    if args.initial_keys:runner.input_command(dict(control='KEY_SET',keys=args.initial_keys.split(',')))
    runner.input_command(dict(control='RF_RX',bank=0,carrier=args.carrier!='absent',
        ctcss=args.carrier if args.carrier in ('match','mismatch') else 'absent'))
    if args.watch_ram:
        from memory_watch import MemoryWatch,parse_range
        runner.memory_watch=MemoryWatch(runner,[parse_range(v) for v in args.watch_ram])
    if args.coverage:
        from execution_coverage import BlockCoverage
        runner.coverage=BlockCoverage(runner.cpu)
    if args.engine=='native':runner.enable_native()
    result,ram=runner.run_hardware(args.instructions,wait_for_input=args.control_stdin)
    from usb_cdc_runtime import final_snapshot
    final_snapshot(runner)
    if args.nand_state:
        from nand_state import save
        result['NAND_persistence']=save(runner.nand,args.nand_state)
    (args.out_dir/'resultat.json').write_text(json.dumps(result,indent=2))
    (args.out_dir/'ram.bin').write_bytes(ram)
    print(json.dumps(dict(mode='hardware',stop=result['stop'],steps=result['steps'],pixels=result['lcd']['total_pixel_writes'])))
    return 0 if result['stop']['category'] in ('control','waiting','reset_requested') else 2

if __name__=='__main__':raise SystemExit(main())
