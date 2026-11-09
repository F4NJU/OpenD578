"""Comparaison de routines isolées PRO/PLUS ; aucun accès matériel."""
from pathlib import Path
import json,hashlib
from unicorn import *
from unicorn.arm_const import *
from analyse import images
def run(model,pc,arg=0):
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
 u.mem_map(0x08000000,0x300000);u.mem_write(0x08000000,images[model]);u.mem_map(0x20000000,0x18000);u.mem_map(0x40000000,0x24000)
 u.reg_write(UC_ARM_REG_SP,0x20017000);u.reg_write(UC_ARM_REG_R0,arg);u.reg_write(UC_ARM_REG_LR,0x080FFF01);u.reg_write(UC_ARM_REG_XPSR,0x1000000)
 writes=[]
 u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,n,v,_:writes.append([a,n,v]),begin=0x40000000,end=0x40023fff)
 u.emu_start(pc|1,0x080FFF00,count=400000)
 assert u.reg_read(UC_ARM_REG_PC)==0x080FFF00,(model,hex(pc))
 return writes
checks=[]
def pair(name,pro,plus,arg=0):
 a=run('PRO',pro,arg);b=run('PLUS',plus,arg);assert a==b,(name,a,b)
 checks.append(dict(name=name,PRO=f'0x{pro:08X}',PLUS=f'0x{plus:08X}',argument=arg,writes=a,result='PASS'))
for name,p,q in [('USB_PE2',0x809B396,0x809B3F2),('SCT_PD1',0x809364C,0x80936A6),('SCT_PC7',0x8093666,0x80936C4),('SCT_PD7',0x8093A5E,0x8093ABC),('RF_PC4',0x808A2C4,0x808A318)]:
 for arg in (0,1):pair(name,p,q,arg)
pair('PC3_init',0x808A1A8,0x808A1FC)
pair('PB9_PWM_AF',0x808C7B6,0x808C80A)
pair('PB9_analog',0x808C796,0x808C7EA)
for arg in (0,1,127,255):pair('PB9_PWM_sample',0x808C834,0x808C888,arg)
pair('BH2226_init',0x808A8A0,0x808A8F4)
gpio=json.loads(Path(__file__).with_name('GPIO_COMPARAISON.json').read_text())
keys=['api','port','mask','mode']
assert len(gpio['PRO'])==len(gpio['PLUS'])==570
assert all(all(a[k]==b[k]for k in keys)for a,b in zip(gpio['PRO'],gpio['PLUS']))
result=dict(method='Routines OEM isolées, données RAM de test à zéro, écritures MMIO enregistrées ; pas de démarrage complet, pas de firmware SCT/Bluetooth exécuté, pas de réponse de module KT fabriquée',PRO_application_sha256=hashlib.sha256(images['PRO'][0x6000:0x6000+1020300]).hexdigest(),PLUS_application_sha256=hashlib.sha256(images['PLUS'][0x6000:]).hexdigest(),paired_cases=len(checks),isolated_executions=2*len(checks),GPIO_direct_calls_compared=570,GPIO_signature_mismatches=0,checks=checks)
Path(__file__).with_name('VALIDATION_PRO_PLUS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(f'PASS : {len(checks)} cas comparés, {2*len(checks)} exécutions OEM isolées ; 570 signatures GPIO identiques')
