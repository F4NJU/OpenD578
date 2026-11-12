"""Build the bench's two unchanged, dependency-free C bridges with portable Zig.

Uses Clang and LLD directly to avoid Zig's MinGW/CRT cache on restricted Windows
hosts. No radio firmware is built. DLLs stay beside the bench's Python modules.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(zig, bench):
    if sys.platform != 'win32':
        raise RuntimeError('Windows only; use bench/build_native.py on other hosts')
    zig = Path(zig).resolve(strict=True)
    bench = Path(bench).resolve(strict=True)
    include = zig.parent / 'lib' / 'include'
    if not include.is_dir():
        raise RuntimeError('Complete portable Zig distribution required')
    results = []
    with tempfile.TemporaryDirectory(prefix='opend578-native-') as directory:
        for name in ('native_gate', 'lcd_bridge'):
            source = bench / (name + '.c')
            output = bench / (name + '.dll')
            obj = Path(directory) / (name + '.obj')
            staged = Path(directory) / (name + '.dll')
            commands = [
                [str(zig), 'clang', '-cc1', '-triple', 'x86_64-pc-windows-msvc',
                 '-emit-obj', '-O2', '-fms-extensions', '-isystem', str(include),
                 '-o', str(obj), '-x', 'c', str(source)],
                [str(zig), 'lld-link', '/dll', '/noentry', '/out:' + str(staged), str(obj)],
            ]
            for command in commands:
                subprocess.run(command, check=True, timeout=120)
            output.write_bytes(staged.read_bytes())
            report = dict(platform=sys.platform, machine='x86_64',
                          compiler_sha256=digest(zig), source_sha256=digest(source),
                          binary_sha256=digest(output), commands=commands)
            output.with_suffix('.dll.build.json').write_text(json.dumps(report, indent=2))
            results.append(dict(name=name, source_sha256=report['source_sha256'],
                                binary_sha256=report['binary_sha256']))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zig', required=True, type=Path)
    parser.add_argument('--bench', default=Path(__file__).resolve().parent.parent / 'bench', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.zig, args.bench), indent=2))
