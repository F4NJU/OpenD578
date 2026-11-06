#!/usr/bin/env python3
"""Analyse hors ligne des transactions serie RF D578.

Ne lit aucun port, ne pilote aucune broche. Le decodage de la paire 29/2A est
celui de l'AT1846S, a VERIFIER sur les quatre QA4818N.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict

IF_CANDIDATES_HZ = (38_550_000, 38_850_000)
QUANTUM_HALF_HZ = 125  # 62.5 Hz = 125 demi-Hz


def as_int(x):
    if isinstance(x, bool):
        raise ValueError('bool is not a register/address')
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        if not x.is_integer():
            raise ValueError('nonintegral numeric data')
        return int(x)
    if isinstance(x, str):
        s = x.strip()
        if s.startswith(('0x', '0X')):
            return int(s, 16)
        return int(s, 10)
    raise ValueError('invalid numeric field: '+repr(x))


def encode_frequency_hz(hz: int):
    hz = as_int(hz)
    if hz < 0:
        raise ValueError('negative frequency')
    # half-up integer quantisation to nearest 62.5 Hz
    word = (hz * 2 + 62) // 125
    if word >= (1 << 30):
        raise ValueError('30-bit AT1846S frequency overflow')
    return (word >> 16) & 0x3FFF, word & 0xFFFF


def decode_frequency_half_hz(high: int, low: int):
    hi = as_int(high)
    lo = as_int(low)
    if not (0 <= hi <= 0xFFFF and 0 <= lo <= 0xFFFF):
        raise ValueError('16-bit register expected')
    # Reg 29 bits [15:14] are *not* part of AT1846S 30-bit frequency.
    return (((hi & 0x3FFF) << 16) | lo) * QUANTUM_HALF_HZ


def pretty_freq(half_hz: int):
    whole = half_hz // 2
    return f'{whole}.5' if half_hz % 2 else str(whole)


def load_frames(path: Path):
    if path.suffix.lower() == '.csv':
        with path.open(newline='', encoding='utf-8-sig') as fh:
            return list(csv.DictReader(fh))
    if path.suffix.lower() == '.jsonl':
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    obj = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(obj, list):
        return obj
    for key in ('RF_control_spi', 'rf_spi', 'RF_SPI', 'rf', 'radio'):
        if key in obj and isinstance(obj[key], dict) and 'frames' in obj[key]:
            return obj[key]['frames']
    if isinstance(obj.get('frames'), list):
        return obj['frames']
    raise ValueError(f'{path}: aucune liste frames JSON trouvee')


def normalise(frame, idx):
    if not isinstance(frame, dict):
        raise ValueError(f'frame {idx}: object expected')
    # From bench/rf_spi.py : bank, page, register, direction, value, step
    bank = as_int(frame['bank'])
    if not 0 <= bank <= 3:
        raise ValueError(f'frame {idx}: bank outside 0..3')
    reg = as_int(frame.get('register', frame.get('address')))
    val = as_int(frame['value'])
    if not 0 <= reg < 128 or not 0 <= val <= 65535:
        raise ValueError(f'frame {idx}: register/value out of range')
    page = as_int(frame.get('page', 0))
    if not 0 <= page < 256:
        raise ValueError(f'frame {idx}: page out of range')
    direction = str(frame.get('direction', 'write')).lower()
    if direction not in ('read', 'write'):
        raise ValueError(f'frame {idx}: unsupported direction')
    return {'index': idx, 'step': frame.get('step', idx), 'bank': bank, 'page': page,
            'register': reg, 'value': val, 'direction': direction}


def classify(half_hz: int, displayed_hz: int | None, tolerance_hz: float = 200):
    # All arithmetic in half Hz, to keep 62.5 Hz exact.
    candidates=[]
    tol2=round(tolerance_hz*2)
    if displayed_hz is not None:
        d=displayed_hz * 2
        if abs(half_hz - d) <= tol2:
            candidates.append('RF directe (egalite frequence affichee)')
        for if_hz in IF_CANDIDATES_HZ:
            off=if_hz*2
            if abs(half_hz-(d+off)) <= tol2:
                candidates.append(f'OL injection haute +{if_hz/1e6:.3f} MHz')
            if d >= off and abs(half_hz-(d-off)) <= tol2:
                candidates.append(f'OL injection basse -{if_hz/1e6:.3f} MHz')
    for if_hz in IF_CANDIDATES_HZ:
        if abs(half_hz-if_hz*2)<=tol2:
            candidates.append(f'FI {if_hz/1e6:.3f} MHz (candidat reception IF)')
    return candidates or ['non classe; contexte/format/montage insuffisants']


def analyse(frames, displayed_hz=None, capture_name=None, provenance='non_verifiee'):
    regcache={}
    written=defaultdict(set)
    rows=[]
    counts=defaultdict(int)
    final_writes={}
    number_writes=defaultdict(int)
    command_timeline=[]
    bad=[]
    for i,raw in enumerate(frames):
        try:
            f=normalise(raw, i)
        except (KeyError, ValueError, TypeError) as err:
            bad.append({'index':i, 'error':str(err)})
            continue
        bank,page,reg,val=f['bank'],f['page'],f['register'],f['value']
        counts[bank]+=1
        if f['direction']!='write':
            continue
        key=f'{bank}:{page}:{reg:02X}'
        final_writes[key]=f'0x{val:04X}'
        number_writes[key]+=1
        if reg in (0x04,0x0F,0x15,0x24,0x29,0x2A,0x30,0x7F):
            sample={'step':f['step'],'bank':bank,'page':page,
                    'register':f'0x{reg:02X}', 'value':f'0x{val:04X}',
                    'interpretation':'AT1846S-CANDIDATE',
                    'note':'Not a validated QA4818N register function'}
            if reg==0x30 and page==0:
                sample['bits_AT1846S_only']={'xtal_26_family':bool(val & 0x4000),
                      'tx_on':bool(val & 0x40),'rx_on':bool(val & 0x20),
                      'power_on':bool(val & 0x04),'soft_reset':bool(val & 0x01)}
            if reg==0x04 and page==0:
                sample['bits_AT1846S_only']={'clock_24_to_28MHz':not bool(val&1)}
            command_timeline.append(sample)
        if reg in (0x29, 0x2A) and page==0:
            regcache[(bank,reg)]=val
            written[bank].add(reg)
            if written[bank] >= {0x29, 0x2A}:
                hi,lo=regcache[(bank,0x29)],regcache[(bank,0x2A)]
                freq=decode_frequency_half_hz(hi,lo)
                rows.append({'capture':capture_name, 'step': f['step'], 'bank': bank,
                             'high':'0x%04X'%hi,'low':'0x%04X'%lo,
                             'frequency_half_hz':freq,'frequency_hz':pretty_freq(freq),
                             'decoding':'AT1846S_29_2A_CANDIDATE',
                             'candidates':classify(freq,displayed_hz),
                             'warning':'Banque logique non attribuee a un boitier; frequence electrique non mesuree'})
        elif reg==0x7F:
            pass
    # Collapse consecutive unchanged register pairs; leave separate captures discrete.
    collapsed=[]
    for row in rows:
        if collapsed and (row['bank'],row['high'],row['low']) == (collapsed[-1]['bank'],collapsed[-1]['high'],collapsed[-1]['low']):
            collapsed[-1]['step_last']=row['step']
        else:
            collapsed.append(row)
    return {'capture':capture_name, 'display_hz':displayed_hz, 'provenance':provenance,
            'assumptions':['AT1846S register 29/2A format (QA4818N not confirmed)',
                           'SPI frames supplied are observations; synthetic simulator frames must be labelled',
                           'LO candidates are derived from IF 38.550 / 38.850 MHz; injection side unknown'],
            'banks_seen':{str(b):n for b,n in sorted(counts.items())},
            'frequency_events':collapsed, 'malformed_frames':bad,
            'written_final_registers':dict(sorted(final_writes.items())),
            'write_counts':dict(sorted(number_writes.items())),
            'critical_command_timeline':command_timeline,
            'incomplete_frequency_pairs':{str(b):['0x%02X'%reg for reg in sorted({0x29,0x2A}-seen)]
               for b,seen in sorted(written.items()) if seen != {0x29,0x2A}}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', nargs='?',type=Path,help='CSV / JSON / JSONL rf_spi.frames')
    p.add_argument('--display-hz',type=int,help='frequence affichee en Hz, si connue')
    p.add_argument('--capture-name',default='capture',help='nom de scenario, ex RX_A_145500')
    p.add_argument('--manifest',type=Path,help='JSON {captures:[{file,name,display_hz,mode}]}')
    p.add_argument('--out',type=Path,help='sauvegarder JSON du rapport')
    args=p.parse_args()
    if args.manifest:
        manifest=json.loads(args.manifest.read_text(encoding='utf8'))
        reports=[]
        for item in manifest['captures']:
            file=(args.manifest.parent / item['file']).resolve()
            obj=json.loads(file.read_text(encoding='utf8')) if file.suffix.lower()=='.json' else {}
            origin='SYNTHETIC_NOT_OEM' if isinstance(obj,dict) and obj.get('synthetic') is True else item.get('provenance','non_verifiee')
            rep=analyse(load_frames(file), item.get('display_hz'), item.get('name'),origin)
            rep['mode']=item.get('mode','unknown')
            reports.append(rep)
        result={'schema_version':1,'reports':reports,'comparison':compare_reports(reports)}
    else:
        if args.trace is None:
            p.error('trace or --manifest required')
        obj=json.loads(args.trace.read_text(encoding='utf8')) if args.trace.suffix.lower()=='.json' else {}
        origin='SYNTHETIC_NOT_OEM' if isinstance(obj,dict) and obj.get('synthetic') is True else 'non_verifiee'
        result=analyse(load_frames(args.trace),args.display_hz,args.capture_name,origin)
    rendered=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.out:
        args.out.write_text(rendered,encoding='utf8')
    else:
        print(rendered,end='')


def compare_reports(reports):
    perbank=defaultdict(list)
    for r in reports:
        if not r['frequency_events']:
            continue
        # only final state per bank of each capture is considered
        finals={}
        for ev in r['frequency_events']:
            finals[ev['bank']]=ev
        for bank,ev in sorted(finals.items()):
            perbank[bank].append({'capture':r['capture'],'mode':r.get('mode','unknown'), 'display_hz':r['display_hz'],
                                  'decoded_hz':ev['frequency_hz'],'candidates':ev['candidates']})
    diffs=[]
    for left,right in zip(reports,reports[1:]):
        a,b=left['written_final_registers'],right['written_final_registers']
        differences=[]
        for key in sorted(set(a)|set(b)):
            if a.get(key)==b.get(key):
                continue
            differences.append({'bank_page_register':key, 'before':a.get(key),
                                'after':b.get(key), 'missing_is_unknown':True})
        diffs.append({'from_capture':left['capture'],'to_capture':right['capture'],
                      'changed_or_unobserved_registers':differences,
                      'warning':'Un registre absent d une trace peut etre inchange et cache; absence n implique pas valeur 0.'})
    return {'banks':{str(b):observations for b,observations in sorted(perbank.items())},
            'adjacent_capture_diffs':diffs,
            'note':'Les correlations ne sont pas des preuves de continuites physiques ou de frequences RF mesurees.'}


if __name__ == '__main__':
    main()
