"""UART3 digital state and an explicitly limited ELET/ET12 Bluetooth peer.

Absent peer means an idle RX line. It does not stop MCU configuration/TX.
AT responses below come from the supplied B707 ET12 QX V10043 image;
unknown requests stop explicitly instead of receiving a universal OK.
"""
from collections import deque
from emulate_clock_v121 import StopModel

BT_SHA = 'b712048f8e0a3c352b68e8c213894c12d1341756f4ef7d9e435d4a487e3ff40f'


class IdlePeer:
    """Disconnected RX. TX completes electrically without an invented reply."""
    mode = 'idle'
    transactions = ()

    def consume(self, byte):
        return b''


class BluetoothPeer:
    def __init__(self, mode='absent'):
        if mode not in ('absent', 'et12'):
            raise ValueError('Bluetooth mode must be absent or et12')
        self.mode = mode
        self.line = bytearray()
        self.transactions = []
        self.aghf = 1

    def consume(self, byte):
        if self.mode == 'absent':
            return b''
        self.line.append(byte)
        if len(self.line) > 128:
            raise StopModel('Bluetooth command longer than qualified AT subset')
        if not self.line.endswith(b'\r\n'):
            return b''
        command = bytes(self.line[:-2])
        self.line.clear()
        if command == b'AT+VER?':
            response = b'\r\n+VER:ET12_AQQX_V10043\r\n'
        elif command in (b'AT+AGHF=0', b'AT+AGHF=1'):
            self.aghf = int(chr(command[-1]))
            response = b'\r\n+AGHF:' + command[-1:] + b'\r\n'
        elif command == b'AT+AGHF?':
            response = f'\r\n+AGHF:{self.aghf}\r\n'.encode()
        else:
            raise StopModel('Bluetooth command outside qualified ET12 subset: ' + repr(command))
        self.transactions.append(dict(request=command.decode(), response_hex=response.hex(' '),
                                      source='B707_Audio_AGHF_ET12_QX-V10043.bin', source_sha256=BT_SHA))
        return response


class Uart3:
    def __init__(self, peer=None, byte_steps=1024, clock_enabled=lambda: True, name='UART3'):
        self.name = name
        if byte_steps < 1:
            raise ValueError('UART byte interval must be positive')
        self.peer = peer if peer is not None else BluetoothPeer()
        self.byte_steps = byte_steps
        self.clock_enabled = clock_enabled
        self.regs = {0: 0xC0, 8: 0, 0xC: 0, 0x10: 0, 0x14: 0}
        self.received_data = None
        self.status_read = False
        self.tx_shift = None
        self.tx_holding = None
        self.rx_wire = deque()
        self.tx = []
        self.rx = []
        self.overruns = 0
        self.step = 0
        self.events = []

    def reset(self):
        self.regs.update({0: 0xC0, 8: 0, 0xC: 0, 0x10: 0, 0x14: 0})
        self.received_data = None
        self.status_read = False
        self.tx_shift = self.tx_holding = None
        self.rx_wire.clear()

    def access(self, offset, size):
        # The authentic OEM accesses these registers with LDRH/STRH although
        # the family manual describes word accesses. Preserve observed accesses.
        if size not in (2, 4) or offset not in (0, 4, 8, 0xC, 0x10, 0x14):
            raise StopModel(self.name+' register/access outside modelled subset')

    def read(self, offset, size):
        self.access(offset, size)
        if offset == 0:
            self.status_read = True
        if offset == 4:
            if self.received_data is None:
                raise StopModel(self.name+' data read with no received byte')
            value = self.received_data
            self.received_data = None
            self.regs[0] &= ~0x20
            if self.status_read:
                self.regs[0] &= ~0x1F
            self.status_read = False
            return value
        return self.regs[offset]

    def write(self, offset, size, value):
        self.access(offset, size)
        if not self.clock_enabled():
            raise StopModel(self.name+' write with clock gated or reset asserted')
        if value & ~0xFFFF:
            raise StopModel(self.name+' reserved upper register bits')
        if offset == 0:
            self.regs[0] &= value | ~0x160  # TC / RBNE / LBDF are rc_w0.
            return
        if offset == 4:
            if self.regs[0xC] & 0x2008 != 0x2008 or not self.regs[8]:
                raise StopModel(self.name+' transmit before UART/transmitter/baud enabled')
            if value > 255 or self.regs[0xC] & 0x1400 or self.regs[0x10] & 0x3000:
                raise StopModel(self.name+' wire only qualifies 8N1 frames')
            if self.tx_holding is not None:
                raise StopModel(self.name+' transmit holding register overwritten')
            self.regs[0] &= ~0xC0
            if self.tx_shift is None:
                self.tx_shift = (value, self.step + self.byte_steps)
                self.regs[0] |= 0x80
            else:
                self.tx_holding = value
            return
        if offset == 8 and self.regs[0xC] & 0x2000:
            raise StopModel(self.name+' baud changed while UART is enabled')
        self.regs[offset] = value

    def schedule(self, data):
        start = max(self.step, self.rx_wire[-1][0] if self.rx_wire else self.step)
        for byte in data:
            start += self.byte_steps
            self.rx_wire.append((start, byte))

    def advance(self, step):
        self.step = step
        if not self.clock_enabled() or not self.regs[0xC] & 0x2000:
            return
        if self.tx_shift is not None and step >= self.tx_shift[1]:
            value, _ = self.tx_shift
            self.tx.append(value)
            self.schedule(self.peer.consume(value))
            if self.tx_holding is None:
                self.tx_shift = None
                self.regs[0] |= 0xC0
            else:
                self.tx_shift = (self.tx_holding, step + self.byte_steps)
                self.tx_holding = None
                self.regs[0] |= 0x80
        if self.regs[0xC] & 4 and self.rx_wire and step >= self.rx_wire[0][0]:
            _, value = self.rx_wire.popleft()
            self.rx.append(value)
            if self.received_data is not None:
                self.regs[0] |= 8
                self.overruns += 1
            else:
                self.received_data = value
                self.regs[0] |= 0x20

    @property
    def irq(self):
        status, control = self.regs[0], self.regs[0xC]
        return bool(control & 0x2000 and (
            (status & 0x28 and control & 0x20) or
            (status & 0x80 and control & 0x80) or
            (status & 0x40 and control & 0x40) or
            (status & 0x10 and control & 0x10) or
            (status & 1 and control & 0x100) or
            (status & 0x0E and self.regs[0x14] & 1)))

    def describe(self):
        return dict(name=self.name, registers={hex(k):hex(v) for k,v in self.regs.items()},
            peer_mode=self.peer.mode, tx_bytes=len(self.tx), rx_bytes=len(self.rx),
            tx_hex=bytes(self.tx).hex(' '), rx_hex=bytes(self.rx).hex(' '),
            overruns=self.overruns, **({'byte_interval_virtual_core_units':self.byte_steps} if getattr(self,'virtual_time',False) else {'byte_interval_executed_instructions':self.byte_steps}),
            cycle_accurate=False, bluetooth_transactions=self.peer.transactions,
            exact_physical_chip_identified=False)
