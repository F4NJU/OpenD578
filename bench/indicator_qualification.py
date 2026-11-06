"""Ordered status-light bus oracle. No OEM PC/RAM/state variables are consulted."""

def assess_status_led(result):
    base=dict(scenario='LED_bus',scope='decoded GPIO command sequence only',physical_radio_certified=False,
              mapping_confidence='firmware_correlated_with_user_observation')
    def verdict(status,reason,**details):return dict(base,status=status,reason=reason,**details)
    if (result.get('stop') or {}).get('kind')!='instruction_budget':
        return verdict('incomplete','Scenario did not finish its bounded instruction run')
    led=result.get('hardware',{}).get('board_outputs',{}).get('indicators',{}).get('radio_status',{})
    frames=led.get('frames',[])
    if not led.get('decoded') or led.get('total_frames')!=len(frames) or led.get('pending_bits'):
        return verdict('incomplete','LED bus evidence absent, partial or truncated')
    events=[]
    for event in result.get('hardware_events',[]):
        kind=event.get('kind')
        if kind=='RF_RX_external_status' and event.get('bank')==0:
            events.append(dict(step=event['step'],kind='carrier',on=event['carrier']))
        elif kind=='microphone_frame':events.append(dict(step=event['step'],kind='PTT',on='PTT' in event['keys']))
    # Independent hardware runner's external input log.
    if not events:
        for event in result.get('inputs',[]):
            command=event.get('input',{})
            if command.get('control')=='RF_RX' and command.get('bank',0)==0:
                events.append(dict(step=event['step'],kind='carrier',on=bool(command.get('carrier'))))
            elif command.get('control')=='MIC_KEYS':events.append(dict(step=event['step'],kind='PTT',on='PTT' in command['keys']))
    if not events:return verdict('incomplete','No external RX/PTT stimuli recorded')
    timeline=sorted(events+[dict(step=f['step'],kind='wire',value=f['value']) for f in frames],key=lambda e:e['step'])
    expected=[('carrier',True),('wire',8),('carrier',False),('wire',0),('PTT',True),('wire',16),('PTT',False),('wire',0)]
    found=[];cursor=0
    for kind,value in expected:
        for i in range(cursor,len(timeline)):
            e=timeline[i]
            match=e['kind']==kind and ((e.get('value',0)&24)==value if kind=='wire' else e.get('on')==value)
            if match:found.append(e);cursor=i+1;break
        else:return verdict('failed','Ordered LED response absent',expected_kind=kind,expected_value=value,observed=found)
    if led.get('raw_command',24)&24:return verdict('failed','LED did not return to off')
    return verdict('passed','Observed green / off / red / off from GPIO bus after external stimuli',observed=found)
