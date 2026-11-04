"""Bounded scenario verdicts using ordered stimuli, responses and invariants."""

def assess(name,result):
    verdict=dict(scenario=name,physical_radio_certified=False)
    def finish(status,reason,**details):
        return dict(verdict,status=status,reason=reason,**details)
    if result.get('stop',{}).get('kind')!='instruction_budget':
        return finish('incomplete',result.get('stop',{}).get('kind','missing stop reason'))
    hardware=result.get('hardware',{})
    if not hardware.get('OEM_state_interpretation_qualified'):
        return finish('incomplete','OEM RAM observations are not qualified for this image')
    if result.get('observation_profile',{}).get('anchors_compatible') is False:
        return finish('incomplete','observation anchors changed')
    if result.get('remaining_scenario_events'):
        return finish('incomplete','scenario stimuli remain pending')
    lcd=result.get('lcd',{})
    if 'command_crosscheck_mismatches' not in lcd:
        return finish('incomplete','LCD bus evidence missing')
    if lcd['command_crosscheck_mismatches']:
        return finish('failed','LCD GPIO and native command observations disagree')
    if result.get('skipped_firmware_functions'):
        return finish('failed','firmware functions were skipped')
    if result.get('flash_cache',{}).get('firmware_application_modified'):
        return finish('failed','application Flash was modified during the scenario')
    for read in result.get('verified_RAM_reads',[]):
        if read.get('matches_model_output') is False:
            return finish('failed','NAND buffer differs from peripheral output')
    if name!='cold_boot':
        for device in ('NAND','Flash'):
            if device not in hardware:
                return finish('incomplete',device+' write evidence missing')
            if any(hardware[device].get(key,0) for key in ('erases','programs')):
                return finish('failed','unexpected '+device+' write during the read-only functional scenario')
    for key in ('usart0','usart1'):
        if result.get(key,{}).get('overruns',0):
            return finish('failed',key+' receive overrun')
    if name=='cold_boot':
        complete=(result.get('application_running') and lcd.get('display_on') and
            not lcd.get('sleeping',True) and lcd.get('total_pixel_writes',0)>100000 and
            result.get('SCT3258_HPI',{}).get('boot_matches_OEM_GPIO_source') and
            any(v.get('label')=='application_main' for v in result.get('checkpoints',[])))
        return finish('passed' if complete else 'failed','application, LCD and SCT boot criteria',
                      persistence_qualified=False)
    specs={
        'FM':[
            ('carrier applied',lambda e:e['kind']=='RF_RX_external_status' and e.get('bank')==0 and e.get('carrier')),
            ('audio opened',lambda e:e['kind']=='RX_OEM_state' and e.get('carrier_gate_A') and e.get('audio_gate_A')),
            ('carrier removed',lambda e:e['kind']=='RF_RX_external_status' and e.get('bank')==0 and e.get('carrier') is False),
            ('audio closed',lambda e:e['kind']=='RX_OEM_state' and e.get('carrier_gate_A') is False and e.get('audio_gate_A') is False)],
        'GPS':[
            ('fix stimulus',lambda e:e['kind']=='GPS_scenario' and e.get('mode')=='fix'),
            ('position acquired',lambda e:e['kind']=='GPS_OEM_state' and e.get('module_detected') and e.get('position_fix')),
            ('loss stimulus',lambda e:e['kind']=='GPS_scenario' and e.get('mode')=='no_fix'),
            ('position lost',lambda e:e['kind']=='GPS_OEM_state' and e.get('module_detected') and e.get('position_fix') is False)],
        'PTT':[
            ('PTT pressed',lambda e:e['kind']=='microphone_frame' and 'PTT' in e.get('keys',[])),
            ('TX and fan requested',lambda e:e['kind']=='TX_FAN_state' and e.get('TX_request') and e.get('FAN_command')),
            ('PTT released',lambda e:e['kind']=='microphone_frame' and 'PTT' not in e.get('keys',['PTT'])),
            ('TX and fan cleared',lambda e:e['kind']=='TX_FAN_state' and e.get('TX_request') is False and e.get('FAN_command') is False)]}
    if name not in specs:return finish('incomplete','no explicit oracle for this scenario')
    events=result.get('hardware_events',[])
    kinds={e.get('kind') for e in events}
    required={'FM':{'RF_RX_external_status','RX_OEM_state'},
              'GPS':{'GPS_scenario','GPS_OEM_state'},
              'PTT':{'microphone_frame','TX_FAN_state','power_DAC_write'}}[name]
    if not required<=kinds:return finish('incomplete','required stimulus or response telemetry missing',missing=sorted(required-kinds))
    counts=result.get('hardware_event_counts',{})
    if any(counts.get(kind,0)>sum(e.get('kind')==kind for e in events) for kind in required):
        return finish('incomplete','required event history was truncated')
    if any(b.get('step',0)<a.get('step',0) for a,b in zip(events,events[1:])):
        return finish('failed','event history is not in execution order')
    phases=[];cursor=0
    for label,predicate in specs[name]:
        for index in range(cursor,len(events)):
            if predicate(events[index]):
                phases.append(dict(phase=label,step=events[index].get('step')))
                cursor=index+1;break
        else:return finish('failed','expected ordered phase missing',phase=label,observed_phases=phases)
    state_kind={'FM':'RX_OEM_state','GPS':'GPS_OEM_state','PTT':'TX_FAN_state'}[name]
    last=next(e for e in reversed(events) if e['kind']==state_kind)
    if not specs[name][-1][1](last):return finish('failed','final response is no longer in the expected idle state')
    if name=='PTT':
        pressed,released=phases[0]['step'],phases[2]['step']
        positive=any(e['kind']=='power_DAC_write' and e.get('register')=='0x40007408' and
            e.get('raw',0)>0 and pressed<=e.get('step',-1)<=released for e in events)
        zero=any(e['kind']=='power_DAC_write' and e.get('register')=='0x40007408' and
            e.get('raw')==0 and e.get('step',-1)>=released for e in events)
        dac=hardware.get('power_observation',{}).get('DAC0_last_raw')
        if not positive or not zero or dac!=0:
            return finish('failed','PTT must command a positive DAC0 value, then return DAC0 to zero')
    return finish('passed','ordered stimuli/responses and scenario invariants',observed_phases=phases)
