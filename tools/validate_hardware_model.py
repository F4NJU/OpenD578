#!/usr/bin/env python3
"""Validate documented board models, referenced evidence, and annotated photos."""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
STATUS={'physical','oem_trace','emulator','datasheet','hypothesis','unknown'}
GROUPS={'facade','logique','peripheriques','radio'}


def check():
    errors=[]
    models=[]
    for path in sorted((ROOT/'hardware/models').glob('*.json')):
        try:
            model=json.loads(path.read_text(encoding='utf-8'))
        except (OSError,ValueError) as ex:
            errors.append(f'{path}: {ex}')
            continue
        vid=model.get('id')
        if not vid or path.stem != vid:
            errors.append(f'{path}: id must be file stem')
        if not model.get('title') or not model.get('version'):
            errors.append(f'{path}: title and version required')
        nodes=model.get('nodes',[])
        edges=model.get('edges',[])
        ids=set()
        eids=set()
        for n in nodes:
            nid=n.get('id')
            if not nid or nid in ids:
                errors.append(f'{path}: invalid/repeated node id {nid!r}')
            ids.add(nid)
            if n.get('group') not in GROUPS:
                errors.append(f'{path}: node {nid} invalid group')
            if n.get('confidence') not in ('identified','partial','candidate'):
                errors.append(f'{path}: node {nid} has no confidence')
            for field in ('x','y','w','h'):
                if not isinstance(n.get(field), (int,float)) or n[field]<0:
                    errors.append(f'{path}: node {nid} bad coordinate {field}')
            for doc in n.get('docs',[]):
                if not (ROOT/doc).is_file():
                    errors.append(f'{path}: node {nid} missing doc {doc}')
        for e in edges:
            eid=e.get('id')
            if not eid or eid in eids:
                errors.append(f'{path}: invalid/repeated edge id {eid!r}')
            eids.add(eid)
            if e.get('source') not in ids or e.get('target') not in ids:
                errors.append(f'{path}: edge {eid} unknown endpoint')
            if e.get('status') not in STATUS:
                errors.append(f'{path}: edge {eid} unknown status')
            if not e.get('details') or not e.get('label'):
                errors.append(f'{path}: edge {eid} missing evidence note/label')
            for p in e.get('pins',[]):
                if p.get('status') not in STATUS:
                    errors.append(f'{path}: edge {eid} pin missing status')
                if not p.get('from_pin') or not p.get('to_pin'):
                    errors.append(f'{path}: edge {eid} invalid pin pair')
            if e.get('status') == 'unknown' and e.get('pins'):
                errors.append(f'{path}: edge {eid} unknown, but declares pins')
            for doc in e.get('docs',[]):
                if not (ROOT/doc).is_file():
                    errors.append(f'{path}: edge {eid} missing doc {doc}')
        photos=ROOT/'hardware/photos'/vid/'manifest.json'
        if not photos.is_file():
            errors.append(f'{path}: missing photo manifest')
        else:
            try:
                contents=json.loads(photos.read_text(encoding='utf-8'))
                for p in contents.get('photos',[]):
                    ref=p.get('file','')
                    file=(photos.parent/ref).resolve()
                    if photos.parent.resolve() not in file.parents or not file.is_file():
                        errors.append(f'{photos}: missing/invalid photo {ref}')
                    for hotspot in p.get('hotspots',[]):
                        if hotspot.get('node') not in ids:
                            errors.append(f'{photos}: unknown hotspot node {hotspot.get("node")}')
                        for k in ('x','y','w','h'):
                            v=hotspot.get(k)
                            if not isinstance(v,(int,float)) or not (0<=v<=100):
                                errors.append(f'{photos}: hotspot {k} must be percent 0..100')
            except (OSError, ValueError) as ex:
                errors.append(f'{photos}: {ex}')
        models.append(model)
    if not models:
        errors.append('No hardware model found')
    if errors:
        print('\n'.join('ERROR: '+x for x in errors),file=sys.stderr)
        return False
    print('OK:', len(models),'model(s);',sum(len(m['nodes']) for m in models),'components;',sum(len(m['edges']) for m in models),'connections')
    return True

if __name__=='__main__':
    sys.exit(0 if check() else 1)
