"""Observed translation-block entries, not assumed instruction/function coverage."""
from unicorn import UC_HOOK_BLOCK


class BlockCoverage:
    def __init__(self,cpu,limit=200000):
        self.blocks={};self.limit=limit;self.entries=0;self.unrecorded=0
        self.handle=cpu.hook_add(UC_HOOK_BLOCK,self.enter)
    def enter(self,cpu,address,size,data):
        self.entries+=1
        if address in self.blocks:self.blocks[address][1]+=1
        elif len(self.blocks)<self.limit:self.blocks[address]=[size,1]
        else:self.unrecorded+=1
    def summary(self):
        return dict(unique_block_entries=len(self.blocks),block_entries=self.entries,
            omitted_entries=self.unrecorded,full_instruction_coverage=False,
            scope='Block entry observed; a mid-block stop does not prove every translated instruction executed')
    def describe(self):
        return dict(**self.summary(),blocks=[dict(address=hex(a),translation_bytes=s,entries=n) for a,(s,n) in sorted(self.blocks.items())])
