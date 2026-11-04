"""Optional SRAM access evidence for CPU instructions and model-side writes.

The observations cover only the executed interval and configured ranges.
No amount of silence from a watch establishes that SRAM is available to a patch.
"""
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC
from audit_ram_v121 import RAM,RAM_SIZE

def parse_range(text):
    try:
        start,length=(int(part,0) for part in text.split(':'))
    except (ValueError,TypeError):
        raise ValueError('SRAM range must be START:SIZE, e.g. 0x200170E0:0xF20') from None
    if length<=0 or not RAM<=start<start+length<=RAM+RAM_SIZE:
        raise ValueError('Watch range must be entirely within GD32 SRAM')
    return start,length

class MemoryWatch:
    def __init__(self,runner,ranges,sample_limit=256):
        self.runner=runner;self.origin_step=runner.steps;self.limit=sample_limit
        self.ranges=[dict(start=start,length=length,reads=bytearray(length),
            writes=bytearray(length),CPU_reads=0,CPU_writes=0,model_writes=0)
            for start,length in ranges]
        self.samples=[];self.total_accesses=0
        # One hook prevents double-counting overlapping user ranges.
        self.hook=runner.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.cpu_access,
            begin=min(start for start,_ in ranges),end=max(start+length-1 for start,length in ranges))
        self.original_write=runner.cpu.mem_write
        def model_write(address,data):
            result=self.original_write(address,data)
            self.record('model_write',address,len(data))
            return result
        runner.cpu.mem_write=model_write
        # These devices captured the original bound method at construction.
        # Retarget them too, otherwise DMA writes would bypass the watch.
        for name in ('adc_dma','flash_cache'):
            device=getattr(runner,name,None)
            if device is not None and hasattr(device,'write_memory'):
                device.write_memory=model_write

    def cpu_access(self,uc,access,address,size,value,opaque):
        self.record('CPU_write' if access==UC_MEM_WRITE else 'CPU_read',address,size)

    def record(self,kind,address,size):
        hits=[]
        for item in self.ranges:
            lo=max(address,item['start']);hi=min(address+size,item['start']+item['length'])
            if lo<hi:hits.append((item,lo,hi))
        if not hits:return
        gate=getattr(self.runner,'native_gate',None)
        if gate:gate.sync()
        self.total_accesses+=1
        for item,lo,hi in hits:
            item[kind+'s']+=1
            bitmap=item['reads' if kind=='CPU_read' else 'writes']
            bitmap[lo-item['start']:hi-item['start']]=b'\x01'*(hi-lo)
        if len(self.samples)<self.limit:
            self.samples.append(dict(step=self.runner.steps,pc=hex(self.runner.cpu.reg_read(UC_ARM_REG_PC)),
                source=kind,address=hex(address),size=size))

    def describe(self):
        return dict(origin_step=self.origin_step,end_step=self.runner.steps,
            total_accesses=self.total_accesses,samples=self.samples,
            samples_truncated=self.total_accesses>len(self.samples),
            ranges=[dict(start=hex(v['start']),size=v['length'],
                CPU_reads=v['CPU_reads'],CPU_writes=v['CPU_writes'],model_writes=v['model_writes'],
                bytes_read=sum(v['reads']),bytes_written=sum(v['writes'])) for v in self.ranges],
            SRAM_proven_free=False,
            coverage='Executed CPU accesses and model mem_write calls after installation; not all possible paths')
