from pathlib import Path
import json,struct,hashlib,collections,sys
import capstone as cs
from capstone.arm import *
BASE=0x08000000
root=Path(__file__).resolve().parent
src=Path(__file__).with_name('scan_gpio_reference.py').read_text().split('records=[]')[0]
g={};exec(src,g)
md=g['md'];interpret=g['interpret'];ports=g['ports']
images={'PRO':Path('inputs/Firmware D578/full_flash_pass1(1).bin').read_bytes(),'PLUS':bytes(0x6000)+Path('native_v05/firmwares/D578UV2_GD_V2.08_20240619.CDD').read_bytes()}
api={0x8008796:'read',0x80087a8:'read-port',0x80087b0:'read-out',0x80087c2:'read-out-port',0x80087ca:'set',0x80087ce:'clear',0x80087d2:'write',0x80087dc:'port-write',0x8008670:'init'}
def calls(b):
 out=[]
 for o in range(0x6000,min(len(b)-4,0x100000),2):
  a,z=struct.unpack_from('<HH',b,o)
  if a&0xf800!=0xf000 or z&0xd000!=0xd000:continue
  s=a>>10&1;i1=1-((z>>13&1)^s);i2=1-((z>>11&1)^s)
  imm=(s<<24)|(i1<<23)|(i2<<22)|((a&1023)<<12)|((z&2047)<<1);imm-=s<<25
  out.append((BASE+o,BASE+o+4+imm))
 return out
def scan(b):
 g['image']=b;records=[]
 for a,t in calls(b):
  if t not in api:continue
  regs={ARM_REG_SP:0x20017000};mem={}
  for ins in md.disasm(b[a-BASE-256:a-BASE+4],a-256):
   if ins.address==a:break
   if not ins.id:continue
   if ins.mnemonic=='push':
    regs={ARM_REG_SP:0x20017000};mem={};continue
   ops=ins.operands
   if ins.mnemonic.split('.')[0]in ('str','strh','strb') and len(ops)>1 and ops[1].type==ARM_OP_MEM:
    q=ops[1].mem;v=g['val'](ops[0],regs);p=regs.get(q.base)
    if v is not None and p is not None and not q.index:
     ad=p+q.disp;n={'str':4,'strh':2,'strb':1}[ins.mnemonic.split('.')[0]]
     if 0x20000000<=ad<0x20018000:
      for k in range(n):mem[ad+k]=(v>>(8*k))&255
   interpret(ins,regs)
  port=regs.get(ARM_REG_R0);mask=regs.get(ARM_REG_R1);mode=None
  if api[t]=='init' and mask is not None:
   if mask in mem and mask+1 in mem:
    p=mask;mask=mem[p]|mem[p+1]<<8;mode=mem.get(p+3)
   else:mask=None
  pins=[ports[port]+str(i)for i in range(16)if mask&(1<<i)]if port in ports and mask is not None and 0<mask<65536 else []
  records.append(dict(call=f'0x{a:08X}',target=f'0x{t:08X}',api=api[t],port=hex(port)if port else None,mask=hex(mask)if mask is not None else None,pins=pins,mode=mode))
 return records
def dump(model,lo,hi):
 b=images[model];out=[]
 for i in md.disasm(b[lo-BASE:hi-BASE],lo):
  ext=''
  if i.id and len(i.operands)>1 and i.operands[1].type==ARM_OP_MEM and i.operands[1].mem.base==ARM_REG_PC:
   ad=((i.address+4)&~3)+i.operands[1].mem.disp
   if BASE<=ad<BASE+len(b)-4:ext=f' ; [{ad:08X}]={struct.unpack_from("<I",b,ad-BASE)[0]:08X}'
  out.append(f'{i.address:08X} {i.mnemonic:10s} {i.op_str}{ext}')
 return '\n'.join(out)+'\n'
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='dump':
  print(dump(sys.argv[2],int(sys.argv[3],16),int(sys.argv[4],16)));raise SystemExit
 results={model:scan(image)for model,image in images.items()}
 (root/'GPIO_COMPARAISON.json').write_text(json.dumps(results,indent=2))
 for model,rs in results.items():
  print(model,'calls',len(rs),'known GPIO',sum(bool(x['pins'])for x in rs))
  for p in ['PC3','PE15','PB9','PE5','PC4','PA8','PC6','PC7','PC12','PD1','PD6','PD7']:
   print(p,[(r['call'],r['api'],r['mode'])for r in rs if p in r['pins']])
  with (root/(model+'_CIBLES.disasm')).open('w')as f:
   for r in rs:
    if set(r['pins'])&{'PC3','PE15','PB9','PA8','PC6','PC7','PC12','PD1','PD6','PD7'}:
     a=int(r['call'],16);f.write('\n'+str(r)+'\n'+dump(model,a-40,a+18))
 psets={model:{p for r in rs for p in r['pins']}for model,rs in results.items()}
 print('PLUS-only pins',sorted(psets['PLUS']-psets['PRO']))
 print('PRO-only pins',sorted(psets['PRO']-psets['PLUS']))
