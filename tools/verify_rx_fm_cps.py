"""Execute the standalone ARM variant on the hardware model and real CDC host.

No OEM image, NAND capture, OEM SRAM layout or synthetic firmware reply.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench'))
from hardware_runner import HardwareRunner
from adc_dma import validate_profile
from unicorn import UC_HOOK_MEM_WRITE


def verify(binary, output):
    image = Path(binary).read_bytes()
    profile = validate_profile(json.loads((ROOT / 'bench/profiles/front_panel.json').read_text()))
    runner = HardwareRunner(image, load_address=0x08006000, vector_address=0x08006000, profile=profile)
    runner.enable_native()
    unsafe = []

    def observe(cpu, access, address, size, value, user):
        for port, bit in ((0x40011800, 6), (0x40011000, 4)):
            if address in (port + 12, port + 16) and value & (1 << bit):
                unsafe.append(dict(address=hex(address), value=hex(value)))
    runner.cpu.hook_add(UC_HOOK_MEM_WRITE, observe, begin=0x40010800, end=0x40011c20)
    deadline = time.monotonic() + 180

    def until(predicate, phase):
        while not predicate():
            if time.monotonic() > deadline:
                raise RuntimeError('Timeout: ' + phase)
            result, _ = runner.run_hardware(30000)
            if result['stop']['category'] not in ('control', 'waiting'):
                raise RuntimeError(json.dumps(dict(phase=phase, stop=result['stop'])))
        print(phase, runner.steps, flush=True)

    # Regression: one long runner call must not stall after its accumulated
    # sleep allowance despite regular SysTick/CPU progress.
    initial_result, _ = runner.run_hardware(10000000)
    if initial_result['stop']['kind'] != 'instruction_budget' or runner.lcd.total_pixels < 20480:
        raise RuntimeError('Premature sleep despite a running SysTick application')
    until(lambda: runner.lcd.total_pixels >= 20480, 'boot')
    runner.input_command(dict(control='USB_CDC_START'))
    until(lambda: runner.cdc.state in ('ready', 'error'), 'enumeration')
    if runner.cdc.state != 'ready':
        raise RuntimeError(runner.cdc.error)

    def request(command, identifier):
        start = runner.cdc.received_total
        runner.cdc.queue(f'OD578/1 {identifier} {command}\n'.encode())
        until(lambda: runner.cdc.state == 'error' or b'\n' in runner.cdc.received[start:], command)
        if runner.cdc.state != 'ready':
            raise RuntimeError(runner.cdc.error)
        reply = json.loads(bytes(runner.cdc.received[start:]))
        if reply.get('id') != identifier or reply.get('protocol') != 'opend578-cps':
            raise RuntimeError('Unexpected application response')
        return reply

    hello = request('HELLO', 1)
    initial = request('VFOS', 2)
    if [v['rxHz'] for v in initial['vfos']] != [145500000, 435000000]:
        raise RuntimeError('Unexpected startup frequencies')
    runner.input_command(dict(control='DIAL_UP'))
    # The state change is produced by EXTI/the alpha loop, not a CPS write.
    for _ in range(8):
        runner.run_hardware(30000)
    changed = request('VFOS', 3)
    if changed['vfos'][0]['rxHz'] != 145512500:
        raise RuntimeError('CPS did not observe encoder change')
    denied = request('WRITE', 4)
    if denied.get('error') != 'unsupported_command':
        raise RuntimeError('Write command was not refused')
    if unsafe:
        raise RuntimeError('TX gate set during execution')
    report = dict(passed=True, scope='Actual independent ARM firmware + GD32 USB model; no physical radio',
                  binarySHA256=hashlib.sha256(image).hexdigest(), firmware=hello['firmware'],
                  capabilities=hello['capabilities'], initial=initial, encoderChanged=changed,
                  writeRejected=True, txGateSetObservations=len(unsafe), steps=runner.steps,
                  USB=dict(state=runner.cdc.state, sentBytes=runner.cdc.sent_total,
                           receivedBytes=runner.cdc.received_total), OEM_PC_hooks=False, OEM_RAM_ABI=False)
    Path(output).write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.binary, args.output), indent=2))
