"""Conservative MCU call/literal candidates for systematic driver review.

Halfword scanning also sees data. Candidates are not recovered functions,
confirmed control flow, or proof that a peripheral is exercised.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from collections import Counter
from board_image import inspect_board_image

REGIONS=[('timers',0x40000000,0x40002000),('RTC',0x40002800,0x40002C00),
 ('watchdogs',0x40002C00,0x40003400),('UART/SPI/I2C',0x40003800,0x40005C00),
 ('USB/BKP',0x40005C00,0x40007000),('PMU/DAC',0x40007000,0x40007800),
 ('GPIO/AFIO/EXTI',0x40010000,0x40012400),('ADC',0x40012400,0x40013000),
 ('USART0/SPI0',0x40013000,0x40014000),('DMA',0x40020000,0x40020800),
 ('RCU',0x40021000,0x40021400),('FMC',0x40022000,0x40022400),
 ('peripheral_bitband',0x42000000,0x44000000),('Cortex/NVIC',0xE000E000,0xE0010000)]


def inventory(data,base,vector_address):
    entries={};calls=[];literal_counts=Counter();literal_sites=[]
    def entry(address,reason):entries.setdefault(address,set()).add(reason)
    vector_offset=vector_address-base
    for i in range(1,min(80,(len(data)-vector_offset)//4)):
        word=struct.unpack_from('<I',data,vector_offset+4*i)[0]
        if word&1 and base<=word&~1<base+len(data):entry(word&~1,'vector '+str(i))
    for offset in range(0,len(data)-3,2):
        first,second=struct.unpack_from('<HH',data,offset)
        if first&0xF800==0xF000 and second&0xD000==0xD000:
            sign=(first>>10)&1;i1=1^((second>>13)&1)^sign;i2=1^((second>>11)&1)^sign
            immediate=(sign<<24)|(i1<<23)|(i2<<22)|((first&1023)<<12)|((second&2047)<<1)
            if sign:immediate-=1<<25
            target=base+offset+4+immediate
            if base<=target<base+len(data):
                entry(target,'direct BL candidate');calls.append(dict(site=hex(base+offset),target=hex(target)))
        if offset%4==0:
            value=struct.unpack_from('<I',data,offset)[0]
            for name,start,end in REGIONS:
                if start<=value<end:
                    literal_counts[name]+=1;literal_sites.append(dict(site=hex(base+offset),value=hex(value),region=name));break
    return dict(image_sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),load_address=hex(base),
        scope='Static candidates, including possible data; not a complete disassembly or function analysis',
        candidate_entries=[dict(address=hex(a),reasons=sorted(reasons)) for a,reasons in sorted(entries.items())],
        direct_BL_candidates=calls,MMIO_literal_counts=dict(literal_counts),MMIO_literal_candidates=literal_sites,
        unresolved=['indirect calls','TBB/TBH dispatch','computed MMIO addresses','code/data separation','component internal firmware execution'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('firmware',type=Path)
    p.add_argument('--load-address',type=lambda n:int(n,0));p.add_argument('--vector-address',type=lambda n:int(n,0))
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    data,meta=inspect_board_image(a.firmware,a.load_address,a.vector_address)
    result=inventory(data,meta['load_address'],meta['vector_address'])
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(candidate_entries=len(result['candidate_entries']),MMIO_literal_counts=result['MMIO_literal_counts'])))


if __name__=='__main__':main()
