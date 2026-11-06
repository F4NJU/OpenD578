"""Numerical FM/AFSK loop through recorded complex I/Q, separate from MCU time.

This is an explicit signal-model prototype. Its filters/gains are configurable
approximations, not execution of SCT3258 firmware or measured D578 analog paths.
Reception reloads the I/Q file; it never returns the microphone PCM as an echo.
"""
import hashlib,io,json,math,uuid,wave
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np


@dataclass
class Config:
    audio_rate:int=48000
    iq_rate:int=192000
    deviation_hz:float=2500
    mic_gain_db:float=0
    speaker_gain_db:float=0
    rf_gain_db:float=0
    attenuation_db:float=0
    snr_db:float=80
    offset_hz:float=0
    rx_tune_hz:float=0
    channel_width_hz:float=12500
    emphasis:bool=True
    ctcss_hz:float=0
    ctcss_level:float=.1
    seed:int=578

    def validate(self):
        for name,value in asdict(self).items():
            if name=='emphasis':
                if not isinstance(value,bool):raise ValueError('emphasis must be boolean')
            elif not isinstance(value,(int,float)) or isinstance(value,bool):raise ValueError('Signal parameters must be numeric')
        if not isinstance(self.seed,int) or not 0<=self.seed<=2**32-1:raise ValueError('Invalid noise seed')
        if self.audio_rate!=48000 or self.iq_rate!=192000:raise ValueError('This prototype uses 48 kHz audio / 192 ksample/s I/Q')
        if not 500<=self.deviation_hz<=5000:raise ValueError('Deviation outside 500..5000 Hz')
        for name in ('mic_gain_db','speaker_gain_db','rf_gain_db'):
            if not -60<=getattr(self,name)<=30:raise ValueError('Gain outside -60..30 dB')
        if not 0<=self.attenuation_db<=80 or not -10<=self.snr_db<=120:raise ValueError('Invalid channel attenuation/SNR')
        if abs(self.offset_hz)>20000 or abs(self.rx_tune_hz)>20000:raise ValueError('Frequency offset outside +/-20 kHz')
        if not 6000<=self.channel_width_hz<=30000:raise ValueError('Invalid receive channel width')
        if self.ctcss_hz and not 60<=self.ctcss_hz<=260:raise ValueError('Invalid CTCSS frequency')
        if not 0<=self.ctcss_level<=.2:raise ValueError('Invalid CTCSS deviation fraction')
        for value in asdict(self).values():
            if isinstance(value,(int,float)) and not math.isfinite(value):raise ValueError('Non-finite signal parameter')
        return self


