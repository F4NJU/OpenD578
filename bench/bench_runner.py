"""External FM receiver status and observable native RF/audio commands."""
from lab_runner import LabRunner
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1

class BenchRunner(LabRunner):
    def __init__(self,*args,**kwargs):
        self.oem_reference=bytes(args[0])
        self.rx_inputs={};self.rx_observed={};self.power_commands=[];self.audio_commands=[]
        self.trace_enabled=True
        super().__init__(*args,**kwargs)
    def input_command(self,command):
        if command['control'].startswith('USB_CDC_'):
            from usb_cdc_runtime import command as cdc_command
            if cdc_command(self,command):return
        if command['control']=='RF_RX':
            bank=int(command.get('bank',0));carrier=bool(command.get('carrier',False))
            tone=command.get('ctcss','absent')
            if bank not in (0,1) or tone not in ('absent','match','mismatch'):raise ValueError('Entrée RX invalide')
            noise=int(command.get('noise',10 if carrier else 127));strength=int(command.get('strength',240 if carrier else 0))
            if not 0<=noise<=127 or not 0<=strength<=511:raise ValueError('Niveau RX brut hors plage')
            # Contract-level discriminator / decoder outputs. This does not
            # demodulate a physical FM waveform or synthesize an RF frequency.
            values={0x0C:2 if carrier else 0,0x60:0xC00 if carrier and tone=='match' else 0,
                    0x61:0,0x65:noise,0x67:strength}
            self.rx_inputs[bank]=dict(carrier=carrier,ctcss_decoder=tone,noise_raw=noise,strength_raw=strength)
            if not hasattr(self.rf_spi,'external_inputs'):self.rf_spi.external_inputs={}
            self.rf_spi.external_inputs[bank]=values
            self.event('RF_RX_external_status',bank=bank,**self.rx_inputs[bank],registers={f'{k:02X}':v for k,v in values.items()})
        elif command['control']=='TRACE':self.trace_enabled=bool(command['enabled'])
        else:super().input_command(command)
    def event(self,kind,**data):
        if self.trace_enabled or kind in ('RF_RX_external_status','OEM_audio_path_request','power_DAC_write','RX_OEM_state','GPS_OEM_state','TX_FAN_state','GPS_scenario','microphone_frame','microphone_connection'):
            super().event(kind,**data)
    def pmu_write(self,uc,off,size,value,data):
        super().pmu_write(uc,off,size,value,data)
        if 0x408<=off<=0x428:
            entry=dict(step=self.steps,register=hex(0x40007000+off),raw=value,size=size,
                       evidence='MCU DAC register write; power-stage wiring and watts not established')
            self.power_commands.append(entry);self.event('power_DAC_write',**{k:v for k,v in entry.items() if k!='step'})
    def on_code(self,uc,address,size,data):
        profile=getattr(self,'observation_profile',None)
        if profile is not None and not profile['anchors_compatible']:
            self.halt('firmware observation profile requires adaptation; test incomplete',address,
                      incompatible_anchors=len(profile['mismatches']))
            return
        super().on_code(uc,address,size,data)
        if self.stop is not None:return
        if address==0x08090B62:
            entry=dict(step=self.steps,channel_mask=uc.reg_read(UC_ARM_REG_R0),argument1=uc.reg_read(UC_ARM_REG_R1))
            self.audio_commands.append(entry);self.event('OEM_audio_path_request',**{k:v for k,v in entry.items() if k!='step'})
        if self.steps>=getattr(self,'rx_poll',0):
            self.rx_poll=self.steps+2048
            value=self.rx_state()
            if value!=self.rx_observed:self.rx_observed=value;self.event('RX_OEM_state',**value)
            gps=dict(module_detected=bool(bytes(uc.mem_read(0x20000944,1))[0]),position_fix=bool(bytes(uc.mem_read(0x20000947,1))[0]))
            if gps!=getattr(self,'observed_gps',None):self.observed_gps=gps;self.event('GPS_OEM_state',**gps)
            tx=dict(TX_request=bool(bytes(uc.mem_read(0x20001118,1))[0]&1),FAN_command=bool(self.rf_spi.registers.get((0,0,0x25),0)&2))
            if tx!=getattr(self,'observed_TX',None):self.observed_TX=tx;self.event('TX_FAN_state',**tx)
    def rx_state(self):
        b=lambda a:bytes(self.cpu.mem_read(a,1))[0]
        return dict(carrier_gate_A=bool(b(0x200011AA)),CTCSS_gate_A=bool(b(0x200011AE)),
                    carrier_gate_B=bool(b(0x200011B5)),audio_gate_A=bool(b(0x200011B3)),audio_gate_B=bool(b(0x200011BE)),
                    audio_open_native=bool(b(0x200011B3) or b(0x200011BE)),
                    evidence='V1.21 observed native state; read only')
    def hardware_state(self):
        h=super().hardware_state()
        from board_observations import describe
        h['board_outputs']=describe(self)
        h['observation_profile']=getattr(self,'observation_profile',None)
        from board_clock import describe_clock,calibration_observation
        h['clocks']=describe_clock(self.clock.regs,self.systick)
        h['calibration']=calibration_observation(self.cpu,h['OEM_state_interpretation_qualified'] and bytes(self.cpu.mem_read(0x20001542,1))==b'\x01')
        h['RX']=dict(external_inputs=self.rx_inputs,OEM=self.rx_state(),
                     signal_level_model='RF discriminator/status contract; no RF waveform demodulation',DMR_supported=False)
        h['power_observation']=dict(DAC_commands=self.power_commands[-40:],calibrated_watts=None,
            evidence='writes observed, not an RF power measurement')
        h['audio']=dict(native_commands=self.audio_commands[-30:],PCM_from_DSP=False,
                        browser_audio='synthetic test tone gated by native OEM audio state')
        channel=int.from_bytes(self.cpu.mem_read(0x2000071C,4),'little')
        h['power_observation']['selected_level_raw']=(bytes(self.cpu.mem_read(channel+8,1))[0]>>2)&3 if 0x20000000<=channel<0x20017FC0 else None
        h['power_observation']['DAC0_last_raw']=self.dac_regs.get(0x408)
        return h
