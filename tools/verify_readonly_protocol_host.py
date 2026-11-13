"""Compile and execute parser self-checks on Windows; no firmware qualification."""
import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def verify(zig):
    zig = Path(zig).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix='opend578-parser-') as directory:
        folder = Path(directory)
        objects = []
        for i, source in enumerate(('firmware/cps/readonly_protocol.c', 'firmware/hal/freestanding_memory.c',
                                    'firmware/tests/test_readonly_protocol.c')):
            obj = folder / f'{i}.obj'
            subprocess.run([str(zig), 'clang', '-cc1', '-triple', 'x86_64-pc-windows-msvc', '-emit-obj',
                            '-O2', '-ffreestanding', '-fno-builtin', '-isystem', str(zig.parent / 'lib/include'),
                            '-o', str(obj), '-x', 'c', str(ROOT / source)], check=True, timeout=60)
            objects.append(str(obj))
        dll = folder / 'protocol.dll'
        subprocess.run([str(zig), 'lld-link', '/dll', '/noentry', '/export:d578_cps_selftest', '/out:' + str(dll), *objects], check=True, timeout=60)
        library = ctypes.CDLL(str(dll))
        library.d578_cps_selftest.restype = ctypes.c_int
        status = library.d578_cps_selftest()
        # Release the DLL before TemporaryDirectory removes it on Windows.
        import _ctypes
        _ctypes.FreeLibrary(library._handle)
        if status:
            raise RuntimeError(f'Parser check failed: {status}')
    return dict(passed=True, checks=8, scope='Host C parser checks, not ARM firmware execution')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zig', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.zig)))
