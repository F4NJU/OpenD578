#!/usr/bin/env python3
"""Read-only search of Bluetooth identifiers in a *user-provided* image.

Does not decrypt, flash, contact the radio, or assume that a raw occurrence
means the original OEM firmware executes the corresponding command.
"""
import argparse
import hashlib
import json
from pathlib import Path

KEYWORDS = (
    'AT+VER?', 'AT+AGHF', 'ET12_AQQX', 'ELET_', 'B707_Audio',
    'BT01', 'Bluetooth', 'PTT Pair', 'PTT Hold', 'PTT Sleep',
    'PTT BatVolt', 'EXTERNAL BT MODE', 'ALL DATA CHECKING',
    'BT PTT Pair', 'RfBT Mic Gain', 'RfBT SPK Gain', 'H-BT Mic Gain',
    'D868BT', 'BHT_BOARD', 'AT+PAIR', 'AT+DISCON',
)


def scan(image: bytes, base: int, keywords=KEYWORDS):
    result=[]
    for term in keywords:
        for encoding,needle in (('ascii', term.encode('ascii')),('utf16le', term.encode('utf-16le'))):
            start=0
            while True:
                ix=image.find(needle,start)
                if ix<0: break
                # An unaligned word-reference search is only a hint, not a proven code XREF.
                address=base+ix
                p=address.to_bytes(4,'little',signed=False) if 0<=address<=0xffffffff else b''
                possible_refs=[]
                if p:
                    k=0
                    while len(possible_refs)<20:
                        j=image.find(p,k)
                        if j<0: break
                        if j%4==0:
                            possible_refs.append({'offset':j,'address':f'0x{base+j:08X}'})
                        k=j+1
                result.append({'token':term,'encoding':encoding,
                               'offset':ix,'address':f'0x{address:08X}',
                               'possible_literal_references':possible_refs,
                               'note':'Occurrence brute; non preuve de fonction executee ou de GPIO.'})
                start=ix+max(1,len(needle))
    return sorted(result,key=lambda h:(h['offset'],h['encoding']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('firmware',type=Path,help='Image binaire deja obtenue par l utilisateur, lecture seule')
    p.add_argument('--base',type=lambda x:int(x,0),default=0x08006000,
                   help='Adresse mappage supposee. Defaut V1.21 application 0x08006000.')
    p.add_argument('--json-out',type=Path,help='Optionnel, rapport JSON')
    a=p.parse_args()
    b=a.firmware.read_bytes()
    if len(b)>256*1024*1024: p.error('Taille image inattendue : au maximum 256 Mio pour cet outil')
    report={'file':a.firmware.name,'file_size':len(b),'sha256':hashlib.sha256(b).hexdigest(),
            'assumed_mapping_base':f'0x{a.base:08X}',
            'notices':['Adresses supposees : valider l en-tete et l adresse de chargement.',
                       'Pas une analyse de flot ni preuve de broche GPIO.'],
            'occurrences':scan(b,a.base)}
    if a.json_out: a.json_out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'{a.firmware.name}: SHA256 {report["sha256"]} ; {len(report["occurrences"])} occurrence(s).')
    for h in report['occurrences']:
        print(f'  {h["address"]} [{h["encoding"]}] {h["token"]} ; {len(h["possible_literal_references"])} xref(s) littérales candidates')
    if a.json_out: print('JSON:',a.json_out)

if __name__=='__main__': main()
