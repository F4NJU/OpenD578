"""CPU-thread attachment and bounded status export for the local serial bridge."""
import json,time
from usb_cdc import CdcHost
from usbd_host import UsbdHost


def command(r,value):
    kind=value.get('control')
    if kind not in ('USB_CDC_START','USB_CDC_STOP','USB_CDC_WRITE'):return False
    if kind=='USB_CDC_START':
        if getattr(r,'cdc',None) and r.cdc.state not in ('disconnected','error'):
            raise ValueError('USB CDC is already active')
        if not isinstance(r.usbd,UsbdHost):
            usb=UsbdHost(clock_enabled=lambda:bool(r.clock.regs[0x1C]&(1<<23)) and not r.clock.regs[0x10]&(1<<23))
            usb.regs=dict(r.usbd.regs);usb.pma=bytearray(r.usbd.pma)
            r.usbd=usb
        r.cdc=CdcHost(r.usbd);r.cdc.start();r.cdc_published=0
        if getattr(r,'hardware_mode',False) and r.usbd.irq:r.nvic_pending[0]|=1<<20
    elif not getattr(r,'cdc',None):raise ValueError('Start USB CDC first')
    elif kind=='USB_CDC_STOP':r.cdc.close()
    else:
        if value.get('session') and value['session']!=r.cdc.session:raise ValueError('USB CDC session changed')
        data=bytes.fromhex(value.get('hex',''))
        if len(data)>4096:raise ValueError('USB CDC write exceeds 4096 bytes')
        r.cdc.queue(data)
    publish(r,force=True)
    return True


def poll(r):
    if not getattr(r,'cdc',None):return
    r.cdc.tick(r.virtual_units);publish(r)


def publish(r,force=False):
    sink=getattr(r,'cdc_sink',None)
    if not sink and not getattr(r,'live_directory',None):return
    now=time.monotonic()
    if not force and now-getattr(r,'cdc_published',0)<.02:return
    c=r.cdc
    key=(c.session,c.state,c.error,len(c.outgoing),c.sent_total,c.received_total,
         (c.control['name'],c.control['stage']) if c.control else None)
    if sink:
        if not force and key==getattr(r,'cdc_published_key',None) and now-getattr(r,'cdc_published',0)<.25:return
        sink(c.describe());r.cdc_published=now;r.cdc_published_key=key
        return
    target=r.live_directory/'usb_cdc.json';temporary=target.with_suffix('.tmp')
    temporary.write_text(json.dumps(r.cdc.describe()),encoding='utf-8')
    try:temporary.replace(target)
    except PermissionError:return  # A Windows reader may hold the previous file.
    r.cdc_published=now


def final_snapshot(r):
    if not getattr(r,'cdc',None) or not getattr(r,'live_directory',None):return
    try:(r.live_directory/'usb_cdc_final.json').write_text(json.dumps(r.cdc.describe()),encoding='utf-8')
    except OSError:pass  # An optional diagnostic export cannot invalidate USB execution.
