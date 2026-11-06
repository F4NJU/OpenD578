"""Locate and decode USB CDC descriptors in a local Flash image; never write it."""
import argparse,hashlib,json
from pathlib import Path

def inspect(data,base=0x08000000):
    devices=[];configs=[]
    for offset in range(len(data)-18):
        if data[offset:offset+4]==b'\x12\x01\x00\x02':
            d=data[offset:offset+18]
            if d[7] not in (8,16,32,64) or not d[17]:continue
            devices.append(dict(address=hex(base+offset),device_class=d[4],EP0_packet_bytes=d[7],VID=f'{int.from_bytes(d[8:10],"little"):04X}',PID=f'{int.from_bytes(d[10:12],"little"):04X}',configurations=d[17]))
        if data[offset:offset+2]!=b'\x09\x02':continue
        total=int.from_bytes(data[offset+2:offset+4],'little')
        if not 9<=total<=4096 or offset+total>len(data):continue
        at=offset;descriptors=[];valid=True
        while at<offset+total:
            size=data[at]
            if size<2 or at+size>offset+total:valid=False;break
            d=data[at:at+size];kind=d[1]
            if kind==4 and size==9:descriptors.append(dict(type='interface',number=d[2],alternate=d[3],class_code=d[5],subclass=d[6],protocol=d[7]))
            elif kind==5 and size==7:descriptors.append(dict(type='endpoint',address=f'0x{d[2]:02X}',direction='IN' if d[2]&128 else 'OUT',transfer={0:'control',1:'isochronous',2:'bulk',3:'interrupt'}[d[3]&3],max_packet_bytes=int.from_bytes(d[4:6],'little')&2047,interval=d[6]))
            at+=size
        if valid and any(d.get('class_code')==2 for d in descriptors) and any(d.get('class_code')==10 for d in descriptors):
            configs.append(dict(address=hex(base+offset),length=total,interfaces=data[offset+4],descriptors=descriptors))
    return dict(image_SHA256=hashlib.sha256(data).hexdigest(),device_descriptors=devices,CDC_configurations=configs,qualification='static descriptors only; runtime enumeration, CPS and firmware transfers not tested')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);p.add_argument('--base',type=lambda n:int(n,0),default=0x08000000);p.add_argument('--output',type=Path)
    a=p.parse_args();result=json.dumps(inspect(a.image.read_bytes(),a.base),indent=2)
    if a.output:a.output.write_text(result+'\n')
    else:print(result)
