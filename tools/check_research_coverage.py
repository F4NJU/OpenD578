#!/usr/bin/env python3
"""Validate documentation coverage (not the physical truth of source claims)."""
from pathlib import Path
import csv, json, sys
ROOT=Path(__file__).resolve().parents[1]
RF=ROOT/'docs/external/radiofoundry'
B=ROOT/'docs/external/db1ig'
assert RF.is_dir() and B.is_dir()
with (RF/'AUDIT_AFFIRMATIONS.csv').open(encoding='utf-8', newline='') as f:
    claims=list(csv.DictReader(f))
assert len(claims)>=100, f"Only {len(claims)} RadioFoundry entries"
assert len({r['id'] for r in claims})==len(claims), 'Duplicate claim IDs'
assert {'1','2.1','2.2','2.3','2.4','2.5','3','4.1','4.2','4.3','4.4','4.5','5','6'} <= {r['section'] for r in claims}
for r in claims:
    assert r['source']=='https://radiofoundry.org/docs/spec/hardware-anytone'
    assert (ROOT/r['document_OpenD578']).is_file(),r
    for k in ('apport','statut','commentaire'): assert r[k].strip(),r
original=list(csv.DictReader((B/'MATRICE_60_THEMES.csv').open(encoding='utf-8',newline='')))
assert len(original)==60
need={r['id'] for r in original if r['statut']=='RESUME_A_DEVELOPPER'}
files=list((B/'approfondissements').glob('VK578-*.md'))
found={f.name[:8] for f in files}
assert len(need)==21 and found==need,(need-found, found-need)
for f in files:
  assert len(f.read_text(encoding='utf-8'))>1200,f
for n in ('INDEX.md','AUDIT_AFFIRMATIONS.md','SCT3258_CHAND_BOOT_ET_CODEC.md','GPIO_868_VS_578.md','CALIBRATIONS_ET_VARIANTES.md','FIRMWARE_MISE_A_JOUR.md'):
    assert (RF/n).is_file()
for p in (ROOT/'hardware/models').glob('*.json'):
    model=json.loads(p.read_text())
    for node in model['nodes']:
        for doc in node['docs']:assert (ROOT/doc).is_file(),f'{p.name}: {doc}'
print(f'PASS: {len(claims)} RadioFoundry claims; {len(files)}/21 deeper articles; {len(original)} historical topics preserved; model documents resolve')
