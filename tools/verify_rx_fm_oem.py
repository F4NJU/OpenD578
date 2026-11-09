#!/usr/bin/env python3
"""Reproduce RX command contracts. Requires reference Flash, Unicorn and C11.
No fixtures or OEM addresses are imported by the browser or radio firmware.
"""
from pathlib import Path
import sys,json,hashlib,ctypes as C,subprocess,tempfile,argparse
from itertools import product
from unicorn import *
from unicorn.arm_const import *
FLASH=None
class Oracle:
 def __init__(self):
  blob=Path(FLASH).read_bytes();assert hashlib.sha256(blob).hexdigest()=='e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e'
  self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);self.u.mem_map(0x8000000,0x300000);self.u.mem_write(0x8000000,blob);self.u.mem_map(0x20000000,0x20000);self.events=[];self.pages=[0]*4
  for a in [0x808ab18,0x808abdc,0x8009f30,0x805d2f2]:self.u.hook_add(UC_HOOK_CODE,self.hook,begin=a,end=a)
 def hook(self,u,a,size,data):
  r0,r1,r2=[u.reg_read(r)for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2]]
  if a==0x808ab18:
   assert r2<4 and r0<128,(hex(a),r0,r1,r2)
   self.events.append([0,r2,r0,r1&65535])
   if r0==127:self.pages[r2]=r1
   val=0
  elif a==0x808abdc:self.events.append([1,r1,r0,0]);val=self.reads.get((r1,r0),255 if r0==68 else 0)
  elif a==0x8009f30:self.events.append([2,0,0,r0]);val=0
  elif a==0x805d2f2:val=1 # explicit enabled squelch fixture
  else:val=0 # explicit isolated fixture: OEM gain-setting getter index 0
  u.reg_write(UC_ARM_REG_R0,val);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 def fixture(self,narrow=0):
  self.u.mem_write(0x20000000,bytes(0x20000));self.events=[];self.pages=[0]*4;self.reads={}
  self.u.mem_write(0x200004de,bytes([narrow]))
  self.u.mem_write(0x200042f8+0x23,b'\x01') # Radio Spk
  for a in range(0x20000704,0x2000072c,4):self.u.mem_write(a,(0x20012000).to_bytes(4,'little'))
  self.u.mem_write(0x20012008,bytes([16*narrow]))
  for a in [0x200009e9,0x200009ea,0x200009eb,0x200009ec]:self.u.mem_write(a,b'\xff')
 def call(self,addr,*args):
  self.events=[]
  for r,v in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2],args):self.u.reg_write(r,v)
  self.u.reg_write(UC_ARM_REG_XPSR,0x01000000);self.u.reg_write(UC_ARM_REG_SP,0x2001ff00);self.u.reg_write(UC_ARM_REG_LR,0x8001001)
  self.u.emu_start(addr|1,0x8001000,count=1000000)
  assert self.u.reg_read(UC_ARM_REG_PC)==0x8001000,hex(self.u.reg_read(UC_ARM_REG_PC))
  return self.events.copy()