def pcm_wav(samples,rate):
    samples=np.asarray(samples,dtype=float)
    values=np.rint(np.clip(samples,-1,1)*32767).astype('<i2')
    stream=io.BytesIO()
    with wave.open(stream,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(values.tobytes())
    return stream.getvalue()


def read_wav(data):
    with wave.open(io.BytesIO(data),'rb') as w:
        if w.getsampwidth()!=2 or w.getnchannels() not in (1,2) or w.getcomptype()!='NONE':raise ValueError('Supply mono/stereo uncompressed PCM16 WAV')
        rate=w.getframerate();count=w.getnframes();channels=w.getnchannels()
        if not 8000<=rate<=96000 or not 1<=count<=12*rate:raise ValueError('Audio must be at most 12 seconds, 8..96 kHz')
        values=np.frombuffer(w.readframes(count),dtype='<i2').astype(float).reshape(-1,channels).mean(axis=1)/32768
        if len(values)!=count:raise ValueError('Truncated WAV')
    return values,rate


def resample(values,source,target):
    if source==target:return np.asarray(values,dtype=float)
    count=round(len(values)*target/source)
    return np.interp(np.arange(count)*source/target,np.arange(len(values)),values)


def filter_audio(values,rate,low=0,high=3000,emphasis=0):
    # Offline frequency-domain model. No claim of the chip's exact coefficients
    # or streaming latency. Padding avoids circular wrap across a clip edge.
    values=np.asarray(values,dtype=float);pad=min(rate//10,len(values))
    data=np.pad(values,(pad,pad));freq=np.fft.rfftfreq(len(data),1/rate)
    response=np.ones_like(freq)
    if high:response*=np.clip((high+300-freq)/300,0,1)
    if low:response*=np.clip((freq-(low-80))/80,0,1)
    if emphasis:
        transfer=(1+2j*np.pi*freq*75e-6)/abs(1+2j*np.pi*1000*75e-6)
        response=response*(transfer if emphasis>0 else 1/transfer)
    result=np.fft.irfft(np.fft.rfft(data)*response,n=len(data))
    return result[pad:pad+len(values)]


def fm_modulate(modulation,rate,deviation):
    phase=2*np.pi*deviation*np.cumsum(modulation,dtype=float)/rate
    return np.exp(1j*phase).astype('<c8')


def fm_demodulate(iq,rate,deviation,tune=0):
    iq=np.asarray(iq)
    result=np.zeros(len(iq),dtype=float)
    result[1:]=np.angle(iq[1:]*np.conj(iq[:-1]))*rate/(2*np.pi*deviation)-tune/deviation
    return result


def record_iq(folder,name,iq,config,stage):
    data=np.asarray(iq,dtype='<c8').tobytes()
    (folder/(name+'.sigmf-data')).write_bytes(data)
    meta={'global':{'core:datatype':'cf32_le','core:sample_rate':config.iq_rate,'core:version':'1.2.0',
        'core:description':'OpenD578 synthetic '+stage+'; normalized amplitude, no physical RF',
        'core:sha512':hashlib.sha512(data).hexdigest()},'captures':[{'core:sample_start':0}],
        'annotations':[]}
    (folder/(name+'.sigmf-meta')).write_text(json.dumps(meta,indent=2))
    return hashlib.sha256(data).hexdigest()


def replay_iq(path):
    data=Path(path).read_bytes()
    if not data or len(data)%8:raise ValueError('Invalid complex float32 I/Q recording')
    return np.frombuffer(data,dtype='<c8').copy()


def channel(iq,config):
    t=np.arange(len(iq))/config.iq_rate
    gain=10**(-config.attenuation_db/20)
    result=np.asarray(iq)*gain*np.exp(2j*np.pi*config.offset_hz*t)
    sigma=10**(-config.snr_db/20)/math.sqrt(2)
    rng=np.random.default_rng(config.seed)
    result+=sigma*(rng.standard_normal(len(iq))+1j*rng.standard_normal(len(iq)))
    return result.astype('<c8')


def receive(iq,config,data_mode=False):
    t=np.arange(len(iq))/config.iq_rate
    tuned=iq*np.exp(-2j*np.pi*config.rx_tune_hz*t)
    frequencies=np.fft.fftfreq(len(tuned),1/config.iq_rate)
    half=config.channel_width_hz/2
    window=np.clip((half+1000-np.abs(frequencies))/1000,0,1)
    filtered=np.fft.ifft(np.fft.fft(tuned)*window)
    demod=fm_demodulate(filtered,config.iq_rate,config.deviation_hz)
    # Lowpass before downsampling. Data mode excludes voice emphasis/HPF.
    audio=filter_audio(demod,config.iq_rate,low=0,high=3000,
                       emphasis=-1 if config.emphasis and not data_mode else 0)
    audio=resample(audio,config.iq_rate,config.audio_rate)
    audio=filter_audio(audio,config.audio_rate,low=300 if not data_mode else 0,high=3000)
    return audio*10**(config.speaker_gain_db/20)


def run_loop(root,pcm=None,input_rate=48000,config=None,mode='fm',source='N0CALL',information='>OpenD578 I/Q test'):
    config=(config or Config()).validate()
    if mode not in ('fm','aprs'):raise ValueError('Full DMR voice loop is not implemented; AMBE/baseband integration is required')
    folder=Path(root)/uuid.uuid4().hex;folder.mkdir(parents=True)
    if mode=='aprs':
        from ax25_afsk import ui_frame,afsk
        original_frame=ui_frame(source=source,information=information)
        pcm=afsk(original_frame,config.audio_rate)
    else:
        pcm=np.asarray(pcm,dtype=float)
        if pcm.ndim!=1 or not 1<=len(pcm)<=12*input_rate or not np.all(np.isfinite(pcm)):
            raise ValueError('Invalid mono PCM audio')
        pcm=resample(pcm,input_rate,config.audio_rate)
    (folder/'input.wav').write_bytes(pcm_wav(pcm,config.audio_rate))
    voice=pcm*10**(config.mic_gain_db/20)
    if mode=='fm':voice=filter_audio(voice,config.audio_rate,low=300,high=3000,emphasis=1 if config.emphasis else 0)
    clipping=float(np.mean(np.abs(voice)>1))
    modulation=np.clip(voice,-1,1)
    modulation=filter_audio(modulation,config.audio_rate,high=3000)
    if config.ctcss_hz and mode=='fm':
        modulation+=config.ctcss_level*np.sin(2*np.pi*config.ctcss_hz*np.arange(len(modulation))/config.audio_rate)
    modulation=resample(modulation,config.audio_rate,config.iq_rate)
    tx=fm_modulate(modulation,config.iq_rate,config.deviation_hz)*10**(config.rf_gain_db/20)
    tx_hash=record_iq(folder,'tx',tx,config,'TX FM I/Q')
    # The channel reads the recorded TX samples, rather than an in-memory shortcut.
    transmitted=replay_iq(folder/'tx.sigmf-data')
    rx=channel(transmitted,config);rx_hash=record_iq(folder,'rx',rx,config,'received I/Q')
    recorded=replay_iq(folder/'rx.sigmf-data')
    recovered=receive(recorded,config,data_mode=mode=='aprs')
    (folder/'received.wav').write_bytes(pcm_wav(recovered,config.audio_rate))
    frames=[]
    if mode=='aprs':
        from ax25_afsk import decode
        frames=decode(recovered,config.audio_rate)
    report=dict(session=folder.name,mode=mode,duration_seconds=len(pcm)/config.audio_rate,
        config=asdict(config),TX_IQ_SHA256=tx_hash,RX_IQ_SHA256=rx_hash,
        decoded_from_recorded_IQ=True,APRS_frames=frames,TX_clipped_fraction=clipping,
        received_peak=float(np.max(np.abs(recovered))),received_RMS=float(np.sqrt(np.mean(recovered**2))),
        qualification='standalone numerical signal model; not a complete D578 firmware audio path',
        MCU_audio_transport_verified=False,SCT_firmware_executed=False,
        gains_source='manual scenario parameters; not measured analog calibration',
        filters='offline approximate filters; no SCT bit-exact response or streaming timing',
        DMR_voice_supported=False,physical_transmission=False)
    (folder/'report.json').write_text(json.dumps(report,indent=2))
    return report
