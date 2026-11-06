#!/usr/bin/env python3
"""Decode an *offline*, passive D578 UART text export; no serial port access.

Input lines: 'TX 41 54 ...' or '0.123 RX 0D 0A ...'.
Can also use --hex for one stream. Unknown traffic stays raw and explicitly unknown.
"""
import argparse
from pathlib import Path
import re

KNOWN = {
    'AT+VER?': 'Requete de version ET12',
    'AT+AGHF=0': 'Reglage AGHF brut : 0 (semantique non qualifiee)',
    'AT+AGHF=1': 'Reglage AGHF brut : 1 (semantique non qualifiee)',
    'AT+AGHF?': 'Lecture AGHF',
}

def parse_hex(s):
    words=s.strip().replace(',',' ').replace('0x','').split()
    if not words: return b''
    if any(not re.fullmatch('[0-9a-fA-F]{2}',x) for x in words):
        raise ValueError('Octets hex attendus : AA 55 0D ...')
    return bytes(int(x,16) for x in words)


def decode_payload(data):
    out=[]
    # Group by CRLF to preserve binary payloads not understood.
    parts=[]
    offset=0
    while offset<len(data):
        end=data.find(b'\r\n',offset)
        if end<0:
            parts.append((offset,data[offset:],False));break
        parts.append((offset,data[offset:end],True))
        offset=end+2
    for position,p,complete in parts:
        if not p and complete: continue
        value=p.decode('ascii','backslashreplace')
        if value in KNOWN:
            meaning=KNOWN[value]
        elif value.startswith('+VER:'):
            meaning='Reponse version declaree par le pair (identite physique non verifiee)'
        elif value in ('+AGHF:0','+AGHF:1'):
            meaning='Retour etat AGHF brut (sens physique non etabli)'
        else:
            meaning='NON DECODE (conserver les octets)'
        out.append({'offset':position,'value':value,'hex':p.hex(' '),
                    'complete_crlf':complete,'meaning':meaning})
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--hex',dest='bytes_hex')
    g.add_argument('--file',type=Path)
    args=ap.parse_args()
    if args.bytes_hex:
        streams=[('-',parse_hex(args.bytes_hex))]
    else:
        streams=[]
        for n,line in enumerate(args.file.read_text(encoding='utf-8').splitlines(),1):
            line=line.split('#',1)[0].strip()
            if not line: continue
            match=re.match(r'(?:(\d+(?:\.\d+)?)\s+)?(TX|RX)\s+(.+)$',line,re.I)
            if match is None: ap.error(f'ligne {n}: forme attendue [timestamp] TX|RX octets_hex')
            label=f'{match.group(1) or "-"} {match.group(2).upper()}'
            streams.append((label,parse_hex(match.group(3))))
    for label,raw in streams:
        print(f'[{label}] {len(raw)} octet(s)  {raw.hex(" ")}')
        for ev in decode_payload(raw):
            print(f'  +{ev["offset"]:04d} {ev["value"]!r}: {ev["meaning"]} '
                  f'({"CRLF" if ev["complete_crlf"] else "TRONQUE"})')

if __name__=='__main__':main()
