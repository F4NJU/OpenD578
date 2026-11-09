/* Cooperative CPU execution. A pause waits for the current bounded call. */
export class ExecutionLoop {
  constructor({run,onState=()=>{},onRunning=()=>{},yieldToUi=()=>new Promise(r=>setTimeout(r,16))}) {
    this.run=run;this.onState=onState;this.onRunning=onRunning;this.yieldToUi=yieldToUi;
    this.running=false;this.task=null;
  }
  start(budget=10000) {
    if(this.task)return this.task;
    this.running=true;this.onRunning(true);
    const task=Promise.resolve().then(async()=>{
      try {
        while(this.running){
          const state=await this.run(budget);
          this.onState(state);
          if(state.cpu?.stop){this.running=false;break;}
          if(this.running)await this.yieldToUi();
        }
      } finally {this.running=false;this.task=null;this.onRunning(false);}
    });
    this.task=task;return task;
  }
  async pause(){this.running=false;if(this.task)await this.task;}
}
