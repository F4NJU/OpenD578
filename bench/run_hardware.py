#!/usr/bin/env python3
"""Run any compatible raw Cortex-M4 image against the known D578 board model."""
import argparse,json
from pathlib import Path
from hardware_runner import HardwareRunner
from adc_dma import validate_profile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware',type=Path)
    parser.add_argument('--load-address',type=lambda n:int(n,0),default=0x08006000)
    parser.add_argument('--instructions',type=int,default=100000)
    parser.add_argument('--out-dir',type=Path,default=Path('results/hardware'))
    parser.add_argument('--nand-dir',type=Path,help='Optional authenticated physical capture; default is synthetic erased NAND')
    parser.add_argument('--sct-boot',type=Path,help='Explicit DSP bootstrap expected by this hardware profile; no OEM code address')
    parser.add_argument('--watch-ram',action='append',default=[],metavar='START:SIZE')
    parser.add_argument('--carrier',choices=('absent','match','mismatch','no_tone'),default='absent')
    args=parser.parse_args()
    if args.instructions<1:parser.error('instructions must be positive')
    profile=validate_profile(json.loads(Path(__file__).with_name('profiles').joinpath('front_panel.json').read_text()))
    nand=None
    if args.nand_dir:
        from nand_overlay import OverlayNand
        nand=OverlayNand(args.nand_dir)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    runner=HardwareRunner(args.firmware.read_bytes(),load_address=args.load_address,nand=nand,profile=profile,
        live_directory=args.out_dir,sct_boot=args.sct_boot.read_bytes() if args.sct_boot else None)
    runner.input_command(dict(control='RF_RX',bank=0,carrier=args.carrier!='absent',
        ctcss=args.carrier if args.carrier in ('match','mismatch') else 'absent'))
    if args.watch_ram:
        from memory_watch import MemoryWatch,parse_range
        runner.memory_watch=MemoryWatch(runner,[parse_range(v) for v in args.watch_ram])
    result,ram=runner.run_hardware(args.instructions)
    (args.out_dir/'resultat.json').write_text(json.dumps(result,indent=2))
    (args.out_dir/'ram.bin').write_bytes(ram)
    print(json.dumps(dict(mode='hardware',stop=result['stop'],steps=result['steps'],pixels=result['lcd']['total_pixel_writes'])))
    return 0 if result['stop']['kind']=='instruction_budget' else 2

if __name__=='__main__':raise SystemExit(main())
