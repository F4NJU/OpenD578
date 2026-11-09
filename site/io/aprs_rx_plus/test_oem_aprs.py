"""Isolated OEM execution; input bytes and RAM configuration are test stimuli.
No RF/audio emulation, full boot or LCD validation is claimed.
"""
from pathlib import Path
import sys,json,struct
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0,str(Path(__file__).parent))
from disassemble_aprs import images
END=0x10000000

def cpu(tag):
 base,b=images[tag];u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
 lo=base&~4095;u.mem_map(lo,((base+len(b)-lo+4095)//4096)*4096);u.mem_write(base,b)
 u.mem_map(0x20000000,0x30000);u.mem_map(END,4096);u.reg_write(UC_ARM_REG_SP,0x2002fff0)
 return u

def call(u,pc,r0=0,r1=0):
 u.reg_write(UC_ARM_REG_R0,r0);u.reg_write(UC_ARM_REG_R1,r1);u.reg_write(UC_ARM_REG_LR,END|1)
 u.emu_start(pc|1,END,count=100000)
 assert u.reg_read(UC_ARM_REG_PC)==END

def addr(s,last=False):
 return bytes((ord(c)<<1) for c in s.ljust(6))+bytes([0x61 if last else 0x60])
frame=b'+APRS:'+b'\x7e'+addr('APD578')+addr('F4EGM',True)+b'\x03\xf0!4900.00N/00400.00E>TEST\x12\x34\x7e'
results=[]
for tag,offset in [('PLUS',0),('PRO',-0x54)]:
 for case,ena,enb,ma,mb,cool,expected in [('VFO_A',1,0,0,1,0,1),('VFO_B',0,1,1,0,0,1),('disabled',0,0,0,0,0,0),('both_nonanalog',1,1,1,1,0,0),('cooldown',1,0,0,0,1,0)]:
  u=cpu(tag)
  for p,v in [(0x2000070c,0x20018000),(0x20000710,0x20018100)]:u.mem_write(p,struct.pack('<I',v))
  for p,e,m in [(0x20018000,ena,ma),(0x20018100,enb,mb)]:
   u.mem_write(p+0x21,bytes([e<<5]));u.mem_write(p+8,bytes([m]))
  u.mem_write(0x20000f7c,struct.pack('<H',cool))
  for n,c in enumerate(frame,1):
   u.mem_write(0x2000b0f0+n-1,bytes([c]));u.mem_write(0x20000ed2,struct.pack('<H',n))
   if n==6:call(u,0x807c634+offset,0x2000b0f0);assert u.mem_read(0x20000f79,1)==b'\1'
   if n>6:call(u,0x807c664+offset)
  assert u.mem_read(0x2000cc4b,len(frame))==frame
  ready=u.mem_read(0x20000f7a,1)[0];assert ready==expected
  results.append(dict(image=tag,case=case,ready=ready,bytes_copied=len(frame),passed=True))
 u=cpu(tag);u.mem_write(0x2000b0f0,b'+APRX:');call(u,0x807c634+offset,0x2000b0f0)
 assert u.mem_read(0x20000f79,1)==b'\0'
 results.append(dict(image=tag,case='wrong_prefix',passed=True))
# Execute original BHT_H emitter and both original loops; intercept only UART send primitive.
u=cpu('H');out=[]
def hook(u,pc,size,data):
 if pc==0x4a7e:
  assert u.reg_read(UC_ARM_REG_R0)==1
  out.append(u.reg_read(UC_ARM_REG_R1)&255);u.reg_write(UC_ARM_REG_R0,0);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
payload=b'\x7e\x82\xa0\x03\xf0TEST\0';u.mem_write(0x20018000,payload);call(u,0x3ef0,len(payload),0x20018000)
assert bytes(out)==b'+APRS:'+payload[:-1]+b'\x7e'
results.append(dict(image='BHT_H',case='native_prefix_payload_UART1',hex=bytes(out).hex(),passed=True))
Path('aprs_rx_plus_20261109/tests_results.json').write_text(json.dumps({'scope':__doc__,'tests':results},indent=2))
print(len(results),'tests passed')
