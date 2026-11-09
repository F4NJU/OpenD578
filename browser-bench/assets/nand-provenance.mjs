/* Passive provenance of bytes actually clocked out of NAND, not cache prefetch.
 * These regions label candidate D578 calibration/configuration areas only.
 * No field values are supplied to the firmware, codec or RF model here. */
export const D578_NAND_REGIONS=Object.freeze([
 {name:'Calibration copy 0 candidate',start:0x02f60000,end:0x02f80000},
 {name:'Calibration copy 1 candidate',start:0x02f80000,end:0x02fa0000},
 {name:'Local configuration copies',start:0x02fa0000,end:0x02fe0000}
]);
export class NandReadProvenance {
 constructor(regions=D578_NAND_REGIONS){this.regions=regions.map(r=>({...r}));this.pages=new Map();this.readBytes=0;}
 observe(e,time=null){
  if(e.zone!=='main')return;
  const region=this.regions.find(r=>e.address>=r.start&&e.address<r.end);if(!region)return;
  this.readBytes++;let p=this.pages.get(e.page);
  if(!p){p={page:e.page,region:region.name,firstAt:time,lastAt:time,readBytes:0,values:new Map(),sources:new Set()};this.pages.set(e.page,p);}
  p.lastAt=time;p.readBytes++;p.values.set(e.column,e.value);p.sources.add(e.source);
 }
 observedByte(address){const p=this.pages.get(Math.floor(address/2048)),value=p?.values.get(address%2048);return value===undefined?{known:false}:{known:true,value,sources:[...p.sources],firstPageReadAt:p.firstAt,lastPageReadAt:p.lastAt};}
 status(){
  return {source:'completed NAND output bytes on GPIO serial wire',classification:'candidate regions; field meaning and copy selection require OEM analysis',directFirmwareStateWrites:false,calibrationOverrides:false,readBytes:this.readBytes,pages:[...this.pages.values()].map(p=>{
   const columns=[...p.values.keys()].sort((a,b)=>a-b),ranges=[];
   for(const c of columns){const last=ranges.at(-1);if(last&&last.end===c)last.end=c+1;else ranges.push({start:c,end:c+1});}
   return {page:p.page,address:p.page*2048,region:p.region,firstAt:p.firstAt,lastAt:p.lastAt,readBytes:p.readBytes,uniqueBytes:columns.length,ranges,sources:[...p.sources]};
  })};
 }
}
