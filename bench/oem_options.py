"""Read V1.21 service permissions; optionally create an in-memory test fixture.

No function in this module writes a capture or communicates with a radio.
The NAND layout is from VK7ZJA's D578 map, cross-checked against AT Options v8
and the captured PRO GD32 V1.21 instructions at 0x08064816.
"""
import argparse
import hashlib
import json
from pathlib import Path

LOCAL_INFO_BLOCKS = (0x02FA0000, 0x02FC0000)
LOCAL_INFO_RAM = 0x20009872
CAPTURE_SIZE = 256 * 1024 * 1024
CAPTURE_SHA256 = '329d22165d234bf0df043e62af11397dea96327925b9db18f3c354230ff40945'


def decode_options(record):
    if len(record) < 14:
        raise ValueError('Local Information record must contain at least 14 bytes')
    # AT Options edits bit zero of each byte. The V1.21 entry gate tests the
    # entire full-test byte for nonzero, but masks bit zero of the band byte.
    full, band = record[2], record[6]
    return dict(full_test_byte=full, band_options_byte=band,
                full_test_option_bit=bool(full & 1),
                band_select_option_bit=bool(band & 1),
                V121_entry_permission=bool(full or band & 1),
                V121_full_adjustment_permission=bool(full),
                band_mode=record[3],
                other_band_bits=band & 0xFE)


def read_nand_options(path):
    path = Path(path)
    if path.stat().st_size != CAPTURE_SIZE:
        raise ValueError('Expected the 256 MiB main NAND image, without OOB bytes')
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
        records = []
        for address in LOCAL_INFO_BLOCKS:
            handle.seek(address)
            records.append(dict(address=f'0x{address:08X}',
                                **decode_options(handle.read(14))))
    return dict(layout='D578 PRO GD32 V1.21 research layout',
                sha256=digest, known_capture=digest == CAPTURE_SHA256,
                records=records, active_record_not_selected_by_this_reader=True,
                source_modified=False,
                scope='Permissions only; does not verify physical key inputs or radio calibration')


def enable_virtual_full_test(nand):
    """Return a synthetic options fixture in an authenticated volatile overlay.

    Both candidate local-info records are updated because OEM selection remains
    the firmware's job. Calibration blocks, identity, band mode and other bits
    are preserved. OverlayNand supplies ideal ECC status for the virtual page;
    these bytes are never a physical programming recipe.
    """
    from nand_overlay import OverlayNand
    if not isinstance(nand, OverlayNand):
        raise ValueError('A volatile OverlayNand instance is required')
    source = nand.sources['nand_main_256MiB.bin']
    if source['sha256'] != CAPTURE_SHA256:
        raise ValueError('Virtual service options require the authenticated V1.21 capture')
    changes = []
    for address in LOCAL_INFO_BLOCKS:
        row = address // 2048
        page = bytearray(nand.page_image(row))
        for offset in (2, 6):
            before = page[offset]
            page[offset] |= 1
            if page[offset] != before:
                changes.append(dict(address=f'0x{address + offset:08X}',
                                    before=before, after=page[offset]))
        nand.overlay[row] = bytes(page)
    return dict(kind='synthetic service permissions in volatile NAND overlay',
                changes=changes, source_files_modified=False,
                OEM_instructions_modified=False, OEM_RAM_forced=False,
                calibration_blocks_modified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('nand_main', type=Path)
    args = parser.parse_args()
    print(json.dumps(read_nand_options(args.nand_main), indent=2))


if __name__ == '__main__':
    main()
