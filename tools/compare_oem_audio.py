#!/usr/bin/env python3
"""Differential unit analysis, NOT an OEM boot or a bench execution.

Loads the unmodified reference Flash in a separate Unicorn instance. Supplies
explicit RAM fixtures to individual routines and records their terminal RF/GPIO
calls. Compares the independently written C functions, including operation order.
No symbols or fixtures from this script are imported by the browser emulator.
Usage: python compare_oem_audio.py FLASH [OUTPUT_JSON]
Requires Python unicorn and a C11 compiler (cc); creates a temporary shared object.
"""
from pathlib import Path
import ctypes as C, hashlib, itertools as I, json, subprocess, sys, tempfile
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_XPSR
FLASH_SHA='e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e'
class Op(C.Structure):
 _fields_=[('kind',C.c_int),('bank',C.c_uint8),('reg',C.c_uint8),('value',C.c_uint16),('immediate',C.c_bool)]
class Plan(C.Structure):
 _fields_=[('ops',Op*4),('count',C.c_size_t),('final_pio25',C.c_uint16)]
class Context(C.Structure):
 _fields_=[('speakers',C.c_int),('path',C.c_int)]+[(s,C.c_bool)for s in ['radio_override','special_mode','aux_enabled','aux_active','sub_gate_hold','output_hold']]
