"""Observe OEM P4+dial startup, optionally with synthetic NAND permissions."""
import argparse,json,struct,sys
from pathlib import Path
from bench_runner import BenchRunner
from native_gate import NativeGate
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,default=Path.home()/'Downloads/D578')
    parser.add_argument('--cache-dir',type=Path,default=Path(__file__).parent/'work/inputs')
    parser.add_argument('--out-dir',type=Path,default=Path('results/test_mode'))
    parser.add_argument('--instructions',type=int,default=90000000)
    parser.add_argument('--engine',choices=('native','python'),default='native')
    parser.add_argument('--auto-release',action='store_true',help='Release held keys when TEST MODE text is observed')
    parser.add_argument('--virtual-full-test',action='store_true',
                        help='Enable service permissions in a volatile NAND fixture; original captures stay read-only')
    parser.add_argument('--stop-after-test-banner',action='store_true',
                        help='Stop after the native TEST MODE text drawing has returned')
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    events=args.out_dir/'text_events.jsonl';events.write_text('')
    original_code=BenchRunner.on_code;original_gate=NativeGate.__init__;original_run=BenchRunner.run_chunks
    pcs=(0x080229CC,0x08038012,0x08038040)
    gate_pcs=(0x08064816,0x08064828,0x0806482A,0x08064504)
    import run_lcd
    from oem_options import decode_options,enable_virtual_full_test
    original_nand=run_lcd.OverlayNand
    fixtures=[]
    if args.virtual_full_test:
        class ServiceOptionsNand(original_nand):
            def __init__(self,*a,**kw):
                super().__init__(*a,**kw)
                fixtures.append(enable_virtual_full_test(self))
        run_lcd.OverlayNand=ServiceOptionsNand
    def on_code(self,uc,address,size,data):
        original_code(self,uc,address,size,data)
        if self.stop:return
        if address==getattr(self,'test_banner_return',None):
            with events.open('a') as handle:
                handle.write(json.dumps(dict(step=self.steps,pc=hex(address),test_banner_draw_returned=True))+'\n')
            self.halt('stopped by simulator user',address,reason='native TEST MODE banner drawing completed')
            return
        if address not in pcs+gate_pcs:return
        event=dict(step=self.steps,pc=hex(address))
        if address in gate_pcs:
            event['service_permissions']=decode_options(bytes(uc.mem_read(0x20009872,14)))
        elif address==pcs[0]:
            sp=uc.reg_read(UC_ARM_REG_SP)
            if not 0x20000000<=sp<=0x20017FFC:return
            pointer=struct.unpack('<I',bytes(uc.mem_read(sp,4)))[0]
            if 0x08000000<=pointer<0x08300000:limit=0x08300000-pointer
            elif 0x20000000<=pointer<0x20018000:limit=0x20018000-pointer
            else:return
            value=bytes(uc.mem_read(pointer,min(96,limit))).split(b'\0')[0]
            if not value or not all(32<=v<127 or v in (10,13) for v in value):return
            event.update(text=value.decode(),pointer=hex(pointer),R0=uc.reg_read(UC_ARM_REG_R0),
                R1=uc.reg_read(UC_ARM_REG_R1),R2=uc.reg_read(UC_ARM_REG_R2))
            if args.stop_after_test_banner and event['text']=='TEST MODE':
                self.test_banner_return=uc.reg_read(UC_ARM_REG_LR)&~1
                if getattr(self,'native_gate',None):self.native_gate.trap(self.test_banner_return)
            if args.auto_release and event['text']=='TEST MODE' and not getattr(self,'test_keys_released',False):
                self.input_command(dict(control='RELEASE_ALL'));self.test_keys_released=True
        else:event['test_mode_render_path']=True
        if not hasattr(self,'test_mode_observations'):self.test_mode_observations=[]
        if len(self.test_mode_observations)<1024:self.test_mode_observations.append(event)
        with events.open('a') as handle:handle.write(json.dumps(event)+'\n')
    def gate(self,*a,**kw):
        original_gate(self,*a,**kw)
        for pc in pcs+gate_pcs:self.trap(pc)
    def run(self,*a,**kw):
        result,ram=original_run(self,*a,**kw)
        result['test_mode_observations']=getattr(self,'test_mode_observations',[])
        result['test_mode_entry_observed']=any(e.get('text')=='TEST MODE' for e in result['test_mode_observations'])
        result['test_mode_fixture']=fixtures[0] if fixtures else None
        return result,ram
    BenchRunner.on_code=on_code;BenchRunner.run_chunks=run;NativeGate.__init__=gate
    saved=sys.argv
    sys.argv=['run_lcd.py','--source-dir',str(args.source_dir),'--cache-dir',str(args.cache_dir),
        '--out-dir',str(args.out_dir),'--instructions',str(args.instructions),'--engine',args.engine,
        '--initial-keys','P4,DIAL_PUSH','--diagnostic-snapshot','--interactive']
    try:
        run_lcd.main()
    finally:
        sys.argv=saved;BenchRunner.on_code=original_code;BenchRunner.run_chunks=original_run;NativeGate.__init__=original_gate
        run_lcd.OverlayNand=original_nand

if __name__=='__main__':main()
