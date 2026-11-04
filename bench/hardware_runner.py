"""D578 digital board model without OEM PC hooks or OEM SRAM structures.

Reuses peripheral implementations from the V11 bench. It deliberately does not
call their inherited OEM instruction observers, bus arming or GPIO-mask guesses.
Missing peripheral behavior is a model boundary, not proof of a firmware defect.
"""
import hashlib,struct,time,json
from pathlib import Path
from collections import Counter
from unicorn import UcError,UC_PROT_READ,UC_PROT_EXEC
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_XPSR
from audit_ram_v121 import APP,RAM,RAM_SIZE
from emulate_clock_v121 import Runner,StopModel
from emulate_front_v121 import FrontRunner
from nand_overlay import OverlayNand


class ConstantImage:
    """Unallocated erased backing store; overlays keep writes in memory."""
    def __init__(self,size,value):self.size=size;self.value=value
    def __getitem__(self,key):
        if isinstance(key,slice):
            start,stop,step=key.indices(self.size)
            return bytes([self.value])*len(range(start,stop,step))
        if not 0<=key<self.size:raise IndexError(key)
        return self.value


class BlankNand(OverlayNand):
    def __init__(self):
        # Same bus state as CapturedNand, with explicitly synthetic erased cells.
        self.sources={'synthetic':dict(kind='erased ideal NAND',captured=False)}
        self.handles=[]
        self.images={'nand_main_256MiB.bin':ConstantImage(268435456,255),
            'nand_oob64_8MiB.bin':ConstantImage(8388608,255),
            'nand_ecc_status_128KiB.bin':ConstantImage(131072,0)}
        self.idle=1;self.busy_polls=1;self.features={0xA0:0x38,0xB0:0x16}
        self.status=0;self.pending_busy=0;self.cached_page=None;self.cache=None
        self.cs=1;self.clk=0;self.mosi=0;self.miso=1;self.io0=1
        self.input_bits=0;self.accumulator=0;self.input_bytes=[];self.outputs={}
        self.transactions=[];self.opcodes=Counter();self.pages=Counter();self.feature_reads=Counter()
        self.read_bytes=0;self.array_writes=[];self.overlay={};self.program_buffer=None
        self.program_operations=[];self.erase_operations=[]
    def describe(self):
        value=super().describe();value['storage_mode']='synthetic erased NAND with volatile writes'
        return value


