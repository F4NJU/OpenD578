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
                 live_directory=None,sct_boot=None,vector_address=None):
        if len(image)<8 or load_address%128 or not self.FLASH<=load_address<load_address+len(image)<=self.FLASH+self.FLASH_SIZE:
            raise ValueError('Image must fit physical Flash and start at a vector-aligned address')
        if vector_address is None:vector_address=load_address
        offset=vector_address-load_address
        if vector_address%128 or not 0<=offset<=len(image)-8:raise ValueError('Invalid vector-table placement')
        stack,entry=struct.unpack_from('<II',image,offset)
        if not RAM<stack<=RAM+RAM_SIZE or stack%8:raise ValueError('Initial stack outside physical SRAM or not 8-byte aligned')
        if not entry&1 or not load_address<=entry&~1<load_address+len(image):raise ValueError('Reset vector must be Thumb code in the supplied image')
        self.board_events=[];self.sampled_inputs=[];self.load_address=load_address
        self.hardware_mode=True;self.interactive_mode=False;self.trace_enabled=False
        self.gpio_mode_cache={};self.sleeping=False;self.sleep_events=[];self.last_control_id=None
        self.serial_virtual_time=True
        seed=image[:self.FLASH_SIZE-(APP-self.FLASH)]
        super().__init__(seed,nand or BlankNand(),poison,profile=profile,
            live_directory=live_directory,rtc_mode='retained',fast_mode=False,wake_once=False,idle_clock_scale=1)
        self.cpu.mem_write(self.FLASH,b'\xFF'*self.FLASH_SIZE)
        self.cpu.mem_write(load_address,image)
        self.image=image
        self.cpu.mem_map(0,self.FLASH_SIZE,UC_PROT_READ|UC_PROT_EXEC)
        self.cpu.mem_write(0,bytes(self.cpu.mem_read(self.FLASH,self.FLASH_SIZE)))
        self.cpu.reg_write(UC_ARM_REG_SP,stack);self.cpu.reg_write(UC_ARM_REG_PC,entry)
        self.cpu.reg_write(UC_ARM_REG_XPSR,0x01000000)
        self.core[0xD08]=vector_address
        self.reset_entry=entry;self.PA0=1
        self.lowest_sp=stack;self.lowest_sp_after_main=stack
        self.rf_spi.armed=False;self.lcd.armed=False;self.lighting.armed=False
        self.held_keys=set();self.gps_scenario=None
        self.mic_connected=False;self.mic_keys=set();self.mic_lock=False;self.mic_code=0
        self.gps_config=dict(mode='absent');self.gps_next=10**30;self.gps_origin=0
        self.gps_startup=False;self.gps_frames=0;self.event_register=False
        from usbd_host import UsbdHost
        self.usbd=UsbdHost(clock_enabled=lambda:bool(self.clock.regs[0x1C]&(1<<23)) and not self.clock.regs[0x10]&(1<<23))
        if sct_boot:self.sct_hpi.start_boot(sct_boot)
        self.peripheral_deadline=0
        self.image_metadata=dict(load_address=hex(load_address),bytes=len(image),sha256=hashlib.sha256(image).hexdigest(),
            initial_stack=hex(stack),reset_vector=hex(entry),vector_address=hex(vector_address),OEM_reference_required=False)

    def enable_native(self):
        if getattr(self,'native_gate',None):return
        self.interactive_mode=True
        from native_gate import NativeGate
        NativeGate(self,hardware=True)

    def serial_deadline(self):
        if not hasattr(self,'serial_devices'):return
        deadlines=[]
        for device,irq,_,_ in self.serial_devices.values():
            if not device.clock_enabled() or not device.regs[0xC]&0x2000:continue
            if device.tx_shift:deadlines.append(device.tx_shift[1])
            if device.rx_wire and device.regs[0xC]&4:deadlines.append(device.rx_wire[0][0])
        self.serial_next=min(deadlines,default=10**30)

    def pending_exceptions(self):
        pending=set(self.core_pending)
        for group in range(2):
            bits=self.nvic_pending[group]&self.nvic_enable[group]
            while bits:
                low=bits&-bits;bits^=low
                pending.add(16+32*group+low.bit_length()-1)
        return pending

    def next_event_delay(self):
        delays=[4096,max(1,self.serial_next-self.virtual_units),max(1,self.gps_next-self.virtual_units)]
        if self.systick[0x10]&1:
            divider=1 if self.systick[0x10]&4 else 8
            delays.append(max(1,(self.systick[0x18] or self.systick[0x14]+1)*divider-self.tick_fraction))
        if self.adc_dma.active and self.adc_dma.next_step is not None:
            delays.append(max(1,self.adc_dma.next_step-self.virtual_units))
        if self.fwdgt.running:delays.append(max(1,self.fwdgt.deadline-self.virtual_units))
        from interactive_runtime import peripheral_interval
        delays.append(peripheral_interval(self))
        if not self.irq_active and any(self.exception_eligible(e) for e in self.pending_exceptions()):delays.append(1)
        return min(delays)

    def advance_time(self,units):
        self.virtual_units+=units
        if self.systick[0x10]&1:
            divider=1 if self.systick[0x10]&4 else 8
            ticks,self.tick_fraction=divmod(self.tick_fraction+units,divider)
            while ticks:
                distance=self.systick[0x18] or self.systick[0x14]+1
                if ticks<distance:
                    self.systick[0x18]=distance-ticks;break
                ticks-=distance;self.systick[0x18]=0
                self.tick_wraps+=1;self.systick[0x10]|=1<<16
                if self.systick[0x10]&2:self.core_pending.add(15)
        self.adc_dma.advance(self.virtual_units)
        if self.adc_dma.irq_requested:self.nvic_pending[0]|=1<<11
        for device,irq,_,_ in self.serial_devices.values():
            if device.tx_shift or device.rx_wire:device.advance(self.virtual_units)
            if device.irq:self.nvic_pending[irq//32]|=1<<(irq%32)
        self.advance_gps()
        self.serial_deadline()
        for timer,irq in self.timers.values():
            timer.advance(self.virtual_units)
            if timer.irq:self.nvic_pending[irq//32]|=1<<(irq%32)
        self.backup.advance(self.virtual_units)
        if self.backup.irq:self.nvic_pending[0]|=1<<3
        for irq,mask in ((6,1),(23,0x300)):
            if self.exti[0x14]&self.exti[0]&mask:self.nvic_pending[irq//32]|=1<<(irq%32)
        if getattr(self,'cdc',None):
            from usb_cdc_runtime import poll as cdc_poll
            cdc_poll(self)
        if getattr(self.usbd,'irq',False):self.nvic_pending[0]|=1<<20
        if self.fwdgt.advance(self.virtual_units):self.halt('watchdog reset requested',source='FWDGT',automatic_reboot=False)

    def advance_gps(self):
        device=self.usart1
        if self.gps_config['mode']=='absent' or self.virtual_units<self.gps_next:return
        if not device.clock_enabled() or device.regs[0xC]&0x2004!=0x2004:return
        if device.rx_wire or device.received_data is not None:return
        from lab_inputs import nmea,gps_sentences
        from datetime import datetime,timedelta
        if self.gps_startup:
            payload=nmea('PMTK010,001');self.gps_startup=False
        else:
            utc=(datetime.fromisoformat(self.gps_config['utc'])+timedelta(seconds=(self.virtual_units-self.gps_origin)/120000000)).isoformat()
            payload=gps_sentences(self.gps_config['latitude'],self.gps_config['longitude'],utc,self.gps_config['mode']=='fix')
            self.gps_frames+=1
        device.advance(self.virtual_units);device.schedule(payload)
        self.gps_next=self.virtual_units+120000000//self.gps_config['hertz']

    def core_set(self,off,size,value):
        word,shift,mask=self.lane(off,size)
        if 0x200<=word<0x220 and size==4:
            self.nvic_pending[(word-0x200)//4]|=value;return
        if word==0xF00 and size==4:
            if value>=64:raise StopModel('Software interrupt outside implemented NVIC IRQ0..63')
            self.nvic_pending[value//32]|=1<<(value%32);return
        return super().core_set(off,size,value)

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
        modes=(self.gpio[base][0],self.gpio[base][4])
        cached=self.gpio_mode_cache.get(base)
        if cached is None or cached[0]!=modes:
            output=sum(1<<pin for pin in range(16) if self.gpio_mode(base,pin)&3)
            cached=(modes,output);self.gpio_mode_cache[base]=cached
        output=cached[1]
        return (self.gpio[base][12]&output)|(external&~output&65535)

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
        word=off&0x3FF
        if base==0x40010400 and word==0x10:
            self.exti[word]|=value;self.exti[0x14]|=value;return
        ports=(0x40010C00,0x40011000,0x40011800)
        mask=(value|(value>>16))&65535 if word==16 else value if word==20 else 65535 if word in (0,4,12) else 0
        rf_relevant=base in ports and bool(mask&{0x40010C00:0x3C,0x40011000:0x2000,0x40011800:2}[base])
        before={p:self.physical_levels(p) for p in ports} if rf_relevant else None
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
        if armed and before is not None:
            after={p:self.physical_levels(p) for p in ports}
            self.rf_spi.gpio(before,after,self.gpio_mode(0x40010C00,4),self.steps)
        if base==0x40011400 and not self.sct_hpi.armed:
            after_d=self.gpio[base][12]
            if not before_d&4 and not after_d&4 and not before_d&8 and after_d&8 and self.gpio[base][4]==0x33333333:
                raise StopModel('SCT bootstrap profile missing; HPI write observed without a qualified boot reference')

    def input_command(self,command):
        kind=command['control']
        if kind.startswith('USB_CDC_'):
            from usb_cdc_runtime import command as cdc_command
            if cdc_command(self,command):return
        if kind=='STOP':self.halt('stopped by simulator user')
        elif kind=='TRACE':self.trace_enabled=bool(command['enabled'])
        elif kind=='EVENT':self.event_register=True
        elif kind=='USB_HOST':
            self.usbd.token(command['token'],int(command.get('endpoint',0)),bytes.fromhex(command.get('hex','')))
            if self.usbd.irq:self.nvic_pending[0]|=1<<20
        elif kind=='UART_RX':
            devices={device.name:device for device,_,_,_ in self.serial_devices.values()}
            device=devices[command['port']];payload=bytes.fromhex(command['hex'])
            if len(payload)>4096:raise ValueError('UART input too long')
            device.advance(self.virtual_units);device.schedule(payload);self.serial_deadline()
        elif kind=='MIC_CONNECT':
            from lab_inputs import MicrophonePeer
            from uart_serial import IdlePeer
            self.mic_connected=bool(command['connected'])
            self.usart0.peer=MicrophonePeer() if self.mic_connected else IdlePeer()
            if not self.mic_connected:self.mic_keys=set();self.usart0.rx_wire.clear()
        elif kind=='MIC_LOCK':self.mic_lock=bool(command['locked'])
        elif kind=='MIC_KEYS':
            from lab_inputs import microphone_frame,MIC_CODES
            if not self.mic_connected:raise ValueError('Connect the simulated microphone first')
            keys=set(command['keys'])
            if self.mic_lock:keys-={'UP','DOWN'}
            payload=microphone_frame(keys,last_code=self.mic_code)
            self.mic_keys=keys
            if keys-{'PTT'}:self.mic_code=MIC_CODES[next(iter(keys-{'PTT'}))]
            self.usart0.advance(self.virtual_units);self.usart0.schedule(payload);self.serial_deadline()
        elif kind=='GPS':
            from lab_inputs import gps_sentences
            mode=command['mode'];rate=int(command.get('hertz',1))
            if mode not in ('absent','fix','no_fix') or rate not in (1,2,4):raise ValueError('Invalid GPS scenario')
            values=dict(mode=mode,latitude=float(command.get('latitude',48)),longitude=float(command.get('longitude',2)),
                utc=command.get('utc','2026-11-05T12:00:00'),hertz=rate)
            gps_sentences(values['latitude'],values['longitude'],values['utc'],mode=='fix')
            self.gps_startup=mode!='absent' and self.gps_config['mode']=='absent'
            self.gps_config=values;self.gps_origin=self.virtual_units
            self.gps_next=self.virtual_units if mode!='absent' else 10**30
        elif kind=='RELEASE_ALL':
            self.input_command(dict(control='KEY_SET',keys=[]))
            if self.mic_connected:self.input_command(dict(control='MIC_KEYS',keys=[]))
        elif kind=='VOLTAGE':raise ValueError('Hardware mode requires raw ADC11 samples; OEM voltage calibration is not assumed')
        elif kind=='RF_RX':
            bank=int(command.get('bank',0));tone=command.get('ctcss','absent');carrier=bool(command.get('carrier',False))
            if bank not in (0,1) or tone not in ('absent','match','mismatch'):raise ValueError('Invalid synthetic RX input')
            if not hasattr(self.rf_spi,'external_inputs'):self.rf_spi.external_inputs={}
            noise=int(command.get('noise',10 if carrier else 127));strength=int(command.get('strength',240 if carrier else 0))
            if not 0<=noise<=127 or not 0<=strength<=511:raise ValueError('Invalid RF sample')
            self.rf_spi.external_inputs[bank]={0x0C:2 if carrier else 0,0x60:0xC00 if carrier and tone=='match' else 0,
                0x61:0,0x65:noise,0x67:strength}
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
        self.steps+=1;self.last_instruction_units=1
        self.lowest_sp=min(self.lowest_sp,uc.reg_read(UC_ARM_REG_SP))
        try:
            self.advance_time(1)
            if not self.irq_active and self.stop is None:
                eligible=[e for e in self.pending_exceptions() if self.exception_eligible(e)]
                if eligible:self.halt('hardware interrupt delivery required',exception=min(eligible,key=lambda e:(self.exception_priority(e),e)))
            if self.steps>=self.input_poll:
                self.input_poll=self.steps+5000;self.poll_inputs()
            opcode=bytes(uc.mem_read(address,2))
            if opcode==b'\x40\xbf':self.event_register=True
            if self.stop is None and opcode in (b'\x20\xbf',b'\x30\xbf'):
                if opcode==b'\x20\xbf' and self.event_register:
                    self.event_register=False;return
                self.sleeping=True
                self.cpu.reg_write(UC_ARM_REG_PC,(address+2)|1)
                self.sleep_events.append(dict(step=self.steps,PC=hex(address),kind='WFI/WFE',virtual_units=self.virtual_units))
                self.halt('waiting for interrupt or event')
        except StopModel as error:self.halt(str(error))
        if self.live_directory and self.steps-self.last_publish>=100000:self.publish()

    def publish(self,final=False):
        if not self.live_directory:return
        self.live_directory.mkdir(parents=True,exist_ok=True)
        if self.lcd.dirty or final:self.lcd.save(self.live_directory/'lcd.png')
        from live_io import publish_status
        publish_status(self.live_directory/'status.json',dict(running=not final,steps=self.steps,
            PC=hex(self.cpu.reg_read(UC_ARM_REG_PC)),stop=self.stop,mode='hardware',OEM_RAM_observers=False,
            pixels=self.lcd.total_pixels,display_on=self.lcd.display_on,sleeping=self.sleeping,
            last_control_id=self.last_control_id,model_seconds=self.virtual_units/120000000,
            execution_engine='native hardware' if getattr(self,'native_gate',None) else 'Python hardware',
            hardware=self.hardware_state()),final)
        self.last_publish=self.steps
        if not final and (self.live_directory/'stop.request').exists():self.halt('stopped by simulator user')

    def hardware_state(self):
        from board_clock import describe_clock
        from board_observations import describe
        return dict(board_outputs=describe(self),OEM_state_interpretation_qualified=False,
            clocks=describe_clock(self.clock.regs,self.systick),
            LCD=dict(display_on=self.lcd.display_on,sleeping=self.lcd.sleeping,brightness=self.lighting.registers.get(8,255)),
            NAND=dict(erases=len(self.nand.erase_operations),programs=len(self.nand.program_operations)),
            Flash=dict(erases=len(self.flash_cache.erases),programs=self.flash_cache.program_count),
            ADC=dict(samples=self.adc_dma.profile['channels'],transfers=self.adc_dma.total_transfers),
            UART={device.name:dict(tx=len(device.tx),rx=len(device.rx),overruns=device.overruns) for device,_,_,_ in self.serial_devices.values()},
            SCT=dict(boot_complete=self.sct_hpi.boot_complete,packets=len(self.sct_hpi.frames)),
            USB=self.usbd.describe(),gps_input=dict(**self.gps_config,frames=self.gps_frames),
            RF_banks={str(bank):dict(transactions=sum(f['bank']==bank for f in self.rf_spi.frames),selector=['PB5','PB2','PC13','PE1'][bank]) for bank in range(4)},
            front_held_keys=sorted(self.held_keys),microphone=dict(connected=self.mic_connected,held_keys=sorted(self.mic_keys)),
            firmware=self.image_metadata,coverage=getattr(self,'coverage',None).summary() if getattr(self,'coverage',None) else None)

    def wake_delay(self):
        delays=[]
        if getattr(self,'cdc',None) and self.cdc.state not in ('disconnected','error'):delays.append(2048)
        if self.core.get(0xD10,0)&4:return None
        if self.systick[0x10]&3==3 and self.exception_eligible(15):
            divider=1 if self.systick[0x10]&4 else 8
            delays.append((self.systick[0x18] or self.systick[0x14]+1)*divider-self.tick_fraction)
        for timer,irq in self.timers.values():
            if self.nvic_enable[irq//32]&(1<<(irq%32)) and timer.clock_enabled() and timer.regs[0]&1 and timer.regs[0xC]&1:
                delays.append(max(1,(timer.regs[0x2C]+1-timer.regs[0x24])*(timer.prescaler+1)-timer.remainder))
        for device,irq,_,_ in self.serial_devices.values():
            if self.nvic_enable[irq//32]&(1<<(irq%32)) and device.regs[0xC]&0x2000:
                if device.tx_shift and device.regs[0xC]&0xC0:delays.append(max(1,device.tx_shift[1]-self.virtual_units))
                if device.rx_wire and device.regs[0xC]&0x24==0x24:delays.append(max(1,device.rx_wire[0][0]-self.virtual_units))
        if self.nvic_enable[0]&(1<<11) and self.adc_dma.active and self.adc_dma.dma[8]&14:
            delays.append(max(1,self.adc_dma.next_step-self.virtual_units))
        return min(delays,default=None)

    def run_hardware(self,instructions,wait_for_input=False):
        if self.stop and self.stop['kind'] in ('instruction_budget','waiting for interrupt or event'):self.stop=None
        start=time.monotonic();limit=self.steps+instructions
        idle_budget=100000
        while self.steps<limit and self.stop is None:
            if self.sleeping:
                self.poll_inputs()
                eligible=[e for e in self.pending_exceptions() if self.exception_eligible(e)]
                if eligible:
                    self.sleeping=False
                    self.deliver_systick(min(eligible,key=lambda e:(self.exception_priority(e),e)))
                elif self.event_register:
                    self.sleeping=False;self.event_register=False
                else:
                    delay=self.wake_delay()
                    if delay is not None and idle_budget>0:
                        try:self.advance_time(min(delay,self.next_event_delay()))
                        except StopModel as error:self.halt(str(error))
                        idle_budget-=1
                        continue
                    if wait_for_input and self.stop is None:
                        if time.monotonic()-getattr(self,'last_wait_publish',0)>.1:
                            self.publish();self.last_wait_publish=time.monotonic()
                        time.sleep(.02);continue
                    self.halt('waiting for interrupt or event');break
            before_steps=self.steps
            try:self.cpu.emu_start(self.cpu.reg_read(UC_ARM_REG_PC)|1,0,count=min(10000,limit-self.steps))
            except UcError as error:
                if self.stop is None:self.halt('CPU execution stopped',error=str(error))
            # Bound a stretch with no CPU progress, not the whole lifetime of
            # an interactive run. Otherwise a healthy SysTick/WFI application
            # eventually exhausts this allowance and stops advancing time.
            if self.steps>before_steps:idle_budget=100000
            if self.stop and self.stop['kind']=='hardware interrupt delivery required':
                exception=self.stop['exception'];self.stop=None;self.deliver_systick(exception)
            if self.stop and self.stop['kind']=='waiting for interrupt or event':self.stop=None
        if self.stop is None:self.stop=dict(kind='instruction_budget',step=self.steps,pc=hex(self.cpu.reg_read(UC_ARM_REG_PC)))
        kind=self.stop['kind']
        self.stop['category']=('control' if kind in ('instruction_budget','stopped by simulator user') else
            'reset_requested' if kind in ('watchdog reset requested','software reset requested') else
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
        result.update(virtual_core_units=self.virtual_units,sleep_events=self.sleep_events,
            USB=self.usbd.describe(),watchdog=self.fwdgt.describe(),MMIO_counts={route+':'+op:count for (route,op),count in self.log_counts.items()})
        if getattr(self,'native_gate',None):result['execution_engine']=self.native_gate.describe()
        if getattr(self,'coverage',None):result['coverage']=self.coverage.describe()
        if hasattr(self,'memory_watch'):result['memory_watch']=self.memory_watch.describe()
        return result,ram
