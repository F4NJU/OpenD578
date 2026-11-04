"""Observe the authentic OEM P4+dial startup, without forcing RAM mode flags."""
import argparse,json,struct,sys
from pathlib import Path
from bench_runner import BenchRunner
from native_gate import NativeGate
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,default=Path.home()/'Downloads/D578')
    parser.add_argument('--cache-dir',type=Path,default=Path(__file__).parent/'work/inputs')
    parser.add_argument('--out-dir',type=Path,default=Path('results/test_mode'))
    parser.add_argument('--instructions',type=int,default=90000000)
    parser.add_argument('--engine',choices=('native','python'),default='python')
    parser.add_argument('--auto-release',action='store_true',help='Release held keys when TEST MODE text is observed')
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    events=args.out_dir/'text_events.jsonl';events.write_text('')
    original_code=BenchRunner.on_code;original_gate=NativeGate.__init__;original_run=BenchRunner.run_chunks
    pcs=(0x080229CC,0x08038012,0x08038040)
    def on_code(self,uc,address,size,data):
        original_code(self,uc,address,size,data)
        if address not in pcs or self.stop:return
        event=dict(step=self.steps,pc=hex(address))
        if address==pcs[0]:
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
            if args.auto_release and event['text']=='TEST MODE' and not getattr(self,'test_keys_released',False):
                self.input_command(dict(control='RELEASE_ALL'));self.test_keys_released=True
        else:event['test_mode_render_path']=True
        if not hasattr(self,'test_mode_observations'):self.test_mode_observations=[]
        if len(self.test_mode_observations)<1024:self.test_mode_observations.append(event)
        with events.open('a') as handle:handle.write(json.dumps(event)+'\n')
    def gate(self,*a,**kw):
        original_gate(self,*a,**kw)
        for pc in pcs:self.trap(pc)
    def run(self,*a,**kw):
        result,ram=original_run(self,*a,**kw)
        result['test_mode_observations']=getattr(self,'test_mode_observations',[])
        result['test_mode_entry_observed']=any(e.get('text')=='TEST MODE' for e in result['test_mode_observations'])
        return result,ram
    BenchRunner.on_code=on_code;BenchRunner.run_chunks=run;NativeGate.__init__=gate
    saved=sys.argv
    sys.argv=['run_lcd.py','--source-dir',str(args.source_dir),'--cache-dir',str(args.cache_dir),
        '--out-dir',str(args.out_dir),'--instructions',str(args.instructions),'--engine',args.engine,
        '--initial-keys','P4,DIAL_PUSH','--diagnostic-snapshot']
    try:
        from run_lcd import main as run_lcd
        run_lcd()
    finally:
        sys.argv=saved;BenchRunner.on_code=original_code;BenchRunner.run_chunks=original_run;NativeGate.__init__=original_gate

if __name__=='__main__':main()
