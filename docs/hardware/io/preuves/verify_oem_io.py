"""Tests isolés des instructions OEM ; aucun accès à un poste ni à sa NAND."""
from pathlib import Path
import hashlib,json
from unicorn import *
from unicorn.arm_const import *
F=Path('inputs/Firmware D578/full_flash_pass1(1).bin').read_bytes()
A=Path('oem_v121.cdd').read_bytes()
assert hashlib.sha256(F).hexdigest()=='e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e'
assert hashlib.sha256(A).hexdigest()=='02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a'
assert F[0x6000:0x6000+len(A)]==A
def run(pc,arg=0):
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
 u.mem_map(0x08000000,0x300000);u.mem_write(0x08000000,F)
 u.mem_map(0x20000000,0x20000);u.mem_map(0x40010000,0x2000)
 u.reg_write(UC_ARM_REG_SP,0x2001f000);u.reg_write(UC_ARM_REG_R0,arg)
 u.reg_write(UC_ARM_REG_LR,0x080fff01);u.reg_write(UC_ARM_REG_XPSR,0x1000000)
 writes=[]
 u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,ad,size,value,_:writes.append([ad,size,value]),begin=0x40010000,end=0x40011fff)
 u.emu_start(pc|1,0x080fff00,count=300000)
 assert u.reg_read(UC_ARM_REG_PC)==0x080fff00,hex(pc)
 return writes
cases=[]
for function,base,mask in [(0x809b396,0x40011800,4),(0x809364c,0x40011400,2),(0x8093666,0x40011000,128),(0x8093a5e,0x40011400,128),(0x808a2c4,0x40011000,16)]:
 for arg in (0,1):
  writes=run(function,arg)
  assert writes==[[base+(0x10 if arg else 0x14),4,mask]],(hex(function),arg,writes)
  cases.append(dict(function=hex(function),argument=arg,writes=[[hex(a),n,hex(v)]for a,n,v in writes],result='PASS'))
levels={0x40010800:32,0x40010c00:0};frames=[];bits=[];active=False
for ad,n,v in run(0x808a8a0):
 base=ad&~0x3ff;off=ad-base
 if base not in levels or off not in (16,20):continue
 before=dict(levels)
 levels[base]=(levels[base]|(v&65535))&~(v>>16) if off==16 else levels[base]&~v
 if before[0x40010800]&32 and not levels[0x40010800]&32:bits=[];active=True
 if active and not before[0x40010c00]&8 and levels[0x40010c00]&8:bits.append(1 if levels[0x40010c00]&16 else 0)
 if active and not before[0x40010800]&32 and levels[0x40010800]&32:
  assert len(bits)==12
  word=int(''.join(map(str,bits)),2);opcode=word>>8
  selector=int(f'{opcode:04b}'[::-1],2)
  frames.append(dict(wire_word=hex(word),opcode_MSB=hex(opcode),selector_D8_D11=selector,DA=selector if 1<=selector<=8 else None,data=word&255))
  active=False
assert [int(f['wire_word'],16)for f in frames]==[0x900,0x3ff,0xfff,0x800,0xc00,0x200,0xa00,0x600,0xe00,0x100]
assert [f['DA']for f in frames[3:]]==[1,3,4,5,6,7,8]
report=dict(method='Exécution isolée des routines OEM Cortex-M4 ; GPIO MMIO enregistrés. Pas un démarrage complet. Aucun périphérique réel. Pas de validation de délai électrique.',full_flash_sha256=hashlib.sha256(F).hexdigest(),application_sha256=hashlib.sha256(A).hexdigest(),boolean_cases=cases,BH2226_init_frames=frames,checks_passed=12)
Path('io_resolution_20261109/VALIDATION_ROUTINES_OEM.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PASS: 10 cas GPIO booléens + séquence série OEM + correspondance des sélections BH2226')