def main():
 blob=Path(sys.argv[1]).read_bytes();assert hashlib.sha256(blob).hexdigest()==FLASH_SHA,'wrong reference Flash'
 root=Path(__file__).resolve().parents[1];hal=root/'firmware/hal'
 with tempfile.TemporaryDirectory(prefix='opend578-audio-')as tmp:
  so=Path(tmp)/'audio.so';subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC',str(hal/'audio_control.c'),'-o',str(so)],check=True);lib=C.CDLL(str(so))
  planptr=C.POINTER(Plan);ctxptr=C.POINTER(Context)
  for name in ['enable','mic_path']:getattr(lib,'d578_audio_'+name).argtypes=[ctxptr,C.c_uint16,C.c_bool,planptr]
  for name in ['route_gate','aux_route']:getattr(lib,'d578_audio_'+name).argtypes=[ctxptr,C.c_bool,C.c_uint16,C.c_bool,planptr]
  lib.d578_audio_mute.argtypes=[C.c_uint16,C.c_bool,planptr]
  lib.d578_audio_fm_microphone.argtypes=[C.c_uint8,C.c_uint8,planptr]
  for name in ['level','code']:getattr(lib,'d578_audio_volume_'+name).argtypes=[C.c_uint16 if name=='level'else C.c_uint8,C.POINTER(C.c_uint8)]
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.mem_map(0x8000000,0x300000);u.mem_write(0x8000000,blob);u.mem_map(0x20000000,0x20000)
  stop=0x8001000;events=[]
  def hook(uc,a,size,data):
   if a not in [0x808ab18,0x806cd9e,0x80087ca,0x80087ce,0x808c354]:return
   r0,r1,r2=[uc.reg_read(x)for x in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]]
   if a in [0x808ab18,0x806cd9e]:events.append([0,r2,r0,r1,a==0x806cd9e])
   elif a==0x808c354:events.append(['U2429',r0,r1])
   else:
    assert r0==0x40010800 and r1==0x80
    events.append([1,0,0,int(a==0x80087ca),False])
   uc.reg_write(UC_ARM_REG_R0,0);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  # Hook only terminal boundaries; all routing wrappers and the common PIO
  # read/modify/write routine execute the actual OEM instructions.
  for address in [0x808ab18,0x806cd9e,0x80087ca,0x80087ce,0x808c354]:u.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
  def byte(a,v):u.mem_write(a,bytes([v]))
  def fixture(c,word):
   for a,v in [(0x200042f8+0x23,c.speakers),(0x200042f8+0x25,c.path),(0x20001050,c.radio_override),(0x200042f8+0x21,c.special_mode),(0x20001085,c.aux_enabled),(0x20000ef4,c.aux_active),(0x200008a9,c.sub_gate_hold),(0x200011e4,c.output_hold)]:byte(a,int(v))
   u.mem_write(0x200009d6,word.to_bytes(2,'little'))
  def call(address,r0=0,r1=0):
   events.clear();u.reg_write(UC_ARM_REG_XPSR,0x01000000);u.reg_write(UC_ARM_REG_SP,0x2001ff00);u.reg_write(UC_ARM_REG_LR,stop|1);u.reg_write(UC_ARM_REG_R0,r0);u.reg_write(UC_ARM_REG_R1,r1);u.emu_start(address|1,stop,count=10000)
   assert u.reg_read(UC_ARM_REG_PC)==stop,hex(u.reg_read(UC_ARM_REG_PC))
   return list(events),u.reg_read(UC_ARM_REG_R0)
  def operations(p):return [[o.kind,o.bank,o.reg,o.value,bool(o.immediate)]for o in p.ops[:p.count]]
  counts={};representative=[]
  def check(name,address,c,word,immediate,request=None):
   fixture(c,word);p=Plan();args=[C.byref(c)]+([]if request is None else[request])+[word,immediate,C.byref(p)]
   fn=getattr(lib,'d578_audio_'+name);assert fn(*args)
   actual,_=call(address,immediate if name in ['enable','mic_path']else int(request),0 if name in ['enable','mic_path']else immediate)
   shadow=int.from_bytes(u.mem_read(0x200009d6,2),'little')
   assert actual==operations(p)and shadow==p.final_pio25,(name,word,vars(c),actual,operations(p),shadow,p.final_pio25)
   counts[name]=counts.get(name,0)+1
  # All 256 low PIO states; a nonzero upper byte checks preservation.
  for low in range(256):
   word=0x5a00|low
   for mode,override,special,hold,immediate in I.product(range(3),range(2),range(2),range(2),range(2)):
    c=Context(mode,0,override,special,False,False,False,hold);check('enable',0x8090a86,c,word,immediate)
   for mode,path,special,aux,hold,immediate in I.product(range(3),range(2),range(2),range(2),range(2),range(2)):
    c=Context(mode,path,False,special,aux,False,hold,False);check('mic_path',0x80929b6,c,word,immediate)
   for mode,path,override,request,immediate in I.product(range(3),range(2),range(2),range(2),range(2)):
    c=Context(mode,path,override,False,False,False,False,False);check('route_gate',0x8090a22,c,word,immediate,request)
   for special,aux,active,request,immediate in I.product(range(2),repeat=5):
    c=Context(0,0,False,special,aux,active,False,False);check('aux_route',0x8090a4c,c,word,immediate,request)
   for immediate in range(2):
    fixture(Context(),word);p=Plan();assert lib.d578_audio_mute(word,immediate,C.byref(p));actual,_=call(0x8090adc,immediate);assert actual==operations(p);assert int.from_bytes(u.mem_read(0x200009d6,2),'little')==p.final_pio25;counts['mute']=counts.get('mute',0)+1
  for factory,level in I.product(range(64),range(6)):
   byte(0x200093f0+0x19,factory);byte(0x200042f8+0x21,0);byte(0x200042f8+0x3e,level);p=Plan();assert lib.d578_audio_fm_microphone(level,factory,C.byref(p));actual,_=call(0x806f07c,0);assert actual==operations(p),(factory,level,actual,operations(p));counts['fm_microphone']=counts.get('fm_microphone',0)+1
   if factory==54:representative.append({'factoryMIC':factory,'userLevel':level+1,'OEMoperations':actual})
  for raw in range(4096):
   value=C.c_uint8();assert lib.d578_audio_volume_level(raw,C.byref(value));_,actual=call(0x808b922,raw,raw);assert value.value==actual,(raw,actual,value.value)
  counts['volume_quantizer']=4096
  for channel,level in I.product([2,3],range(33)):
   byte(0x2000114c,255);byte(0x2000114d,255);actual,_=call(0x808c3ec,channel,level);value=C.c_uint8();assert lib.d578_audio_volume_code(level,C.byref(value));assert actual==[['U2429',channel,value.value]],(channel,level,actual,value.value)
  counts['volume_encoder']=66
  summary={'referenceFlashSHA256':FLASH_SHA,'method':'isolated OEM routine differential execution; explicit RAM input fixtures, terminal RF/GPIO calls recorded','coldBoot':False,'browserGuestStateWritten':False,'routines':{'enable':'0x08090A86','mute':'0x08090ADC','mic_path':'0x080929B6','route_gate':'0x08090A22','aux_route':'0x08090A4C','fm_microphone':'0x0806F07C','volume_quantizer':'0x0808B922','volume_encoder':'0x0808C3EC'},'passed':counts,'total':sum(counts.values()),'mismatches':0,'microphoneExamples':representative,'scope':'digital commands, exact order and cached writes; no PCM, analog transfer or new full boot qualification'}
  output=Path(sys.argv[2])if len(sys.argv)>2 else Path('audio_contract_differential.json');output.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'output':str(output),'passed':counts,'total':sum(counts.values()),'mismatches':0}))
if __name__=='__main__':main()
