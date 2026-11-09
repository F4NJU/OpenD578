/* User-requested cold start. No PC/address checks, RAM writes or LCD injection.
 * At most one external Power pulse, at the first reported WFI/WFE stop.
 */
export class GuidedBoot {
 constructor({run,powerPulse,onPower=()=>{}}){this.execute=run;this.powerPulse=powerPulse;this.onPower=onPower;this.pending=false;}
 arm(){this.pending=true;}
 cancel(){this.pending=false;}
 async run(budget){
  const state=await this.execute(budget);
  if(!this.pending||state.cpu?.stop?.category!=='waiting')return state;
  this.pending=false;
  await this.powerPulse();this.onPower();
  return this.execute(budget);
 }
}
