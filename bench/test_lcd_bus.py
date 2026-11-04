import unittest
from lcd_bus import LcdBus
from emulate_clock_v121 import StopModel


class LcdTests(unittest.TestCase):
    def setUp(self):
        self.lcd = LcdBus()
        self.lcd.armed = True

    def emit(self, byte, data=False, selected=True):
        control = (0x800 if data else 0) | (0 if selected else 0x2000)
        self.lcd.gpio(control, control | 0x400, byte << 7)

    def command(self, byte, data=()):
        self.emit(byte)
        for value in data:
            self.emit(value, True)

    def window(self, x0=0, x1=1, y0=0, y1=1):
        self.command(0x3A, [0x55])
        self.command(0x2A, [0, x0, 0, x1])
        self.command(0x2B, [0, y0, 0, y1])

    def test_rgb565_bus_to_independent_2x2_image(self):
        self.window()
        self.command(0x11)
        self.command(0x29)
        self.command(0x2C, [0xF8, 0, 0x07, 0xE0, 0, 0x1F, 0xFF, 0xFF])
        self.assertEqual(list(self.lcd.frame().get_flattened_data()),
                         [(255,0,0), (0,255,0), (0,0,255), (255,255,255)])
        self.assertEqual(self.lcd.total_pixels, 4)

    def test_empty_contact_interval_without_pixels_can_be_followed_by_valid_window(self):
        self.window(0,1,21,20)
        self.command(0x2C)
        self.assertEqual(self.lcd.total_pixels,0)
        self.window(0,0,0,0)
        self.command(0x2C,[0xFF,0xFF])
        self.assertEqual(self.lcd.total_pixels,1)

    def test_actual_pixel_in_empty_interval_is_explicit_boundary(self):
        self.window(0,1,21,20)
        self.command(0x2C)
        with self.assertRaisesRegex(StopModel,'empty OEM'):
            self.emit(0xFF,True)

    def test_cs_high_and_falling_edge_do_not_latch(self):
        self.emit(0x3A, selected=False)
        self.lcd.gpio(0x400, 0, 0x3A << 7)
        self.assertIsNone(self.lcd.command)
        self.assertEqual(self.lcd.write_edges, 0)

    def test_gpio_data_pins_are_7_through_14(self):
        self.lcd.gpio(0, 0x400, (0x36 << 7) | 0x807F)
        self.assertEqual(self.lcd.command, 0x36)

    def test_display_and_sleep_gate_visible_frame(self):
        self.window(0,0,0,0)
        self.command(0x2C, [0xFF,0xFF])
        self.assertEqual(self.lcd.frame().getpixel((0,0)), (0,0,0))
        self.assertEqual(self.lcd.frame(False).getpixel((0,0)), (255,255,255))
        self.command(0x11)
        self.command(0x29)
        self.assertEqual(self.lcd.frame().getpixel((0,0)), (255,255,255))
        self.command(0x28)
        self.assertEqual(self.lcd.frame().getpixel((0,0)), (0,0,0))

    def test_empty_initial_ramwr_is_allowed(self):
        self.command(0x2C)
        self.command(0x29)
        self.assertEqual(self.lcd.total_pixels, 0)

    def test_actual_pixel_without_window_is_rejected(self):
        self.command(0x3A, [0x55])
        self.command(0x2C)
        with self.assertRaisesRegex(StopModel, 'before an address window'):
            self.emit(0, True)

    def test_partial_pixel_never_draws(self):
        self.window()
        self.command(0x2C, [0xF8])
        self.assertEqual(self.lcd.total_pixels, 0)
        self.command(0x2C, [0,0x1F])
        self.assertEqual(self.lcd.pixels[0,0], 0x1F)

    def test_window_offsets_and_wrap(self):
        self.window(2,3,3,3)
        self.command(0x2C, [0xF8,0, 0,0x1F, 0x07,0xE0])
        self.assertEqual(self.lcd.pixels, {(2,3):0x7E0, (3,3):0x1F})

    def test_unsupported_format_stops(self):
        self.window()
        self.command(0x3A,[0x66])
        self.command(0x2C)
        with self.assertRaisesRegex(StopModel, 'RGB565'):
            self.emit(0, True)

    def test_reversed_window_is_rejected(self):
        with self.assertRaisesRegex(StopModel, 'outside bounded'):
            self.window(5,2)

    def test_command_crosscheck_detects_bus_mismatch(self):
        self.lcd.expected_commands = [0x11]
        self.command(0x29)
        self.assertEqual(len(self.lcd.command_mismatches), 1)

    def test_software_reset_clears_decoded_state(self):
        self.window()
        self.command(0x2C,[0xF8,0])
        self.command(1)
        self.assertEqual(self.lcd.pixels,{})
        self.assertTrue(self.lcd.sleeping)


if __name__ == '__main__':
    unittest.main()
