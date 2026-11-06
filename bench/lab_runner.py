"""V9 external stimuli and evidence-labelled hardware telemetry."""
import json
from collections import deque
from emulate_front_v121 import FrontRunner
from lab_inputs import FRONT_KEYS,validate_keys,microphone_frame,MIC_CODES,MicrophonePeer,GpsScenario,GpsPeer
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_R0,UC_ARM_REG_R1

class LabRunner(FrontRunner):
    def __init__(self,*args,**kwargs):
        self.front_key_queue=deque()
        self.held_keys=set();self.mic_keys=set();self.mic_last_code=0
        self.mic_connected=False;self.mic_next_tick=0;self.mic_long_sent=False;self.mic_press_tick=0;self.mic_lock=False
        self.gps_scenario=GpsScenario();self.serial_virtual_time=False
        self.lab_events=[];self.lab_counts={};self.lab_next=0;self.signal_states={}
        self.scenario=[];self.scenario_origin=0;self.storage_origin=(0,0,0,0)
        self.pending_voltage=None
        super().__init__(*args,**kwargs)
        self.rf_spi.control_readback_keys={(0,0,0x51),(0,1,0x17)}
    def arm_lab(self):
        self.rf_spi.control_readback_keys={(0,0,0x51),(0,1,0x17)}
        self.scenario_origin=self.steps
        self.storage_origin=(len(getattr(self.nand,'erase_operations',[])),len(getattr(self.nand,'program_operations',[])),
                             len(self.flash_cache.erases),self.flash_cache.program_count)
    def load_scenario(self,path):
        values=json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(values,list):raise ValueError('Le scénario doit contenir une liste')
        for value in values:
            if type(value.get('after_instructions')) is not int or value['after_instructions']<0 or not isinstance(value.get('command'),dict):raise ValueError('Événement de scénario invalide')
        self.scenario=sorted(values,key=lambda v:v['after_instructions'])
    def voltage_sample(self,volts):
        volts=float(volts)
        if not 5<=volts<=30:raise ValueError('Tension de test hors plage 5..30 V')
        if bytes(self.cpu.mem_read(0x20001542,1))!=b'\x01':
            self.pending_voltage=volts;return
        calibration=bytes(self.cpu.mem_read(0x200093F0+0x14,1))[0]
        target=round(volts*10)
        raw=min(range(4096),key=lambda n:abs((n*363//4096)+calibration-100-target))
        self.adc_dma.profile['channels']['11']=raw
        self.event('supply_voltage_input',requested_volts=volts,ADC11=raw,calibration_byte=calibration,source='inverse of native 0808C01A conversion')
    def event(self,kind,**data):
        self.lab_counts[kind]=self.lab_counts.get(kind,0)+1
        if len(self.lab_events)<8192:
            value=dict(step=self.steps,tick=self.tick_wraps,pc=hex(self.cpu.reg_read(UC_ARM_REG_PC)),kind=kind)
            value.update(data)
            self.lab_events.append(value)
            if self.live_directory:
                with (self.live_directory/'hardware_events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False)+'\n')
    def enable_serial_time(self):
        if self.serial_virtual_time:return
        self.serial_virtual_time=True
        for base,(device,_,_,_) in self.serial_devices.items():
            shift=self.virtual_units-device.step
            if device.tx_shift:device.tx_shift=(device.tx_shift[0],device.tx_shift[1]+shift)
            device.rx_wire=type(device.rx_wire)((when+shift,value) for when,value in device.rx_wire)
            device.step=self.virtual_units;device.virtual_time=True
            device.byte_steps=(device.regs[8] or (1042 if base==0x40013800 else 6250))*10*(1 if base==0x40013800 else 2)
        self.serial_deadline()
    def set_keys(self,keys):
        keys=validate_keys(keys)
        if getattr(self,'interactive_mode',False):
            self.front_key_queue.append(keys)
            self.drain_front_keys()
        else:self.apply_front_keys(keys)
    def drain_front_keys(self):
        while self.front_key_queue:
            keys=self.front_key_queue[0]
            if self.held_keys-keys and self.tick_wraps<getattr(self,'front_press_tick',-1000)+(15 if self.held_keys=={'DIAL_PUSH'} else 80):return
            self.front_key_queue.popleft()
            self.apply_front_keys(keys)
    def apply_front_keys(self,keys):
        if keys-self.held_keys:self.front_press_tick=self.tick_wraps
        self.held_keys=keys;self.key_releases=[];self.power_release=None
        self.adc_dma.profile['channels'].update({'8':4095,'9':4095})
        for key in keys:
            if key in FRONT_KEYS:
                channel,value=FRONT_KEYS[key];self.adc_dma.profile['channels'][str(channel)]=value
        self.panel_inputs[0x40010800]=(self.panel_inputs[0x40010800]|2)&(~2 if 'DIAL_PUSH' in keys else -1)
        self.PA0=0 if 'POWER' in keys else 1
        if 'POWER' in keys and not self.afio[8]&15 and self.exti[0]&1 and self.exti[0xC]&1:
            self.exti[0x14]|=1;self.nvic_pending[0]|=1<<6
        self.event('front_held_keys',keys=sorted(keys))
    def set_microphone(self,connected):
        self.enable_serial_time();self.mic_connected=bool(connected)
        self.usart0.peer=MicrophonePeer() if connected else __import__('uart_serial').IdlePeer()
        if not connected:
            self.mic_keys=set();self.usart0.rx_wire.clear();self.serial_deadline()
        self.mic_next_tick=self.tick_wraps
        self.event('microphone_connection',connected=self.mic_connected)
    def schedule_serial(self,device,data):
        device.advance(self.serial_time())
        device.schedule(data);self.serial_deadline()
    def send_microphone(self,keys,long=False):
        if not self.mic_connected and keys:raise ValueError('Brancher le microphone simulé')
        keys=set(keys)
        if self.mic_lock and keys&{'UP','DOWN'}:
            self.event('microphone_locked_key_suppressed',keys=sorted(keys&{'UP','DOWN'}))
            keys-= {'UP','DOWN'}
        frame=microphone_frame(keys,long,self.mic_last_code)
        self.mic_keys=set(keys)
        if self.mic_keys-{'PTT'}:self.mic_last_code=frame[4]
        self.schedule_serial(self.usart0,frame)
        if not long:self.mic_press_tick=self.tick_wraps;self.mic_long_sent=False
        self.event('microphone_frame',keys=sorted(keys),long=long,wire_hex=frame.hex(' '),source='captured D578 microphone protocol')
    def input_command(self,command):
        kind=command['control']
        if kind=='KEY_SET':self.set_keys(command['keys'])
        elif kind=='MIC_CONNECT':self.set_microphone(command['connected'])
        elif kind=='MIC_KEYS':self.send_microphone(command['keys'],command.get('long',False))
        elif kind=='MIC_LOCK':
            self.mic_lock=bool(command['locked'])
            if self.mic_connected and self.mic_lock and self.mic_keys&{'UP','DOWN'}:self.send_microphone(self.mic_keys-{'UP','DOWN'})
        elif kind=='GPS':
            self.enable_serial_time()
            self.usart1.peer=GpsPeer() if command['mode']!='absent' else __import__('uart_serial').IdlePeer()
            self.gps_scenario.configure(command['mode'],self.tick_wraps,command.get('latitude',48),command.get('longitude',2),command.get('utc','2026-11-04T12:00:00'),command.get('hertz',1))
            self.event('GPS_scenario',**self.gps_scenario.events[-1])
        elif kind=='ADC_RAW':
            channel=str(command['channel']);value=int(command['value'])
            if channel not in self.adc_dma.profile['channels'] or not 0<=value<=4095:raise ValueError('Canal ou valeur ADC invalide')
            self.adc_dma.profile['channels'][channel]=value;self.event('ADC_external_sample',channel=channel,value=value)
        elif kind=='VOLTAGE':self.voltage_sample(command['volts'])
        elif kind=='RELEASE_ALL':
            self.front_key_queue.clear();self.apply_front_keys(set())
            if self.mic_connected:self.send_microphone([])
        else:super().input_command(command)
    def gpio_set(self,off,size,value):
        if getattr(self,'interactive_mode',False):
            from interactive_runtime import fast_lcd_gpio
            if fast_lcd_gpio(self,off,size,value):return
        base=(0x40010000+off)&~0x3FF
        previous=self.gpio.get(base,{}).get(12)
        super().gpio_set(off,size,value)
        current=self.gpio.get(base,{}).get(12)
        # Exclude sampled data buses. Retain unexplained output transitions
        # for fan/TX/LED discovery, without naming them by assumption.
        excluded={0x40010800:0x8020,0x40010C00:0xFCFC,0x40011000:0x2000,
                  0x40011400:0xFF7E,0x40011800:0x7F82}
        if previous is not None and current is not None:
            changed=(previous^current)&~excluded.get(base,0)&65535
            if changed:self.event('GPIO_output_transition',port=hex(base),changed=hex(changed),value=hex(current))
    def on_code(self,uc,address,size,data):
        self.uart_wait_extra=0
        if self.serial_virtual_time and self.fast_mode and address in (0x0808E522,0x0808D86C,0x0808D8A6):
            device=self.usart1 if address==0x0808E522 else self.usart0
            if device.tx_shift is not None:
                self.uart_wait_extra=max(0,min(device.tx_shift[1],self.serial_next)-self.virtual_units-1)
                if self.uart_wait_extra:self.lab_counts['UART_wait_accelerations']=self.lab_counts.get('UART_wait_accelerations',0)+1
        super().on_code(uc,address,size,data)
        if self.stop is not None:return
        if address==0x08072426:
            self.event('FAN_native_request',on=bool(uc.reg_read(UC_ARM_REG_R0)),serialized=bool(uc.reg_read(UC_ARM_REG_R1)),
                destination='radio bank 0 register 25h bit 1; hardware continuity not measured')
        if address==0x0808BE9C and uc.reg_read(UC_ARM_REG_R0)!=255:
            self.event('FAN_PTT_input_native',on=bool(uc.reg_read(UC_ARM_REG_R0)))
        if address in (0x08074EB4,0x0806CD02):
            name='TX_entry_candidate' if address==0x08074EB4 else 'GPS_native_byte_parser'
            self.lab_counts[name]=self.lab_counts.get(name,0)+1
            if name=='TX_entry_candidate':self.event('OEM_TX_candidate_entered',evidence='candidate native path; no RF waveform model')
        if address in (0x0806624C,0x08066306):
            self.event('APRS_schedule' if address==0x0806624C else 'APRS_modulator_entry',evidence='native OEM PC observed')
        if self.steps>=self.lab_next:
            self.lab_next=self.steps+256
            if getattr(self,'interactive_mode',False):self.drain_front_keys()
            if self.pending_voltage is not None and bytes(uc.mem_read(0x20001542,1))==b'\x01':
                volts=self.pending_voltage;self.pending_voltage=None;self.voltage_sample(volts)
            while self.scenario and self.steps-self.scenario_origin>=self.scenario[0]['after_instructions']:
                value=self.scenario.pop(0);self.input_command(value['command'])
            if self.mic_connected:
                if self.tick_wraps>=self.mic_next_tick and not self.usart0.rx_wire and self.usart0.received_data is None:
                    self.schedule_serial(self.usart0,b'\x06');self.mic_next_tick=self.tick_wraps+200
                if self.mic_keys-{'PTT'} and not self.mic_long_sent and self.tick_wraps-self.mic_press_tick>=160:
                    self.send_microphone(self.mic_keys,True);self.mic_long_sent=True
            self.gps_scenario.advance(self)
    def hardware_state(self):
        def word(address):return int.from_bytes(self.cpu.mem_read(address,2),'little')
        byte=lambda address:bytes(self.cpu.mem_read(address,1))[0]
        fan_register=self.rf_spi.registers.get((0,0,0x25))
        channel=int.from_bytes(self.cpu.mem_read(0x20000704,4),'little')
        channel_APRS=byte(channel+0x35) if 0x20000000<=channel<0x20017FC0 else None
        abi_known=not getattr(self,'firmware_selection',{}).get('experimental',False)
        return dict(OEM_state_interpretation_qualified=abi_known,
            gps_input=self.gps_scenario.describe(),gps_OEM=dict(parser_bytes=self.lab_counts.get('GPS_native_byte_parser',0),
            module_detected=bool(byte(0x20000944)),position_fix=bool(byte(0x20000947)),
            consecutive_RMC=byte(0x20000945),evidence='OEM PMTK startup detection 0806C7DE; position gate 0806C638..6C6B8'),microphone=dict(connected=self.mic_connected,
            held_keys=sorted(self.mic_keys),up_down_locked=self.mic_lock,received_bytes=len(self.usart0.rx),overruns=self.usart0.overruns),
            front_held_keys=sorted(self.held_keys),TX=dict(candidate_path_entries=self.lab_counts.get('TX_entry_candidate',0),
                native_request=bool(word(0x20001118)&1),
                RF_emission_simulated=False,qualified_TX_state=None),
            FAN=dict(command_on=bool(fan_register&2) if fan_register is not None else None,
                     mode={0:'PTT',1:'Temperature',2:'Both'}.get(byte(0x200042F8+0x29),'unknown'),
                     ADC6_raw=word(0x20001114),hysteresis_on_raw=992,hysteresis_off_raw=868,
                     route='RF bank 0, page 0, register 25h bit 1; physical output not measured',
                     physical_RPM_simulated=False),
            APRS=dict(native_countdown=word(0x20000900),channel_mode_raw=channel_APRS,
                      periodic_setting_raw=byte(0x2000988B),fixed_beacon_setting_raw=byte(0x2000988D),
                      modulator_entries=self.lab_counts.get('APRS_modulator_entry',0),
                      DMA6_enabled=bool(self.adc_dma.dma.get(0x80,0)&1),
                      RF_waveform_simulated=False),
            ADC=dict(samples=self.adc_dma.profile['channels'],converted_OEM_1130=word(0x20001130),
                supply_volts_OEM=word(0x20001130)/10,calibration_byte=byte(0x20009404),
                temperature_units='ADC6 raw; degrees Celsius calibration not established'),
            GPIO_outputs={hex(k):hex(v[12]) for k,v in self.gpio.items()},
            NAND=dict(erases=len(getattr(self.nand,'erase_operations',[]))-self.storage_origin[0],
                      programs=len(getattr(self.nand,'program_operations',[]))-self.storage_origin[1]),
            Flash=dict(erases=len(self.flash_cache.erases)-self.storage_origin[2],programs=self.flash_cache.program_count-self.storage_origin[3]),
            LCD=dict(display_on=self.lcd.display_on,sleeping=self.lcd.sleeping,brightness=self.lighting.registers.get(8)),
            SCT=dict(boot_complete=self.sct_hpi.boot_complete,packets=len(self.sct_hpi.frames)),
            RF_banks={str(bank):dict(transactions=sum(f['bank']==bank for f in self.rf_spi.frames),
                                   selector=['PB5','PB2','PC13','PE1'][bank]) for bank in range(4)},
            FM=dict(transactions=len(self.fm_i2c.frames),RF_station_simulated=False),
            RTC=dict(battery_mode=self.rtc_initial_mode,synthetic=True),
            lighting_registers={str(k):v for k,v in self.lighting.registers.items()},
            USB=dict(host_connected=getattr(self.usbd,'connected',False),CDC_state=getattr(getattr(self,'cdc',None),'state','disconnected')),
            Bluetooth=dict(peer=self.uart3.peer.mode),
            firmware=getattr(self,'firmware_selection',None))
    def run_chunks(self,*args,**kwargs):
        result,ram=super().run_chunks(*args,**kwargs)
        result.update(simulator_version='V10',hardware=self.hardware_state(),hardware_events=self.lab_events,
                      hardware_event_counts=self.lab_counts,firmware_selection=getattr(self,'firmware_selection',None))
        return result,ram
