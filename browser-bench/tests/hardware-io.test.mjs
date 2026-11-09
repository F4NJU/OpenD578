import test from 'node:test';
import assert from 'node:assert/strict';
import {BoardIO,Lcd8080,GPIO_BASE,ADC0,USART0} from '../assets/board-io.mjs';
function lbus(b,byte,data=false){const B=GPIO_BASE.B,E=GPIO_BASE.E;
 b.write(B+4,0x33333333);b.write(E,0x34444444);b.write(E+4,0x33333333);
 b.write(B+0x0c,0x3c00); // CS high, WR high, Reset high
 b.write(E+0x0c,(byte&255)<<7);
 b.write(B+0x0c,data?0x1800:0x1000); // CS low, WR low, D/C data bit, RESET high
 b.write(B+0x0c,data?0x1c00:0x1400); // WR rising while CS low
}
test('front inputs: power PA0, encoder push PA1 and ADC resistor arrays',()=>{
 const b=new BoardIO();assert.equal(b.read(GPIO_BASE.A+8)&3,3);
 b.setKey('POWER',true);b.setKey('DIAL_PRESS',true);assert.equal(b.read(GPIO_BASE.A+8)&3,0);
 b.setKey('P1',true);assert.equal(b.adc.get(8),250);
 b.setKey('P1',false);b.setKey('MENU',true);assert.equal(b.adc.get(8),3000);
 b.setKey('P4',true);assert.equal(b.adc.get(9),250);
 b.setVolume('A',1234);assert.equal(b.adc.get(12),1234);
 b.write(ADC0+0x34,12);assert.equal(b.read(ADC0+0x4c),1234);
});
test('only valid LCD bus strobes can change LCD pixels; no synthetic screen',()=>{
 const b=new BoardIO();assert.equal(b.lcd.writes,0);
 lbus(b,0x11);lbus(b,0x29);
 // Set a one-pixel column and row window
 for(const [cmd,values] of [[0x2a,[0,0,0,0]],[0x2b,[0,0,0,0]]]){
  lbus(b,cmd);for(const v of values)lbus(b,v,true);
 }
 lbus(b,0x2c);lbus(b,0xf8,true);lbus(b,0x00,true);
 assert.equal(b.lcd.pixels[0],0xf800);assert.equal(b.lcd.displayOn,true);
 assert.equal(b.lcd.writes,1);
});
test('front LED shift frame 8 bits LSB from PE3 and PE4',()=>{
 const b=new BoardIO(),E=GPIO_BASE.E;
 b.write(E,0x44433444);const data=0x18;
 for(let i=0;i<8;i++){b.write(E+0x0c,((data>>i)&1)<<3);b.write(E+0x0c,(((data>>i)&1)<<3)|(1<<4));}
 assert.equal(b.ledRaw,data);assert.equal(b.green,true);assert.equal(b.red,true);
});
test('backlight 12-bit serial PA5/PB3/PB4 channel 8',()=>{
 const b=new BoardIO(),A=GPIO_BASE.A,B=GPIO_BASE.B,word=(8<<8)|128;
 b.write(A,0x44344444);b.write(B,0x44433444);
 b.write(A+0x0c,0x20);b.write(A+0x0c,0); // latch low
 for(let i=11;i>=0;i--){const bit=(word>>i)&1;b.write(B+0x0c,bit<<4);b.write(B+0x0c,(bit<<4)|8);}
 b.write(A+0x0c,0x20);assert.equal(b.lcdBacklight,128);
 assert.equal(b.lightRaw.get(8),128);
});
test('wired microphone PTT uses actual UART RX FIFO bytes',()=>{
 const b=new BoardIO();const sent=b.micPress({ptt:true,active:true});
 assert.deepEqual([...sent],[0x41,1,1,0,0,0,0,6]);
 assert.equal(b.read(USART0)&0x20,0x20);
 for(const x of sent)assert.equal(b.read(USART0+4),x);
 assert.equal(b.read(USART0)&0x20,0);
});


test('GPIO input latches cannot fabricate LCD or lighting edges',()=>{
 const b=new BoardIO();for(let i=0;i<16;i++){b.write(GPIO_BASE.E+12,0);b.write(GPIO_BASE.E+12,24);b.write(GPIO_BASE.B+12,0x1000);b.write(GPIO_BASE.B+12,0x1400);}
 assert.equal(b.lcd.writes,0);assert.equal(b.lcd.displayOn,false);assert.equal(b.ledRaw,null);
});
test('an unsupported key chord does not corrupt the accepted ADC input',()=>{
 const b=new BoardIO();b.setKey('P1',true);assert.throws(()=>b.setKey('P2',true),/simultanees/);assert.deepEqual([...b.keys],['P1']);assert.equal(b.adc.get(8),250);
});
