import test from 'node:test';
import assert from 'node:assert/strict';
import {VirtualUsbCable,CpsUsbTransport,UsbNotConnected} from '../assets/usb-cps.mjs';
import {MIC_CODES,encodeMicKey,WiredMicReceiver,WiredMicrophoneCable} from '../assets/wired-microphone.mjs';

test('USB/CPS cannot read a codeplug when firmware USB controller is absent',async()=>{
  const usb=new VirtualUsbCable();
  const cps=new CpsUsbTransport(usb,{endpointIn:2,endpointOut:1});
  await assert.rejects(()=>cps.exchange(Uint8Array.of(0x12)),UsbNotConnected);
  await assert.rejects(()=>usb.enumerate(),UsbNotConnected);
});
test('USB CPS raw exchange goes strictly via device controller, no memory backing',async()=>{
  const calls=[];
  const usb=new VirtualUsbCable();
  usb.attachPeripheral({
    enumerate:async()=>({deviceAddress:1}),
    control:async(setup)=>{calls.push(['setup',...setup]);return Uint8Array.of();},
    out:async(ep,bytes)=>{calls.push(['out',ep,...bytes]);return bytes.length;},
    in:async(ep,length)=>{calls.push(['in',ep,length]);return Uint8Array.of(0xb1,0xb2);}
  });
  const cps=new CpsUsbTransport(usb,{endpointIn:2,endpointOut:3});
  assert.deepEqual(Array.from(await cps.exchange(Uint8Array.of(0xa1,0xa2))),[0xb1,0xb2]);
  assert.deepEqual(calls,[['out',3,0xa1,0xa2],['in',2,64]]);
  assert.deepEqual(await usb.enumerate(),{deviceAddress:1});
  usb.disconnect();
  await assert.rejects(()=>cps.exchange(Uint8Array.of(1)),UsbNotConnected);
});
test('USB rejects invalid peripheral responses and endpoint injection',async()=>{
  const usb=new VirtualUsbCable();
  assert.throws(()=>new CpsUsbTransport(usb,{endpointIn:-1,endpointOut:0}),RangeError);
  assert.throws(()=>usb.attachPeripheral({out(){}}),TypeError);
  usb.attachPeripheral({enumerate:async()=>({}),control:async()=>Uint8Array.of(),out:async()=>{},in:async()=>new Uint8Array(129)});
  await assert.rejects(()=>usb.bulkIn(1,64),TypeError);
  await assert.rejects(()=>usb.control(Uint8Array.of(1)),TypeError);
});
test('wired microphone keyboard and PTT frames match documented profile',()=>{
  assert.deepEqual([...encodeMicKey({ptt:true})],[0x41,1,0,0,0,0,0,6]);
  assert.deepEqual([...encodeMicKey({name:'3',active:true})],[0x41,0,1,0,4,0,0,6]);
  assert.equal(MIC_CODES['SUB A/B'],13);
  assert.throws(()=>encodeMicKey({name:'P4'}),RangeError);
});
test('wired microphone physical UART FIFO gets 8 individual bytes; no fake outputs',()=>{
  const uartRx=[];
  const mic=new WiredMicrophoneCable({rxByteFromWire:byte=>uartRx.push(byte)});
  assert.equal(mic.status().received,false);
  mic.press({name:'UP',active:true});
  assert.deepEqual(uartRx,[0x41,0,1,0,16,0,0,6]);
  assert.equal(mic.status().received,false);
});
test('wired mic radio responses only appear after full valid USART frame',()=>{
  const receiver=new WiredMicReceiver();
  const sample=Uint8Array.of(0x53,1,0,0,0,1,0,1,0,0x10,0,0,0,0,0,0x06);
  receiver.inputBytes(sample.slice(0,7));
  assert.equal(receiver.status().received,false);
  receiver.inputBytes(sample.slice(7));
  assert.equal(receiver.status().main,'B');
  assert.equal(receiver.status().rxA,1);
  assert.equal(receiver.status().unknown[9],0x10);
  assert.equal(receiver.status().frames,1);
  const invalid=sample.slice(); invalid[15]=0x99;
  receiver.inputBytes(invalid);
  assert.equal(receiver.status().rejected,1);
  assert.equal(receiver.status().frames,1);
});
