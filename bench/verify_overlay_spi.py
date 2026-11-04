"""Verify erase/program by actual single/dual SPI bits, without changing dumps."""
import argparse,json,hashlib
from pathlib import Path
from nand_overlay import OverlayNand
from verify_spi_wire import HostWire
from emulate_clock_v121 import StopModel


def verify(directory):
    n=OverlayNand(directory)
    w=HostWire(n)
    row=19008
    original=n.page_image(row)
    before={name:hashlib.sha256(data).hexdigest() for name,data in n.images.items()}
    checks=[]
    try:
        w.transaction(bytes([0xD8])+row.to_bytes(3,'big'))
        raise AssertionError('Erase without WEL accepted')
    except StopModel as error:
        assert 'WEL' in str(error)
        n.cs=1
        w.levels|=0x100
    checks.append('erase_requires_WEL')
    w.transaction(bytes.fromhex('1f a0 00'))
    w.transaction(b'\x06')
    w.transaction(bytes([0xD8])+row.to_bytes(3,'big'))
    assert len(n.overlay)==64 and all(v==b'\xFF'*2112 for v in n.overlay.values())
    checks.append('erase_exactly_64_pages_in_overlay')
    status=w.transaction(bytes.fromhex('0f c0'),1)[0]
    assert status&1 and not status&2
    checks.append('erase_busy_and_WEL_clear')
    payload=bytes(range(256))*8
    w.transaction(b'\x02\x00\x00'+payload)
    w.transaction(b'\x84\x08\x00'+b'\xF0'*64)
    w.transaction(b'\x06')
    w.transaction(b'\x10'+row.to_bytes(3,'big'))
    w.transaction(b'\x13'+row.to_bytes(3,'big'))
    expected=payload+b'\xF0'*64
    assert w.transaction(bytes.fromhex('03 00 00 00'),2112)==expected
    assert w.transaction(bytes.fromhex('3b 00 00 00'),2112,True)==expected
    checks.append('program_load_random_execute_single_dual_readback')
    w.transaction(b'\x02\x00\x00'+b'\xFF'*16)
    w.transaction(b'\x06')
    w.transaction(b'\x10'+row.to_bytes(3,'big'))
    assert n.page_image(row)==expected
    checks.append('programming_ones_preserves_existing_zero_bits')
    assert n.images['nand_main_256MiB.bin'][row*2048:(row+1)*2048]==original[:2048]
    assert before=={name:hashlib.sha256(data).hexdigest() for name,data in n.images.items()}
    checks.append('all_three_original_dumps_hashes_unchanged')
    return dict(passed=True,checks=checks,count=len(checks),overlay_pages=len(n.overlay),source_files_modified=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('nand_directory',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    result=verify(a.nand_directory)
    a.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
