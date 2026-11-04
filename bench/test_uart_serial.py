import unittest
from uart_serial import Uart3, BluetoothPeer
from emulate_clock_v121 import StopModel


class UartTests(unittest.TestCase):
    def configured(self, peer=None):
        uart = Uart3(peer, byte_steps=20)
        uart.write(8, 2, 0x209)
        uart.write(0xC, 2, 0x202C)
        return uart

    def test_absent_optional_card_does_not_prevent_uart_configuration(self):
        uart = self.configured()
        self.assertEqual(uart.read(0,2), 0xC0)
        self.assertFalse(uart.irq)

    def test_transmission_completes_even_without_peer(self):
        uart = self.configured()
        uart.write(4,2,ord('A'))
        self.assertFalse(uart.read(0,2) & 0x40)
        uart.advance(19)
        self.assertEqual(uart.tx, [])
        uart.advance(20)
        self.assertEqual(uart.tx,[65])
        self.assertEqual(uart.read(0,2),0xC0)

    def test_receive_irq_and_read_to_clear(self):
        uart = self.configured()
        uart.schedule(b'A')
        uart.advance(20)
        self.assertTrue(uart.irq)
        self.assertEqual(uart.read(4,2),65)
        self.assertFalse(uart.irq)

    def test_overrun_preserves_unread_byte_and_clear_sequence(self):
        uart = self.configured()
        uart.schedule(b'AB')
        uart.advance(20)
        uart.advance(40)
        self.assertEqual(uart.overruns,1)
        self.assertTrue(uart.read(0,2) & 8)
        self.assertEqual(uart.read(4,2),65)
        self.assertEqual(uart.read(0,2) & 0x28,0)

    def test_tx_before_enable_is_rejected(self):
        with self.assertRaisesRegex(StopModel,'before UART'):
            Uart3().write(4,2,65)

    def test_version_reply_has_authenticated_et12_identifier(self):
        peer = BluetoothPeer('et12')
        response = b''.join(peer.consume(b) for b in b'AT+VER?\r\n')
        self.assertEqual(response,b'\r\n+VER:ET12_AQQX_V10043\r\n')

    def test_unknown_command_does_not_receive_fabricated_ok(self):
        peer = BluetoothPeer('et12')
        with self.assertRaisesRegex(StopModel,'outside qualified'):
            for b in b'AT+UNKNOWN\r\n':
                peer.consume(b)

    def test_absent_peer_produces_no_rx_bytes(self):
        peer = BluetoothPeer('absent')
        self.assertEqual(b''.join(peer.consume(b) for b in b'AT+VER?\r\n'),b'')


if __name__ == '__main__':
    unittest.main()
