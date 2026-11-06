"""V6 front panel, timer and battery-domain extension of the LCD simulator."""
from emulate_lcd_v121 import LcdRunner
from emulate_clock_v121 import StopModel
from timers import Timer
from backup_rtc import BackupRtc
from unicorn.arm_const import UC_ARM_REG_PRIMASK,UC_ARM_REG_FAULTMASK,UC_ARM_REG_BASEPRI,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_PC
import json
from lighting import LightingBus
from status_led import StatusLedBus
from datetime import datetime,timezone
from flash_cache import FlashCache
from rf_spi import RfSpi
from fm_i2c import FmI2c
from cortex_exceptions import CortexExceptions
from sct_hpi import SctHpi
from usbd_idle import UsbdIdle
from unicorn.arm_const import UC_ARM_REG_R2
from unicorn import UC_HOOK_MEM_WRITE,UC_PROT_ALL


class FrontRunner(CortexExceptions,LcdRunner):
    def __init__(self,*args,rtc_mode='retained',rtc_date='2026-11-04T12:00:00',**kwargs):
        if rtc_mode not in ('retained','empty'):
            raise ValueError('RTC mode must be retained or empty')
        self.rtc_initial_mode=rtc_mode
        self.rtc_initial_date=rtc_date if rtc_mode=='retained' else None
        self.virtual_units = 0
        self.peripheral_deadline = 10**30
        self.timers = {}
        self.backup = None
        self.lighting=LightingBus()
        self.status_led=StatusLedBus()
        self.panel_inputs = {0x40010800:0x403,0x40011000:0x300,0x40011400:1}
        self.panel_events = []
        self.input_poll = 0
        self.key_releases = []
        self.power_release = None
        self.i2c_absent_reads=0
        self.i2c_oem_bytes=[]
        self.baseband_idle_reads=0
        self.flash_cache=None
        self.rf_spi=RfSpi()
        self.fm_i2c=FmI2c()
        self.sct_hpi=SctHpi()
        self.usbd=UsbdIdle()
        from watchdog import FreeWatchdog
        self.fwdgt=FreeWatchdog()
        super().__init__(*args,**kwargs)
        self.flash_cache=FlashCache(self.cpu.mem_read,self.cpu.mem_write)
        self.cpu.mem_protect(FlashCache.START,FlashCache.END-FlashCache.START,UC_PROT_ALL)
        self.cpu.hook_add(UC_HOOK_MEM_WRITE,self.flash_program,
                          begin=FlashCache.START,end=FlashCache.END-1)
        for index,irq in ((1,28),(2,29),(3,30),(4,50),(5,54),(6,55)):
            bit = index-1 if index<5 else index-1
            self.timers[0x40000000+(index-1)*0x400] = (Timer('TIMER'+str(index),
                clock_enabled=lambda bit=bit:bool(self.clock.regs[0x1C] & (1<<bit)) and not bool(self.clock.regs[0x10] & (1<<bit))),irq)
        for base in (0x40000000,0x40001000):
            self.cpu.mmio_map(base,4096,
                lambda uc,off,size,data,base=base:self.timer_read(base+off,size),None,
                lambda uc,off,size,value,data,base=base:self.timer_write(base+off,size,value),None)
        self.backup = BackupRtc(write_enabled=lambda:bool(self.pmu_ctl & 0x100),
            enabled=lambda:self.clock.regs[0x20] & 0x8303 == 0x8103)
        if rtc_mode=='retained':
            stamp=int(datetime.fromisoformat(rtc_date).replace(tzinfo=timezone.utc).timestamp())
            self.backup.backup[4]=0x5050
            self.backup.regs.update({4:0x28,12:0x7FFF,24:stamp>>16,28:stamp&0xFFFF})
            self.clock.regs[0x20]=0x8103
        self.cpu.mmio_map(0x40002000,4096,
            lambda uc,off,size,data:self.rtc_read(off-0x800,size),None,
            lambda uc,off,size,value,data:self.rtc_write(off-0x800,size,value),None)
        self.cpu.mmio_map(0x40005000,4096,
            lambda uc,off,size,data:self.usbd_read(off-0xC00,size),None,
            lambda uc,off,size,value,data:self.usbd_write(off-0xC00,size,value),None)
        self.cpu.mmio_map(0x40006000,4096,
            lambda uc,off,size,data:self.rtc_read(off-0xC00,size,True) if off>=0xC00 else self.usbd_read(off,size,True),None,
            lambda uc,off,size,value,data:self.rtc_write(off-0xC00,size,value,True) if off>=0xC00 else self.usbd_write(off,size,value,True),None)
        self.cpu.mmio_map(0x420D8000,4096,self.bkp_alias_read,None,self.bkp_alias_write,None)
        self.cpu.mmio_map(0x420E0000,4096,self.pmu_alias_read,None,self.pmu_alias_write,None)
        self.cpu.mmio_map(0x40003000,4096,
            lambda uc,off,size,data:self.checked_read(lambda:self.fwdgt.read(off,size),0x40003000+off,size,'FWDGT'),None,
            lambda uc,off,size,value,data:self.checked_write(lambda:self.fwdgt.write(off,size,value,self.virtual_units),0x40003000+off,size,value,'FWDGT'),None)

    def fmc_read(self,uc,off,size,data):
        if off==0:return super().fmc_read(uc,off,size,data)
        return self.checked_read(lambda:self.flash_cache.read(off,size),0x40022000+off,size,'FMC_CACHE')

    def usbd_read(self,off,size,memory=False):
        return self.checked_read(lambda:(self.usbd.memory_read if memory else self.usbd.read)(off,size),
            (0x40006000 if memory else 0x40005C00)+off,size,'USBD')

    def usbd_write(self,off,size,value,memory=False):
        self.checked_write(lambda:(self.usbd.memory_write if memory else self.usbd.write)(off,size,value),
            (0x40006000 if memory else 0x40005C00)+off,size,value,'USBD')

    def fmc_write(self,uc,off,size,value,data):
        if off==0:return super().fmc_write(uc,off,size,value,data)
        self.checked_write(lambda:self.flash_cache.write(off,size,value),0x40022000+off,size,value,'FMC_CACHE')

    def flash_program(self,uc,access,address,size,value,data):
        try:self.flash_cache.program(address,size,value)
        except StopModel as error:self.halt(str(error),address)

    def gpio_get(self,off,size):
        if getattr(self,'interactive_mode',False) and off==0x180C and size==4:
            return self.gpio[0x40011800][12]
        address=0x40010000+off
        if address & 0x3FF == 8 and size==4:
            base=address & ~0x3FF
            mask=self.cpu.reg_read(UC_ARM_REG_R1)
            if base==0x40011400 and mask==0x20 and (self.gpio[base][0]>>20)&15==8:
                # OEM 0x08092FE8 configures PD5 as an input with pull-up.
                # Disconnected host-port interrupt line: no active-low event.
                self.baseband_idle_reads+=1
                return self.sct_hpi.status() if self.sct_hpi.armed else self.gpio[base][12]&0x20
            if base==0x40010C00 and mask==0x40 and (self.gpio[base][0]>>24)&15==8 and self.gpio[base][12]&0x40:
                self.i2c_absent_reads+=1
                return self.fm_i2c.input_bit()<<6
            if base==0x40010C00 and mask==0x10 and (self.gpio[base][0]>>16)&15==8:
                return self.rf_spi.input_bit()<<4
            if base in self.panel_inputs and mask and not mask & ~({0x40010800:0x403,0x40011000:0x300,0x40011400:1}[base]):
                value=self.panel_inputs[base]
                if base==0x40010800 and self.PA0 is not None:
                    value=(value & ~1)|self.PA0
                return value
            if base==0x40011400 and self.sct_hpi.armed and self.gpio[base][4]==0x88888888:
                return self.sct_hpi.input_data(self.gpio[base][12])
        return super().gpio_get(off,size)

    def gpio_set(self,off,size,value):
        address=0x40010000+off
        before_status=self.gpio[0x40011800][12] if address&~0x3FF==0x40011800 else None
        watched=(0x40010C00,0x40011000,0x40011800)
        base=address&~0x3FF
        word=off&0x3FF
        drive_mask=(value|(value>>16))&0xFFFF if word==16 else value if word==20 else 0xFFFF if word==12 else 0
        rf_relevant=base in watched and bool(drive_mask&{0x40010C00:0x3C,0x40011000:0x2000,0x40011800:2}[base])
        before_d=self.gpio[0x40011400][12] if self.sct_hpi.armed and base==0x40011400 and drive_mask&0xFF1C else None
        if base==0x40010C00 and (drive_mask&0xC0 or word==0 and (value^self.gpio[base][0])&0xFF000000):
            before_b=self.gpio[0x40010C00][12]
            old_mode=(self.gpio[0x40010C00][0]>>24)&15
        else:before_b=None
        if self.rf_spi.armed and rf_relevant:
            before={port:self.gpio[port][12] for port in watched}
            self.gpio_set_devices(off,size,value)
            after={port:self.gpio[port][12] for port in watched}
            self.rf_spi.gpio(before,after,(self.gpio[0x40010C00][0]>>16)&15,self.steps)
        else:self.gpio_set_devices(off,size,value)
        if before_b is not None:
            self.fm_i2c.gpio(before_b,self.gpio[0x40010C00][12],old_mode,
                (self.gpio[0x40010C00][0]>>24)&15,self.steps)
        if before_status is not None:
            self.status_led.gpio(before_status,self.gpio[0x40011800][12],self.gpio[0x40011800][0],self.steps)
        if before_d is not None:
            self.sct_hpi.gpio(before_d,self.gpio[0x40011400][12],self.gpio[0x40011400][4])

    def gpio_set_devices(self,off,size,value):
        base=(0x40010000+off)&~0x3FF
        word=off&0x3FF
        mask=value | (value>>16) if word==0x10 else value if word==0x14 else 0xFFFF if word==12 else 0
        relevant=(base==0x40010800 and mask&32) or (base==0x40010C00 and mask&24)
        if not relevant:
            return super().gpio_set(off,size,value)
        before_a=self.gpio[0x40010800][12]
        before_b=self.gpio[0x40010C00][12]
        super().gpio_set(off,size,value)
        self.lighting.gpio(before_a,self.gpio[0x40010800][12],
                           before_b,self.gpio[0x40010C00][12],self.steps)

    def input_command(self,command):
        kind=command['control']
        event=dict(step=self.steps,virtual_units=self.virtual_units,command=command.copy())
        self.panel_events.append(event)
        keys={'P1':(8,250),'P2':(8,1000),'P3':(8,2000),'MENU':(8,3000),
              'P4':(9,250),'P5':(9,1000),'P6':(9,2000),'EXIT':(9,3000)}
        if kind in keys:
            channel,value=keys[kind]
            self.adc_dma.profile['channels'][str(channel)] = value
            self.key_releases.append((self.tick_wraps+80,'adc',channel))
        elif kind=='RELEASE_KEYS':
            self.adc_dma.profile['channels'].update({'8':4095,'9':4095})
            self.panel_inputs[0x40010800]|=2
            self.key_releases=[]
        elif kind=='DIAL_PUSH':
            self.panel_inputs[0x40010800] &= ~2
            self.key_releases.append((self.tick_wraps+15,'gpio',2))
        elif kind in ('DIAL_UP','DIAL_DOWN'):
            self.panel_inputs[0x40011000]=(0 if kind=='DIAL_UP' else 0x200)
            self.exti[0x14] |= 0x100
            self.nvic_pending[0] |= 1<<23
            self.key_releases.append((self.tick_wraps+1,'encoder',0))
        elif kind in ('VOLUME_A','VOLUME_B'):
            value=int(command['value'])
            if not 0<=value<=4095:
                raise ValueError('Volume outside 12-bit range')
            self.adc_dma.profile['channels']['12' if kind=='VOLUME_A' else '15']=value
        elif kind=='POWER':
            self.PA0=0
            self.power_release=self.tick_wraps+400
            # Only the initial standby routes PA0 to EXTI0. In normal mode
            # OEM software polls PA0; IRQ6 may be remapped to microphone PD0.
            if not self.afio[8]&15 and self.exti[0]&1 and self.exti[0xC]&1:
                self.exti[0x14]|=1
                self.nvic_pending[0]|=1<<6
        else:
            raise ValueError('Unknown front control '+kind)

    def poll_inputs(self):
        inbox=getattr(self,'control_inbox',None)
        if inbox:
            for command in inbox.drain():
                request_id=command.pop('_request_id',None)
                if command.get('control')=='STOP':
                    self.halt('stopped by simulator user')
                else:
                    try:self.input_command(command)
                    except (OSError,ValueError,KeyError) as error:
                        self.panel_events.append(dict(step=self.steps,error=str(error)))
                self.last_control_id=request_id
        if self.live_directory and not inbox:
            for path in sorted(self.live_directory.glob('input_*.json')):
                try:
                    self.input_command(json.loads(path.read_text(encoding='utf-8')))
                except (OSError,ValueError,KeyError) as error:
                    self.panel_events.append(dict(step=self.steps,error=str(error)))
                path.unlink(missing_ok=True)
        for release in self.key_releases[:]:
            tick,kind,value=release
            if self.tick_wraps>=tick:
                if kind=='adc':self.adc_dma.profile['channels'][str(value)]=4095
                elif kind=='gpio':self.panel_inputs[0x40010800]|=value
                elif kind=='encoder':self.panel_inputs[0x40011000]=0x300
                self.key_releases.remove(release)
        if self.power_release and self.tick_wraps>=self.power_release:
            self.PA0=1
            self.power_release=None

    def pmu_alias_read(self,uc,off,size,data):
        word,bit=self.alias_decode(off,size)
        if word != 0:
            self.halt('PMU bit-band register outside subset',0x420E0000+off)
            return 0
        return (self.pmu_ctl>>bit)&1

    def pmu_alias_write(self,uc,off,size,value,data):
        word,bit=self.alias_decode(off,size)
        if word != 0:
            self.halt('PMU bit-band register outside subset',0x420E0000+off)
            return
        self.pmu_ctl=(self.pmu_ctl & ~(1<<bit))|((value&1)<<bit)

    def timer_device(self,address):
        base = address & ~0x3FF
        if base not in self.timers:
            raise StopModel('timer outside qualified subset')
        timer,irq = self.timers[base]
        timer.advance(self.virtual_units)
        return timer,address-base

    def timer_read(self,address,size):
        def read():
            timer,offset = self.timer_device(address)
            return timer.read(offset,size)
        return self.checked_read(read,address,size,'TIMER')

    def timer_write(self,address,size,value):
        def write():
            timer,offset = self.timer_device(address)
            timer.write(offset,size,value)
            self.peripheral_deadline = min(self.peripheral_deadline,self.virtual_units+1)
        self.checked_write(write,address,size,value,'TIMER')

    def rtc_read(self,off,size,backup=False):
        self.backup.advance(self.virtual_units)
        return self.checked_read(lambda:self.backup.read(off,size,backup),
            (0x40006C00 if backup else 0x40002800)+off,size,'BKP' if backup else 'RTC')

    def rtc_write(self,off,size,value,backup=False):
        self.backup.advance(self.virtual_units)
        self.checked_write(lambda:self.backup.write(off,size,value,backup),
            (0x40006C00 if backup else 0x40002800)+off,size,value,'BKP' if backup else 'RTC')
        self.peripheral_deadline = min(self.peripheral_deadline,self.virtual_units+1)

    def bkp_alias_read(self,uc,off,size,data):
        word,bit = self.alias_decode(off,size)
        return (self.rtc_read(word,4,True)>>bit)&1

    def bkp_alias_write(self,uc,off,size,value,data):
        word,bit = self.alias_decode(off,size)
        old = self.backup.backup.get(word)
        if old is None:
            self.halt('BKP bit-band register outside subset',0x420D8000+off)
        else:
            self.rtc_write(word,4,(old & ~(1<<bit))|((value&1)<<bit),True)

    def clock_set(self,off,size,value):
        super().clock_set(off,size,value)
        self.refresh_backup_clock()

    def alias_set(self,off,size,value):
        super().alias_set(off,size,value)
        self.refresh_backup_clock()

    def refresh_backup_clock(self):
        # LXTAL stable follows enable in this explicitly ideal oscillator model.
        bd = self.clock.regs[0x20]
        self.clock.regs[0x20] = (bd & ~2) | (2 if bd & 1 else 0)
        if bd & 0x10000 and self.backup is not None:
            self.backup.reset()

    def irq_eligible(self,irq):
        cpu = self.cpu
        priority = (self.nvic_priorities.get(0x400+(irq & ~3),0)>>(8*(irq%4)))&255
        basepri = cpu.reg_read(UC_ARM_REG_BASEPRI)
        return (not self.irq_active and self.nvic_enable[irq//32] & (1<<(irq%32)) and
            not (cpu.reg_read(UC_ARM_REG_PRIMASK) or cpu.reg_read(UC_ARM_REG_FAULTMASK)) and
            (not basepri or priority < basepri))

    def on_code(self,uc,address,size,data):
        super().on_code(uc,address,size,data)
        self.virtual_units += self.last_instruction_units
        # An interrupt may stop Unicorn before this instruction executes.
        # Its PC is visited again after exception return. Do not enqueue an
        # OEM call twice (one expectation would remain ahead of the next frame).
        if self.stop is not None:return
        if getattr(self,'cdc',None):
            from usb_cdc_runtime import poll as cdc_poll
            cdc_poll(self)
            if self.usbd.irq and self.irq_eligible(20):
                self.halt('front peripheral interrupt delivery required',irq=20)
                return
        if self.fwdgt.advance(self.virtual_units):
            self.halt('watchdog reset requested',source='FWDGT',automatic_reboot=False)
            return
        if address==0x0808A7C0:
            self.lighting.armed=True
            self.lighting.expected.append((uc.reg_read(UC_ARM_REG_R0)&15,uc.reg_read(UC_ARM_REG_R1)&255))
        if address==0x08088876:
            self.i2c_oem_bytes.append(dict(step=self.steps,value=uc.reg_read(UC_ARM_REG_R0)&255))
        if address==0x080A2AA4:
            kind=bytes(uc.mem_read(0x200014D1,1))[0]
            if kind!=0:self.halt('SCT boot image variant outside qualified 2048-byte mode',variant=kind)
            else:self.sct_hpi.start_boot(bytes(uc.mem_read(0x080F56CC,2048)))
        if address==0x0808AB18:
            self.rf_spi.expect(uc.reg_read(UC_ARM_REG_R2),uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1)&65535)
        elif address==0x0808ABDC:
            self.rf_spi.expect(uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R0))
        if self.steps>=self.input_poll:
            self.input_poll=self.steps+5000
            self.poll_inputs()
        if self.stop is None:
            for irq,mask in ((6,1),(23,0x300)):
                if self.exti[0x14] & self.exti[0] & mask and self.irq_eligible(irq):
                    self.halt('front peripheral interrupt delivery required',irq=irq)
                    return
        if self.stop or self.virtual_units < self.peripheral_deadline:
            return
        try:
            self.peripheral_deadline = self.virtual_units+64
            for timer,irq in self.timers.values():
                timer.advance(self.virtual_units)
                if timer.irq:
                    self.nvic_pending[irq//32] |= 1<<(irq%32)
                    if self.irq_eligible(irq):
                        self.halt('front peripheral interrupt delivery required',irq=irq)
                        return
            self.backup.advance(self.virtual_units)
            if getattr(self,'interactive_mode',False):
                from interactive_runtime import peripheral_interval
                self.peripheral_deadline = self.virtual_units+peripheral_interval(self)
            if self.backup.irq and self.irq_eligible(3):
                self.halt('front peripheral interrupt delivery required',irq=3)
        except StopModel as error:
            self.halt(str(error))

    def service_extra_stop(self):
        super().service_extra_stop()
        if self.stop and self.stop['kind']=='front peripheral interrupt delivery required':
            irq=self.stop['irq']
            self.stop=None
            self.deliver_systick(irq+16)

    def run_chunks(self,*args,**kwargs):
        result,state=super().run_chunks(*args,**kwargs)
        result.update(timers={hex(k):v[0].describe() for k,v in self.timers.items()},
                      rtc=self.backup.describe(),virtual_core_units=self.virtual_units,
                      rtc_initial_mode=self.rtc_initial_mode,rtc_initial_synthetic_date=self.rtc_initial_date,
                      front_panel_events=self.panel_events,
                      lighting=self.lighting.describe(),
                      flash_cache=self.flash_cache.describe(),
                      full_flash_capture=getattr(self,'full_flash_source',None),
                      boot_alias_read_count=getattr(self,'boot_alias_read_count',0),
                      first_boot_alias_reads=getattr(self,'boot_alias_reads',[]),
                      baseband_idle_pullup_reads=self.baseband_idle_reads,
                      RF_control_spi=self.rf_spi.describe(),
                      software_i2c=self.fm_i2c.describe(),
                      SCT3258_HPI=self.sct_hpi.describe(),
                      USB_device=self.usbd.describe(),
                      pending_core_exceptions=sorted(self.core_pending),
                      core_pending_register_writes=self.core_pend_events,
                      session_origin=getattr(self,'session_origin',dict(kind='application reset in this process')),
                      peripheral_poll_maximum_virtual_units=64)
        return result,state
