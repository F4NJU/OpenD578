import test from 'node:test';
import assert from 'node:assert/strict';
import {BootPeripherals,RCU_BASE,SCB_BASE,BITBAND_RCU,FMC_BASE} from '../assets/startup-peripherals.mjs';
import {NandOverlay,NAND_MAIN_SIZE,NAND_OOB_SIZE,NAND_ECC_SIZE} from '../assets/nand.mjs';
import {NandSpi} from '../assets/nand-spi.mjs';
import {BoardIO,GPIO_BASE,USART0,USART1,AFIO,EXTI} from '../assets/board-io.mjs';

test('RCU boot oscillator reset and readiness sourced from real enable bits',()=>{
 const p=new BootPeripherals();
 assert.equal(p.read(RCU_BASE,4)&3,3);
 p.write(RCU_BASE,0x10001,4);
 assert.equal(p.read(RCU_BASE,4)&(1<<17),1<<17);
 p.write(RCU_BASE+4,1,4);assert.equal(p.read(RCU_BASE+4,4)&12,4);
 p.write(RCU_BASE,0x1010001,4);
 assert.equal(p.read(RCU_BASE,4)&(1<<25),1<<25);
 p.write(RCU_BASE+4,2,4);assert.equal(p.read(RCU_BASE+4,4)&12,8);
 assert.throws(()=>p.read(RCU_BASE+0x94,4),/non modelisee/);
});
test('RCU bitband and FMC and SCB VTOR: hardware register writes, no OEM RAM',()=>{
 const p=new BootPeripherals();const clkBit=BITBAND_RCU+32*0+4*16;
 p.write(clkBit,1,4);assert.equal(p.read(clkBit,4),1);
 p.write(FMC_BASE,3,4);assert.equal(p.read(FMC_BASE,4),3);
 p.write(SCB_BASE+0xd08,0x08006000,4);assert.equal(p.read(SCB_BASE+0xd08,4),0x08006000);
 p.write(SCB_BASE+0x100,1<<23,4);assert.equal(p.read(SCB_BASE+0x100,4),1<<23);
 p.write(SCB_BASE+0x180,1<<23,4);assert.equal(p.read(SCB_BASE+0x100,4),0);
 assert.throws(()=>p.write(FMC_BASE+4,0x55,4),/FMC/);
});
test('SysTick reads alone do not advance time or manufacture COUNTFLAG',()=>{
 const p=new BootPeripherals();p.write(SCB_BASE+0x14,2,4);p.write(SCB_BASE+0x10,5,4);
 p.read(SCB_BASE+0x18,4);p.read(SCB_BASE+0x18,4);p.read(SCB_BASE+0x18,4);
 assert.equal(p.read(SCB_BASE+0x18,4),0);assert.equal(p.read(SCB_BASE+0x10,4)&(1<<16),0);
 assert.equal(p.read(SCB_BASE+0x10,4)&(1<<16),0);
});

// Read one synthetic page from a 256-MiB source without allocating 256 MiB.
function captured(){
 const overlay=new NandOverlay({syncReader:(f,from,to)=>{
   const b=new Uint8Array(to-from).fill(0xff);
   if(f.name==='main'&&from===0)b[0]=0x12,b[1]=0x34;
   if(f.name==='ecc'&&from===0)b[0]=0x20;
   return b;
 }});
 overlay.attach('main',{name:'main',size:NAND_MAIN_SIZE});
 overlay.attach('oob',{name:'oob',size:NAND_OOB_SIZE});
 overlay.attach('ecc',{name:'ecc',size:NAND_ECC_SIZE});
 return overlay;
}
function transaction(n,bytes){
 // CS# PB8, CLK PB15, DATA PB14. No direct NAND calls outside GPIO transitions.
 n.drive(0,1<<8);
 for(const byte of bytes){
  for(let i=7;i>=0;i--){
   const bit=(byte>>i)&1;
   const signal=bit<<14;
   n.drive(signal,(1<<14)|(1<<15));
   n.drive(signal|(1<<15),1<<15);
  }
 }
 n.drive(1<<8,1<<8);
}
test('NAND bit-banged GPIO page-read 0x13, cache 0x03, ECC and JEDEC ID',()=>{
 const n=new NandSpi(captured());
 transaction(n,[0x13,0,0,0]);
 assert.equal(n.cachedPage,0);assert.equal(n.status&0x30,0x20);
 assert.deepEqual(Array.from(n.cache.subarray(0,2)),[0x12,0x34]);
 assert.equal(n.outputByte(0),0xff);
 transaction(n,[0x9f,0,0,0]);
 assert.equal(n.outputByte(2),0x98);assert.equal(n.outputByte(3),0xcb);
 assert.equal(n.summary().transactions,2);
});
test('NAND copy-on-write programming and protected erase, no change to source image',()=>{
 const storage=captured(),n=new NandSpi(storage),blocked=new NandSpi(storage);
 transaction(blocked,[0x06]);
 assert.throws(()=>transaction(blocked,[0xd8,0,0,0]),/proteges/);
 transaction(n,[0x06]);
 transaction(n,[0x1f,0xa0,0]);
 transaction(n,[0x02,0,0,0x0f]);
 transaction(n,[0x10,0,0,0]);
 assert.equal(storage.readPageSync('main',0).bytes[0],0x02); // 0x12 & 0x0F
 assert.equal(storage.readPageSync('main',0).source,'overlay');
 assert.equal(n.writes,1);
});
test('GPIO input/output, ADC keys, wired microphone and UART1 GPS are physical peripherals',()=>{
 const b=new BoardIO();
 b.setKey('POWER',true);assert.equal(b.read(GPIO_BASE.A+8,4)&1,0);
 b.setKey('POWER',false);assert.equal(b.read(GPIO_BASE.A+8,4)&1,1);
 b.write(GPIO_BASE.A,0x44444443);b.write(GPIO_BASE.A+0x10,1);
 assert.equal(b.read(GPIO_BASE.A+8,4)&1,1);
 b.write(AFIO+4,123);assert.equal(b.read(AFIO+4),123);
 b.write(EXTI+0x14,0x100);assert.equal(b.read(EXTI+0x14),0);
 b.write(USART0+8,0x44);b.write(USART0+0x0c,0x2008);b.write(USART0+4,0x53);
 assert.equal(b.uartTxCount,1);
 b.injectGpsNmea('$GPRMC,123000,A,4807.038,N,01131.000,E,0.0,0.0,230394,,');
 assert.equal(b.read(USART1,4)&0x20,0x20);
 assert.equal(b.read(USART1+4,4),36);
 assert.throws(()=>b.read(0x4000f000,4),/inconnu/);
});

test('Whole NAND GPIO path from MCU writes: BOP/BC drive serial flash, input sampled at PA15',()=>{
 const b=new BoardIO({nandStorage:captured()}),base=GPIO_BASE.B;
 // Begin idle CS high. The simulated MCU drives PB8/PB14/PB15 through GPIO.
 b.write(base+0x0c,1<<8);
 b.write(base+0x14,1<<8);
 for(const byte of [0x13,0,0,0])for(let i=7;i>=0;i--){
   b.write(base+0x14,1<<15);
   if((byte>>i)&1)b.write(base+0x10,1<<14);
   else b.write(base+0x14,1<<14);
   b.write(base+0x10,1<<15);
 }
 b.write(base+0x10,1<<8);
 assert.equal(b.nand.cachedPage,0);
 assert.equal(b.nand.cache[0],0x12);
 assert.equal(b.read(GPIO_BASE.A+8,4)>>15&1,b.nand.miso);
});
