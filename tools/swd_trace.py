"""Describe debug-port configuration writes in an existing emulator report."""
import argparse,json
from pathlib import Path
ADDRESS=0x40010004
def inspect(report):
    writes=[]
    for event in report.get('first_4096_MMIO_events',[]):
        address=event.get('address',0)
        if isinstance(address,str):address=int(address,0)
        if event.get('op')!='write' or address!=ADDRESS or event.get('size')!=4:continue
        value=event.get('value',0)
        if isinstance(value,str):value=int(value,0)
        field=(value>>24)&7
        writes.append(dict(step=event.get('step'),value=hex(value),SWJ_CFG=field,
            meaning={0:'JTAG and SWD enabled',1:'JTAG and SWD enabled without NJTRST',
                2:'JTAG disabled; SWD enabled',4:'JTAG and SWD disabled'}.get(field,'reserved/no effect')))
    return dict(configuration_writes=writes,physical_connection_tested=False,
        note='SWJ_CFG is write-only; its hardware read value is undefined. These are observed writes, not register readback.',
        recovery_proven=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);a=p.parse_args()
    print(json.dumps(inspect(json.loads(a.report.read_text())),indent=2))
