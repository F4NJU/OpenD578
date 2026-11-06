"""Expose board outputs without inferring physical effects from OEM UI/RAM flags."""


def microphone_output(tx):
    """Frame structure observed on USART0; LED/audio payload semantics unqualified."""
    raw=bytes(tx);frames=[];cursor=0
    while cursor<len(raw):
        if raw[cursor]==0x53 and cursor+16<=len(raw) and raw[cursor+15]==6:
            frames.append(raw[cursor:cursor+16].hex(' '));cursor+=16
        else:cursor+=1
    return dict(observed_frames=len(frames),last_frames=frames[-4:],
        source='USART0 transmitted bytes',payload_semantics_qualified=False,
        LEDs='unknown',speaker_route='unknown')


def describe(runner):
    gpio={hex(port):hex(values[12]) for port,values in runner.gpio.items()}
    lighting={str(k):v for k,v in runner.lighting.registers.items()}
    indicators={name:dict(state='unknown',qualified=False,
            reason='Physical drive mapping and polarity not established')
            for name in ('radio_status','radio_keys','microphone_main_A','microphone_main_B',
                         'microphone_RT_A','microphone_RT_B','microphone_keypad')}
    if hasattr(runner,'status_led'):indicators['radio_status']=runner.status_led.describe()
    return dict(indicators=indicators,
        raw_GPIO_output_latches=gpio,raw_lighting_registers=lighting,
        microphone_output=microphone_output(runner.usart0.tx),
        audio_outputs={name:dict(selected=None,qualified=False,
            reason='Control-to-physical-route mapping and audio samples not qualified')
            for name in ('radio_internal','microphone_speaker','external_A','external_B','bluetooth')},
        bluetooth=dict(peer_mode=runner.uart3.peer.mode,internal_firmware_executed=False,
            modeled='ET12 version and AGHF AT subset only; no Bluetooth audio',
            unsupported_commands_policy='explicit model boundary',
            audio_samples_routed=False),
        provenance='Peripheral output registers and transmitted bytes only; no OEM RX/TX variables')
