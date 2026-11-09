import test from 'node:test';import assert from 'node:assert/strict';
import {ExecutionLoop} from '../assets/execution-loop.mjs';
test('a model stop ends continuous execution without retrying the CPU',async()=>{
 let calls=0,states=[];const loop=new ExecutionLoop({run:async()=>({cpu:{stop:++calls===3?{category:'model_incomplete'}:null}}),onState:s=>states.push(s),yieldToUi:async()=>{}});
 await loop.start();assert.equal(calls,3);assert.equal(states.length,3);assert.equal(loop.running,false);
});
test('pause waits for the pending call and does not queue another run',async()=>{
 let finish,calls=0;const loop=new ExecutionLoop({run:()=>{calls++;return new Promise(r=>finish=r)},yieldToUi:async()=>{}});
 const task=loop.start();await Promise.resolve();const paused=loop.pause();assert.equal(calls,1);
 finish({cpu:{stop:null}});await paused;await task;assert.equal(calls,1);assert.equal(loop.running,false);
});
test('repeated start cannot create two CPU loops',async()=>{
 let finish,calls=0;const loop=new ExecutionLoop({run:()=>{calls++;return new Promise(r=>finish=r)}});
 const a=loop.start(),b=loop.start();assert.equal(a,b);await Promise.resolve();const p=loop.pause();finish({cpu:{stop:null}});await p;assert.equal(calls,1);
});
test('an engine error leaves the controls resumable after a reset',async()=>{
 const events=[];let fail=true;const loop=new ExecutionLoop({run:async()=>{if(fail)throw Error('engine fault');return {cpu:{stop:{category:'model_incomplete'}}}},onRunning:s=>events.push(s)});
 await assert.rejects(loop.start(),/engine fault/);assert.equal(loop.task,null);fail=false;await loop.start();assert.deepEqual(events,[true,false,true,false]);
});
