"""Build the opt-in read-only USB variant; preserve F4EGM's baseline binaries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import struct


def raw_flash(elf):
    """Extract ELF32 ARM load segments by physical Flash address, including .data LMA."""
    data = Path(elf).read_bytes()
    if data[:7] != b'\x7fELF\x01\x01\x01' or struct.unpack_from('<H', data, 18)[0] != 40:
        raise ValueError('Expected little-endian ELF32 ARM')
    offset = struct.unpack_from('<I', data, 28)[0]
    stride, count = struct.unpack_from('<HH', data, 42)
    segments = []
    for i in range(count):
        kind, at, _, physical, size, _, _, _ = struct.unpack_from('<8I', data, offset + i * stride)
        if kind == 1 and size and 0x08006000 <= physical < 0x08026000:
            if physical + size > 0x08026000 or at + size > len(data):
                raise ValueError('Flash load segment out of bounds')
            segments.append((physical - 0x08006000, data[at:at + size]))
    if not segments or min(at for at, _ in segments) != 0:
        raise ValueError('Missing application vectors')
    result = bytearray(b'\xff' * max(at + len(value) for at, value in segments))
    for at, value in segments:
        result[at:at + len(value)] = value
    return bytes(result)


def build(zig, output):
    root = Path(__file__).resolve().parents[1]
    zig = Path(zig).resolve(strict=True)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    sources = ['firmware/experiments/rx_fm_alpha/main.c', 'firmware/hal/audio_control.c',
               'firmware/rf/rx_fm.c', 'firmware/cps/readonly_protocol.c', 'firmware/hal/usb_cdc_poll.c',
               'firmware/hal/freestanding_memory.c']
    commands = []
    with tempfile.TemporaryDirectory(prefix='opend578-cps-') as temporary:
        objects = []
        for index, source in enumerate(sources):
            obj = Path(temporary) / f'{index}.obj'
            command = [str(zig), 'clang', '-cc1', '-triple', 'thumbv7em-none-unknown-eabi',
                       '-target-cpu', 'cortex-m4', '-target-abi', 'aapcs', '-mfloat-abi', 'soft',
                       '-ffreestanding', '-fno-builtin', '-Oz', '-emit-obj', '-DOPEND578_CPS_READONLY=1',
                       '-isystem', str(zig.parent / 'lib/include'), '-o', str(obj), '-x', 'c', str(root / source)]
            subprocess.run(command, check=True, timeout=120)
            commands.append(command)
            objects.append(str(obj))
        elf, binary = output / 'rx_fm_cps.elf', output / 'rx_fm_cps.bin'
        command = [str(zig), 'ld.lld', '-T', str(root / 'firmware/experiments/rx_fm_alpha/link.ld'),
                   '--entry=Reset_Handler', '-o', str(elf), *objects]
        subprocess.run(command, check=True, timeout=120)
        commands.append(command)
        binary.write_bytes(raw_flash(elf))
    report = dict(scope='Independent RX FM + read-only USB bench experiment; not a flashable OEM package',
                  target='Cortex-M4 soft-float', loadAddress='0x08006000', binaryBytes=binary.stat().st_size,
                  binarySHA256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  sources={source: hashlib.sha256((root / source).read_bytes()).hexdigest() for source in sources},
                  compiler=subprocess.check_output([str(zig), 'version'], text=True).strip())
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zig', required=True, type=Path)
    parser.add_argument('--out-dir', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.zig, args.out_dir), indent=2))