if __name__=='__main__':
 a=argparse.ArgumentParser(description="Differential isolated OEM RX execution, not a cold boot or hardware test")
 a.add_argument('flash');a.add_argument('--output',required=True);args=a.parse_args();FLASH=args.flash
 root=Path(__file__).resolve().parents[1];o=Oracle();counts={};trace=[]
 class Op(C.Structure):_fields_=[('kind',C.c_uint8),('bank',C.c_uint8),('reg',C.c_uint8),('value',C.c_uint16)]
 class Sq(C.Structure):_fields_=[('open',C.c_bool),('count',C.c_uint8)]
 Backend=C.CFUNCTYPE(C.c_int,C.c_void_p,C.POINTER(Op))
 @Backend
 def record(user,p):
  x=p.contents;trace.append([x.kind,x.bank,x.reg,x.value]);return 0
 def check(name,actual):
  assert trace==actual,(name,trace,actual)
  counts[name]=counts.get(name,0)+1
 with tempfile.TemporaryDirectory() as tmp:
  so=Path(tmp)/'rx.so';subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC',str(root/'firmware/rf/rx_fm.c'),'-o',str(so)],check=True)
  c=C.CDLL(str(so));c.d578_rx_reset.argtypes=[Backend,C.c_void_p]
  c.d578_rx_fm_mode.argtypes=[C.c_uint8,C.c_bool,Backend,C.c_void_p]
  c.d578_rx_tune.argtypes=[C.c_uint8,C.c_uint32,Backend,C.c_void_p]
  c.d578_rx_begin.argtypes=[C.c_uint8,C.c_bool,C.c_uint8,Backend,C.c_void_p]
  c.d578_rx_start.argtypes=[C.c_uint8,Backend,C.c_void_p]
  c.d578_rx_threshold.argtypes=[C.c_uint8,C.c_uint8,Backend,C.c_void_p]
  c.d578_rx_squelch_update.argtypes=[C.POINTER(Sq)]+[C.c_uint16]*4;c.d578_rx_squelch_update.restype=C.c_bool
  o.fixture();expected=o.call(0x80723e6);trace.clear();assert c.d578_rx_reset(record,None)==0;check('reset_profile',expected)
  examples={}
  for b,narrow in product(range(2),range(2)):
   o.fixture(narrow);expected=o.call(0x806e84a,0,b);trace.clear();assert c.d578_rx_fm_mode(b,narrow,record,None)==0;check('FM_bandwidth',expected)
  for b,narrow,raw in product(range(2),range(2),[0,70,120,255]):
   o.fixture(narrow);expected=[[0,b,3,0]]+o.call(0x806e84a,0,b)+o.call(0x806e5b2,0,b)+o.call(0x806e4ba,0,b)+o.call(0x806dd92,2 if narrow else 1,b)+o.call(0x806d1cc,raw,b)
   trace.clear();assert c.d578_rx_begin(b,narrow,raw,record,None)==0;check('receive_begin',expected)
   expected=o.call(0x806d06a,b,0);trace.clear();assert c.d578_rx_start(b,record,None)==0;check('receive_start',expected)
  freqs=set(range(13600000,17400001,1250))|set(range(40000000,48000001,1250))|{13600000,17400000,40000000,48000000}
  for b in range(2):
   for f in sorted(freqs):
    o.fixture();expected=o.call(0x806e3f0,f,b);trace.clear();assert c.d578_rx_tune(b,f,record,None)==0;check('frequency',expected)
    if f in [14550000,43500000]:examples[f'{b}:{f}']=trace.copy()
   for raw in range(256):
    o.fixture();expected=o.call(0x806d1cc,raw,b);trace.clear();assert c.d578_rx_threshold(b,raw,record,None)==0;check('threshold',expected)
  # Original SQ routine with explicit standard analog channel, no CTCSS.
  # The terminal RF reads are supplied fixtures; the OEM comparator executes.
  for opened,count,status,noise,level,threshold in product(range(2),range(3),[0,2],[0,43,44,127],[0,69,70,120,255,511],[70,120,255,511]):
   o.fixture();o.reads={(0,12):status,(0,101):noise,(0,103):level}
   o.u.mem_write(0x200011aa,bytes([opened]));o.u.mem_write(0x200011ad,bytes([count]));o.u.mem_write(0x200011a6,threshold.to_bytes(2,'little'))
   o.call(0x808f932)
   expected=[o.u.mem_read(0x200011aa,1)[0],o.u.mem_read(0x200011ad,1)[0]]
   sq=Sq(opened,count);c.d578_rx_squelch_update(C.byref(sq),status,noise,level,threshold)
   assert [int(sq.open),sq.count]==expected,(opened,count,status,noise,level,threshold,expected,[sq.open,sq.count])
   counts['squelch']=counts.get('squelch',0)+1
 summary={'referenceFlashSHA256':hashlib.sha256(Path(FLASH).read_bytes()).hexdigest(),'method':'isolated OEM routine execution with explicit RAM fixtures; terminal RF writes, reads and delays compared to independent C','coldBoot':False,'hardwareTest':False,'fixtures':{'reset':'Radio Spk, MAIN, ordinary mode; getter index 0','FM':'ordinary analog, bandwidth selector 0/1, auxiliary flag 0','squelch':'enabled level, analog channel, no CTCSS; raw RF samples'},'routines':{'reset':'0x080723E6','FM':'0x0806E84A','tune':'0x0806E3F0','threshold':'0x0806D1CC','squelch':'0x0808F932'},'passed':counts,'total':sum(counts.values()),'mismatches':0,'frequencyExamples':examples}
 Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'passed':counts,'total':sum(counts.values()),'mismatches':0}))