class HardwareRunner(FrontRunner):
    FLASH=0x08000000
    FLASH_SIZE=0x300000
    def __init__(self,image,*,load_address=APP,nand=None,profile=None,poison=0xA5,
                 live_directory=None,sct_boot=None):
        if len(image)<8 or load_address%128 or not self.FLASH<=load_address<load_address+len(image)<=self.FLASH+self.FLASH_SIZE:
            raise ValueError('Image must fit physical Flash and start at a vector-aligned address')
        stack,entry=struct.unpack_from('<II',image)
        if not RAM<stack<=RAM+RAM_SIZE or stack%8:raise ValueError('Initial stack outside physical SRAM or not 8-byte aligned')
        if not entry&1 or not load_address<=entry&~1<load_address+len(image):raise ValueError('Reset vector must be Thumb code in the supplied image')
        self.board_events=[];self.sampled_inputs=[];self.load_address=load_address
        super().__init__(image,nand or BlankNand(),poison,profile=profile,
            live_directory=live_directory,rtc_mode='retained',fast_mode=False,wake_once=False,idle_clock_scale=1)
        self.cpu.mem_write(self.FLASH,b'\xFF'*self.FLASH_SIZE)
        self.cpu.mem_write(load_address,image)
        self.cpu.mem_map(0,self.FLASH_SIZE,UC_PROT_READ|UC_PROT_EXEC)
        self.cpu.mem_write(0,bytes(self.cpu.mem_read(self.FLASH,self.FLASH_SIZE)))
        self.cpu.reg_write(UC_ARM_REG_SP,stack);self.cpu.reg_write(UC_ARM_REG_PC,entry)
        self.cpu.reg_write(UC_ARM_REG_XPSR,0x01000000)
        self.core[0xD08]=load_address
        self.reset_entry=entry;self.PA0=1
        self.lowest_sp=stack;self.lowest_sp_after_main=stack
        self.rf_spi.armed=False;self.lcd.armed=False;self.lighting.armed=False
        self.held_keys=set();self.gps_scenario=None
        if sct_boot:self.sct_hpi.start_boot(sct_boot)
        self.peripheral_deadline=0
        self.image_metadata=dict(load_address=hex(load_address),bytes=len(image),sha256=hashlib.sha256(image).hexdigest(),
            initial_stack=hex(stack),reset_vector=hex(entry),OEM_reference_required=False)

    def execution_address_valid(self,address):
        return (0<=address<self.FLASH_SIZE or self.FLASH<=address<self.FLASH+self.FLASH_SIZE or RAM<=address<RAM+RAM_SIZE)

    def gpio_mode(self,base,pin):
        return (self.gpio[base][4 if pin>=8 else 0]>>(4*(pin%8)))&15

    def physical_levels(self,base):
        # Known panel idle inputs; other floating inputs use an explicit pull-up
        # scenario, not an inference from the current CPU register or PC.
        external={0x40010800:0xFFFF,0x40010C00:0xFFFF,0x40011000:0xFFFF,
                  0x40011400:0xFFFF,0x40011800:0xFFFF}.get(base,0xFFFF)
        if base in self.panel_inputs:
            mask={0x40010800:0x403,0x40011000:0x300,0x40011400:1}[base]
            external=(external&~mask)|(self.panel_inputs[base]&mask)
        if base==0x40010800:
            external=(external&~0x8001)|(self.nand.miso<<15)|int(self.PA0!=0)
        if base==0x40010C00:
            external=(external&~0x4040)|(self.nand.io0<<14)|(self.fm_i2c.input_bit()<<6)
            if self.rf_spi.bank is not None and self.rf_spi.miso is not None:
                external=(external&~16)|(self.rf_spi.miso<<4)
        if base==0x40011400:
            external=(external&~0x20)|self.sct_hpi.status()
            if self.sct_hpi.armed and not self.gpio[base][12]&0x14:
                external=(external&255)|self.sct_hpi.input_data(self.gpio[base][12])
        value=0
        for pin in range(16):
            mode=self.gpio_mode(base,pin)
            level=(self.gpio[base][12] if mode&3 or mode==8 else external)
            # Connected external devices override input pull-up/down samples.
            if not mode&3:level=external
            value|=level&(1<<pin)
        return value

    def gpio_get(self,off,size):
        address=0x40010000+off;base=address&~0x3FF
        if 0x40010400<=address<0x40010800:
            word,shift,mask=self.lane(address-0x40010400,size)
            if word not in self.exti:raise StopModel('EXTI register not modelled')
            return (self.exti[word]>>shift)&mask
        if base in self.gpio:
            word,shift,mask=self.lane(address-base,size)
            if word==8:return (self.physical_levels(base)>>shift)&mask
        return Runner.gpio_get(self,off,size)

    def gpio_set(self,off,size,value):
        base=(0x40010000+off)&~0x3FF
        ports=(0x40010C00,0x40011000,0x40011800)
        before={p:self.physical_levels(p) for p in ports}
        before_d=self.gpio[0x40011400][12]
        lcd_ready=all(self.gpio_mode(0x40010C00,p)&3 for p in (10,11,13)) and all(self.gpio_mode(0x40011800,p)&3 for p in range(7,15))
        self.lcd.armed=lcd_ready
        self.lighting.armed=all(self.gpio_mode(p,n)&3 for p,n in ((0x40010800,5),(0x40010C00,3),(0x40010C00,4)))
        rf_ready=bool(self.gpio_mode(0x40010C00,3)&3)
        if rf_ready and not self.rf_spi.armed:self.rf_spi.armed=True
        # Bypass FrontRunner's RF dispatcher; invoke the other wire models and
        # generic GPIO/NAND writes, then feed RF with resolved pin levels.
        armed=self.rf_spi.armed;self.rf_spi.armed=False
        try:super().gpio_set(off,size,value)
        finally:self.rf_spi.armed=armed
        if armed:
            after={p:self.physical_levels(p) for p in ports}
            self.rf_spi.gpio(before,after,self.gpio_mode(0x40010C00,4),self.steps)
        if base==0x40011400 and not self.sct_hpi.armed:
            after_d=self.gpio[base][12]
            if not before_d&4 and not after_d&4 and not before_d&8 and after_d&8 and self.gpio[base][4]==0x33333333:
                raise StopModel('SCT bootstrap profile missing; HPI write observed without a qualified boot reference')

    def input_command(self,command):
        kind=command['control']
        if kind=='RF_RX':
            bank=int(command.get('bank',0));tone=command.get('ctcss','absent');carrier=bool(command.get('carrier',False))
            if bank not in (0,1) or tone not in ('absent','match','mismatch'):raise ValueError('Invalid synthetic RX input')
            if not hasattr(self.rf_spi,'external_inputs'):self.rf_spi.external_inputs={}
            self.rf_spi.external_inputs[bank]={0x0C:2 if carrier else 0,0x60:0xC00 if carrier and tone=='match' else 0,
                0x61:0,0x65:10 if carrier else 127,0x67:240 if carrier else 0}
        elif kind=='ADC_RAW':
            channel=str(command['channel']);value=int(command['value'])
            if not self.adc_dma.profile or channel not in self.adc_dma.profile['channels'] or not 0<=value<=4095:raise ValueError('Invalid ADC input')
            self.adc_dma.profile['channels'][channel]=value
        elif kind=='KEY_SET':
            from lab_inputs import validate_keys,FRONT_KEYS
            keys=validate_keys(command['keys']);self.held_keys=keys
            self.adc_dma.profile['channels'].update({'8':4095,'9':4095})
            for key in keys:
                if key in FRONT_KEYS:
                    channel,value=FRONT_KEYS[key];self.adc_dma.profile['channels'][str(channel)]=value
            previous=self.PA0;self.PA0=0 if 'POWER' in keys else 1
            if previous and not self.PA0 and not self.afio[8]&15 and self.exti[0]&self.exti[0xC]&1:
                self.exti[0x14]|=1;self.nvic_pending[0]|=1<<6
            self.panel_inputs[0x40010800]=(self.panel_inputs[0x40010800]|2)&(~2 if 'DIAL_PUSH' in keys else -1)
        else:super().input_command(command)
        self.board_events.append(dict(step=self.steps,input=command))

    def on_code(self,uc,address,size,data):
        # No calls to the inherited V1.21 observers or RAM interpretations.
        self.steps+=1;self.virtual_units+=1;self.last_instruction_units=1
        self.lowest_sp=min(self.lowest_sp,uc.reg_read(UC_ARM_REG_SP))
        if self.systick[0x10]&1:
            self.tick_fraction+=1;divider=1 if self.systick[0x10]&4 else 8
            if self.tick_fraction>=divider:
                self.tick_fraction=0;old=self.systick[0x18]
                self.systick[0x18]=old-1 if old else self.systick[0x14]
                if old==1:
                    self.tick_wraps+=1;self.systick[0x10]|=1<<16
                    if self.systick[0x10]&2:self.core_pending.add(15)
        try:
            self.adc_dma.advance(self.steps)
            if self.adc_dma.irq_requested:self.nvic_pending[0]|=1<<11
            for device,irq,_,_ in self.serial_devices.values():
                device.advance(self.steps)
                if device.irq:self.nvic_pending[irq//32]|=1<<(irq%32)
            if self.virtual_units>=self.peripheral_deadline:
                self.peripheral_deadline=self.virtual_units+64
                for timer,irq in self.timers.values():
                    timer.advance(self.virtual_units)
                    if timer.irq:self.nvic_pending[irq//32]|=1<<(irq%32)
                self.backup.advance(self.virtual_units)
                if self.backup.irq:self.nvic_pending[0]|=1<<3
            for irq,mask in ((6,1),(23,0x300)):
                if self.exti[0x14]&self.exti[0]&mask:self.nvic_pending[irq//32]|=1<<(irq%32)
            if not self.irq_active and self.stop is None:
                eligible=[e for e in self.core_pending if self.exception_eligible(e)]
                eligible += [irq+16 for irq in range(64) if self.nvic_pending[irq//32]&self.nvic_enable[irq//32]&(1<<(irq%32)) and self.exception_eligible(irq+16)]
                if eligible:self.halt('hardware interrupt delivery required',exception=min(eligible,key=lambda e:(self.exception_priority(e),e)))
            if self.steps>=self.input_poll:
                self.input_poll=self.steps+5000;self.poll_inputs()
            if self.stop is None and bytes(uc.mem_read(address,2)) in (b'\x20\xbf',b'\x30\xbf'):
                self.halt('waiting for interrupt or event')
        except StopModel as error:self.halt(str(error))
        if self.live_directory and self.steps-self.last_publish>=100000:self.publish()

    def publish(self,final=False):
        if not self.live_directory:return
        self.live_directory.mkdir(parents=True,exist_ok=True)
        if self.lcd.dirty or final:self.lcd.save(self.live_directory/'lcd.png')
        from live_io import publish_status
        publish_status(self.live_directory/'status.json',dict(running=not final,steps=self.steps,
            PC=hex(self.cpu.reg_read(UC_ARM_REG_PC)),stop=self.stop,mode='hardware',OEM_RAM_observers=False),final)
        self.last_publish=self.steps
        if not final and (self.live_directory/'stop.request').exists():self.halt('stopped by simulator user')

    def run_hardware(self,instructions):
        start=time.monotonic();limit=self.steps+instructions
        while self.steps<limit and self.stop is None:
            try:self.cpu.emu_start(self.cpu.reg_read(UC_ARM_REG_PC)|1,0,count=min(10000,limit-self.steps))
            except UcError as error:
                if self.stop is None:self.halt('CPU execution stopped',error=str(error))
            if self.stop and self.stop['kind']=='hardware interrupt delivery required':
                exception=self.stop['exception'];self.stop=None;self.deliver_systick(exception)
        if self.stop is None:self.stop=dict(kind='instruction_budget',step=self.steps,pc=hex(self.cpu.reg_read(UC_ARM_REG_PC)))
        kind=self.stop['kind']
        self.stop['category']=('control' if kind in ('instruction_budget','stopped by simulator user') else
            'waiting' if kind=='waiting for interrupt or event' else
            'physical_address_unmapped' if kind=='unmapped memory' else
            'model_incomplete' if any(word in kind.lower() for word in ('model','subset','profile','unsupported','required')) else
            'execution_boundary')
        self.publish(final=True)
        ram=bytes(self.cpu.mem_read(RAM,RAM_SIZE))
        result=dict(mode='hardware',image=self.image_metadata,steps=self.steps,stop=self.stop,
            host_seconds=round(time.monotonic()-start,3),ram_sha256=hashlib.sha256(ram).hexdigest(),
            CPU_PC=hex(self.cpu.reg_read(UC_ARM_REG_PC)),minimum_observed_SP=hex(self.lowest_sp),
            OEM_PC_hooks=False,OEM_RAM_observers=False,firmware_profile_required=False,
            execution_regions=[dict(start=hex(a),end_exclusive=hex(b)) for a,b in [(0,self.FLASH_SIZE),(self.FLASH,self.FLASH+self.FLASH_SIZE),(RAM,RAM+RAM_SIZE)]],
            lcd=self.lcd.describe(),radio=self.rf_spi.describe(),nand=self.nand.describe(),adc_dma=self.adc_dma.describe(),
            serial={d.name:d.describe() for d,_,_,_ in self.serial_devices.values()},
            SCT=self.sct_hpi.describe(),lighting=self.lighting.describe(),interrupts=self.irq_log,
            MMIO_events=self.events,inputs=self.board_events,
            qualified_for_physical_radio=False,cycle_accurate=False,
            limitations=['DSP/AMBE execution','PCM audio','APRS modulation DMA','all FMC modes',
                        'RF waveform and frequency-selective stimulus','nested and floating-point exceptions'])
        if hasattr(self,'memory_watch'):result['memory_watch']=self.memory_watch.describe()
        return result,ram
