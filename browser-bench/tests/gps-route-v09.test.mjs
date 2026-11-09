import test from 'node:test';import assert from 'node:assert/strict';
import {compileMotion,motionAt,inverse,direct} from '../assets/gps-route.mjs';import {GpsInput,gpsSentences,nmea,VIRTUAL_HZ} from '../assets/gps-input.mjs';import {Uart} from '../assets/timed-devices.mjs';
const cfg={mode:'fix',latitude:48,longitude:2,utc:'2026-11-08T23:59:59Z',hertz:1,motion:'square',sideMeters:30,speedKmh:36,startDelaySeconds:2};
test('RMC encodes knots and true course; VTG includes km/h; midnight and hemispheres stay coherent',()=>{
 const text=gpsSentences(-48,-2,'2026-11-09T00:00:00Z',true,{speedKmh:18.52,course:90,vtg:true,talker:'GN'});assert(text.includes(',S,00200.0000,W,10.00,90.00,091126,'));assert(text.includes('GNVTG,90.00,T,,M,10.00,N,18.52,K,A*'));for(const l of text.trim().split('\r\n'))assert.equal(nmea(l.slice(1,l.indexOf('*'))).trim(),l);
 assert(gpsSentences(0,0,'2026-11-08T12:00:00Z',true,{course:359.999}).includes(',0.00,0.00,'));
});
test('30m square is continuous, changes course, returns to origin and stops; line wraps the dateline',()=>{
 const m=compileMotion(cfg);assert(Math.abs(m.duration-12)<0.001);assert.equal(motionAt(m,1).speedKmh,0);const a=motionAt(m,3),b=motionAt(m,4);assert.equal(a.speedKmh,36);assert(Math.abs(inverse(a,b).distance-10)<0.001);assert(Math.abs(a.course-90)<0.01);assert(Math.abs(motionAt(m,6).course-180)<0.01);const end=motionAt(m,15);assert.equal(end.speedKmh,0);assert.equal(end.phase,'finished');assert.equal(end.latitude,48);assert.equal(end.longitude,2);
 const line=compileMotion({...cfg,motion:'line',latitude:0,longitude:179.999,speedKmh:360,course:90,durationSeconds:10,startDelaySeconds:0});assert.throws(()=>compileMotion({...cfg,motion:'line',speedKmh:1000,durationSeconds:86400}),/distance maximale/);assert(motionAt(line,5).longitude<0);assert.equal(motionAt(line,11).speedKmh,0);assert(inverse({latitude:0,longitude:0},direct({latitude:0,longitude:0},90,100)).distance>99.999);
});
test('GNSS scheduling has no receiver backpressure, supports corrupt/truncated sentences and rejects overfull UART profiles atomically',()=>{
 const u=new Uart('USART1',()=>true);u.r[12]=0x2004;u.byteSteps=125000;const g=new GpsInput();g.configure({...cfg,fault:'checksum',faultEvery:2},0);g.advance(0,u);u.advance(VIRTUAL_HZ);assert(u.overruns>0);const first=u.data;g.advance(VIRTUAL_HZ,u);assert.equal(g.frames,2);assert(g.status().lastSample.corrupted);assert.equal(u.data,first);const before=g.status().mode;assert.throws(()=>g.configure({...cfg,baud:4800,hertz:4},0),/insuffisant/);assert.equal(g.status().mode,before);assert.throws(()=>g.configure({...cfg,utc:'2026-11-08T12:00:00'},0),/UTC/);
 const bad=g.events.at(-1).hex.match(/../g).map(x=>parseInt(x,16)),text=String.fromCharCode(...bad);const line=text.split('\r\n')[0];assert.notEqual(nmea(line.slice(1,line.indexOf('*'))).trim(),line);
 g.configure({...cfg,fault:'truncated',faultEvery:1},2*VIRTUAL_HZ);g.advance(2*VIRTUAL_HZ,u);assert(!String.fromCharCode(...g.events.at(-1).hex.match(/../g).map(x=>parseInt(x,16))).includes('\r\n'));
});
test('10,000 input epochs keep exact cadence, bounded history and no delayed bytes when UART is disabled',()=>{
 const u=new Uart('USART1',()=>false),g=new GpsInput();g.configure(cfg,0);for(let i=0;i<10000;i++){g.advance(i*VIRTUAL_HZ,u);u.advance((i+1)*VIRTUAL_HZ-1);}assert.equal(g.frames,10000);assert.equal(g.missedPeriods,0);assert.equal(g.events.length,16);assert.equal(u.disabledDrops,g.bytes);assert.equal(u.rxTotal,0);assert.equal(u.wire.length,0);assert.equal(g.status().lastSample.phase,'finished');assert(g.status().lastSample.utc.startsWith('2026-11-09'));
});

test('UART peripheral reset keeps the independent external wire; disabled reception loses bytes instead of replaying',()=>{const u=new Uart('USART1',()=>true);u.byteSteps=125000;u.r[12]=0x2004;u.schedule([65,66],{at:0,byteSteps:125000});u.reset();assert.equal(u.wire.length,2);u.advance(125000);assert.equal(u.disabledDrops,1);u.r[12]=0x2004;u.advance(250000);assert.equal(u.read(4,4),66);assert.equal(u.overruns,0);});
