"""Index feature clues and unresolved routine candidates without claiming completeness."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from firmware_inventory import inventory
from board_image import inspect_board_image
ROOT=Path(__file__).resolve().parent


def discover(data,base,vector,catalog):
    static=inventory(data,base,vector)
    strings=[(base+m.start(),m.group()[:-1].decode('ascii')) for m in re.finditer(rb'[\x20-\x7e]{4,80}\x00',data)]
    pointers={}
    string_addresses={a for a,_ in strings}
    for offset in range(0,len(data)-3,4):
        target=struct.unpack_from('<I',data,offset)[0]
        if target in string_addresses:pointers.setdefault(target,[]).append(hex(base+offset))
    features=[]
    for feature in catalog['features']:
        key=feature['keyword'].casefold()
        matches=[dict(address=hex(a),label=text,aligned_pointer_candidates=pointers.get(a,[]))
                 for a,text in strings if key in text.casefold()]
        features.append(dict(id=feature['id'],string_candidates=matches[:20],matching_strings=len(matches),
            presence_proven=False,reason='String/pointer presence does not establish reachability, variant support, or hardware behavior'))
    return dict(schema_version=1,image_sha256=hashlib.sha256(data).hexdigest(),load_address=hex(base),
        scope='Static halfword/string/literal candidates. Not a complete disassembly, call graph or function inventory.',
        complete=False,all_functions_understood=False,physical_radio_certified=False,
        candidate_entries=static['candidate_entries'],MMIO_literal_counts=static['MMIO_literal_counts'],
        features=features,unresolved=static['unresolved']+['shared PRO/PLUS resources','disabled menu branches','opaque DSP and Bluetooth firmware','unmapped candidates not linked to a catalog feature'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('firmware',type=Path)
    p.add_argument('--catalog',type=Path,default=ROOT/'qualification_data/catalog.json');p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();data,meta=inspect_board_image(a.firmware)
    result=discover(data,meta['load_address'],meta['vector_address'],json.loads(a.catalog.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(candidate_entries=len(result['candidate_entries']),features_with_string_candidates=sum(bool(f['matching_strings']) for f in result['features']),complete=False)))
if __name__=='__main__':main()
