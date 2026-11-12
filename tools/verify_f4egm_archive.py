"""Authenticate F4EGM.zip without extracting, executing or modifying its contents."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

EXPECTED_CAPTURE_FILES = {
    'full_flash_pass1.bin': (3145728, 'e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e'),
    'nand_main_256MiB.bin': (268435456, '329d22165d234bf0df043e62af11397dea96327925b9db18f3c354230ff40945'),
    'nand_oob64_8MiB.bin': (8388608, '9a999b9fd13a02b45ed4d38e68f9e9c7d1095994c751e36e04f4a62b2e4c5106'),
    'nand_ecc_status_128KiB.bin': (131072, 'b40ebd3ebc3923f01d9d98a52a3b019b65785641ba76687127678b788ea793c6'),
}


def verify_archive(archive_path, expected=None):
    expected = EXPECTED_CAPTURE_FILES if expected is None else expected
    result = {}
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        if len(entries) != len(expected) or {entry.filename for entry in entries} != set(expected):
            raise ValueError('Archive members differ from the four expected capture files')
        for entry in entries:
            size, digest = expected[entry.filename]
            if entry.is_dir() or entry.file_size != size:
                raise ValueError('Unexpected size: ' + entry.filename)
            actual = hashlib.sha256()
            with archive.open(entry) as source:
                while chunk := source.read(1024 * 1024):
                    actual.update(chunk)
            if actual.hexdigest() != digest:
                raise ValueError('Unexpected SHA256: ' + entry.filename)
            result[entry.filename] = {'bytes': size, 'sha256': digest}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    files = verify_archive(args.archive)
    with args.archive.open('rb') as source:
        archive_sha256 = hashlib.file_digest(source, 'sha256').hexdigest()
    report = dict(captures_authenticated=True, archive_sha256=archive_sha256,
                  files=files, source_files_modified=False, firmware_executed=False,
                  python_reference='3.13.5 (F4EGM)',
                  python_bench_additional_input='SCT3258TD_UpdateFlash_V2_01_07BF.hex is required by bench/prepare_inputs.py and is not in this ZIP',
                  scope='Input verification only; not USB/CPS qualification')
    text = json.dumps(report, indent=2)
    if args.report:
        args.report.write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
