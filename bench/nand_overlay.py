"""Ideal digital NAND program/erase in a volatile copy-on-write overlay.

Captured files stay mmap.ACCESS_READ. This models successful cells, busy/WEL,
block geometry and one-way programming, not analog wear or ECC generation.
"""
import hashlib
from emulate_nand_v121 import CapturedNand
from emulate_clock_v121 import StopModel


class OverlayNand(CapturedNand):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.overlay={}
        self.program_buffer=None
        self.program_operations=[]
        self.erase_operations=[]

    def page_image(self,row):
        if row in self.overlay:return self.overlay[row]
        return (self.images['nand_main_256MiB.bin'][row*2048:(row+1)*2048]+
                self.images['nand_oob64_8MiB.bin'][row*64:(row+1)*64])

    def end(self):
        data=self.input_bytes
        if not data:return
        command=data[0]
        if command not in (2,0x84,0x10,0xD8):
            super().end()
            if command==0x13 and self.cached_page in self.overlay:
                self.cache=self.overlay[self.cached_page]
                self.status &= ~0x30  # Ideal no-error digital overlay.
            return
        entry=dict(command=f'{command:02X}',input_prefix=bytes(data[:16]).hex(' '),
                   bytes_clocked=len(data),response_prefix='',storage='volatile_overlay')
        if command in (2,0x84):
            if len(data)<4:raise StopModel('NAND program load requires column and data')
            column=int.from_bytes(bytes(data[1:3]),'big')
            if column+len(data)-3>2112:raise StopModel('NAND program load outside ECC-on 2048+64 buffer')
            if command==2:self.program_buffer=bytearray(b'\xFF'*2112)
            if self.program_buffer is None:raise StopModel('NAND random load without initial load')
            self.program_buffer[column:column+len(data)-3]=bytes(data[3:])
            entry.update(column=column,data_bytes=len(data)-3)
        else:
            if len(data)!=4:raise StopModel('NAND execute/erase requires three row bytes')
            row=int.from_bytes(bytes(data[1:4]),'big')
            if row>=131072:raise StopModel('NAND write row outside device')
            if not self.status&2:raise StopModel('NAND execute/erase with WEL clear')
            if self.features[0xA0]&0x38:raise StopModel('NAND protected block writes outside overlay subset')
            if command==0xD8:
                start=row & ~63
                for page in range(start,start+64):self.overlay[page]=b'\xFF'*2112
                entry.update(first_page=start,pages=64)
                self.erase_operations.append(entry.copy())
            else:
                if self.program_buffer is None:raise StopModel('NAND execute without loaded buffer')
                old=self.page_image(row)
                # A 1 in the load buffer leaves a cell unchanged. In particular
                # untouched FF bytes in a partial load must not restore zeros.
                programmed=bytes(before&after for before,after in zip(old,self.program_buffer))
                self.overlay[row]=programmed
                entry.update(page=row,main_sha256=hashlib.sha256(programmed[:2048]).hexdigest())
                self.program_operations.append(entry.copy())
                self.program_buffer=None
            self.status=0
            self.pending_busy=self.busy_polls
            self.array_writes.append(entry.copy())
        self.opcodes[command]+=1
        self.transactions.append(entry)

    def describe(self):
        result=super().describe()
        result.update(storage_mode='captured read-only files plus volatile overlay',
            overlay_pages=len(self.overlay),program_operations=self.program_operations,
            erase_operations=self.erase_operations,ECC_for_overlay='ideal no-error, parity not generated',
            overlay_page_sha256={str(k):hashlib.sha256(v).hexdigest() for k,v in self.overlay.items()})
        return result
