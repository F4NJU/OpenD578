#!/usr/bin/env python3
"""Passive audit of OpenD578 cps_bridge.py JSONL (no USB/serial access).

Emits only command type, address, payload length and integrity result. It never
writes codeplug data nor includes raw payloads in output. Supports fragmented
stream input and the documented OEM V1.21 PROGRAM/ID/R/W/END subset.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import json
from pathlib import Path
import sys

MAX_FILE_SIZE = 128 * 1024 * 1024
MAX_BUFFER_SIZE = 65536
MAX_EVENTS = 5000
DIRECTIONS = {'CPS_to_firmware': 'host', 'firmware_to_CPS': 'radio'}


def text_hex(value: object) -> bytes:
    if not isinstance(value, str) or len(value) % 2 or len(value) > MAX_BUFFER_SIZE * 2:
        raise ValueError('invalid/oversize hex field')
    return bytes.fromhex(value)


class TraceAudit:
    def __init__(self) -> None:
        self.host = bytearray()
        self.radio = bytearray()
        self.pending = deque()
        self.events: list[dict] = []
        self.counts = Counter()
        self.warnings: list[str] = []
        self.lines = 0

    def event(self, kind: str, **fields: object) -> None:
        self.counts[kind] += 1
        if len(self.events) < MAX_EVENTS:
            self.events.append({'type': kind, **fields})

    def warning(self, msg: str) -> None:
        if len(self.warnings) < 100:
            self.warnings.append(msg)
        self.counts['warnings'] += 1

    def feed(self, direction: str, data: bytes) -> None:
        if direction not in DIRECTIONS:
            self.warning(f'line {self.lines}: unknown direction')
            return
        target = self.host if DIRECTIONS[direction] == 'host' else self.radio
        target.extend(data)
        if len(target) > MAX_BUFFER_SIZE:
            self.warning(f'line {self.lines}: buffer overflow, stream reset')
            target.clear()
            self.pending.clear()
            return
        if target is self.host:
            self.parse_host()
        else:
            self.parse_radio()

    def parse_host(self) -> None:
        while self.host:
            b = self.host
            if b[0] == 0x50:  # PROGRAM
                word = b'PROGRAM'
                if bytes(b).startswith(word):
                    del b[:len(word)]
                    self.pending.append(('PROGRAM', None, None))
                    self.event('request_PROGRAM')
                    self.parse_radio()
                    continue
                if word.startswith(bytes(b)):
                    break
            if b[0] == 0x45:  # END
                word = b'END'
                if bytes(b).startswith(word):
                    del b[:len(word)]
                    self.pending.append(('END', None, None))
                    self.event('request_END')
                    self.parse_radio()
                    continue
                if word.startswith(bytes(b)):
                    break
            if b[0] == 0x02:
                del b[0]
                self.pending.append(('IDENTITY', None, None))
                self.event('request_IDENTITY')
                self.parse_radio()
                continue
            if b[0] == 0x52:  # R, 4-byte BE address, length
                if len(b) < 6:
                    break
                addr = int.from_bytes(b[1:5], 'big')
                n = b[5]
                del b[:6]
                if n < 1 or n > 255:
                    self.warning(f'line {self.lines}: invalid read length')
                    continue
                self.pending.append(('READ', addr, n))
                self.event('request_READ', address=f'0x{addr:08X}', length=n)
                self.parse_radio()
                continue
            if b[0] == 0x57:  # W, addr, length, data, checksum, ETX
                if len(b) < 6:
                    break
                addr = int.from_bytes(b[1:5], 'big')
                n = b[5]
                size = 6 + n + 2
                if len(b) < size:
                    break
                raw = bytes(b[:size])
                del b[:size]
                good = raw[-1] == 0x06 and (sum(raw[1:-2]) & 0xFF) == raw[-2]
                self.pending.append(('WRITE', addr, n))
                self.event('request_WRITE', address=f'0x{addr:08X}', length=n,
                           checksum_ok=good)
                if not good:
                    self.warning(f'line {self.lines}: write checksum/terminator invalid')
                self.parse_radio()
                continue
            self.counts['unknown_host_bytes'] += 1
            del b[0]

    def parse_radio(self) -> None:
        while self.pending and self.radio:
            kind, addr, n = self.pending[0]
            required = {'PROGRAM': 3, 'IDENTITY': 16, 'READ': (n or 0) + 8,
                        'WRITE': 1, 'END': 1}[kind]
            if len(self.radio) < required:
                return
            raw = bytes(self.radio[:required])
            del self.radio[:required]
            self.pending.popleft()
            if kind == 'PROGRAM':
                good = raw == b'QX\x06'
                self.event('response_PROGRAM', valid=good)
            elif kind == 'IDENTITY':
                good = raw[:1] == b'I' and raw[-1:] == b'\x06'
                # Do not disclose serial numbers or metadata from the response.
                model = raw[1:8].rstrip(b'\x00').decode('ascii', errors='replace')
                self.event('response_IDENTITY', valid=good, model=model if model == 'D578UV' else 'other')
            elif kind == 'READ':
                good = (raw[0] == 0x57 and int.from_bytes(raw[1:5], 'big') == addr and
                        raw[5] == n and raw[-1] == 0x06 and
                        (sum(raw[1:-2]) & 0xFF) == raw[-2])
                self.event('response_READ', address=f'0x{addr:08X}', length=n, checksum_ok=good)
            else:
                good = raw == b'\x06'
                self.event('response_' + kind, acknowledged=good)
            if not good:
                self.warning(f'line {self.lines}: invalid response for {kind}')
        if self.radio and not self.pending:
            self.counts['unsolicited_radio_bytes'] += len(self.radio)
            self.radio.clear()

    def result(self) -> dict:
        if self.host:
            self.warning(f'end-of-file: {len(self.host)} unparsed host bytes')
        if self.radio:
            self.warning(f'end-of-file: {len(self.radio)} unparsed response bytes')
        if self.pending:
            self.warning(f'end-of-file: {len(self.pending)} incomplete transactions')
        return {
            'format': 'OpenD578_cps_trace_audit_v1',
            'source_protocol': 'OEM V1.21 documented subset only',
            'mode': 'offline_read_only',
            'lines': self.lines,
            'counts': dict(sorted(self.counts.items())),
            'events': self.events,
            'events_truncated': len(self.events) == MAX_EVENTS,
            'warnings': self.warnings,
            'contains_payload_bytes': False,
        }


def audit(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError('input does not exist or exceeds 128 MiB')
    state = TraceAudit()
    with path.open('r', encoding='utf-8') as reader:
        for index, line in enumerate(reader, 1):
            state.lines = index
            if len(line) > MAX_BUFFER_SIZE * 2 + 4096:
                state.warning(f'line {index}: excessive JSON record size')
                continue
            try:
                entry = json.loads(line)
                if not isinstance(entry, dict):
                    raise ValueError('not an object')
                data = text_hex(entry.get('hex'))
            except (ValueError, TypeError, json.JSONDecodeError):
                state.warning(f'line {index}: invalid JSON/hex')
                continue
            state.feed(entry.get('direction', ''), data)
    return state.result()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Private cps_bridge.py JSONL capture')
    parser.add_argument('--output', type=Path, help='Sanitized JSON report; defaults to stdout')
    args = parser.parse_args()
    try:
        report = audit(args.input)
        content = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding='utf-8')
            print(f'Sanitized report saved to {args.output}; {len(report["events"])} events')
        else:
            print(content, end='')
    except (OSError, ValueError) as error:
        parser.exit(1, f'Error: {error}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
