"""Portable NAND overlay checkpoint, bound to its immutable backing capture."""
import hashlib,json,os,struct
from pathlib import Path

MAGIC=b'D578NAND1\n'
MAX_PAGES=131072
PAGE_BYTES=2112


def save(nand,path):
    path=Path(path);pages=nand.overlay
    payload=b''.join(struct.pack('<I',row)+bytes(data) for row,data in sorted(pages.items()))
    metadata=dict(schema=1,sources=nand.sources,pages=len(pages),payload_SHA256=hashlib.sha256(payload).hexdigest())
    header=json.dumps(metadata,sort_keys=True).encode()
    temporary=path.with_suffix(path.suffix+'.part');path.parent.mkdir(parents=True,exist_ok=True)
    with temporary.open('wb') as stream:
        stream.write(MAGIC+struct.pack('<I',len(header))+header+payload);stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)
    return dict(saved=True,pages=len(pages),path=str(path),payload_SHA256=metadata['payload_SHA256'])


def load(nand,path):
    path=Path(path)
    if path.stat().st_size>MAX_PAGES*(PAGE_BYTES+4)+65536:raise ValueError('NAND checkpoint too large')
    with path.open('rb') as stream:
        if stream.read(len(MAGIC))!=MAGIC:raise ValueError('Invalid NAND checkpoint magic')
        raw=stream.read(4)
        if len(raw)!=4:raise ValueError('Truncated NAND checkpoint header')
        count=struct.unpack('<I',raw)[0]
        if not 1<=count<=65536:raise ValueError('Invalid NAND checkpoint metadata length')
        meta=json.loads(stream.read(count));payload=stream.read()
    if not isinstance(meta,dict) or meta.get('schema')!=1 or meta.get('sources')!=nand.sources:raise ValueError('NAND checkpoint belongs to a different backing image')
    count=meta.get('pages')
    if type(count) is not int or not 0<=count<=MAX_PAGES or len(payload)!=count*(PAGE_BYTES+4):raise ValueError('Invalid NAND checkpoint page count')
    if hashlib.sha256(payload).hexdigest()!=meta.get('payload_SHA256'):raise ValueError('NAND checkpoint checksum mismatch')
    pages={}
    for offset in range(0,len(payload),PAGE_BYTES+4):
        row=struct.unpack_from('<I',payload,offset)[0]
        if row>=MAX_PAGES or row in pages:raise ValueError('Duplicate or out-of-range NAND checkpoint page')
        pages[row]=payload[offset+4:offset+4+PAGE_BYTES]
    nand.overlay=pages;nand.cache=None;nand.cached_page=None
    return dict(loaded=True,pages=count,path=str(path),payload_SHA256=meta['payload_SHA256'])
