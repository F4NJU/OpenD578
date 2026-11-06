"""Decode the actual OEM GPIO 8080 write bus into LCD address-space pixels.

V1.21 instructions prove PE7..14=data, PB10=WR#, PB11=D/C, PB13=CS#.
This models the observed address-window / RGB565 command subset, without
claiming the exact physical LCD controller or electrical pin continuity.
"""
from collections import Counter
import hashlib
import struct
import time
from pathlib import Path
from PIL import Image
from emulate_clock_v121 import StopModel


class LcdBus:
    def __init__(self):
        self.armed = False
        self.command = None
        self.arguments = []
        self.columns = None
        self.rows = None
        self.x = self.y = 0
        self.width = self.height = 0
        self.pixel_format = None
        self.madctl = None
        self.display_on = False
        self.sleeping = True
        self.high_byte = None
        self.pixels = {}
        self.total_pixels = 0
        self.write_edges = 0
        self.command_counts = Counter()
        self.commands = []
        self.expected_commands = []
        self.command_mismatches = []
        self.dirty = False
        self.step = 0
        self.empty_windows=[]
        self._rgb_buffer=None

    def gpio(self, before, after, data_levels):
        if self.armed and not before & 0x400 and after & 0x400 and not after & 0x2000:
            value = (data_levels >> 7) & 255
            self.write_edges += 1
            if after & 0x800:
                self.data(value)
            else:
                self.new_command(value)

    def new_command(self, value):
        self.command = value
        self.arguments = []
        self.high_byte = None
        self.command_counts[value] += 1
        if len(self.commands) < 8192:
            self.commands.append(dict(step=self.step, command=f'{value:02X}', arguments=self.arguments))
        index = sum(self.command_counts.values()) - 1
        if index < len(self.expected_commands) and value != self.expected_commands[index]:
            self.command_mismatches.append(dict(index=index, actual=value, expected=self.expected_commands[index]))
        if value == 0x01:
            self.columns = self.rows = None
            self.pixel_format = self.madctl = None
            self.pixels.clear()
            self._rgb_buffer=None
            self.dirty = True
            self.display_on = False
            self.sleeping = True
        elif value in (0x28, 0x29):
            self.display_on = value == 0x29
            self.dirty = True
        elif value in (0x10, 0x11):
            self.sleeping = value == 0x10
            self.dirty = True
        elif value == 0x2C:
            # The OEM issues an empty RAMWR during initialization, before
            # any window. Only actual pixel data would require reset bounds.
            if self.columns is not None and self.rows is not None:
                self.x, self.y = self.columns[0], self.rows[0]

    def data(self, value):
        if self.command is None:
            raise StopModel('LCD data without preceding command')
        if self.command == 0x2C:
            if self.columns is None or self.rows is None:
                raise StopModel('LCD pixel data before an address window is configured')
            if self.columns[0]>self.columns[1] or self.rows[0]>self.rows[1]:
                raise StopModel('LCD pixel data within an empty OEM address interval')
            if self.pixel_format != 0x55:
                raise StopModel('LCD pixel format outside qualified RGB565 subset')
            if self.high_byte is None:
                self.high_byte = value
                return
            color = (self.high_byte << 8) | value
            self.high_byte = None
            self.ensure_rgb_buffer()
            self.pixels[self.x, self.y] = color
            offset=(self.y*512+self.x)*3
            self._rgb_buffer[offset:offset+3]=bytes(self.rgb(color))
            self.total_pixels += 1
            self.dirty = True
            self.x += 1
            if self.x > self.columns[1]:
                self.x = self.columns[0]
                self.y += 1
                if self.y > self.rows[1]:
                    self.y = self.rows[0]
            return
        if len(self.arguments) < 256:
            self.arguments.append(value)
        if self.command in (0x2A, 0x2B) and len(self.arguments) == 4:
            self.apply_window()
        elif self.command == 0x3A and len(self.arguments) == 1:
            self.pixel_format = value
        elif self.command == 0x36 and len(self.arguments) == 1:
            self.madctl = value

    def apply_window(self):
        start,end=struct.unpack('>HH',bytes(self.arguments))
        if not (0<=start<512 and 0<=end<512) or start>end+1:
            raise StopModel('LCD address window outside bounded decoder surface')
        # Empty text/contact rows may emit end=start-1 followed by no pixel
        # bytes. Reject actual RAMWR data, whose behavior is unknown here.
        if start>end:self.empty_windows.append(dict(step=self.step,command=f'{self.command:02X}',start=start,end=end))
        if self.command==0x2A:
            self.columns=(start,end)
            self.width=max(self.width,end+1)
        else:
            self.rows=(start,end)
            self.height=max(self.height,end+1)

    @staticmethod
    def rgb(value, bgr=False):
        r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
        red, green, blue = (r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)
        return (blue, green, red) if bgr else (red, green, blue)

    def ensure_rgb_buffer(self):
        if getattr(self,'_rgb_buffer',None) is None:
            self._rgb_buffer=bytearray(512*512*3)
            for (x,y),color in self.pixels.items():
                offset=(y*512+x)*3
                self._rgb_buffer[offset:offset+3]=bytes(self.rgb(color))

    def frame(self, honor_display=True, bgr=False):
        width,height=max(1,self.width),max(1,self.height)
        if honor_display and not (self.display_on and not self.sleeping):
            return Image.new('RGB',(width,height))
        self.ensure_rgb_buffer()
        return Image.frombytes('RGB',(width,height),bytes(self._rgb_buffer),
                               'raw','BGR' if bgr else 'RGB',512*3,1)

    def save(self, filename, honor_display=True):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.stem + '.tmp.png')
        self.frame(honor_display).save(temporary)
        for attempt in range(4):
            try:
                temporary.replace(path)
                self.dirty = False
                return True
            except PermissionError:
                if attempt<3:time.sleep(.002)
        self.dirty=True
        return False

    def describe(self):
        image = self.frame(honor_display=False)
        return dict(source='OEM GPIO write edges, no replacement drawing',
            wiring=dict(data='PE7..PE14', WR='PB10', DC='PB11', CS='PB13'),
            dimensions_observed=[self.width, self.height], display_on=self.display_on,
            sleeping=self.sleeping, pixel_format=self.pixel_format, madctl=self.madctl,
            total_pixel_writes=self.total_pixels, unique_pixels_written=len(self.pixels),
            distinct_colors=len(set(self.pixels.values())), write_edges=self.write_edges,
            raw_rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest(),
            commands_by_opcode={f'{k:02X}': v for k,v in self.command_counts.items()},
            commands=self.commands, command_crosscheck_mismatches=self.command_mismatches,
            empty_address_intervals=self.empty_windows,
            expected_command_calls=len(self.expected_commands),
            exact_controller_identified=False, physical_pin_continuity_proven=False,
            coordinates='LCD address coordinates emitted by OEM; physical panel orientation not asserted')
