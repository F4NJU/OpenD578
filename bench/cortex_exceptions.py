"""Basic Cortex-M thread/handler frames, pending ticks and native PendSV.

Implements the basic F9/FD EXC_RETURN forms from ARM DUI0553B.
Extended FP frames and nested/preempting handler execution remain unsupported.
The OEM PendSV saves/restores R4-R11 and selects its own task stack.
"""
import struct
from unicorn import UcError
from unicorn.arm_const import *
from audit_ram_v121 import APP,RAM,RAM_SIZE,hx
from emulate_clock_v121 import StopModel


class CortexExceptions:
    def __init__(self,*args,**kwargs):
        self.core_pending=set()
        self.core_pend_events=[]
        self.exception_return_target=None
        super().__init__(*args,**kwargs)

    def exception_priority(self,exception):
        if exception in (14,15):return (self.core[0xD20]>>(16+8*(exception-14)))&255
        irq=exception-16
        return (self.nvic_priorities.get(0x400+(irq&~3),0)>>(8*(irq&3)))&255

    def exception_eligible(self,exception):
        cpu=self.cpu
        basepri=cpu.reg_read(UC_ARM_REG_BASEPRI)
        return (not self.irq_active and not cpu.reg_read(UC_ARM_REG_IPSR)
            and not (cpu.reg_read(UC_ARM_REG_PRIMASK) or cpu.reg_read(UC_ARM_REG_FAULTMASK))
            and (not basepri or self.exception_priority(exception)<basepri))

    def halt(self,kind,*args,**kwargs):
        if kind=='SysTick exception delivery required':
            self.core_pending.add(15)
            if not self.exception_eligible(15):return
        return super().halt(kind,*args,**kwargs)

    def core_get(self,off,size):
        word,shift,mask=self.lane(off,size)
        if word==0xD04:
            value=self.cpu.reg_read(UC_ARM_REG_IPSR)
            value|=(14 in self.core_pending)<<28|(15 in self.core_pending)<<26
            return (value>>shift)&mask
        return super().core_get(off,size)

    def core_set(self,off,size,value):
        word,shift,mask=self.lane(off,size)
        if word==0xD0C:
            if size!=4:raise StopModel('AIRCR requires a word access')
            if value>>16!=0x05FA:return
            if value&4:self.halt('software reset requested',source='AIRCR.SYSRESETREQ',automatic_reboot=False)
            else:self.core[word]=0xFA050000|(value&0x700)
            return
        if word==0xD04:
            value<<=shift
            if value&~0x1E000000:raise StopModel('ICSR command outside PendSV/SysTick subset')
            for exception,setbit,clearbit in ((14,28,27),(15,26,25)):
                if value&(1<<clearbit):self.core_pending.discard(exception)
                if value&(1<<setbit):self.core_pending.add(exception)
            if len(self.core_pend_events)<256:
                self.core_pend_events.append(dict(step=self.steps,value=hx(value),pending=sorted(self.core_pending)))
            return
        result=super().core_set(off,size,value)
        if getattr(self,'interactive_mode',False) and 0x100<=word<0x1A0:
            self.peripheral_deadline=min(self.peripheral_deadline,self.virtual_units+1)
            self.serial_deadline()
        return result

    def on_code(self,uc,address,size,data):
        super().on_code(uc,address,size,data)
        if self.stop is None:
            eligible=[n for n in self.core_pending if self.exception_eligible(n)]
            if eligible:self.halt('core pending exception delivery required',exception=min(eligible,key=lambda n:(self.exception_priority(n),n)))

    def on_intr(self,uc,number,data):
        if number==8 and self.irq_active:
            target=uc.reg_read(UC_ARM_REG_PC)|1
            if target not in (0xFFFFFFF9,0xFFFFFFFD):target=uc.reg_read(UC_ARM_REG_LR)
            self.exception_return_target=target
            self.irq_returned=True
            uc.emu_stop()
            return
        return super().on_intr(uc,number,data)

    def deliver_systick(self,exception=15):
        cpu=self.cpu
        if not self.exception_eligible(exception):
            if exception in (14,15):self.core_pending.add(exception);return
            self.halt('external interrupt requested while masked or active',exception=exception)
            return
        resume=cpu.reg_read(UC_ARM_REG_PC)
        original_sp=cpu.reg_read(UC_ARM_REG_SP)
        psp_active=bool(cpu.reg_read(UC_ARM_REG_CONTROL)&2)
        pad=original_sp&7
        frame_address=original_sp-32-pad
        if pad not in (0,4) or not RAM<=frame_address<=RAM+RAM_SIZE-32:
            self.halt('invalid basic exception stack');return
        registers=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
            UC_ARM_REG_R12,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_XPSR)
        values=[cpu.reg_read(reg) for reg in registers]
        values[-1]=(values[-1]&~(1<<9))|(bool(pad)<<9)
        frame=struct.pack('<8I',*values)
        callee=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
            UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
        callee_values=[cpu.reg_read(reg) for reg in callee]
        handler=struct.unpack('<I',bytes(cpu.mem_read(self.core[0xD08]+4*exception,4)))[0]
        valid=(self.execution_address_valid(handler&~1) if hasattr(self,'execution_address_valid')
               else APP<=handler&~1<APP+len(self.image))
        if not handler&1 or not valid:
            self.halt('invalid exception vector',exception=exception);return
        cpu.mem_write(frame_address,frame)
        cpu.reg_write(UC_ARM_REG_PSP if psp_active else UC_ARM_REG_MSP,frame_address)
        handler_sp=cpu.reg_read(UC_ARM_REG_MSP)
        cpu.reg_write(UC_ARM_REG_XPSR,(values[-1]&0xF8000000)|0x01000000|exception)
        cpu.reg_write(UC_ARM_REG_SP,handler_sp)
        cpu.reg_write(UC_ARM_REG_LR,0xFFFFFFFD if psp_active else 0xFFFFFFF9)
        self.irq_active=True
        self.irq_returned=False
        self.exception_return_target=None
        self.core_pending.discard(exception)
        if exception>=16:self.nvic_pending[(exception-16)//32]&=~(1<<((exception-16)%32))
        entry=dict(step=self.steps,exception=exception,
            name={14:'PendSV',15:'SysTick'}.get(exception,f'IRQ{exception-16}'),
            vector=hx(handler),interrupted_pc=hx(resume),frame_address=hx(frame_address),stack='PSP' if psp_active else 'MSP')
        self.irq_log.append(entry)
        try:
            cpu.emu_start(handler,0,count=100000)
        except UcError as error:
            if not self.irq_returned:self.halt('CPU exception inside handler',error=str(error))
        if self.irq_returned and self.stop is None:
            target=self.exception_return_target
            if target not in (0xFFFFFFF9,0xFFFFFFFD):
                self.halt('unsupported exception return form',EXC_RETURN=hx(target or 0))
            elif cpu.reg_read(UC_ARM_REG_MSP)!=handler_sp:
                self.halt('handler MSP did not balance')
            else:
                use_psp=target==0xFFFFFFFD
                stackreg=UC_ARM_REG_PSP if use_psp else UC_ARM_REG_MSP
                unstack=cpu.reg_read(stackreg)
                if not RAM<=unstack<=RAM+RAM_SIZE-32:
                    self.halt('exception return stack outside SRAM')
                else:
                    restored=list(struct.unpack('<8I',bytes(cpu.mem_read(unstack,32))))
                    if not restored[-1]&(1<<24) or restored[-1]&0x1FF:
                        self.halt('exception return frame is not Thumb thread mode')
                    elif exception!=14 and (unstack!=frame_address or restored!=values or [cpu.reg_read(reg) for reg in callee]!=callee_values):
                        self.halt('unexpected non-PendSV exception frame/context change')
                    else:
                        new_sp=unstack+32+(4 if restored[-1]&(1<<9) else 0)
                        cpu.reg_write(UC_ARM_REG_XPSR,restored[-1]&~(1<<9))
                        control=cpu.reg_read(UC_ARM_REG_CONTROL)
                        cpu.reg_write(UC_ARM_REG_CONTROL,(control&~2)|(2 if use_psp else 0))
                        cpu.reg_write(stackreg,new_sp)
                        for register,value in zip(registers[:-1],restored[:-1]):
                            cpu.reg_write(register,value|1 if register==UC_ARM_REG_PC else value)
                        entry.update(returned=True,returned_step=self.steps,EXC_RETURN=hx(target),
                            resumed_pc=hx(restored[6]),resumed_stack='PSP' if use_psp else 'MSP')
        elif self.stop is None:self.halt('exception handler budget exhausted',exception=exception)
        self.irq_active=False

    def service_extra_stop(self):
        super().service_extra_stop()
        if self.stop and self.stop['kind']=='core pending exception delivery required':
            exception=self.stop['exception']
            self.stop=None
            self.deliver_systick(exception)
