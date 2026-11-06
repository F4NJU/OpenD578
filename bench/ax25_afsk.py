"""Original AX.25 UI/HDLC and Bell 202 diagnostic modem, 1200 bit/s.

Receiver searches symbol offsets and HDLC flags and accepts only valid FCS.
It consumes recovered audio, not the transmitter's payload or bit clock phase.
This is a laboratory decoder, not a qualified radio APRS receiver.
"""
import numpy as np


def fcs(data):
    crc=0xFFFF
    for value in data:
        crc^=value
        for _ in range(8):crc=(crc>>1)^(0x8408 if crc&1 else 0)
    return crc^0xFFFF


def address(call,last=False):
    parts=call.upper().split('-');name=parts[0]
    ssid=int(parts[1]) if len(parts)==2 else 0
    if len(parts)>2 or not 1<=len(name)<=6 or not name.isascii() or not name.isalnum() or not 0<=ssid<=15:
        raise ValueError('AX.25 callsign must be 1..6 ASCII letters/digits, optional SSID 0..15')
    return bytes(ord(v)<<1 for v in name.ljust(6))+bytes([0x60|(ssid<<1)|int(last)])


def ui_frame(source='N0CALL',destination='APD578',information='>OpenD578 I/Q test'):
    info=information.encode('ascii')
    if len(info)>256:raise ValueError('Diagnostic AX.25 information is limited to 256 bytes')
    frame=address(destination)+address(source,True)+b'\x03\xF0'+info
    return frame+fcs(frame).to_bytes(2,'little')


def bits_lsb(data):
    return [(value>>bit)&1 for value in data for bit in range(8)]


def afsk(frame,rate=48000,preamble_flags=32):
    if rate%1200:raise ValueError('AFSK sample rate must be divisible by 1200')
    flag=bits_lsb(b'\x7E');bits=flag*preamble_flags;ones=0
    for value in bits_lsb(frame):
        bits.append(value);ones=ones+1 if value else 0
        if ones==5:bits.append(0);ones=0
    bits+=flag*4
    tone=0;frequencies=[]
    for bit in bits:
        if not bit:tone^=1
        frequencies.append(1200 if tone else 2200)
    values=np.repeat(frequencies,rate//1200)
    return .55*np.sin(2*np.pi*np.cumsum(values,dtype=np.float64)/rate)


def extract_frames(bits):
    flag=bits_lsb(b'\x7E');positions=[]
    for i in range(len(bits)-7):
        if bits[i:i+8]==flag:positions.append(i)
    frames=[]
    for start,end in zip(positions,positions[1:]):
        data=bits[start+8:end]
        if len(data)<18*8:continue
        unstuffed=[];ones=0;invalid=False
        for bit in data:
            if ones==5:
                if bit:invalid=True;break
                ones=0;continue
            unstuffed.append(bit);ones=ones+1 if bit else 0
        if invalid or len(unstuffed)%8:continue
        raw=bytes(sum(unstuffed[i+b]<<b for b in range(8)) for i in range(0,len(unstuffed),8))
        if len(raw)>=18 and fcs(raw[:-2])==int.from_bytes(raw[-2:],'little') and raw not in frames:frames.append(raw)
    return frames


def decode(audio,rate=48000):
    if rate%1200:raise ValueError('AFSK decoder sample rate must be divisible by 1200')
    audio=np.asarray(audio,dtype=float);width=rate//1200
    t=np.arange(width)/rate
    mark=np.exp(-2j*np.pi*1200*t);space=np.exp(-2j*np.pi*2200*t)
    for offset in range(width):
        count=(len(audio)-offset)//width
        if count<150:continue
        chunks=audio[offset:offset+count*width].reshape(-1,width)
        tones=np.abs(chunks@mark)>np.abs(chunks@space)
        bits=(tones[1:]==tones[:-1]).astype(np.uint8).tolist()
        frames=extract_frames(bits)
        if frames:return [describe(frame,offset) for frame in frames]
    return []


def describe(frame,offset):
    def call(raw):
        name=''.join(chr(v>>1) for v in raw[:6]).strip();ssid=(raw[6]>>1)&15
        return name+('-'+str(ssid) if ssid else '')
    index=0;addresses=[]
    while index+7<=len(frame)-4:
        raw=frame[index:index+7];addresses.append(call(raw));index+=7
        if raw[-1]&1:break
    return dict(frame_hex=frame.hex(),FCS_valid=True,destination=addresses[0],source=addresses[1],
        information=frame[index+2:-2].decode('ascii',errors='replace'),symbol_offset_samples=offset)
