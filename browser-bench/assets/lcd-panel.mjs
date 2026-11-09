/* Address-to-panel projection. MADCTL MY/MX/MV and RGB/BGR as in the
 * Sitronix command set (ST7735R V0.2 pp.112-114); exact D578 controller
 * silicon is not identified. The panel is mounted landscape on the facade. */
export function landscapePixels(model){
 const rgba=new Uint8ClampedArray(160*128*4),p=model.pixels??[],ctl=model.orientation??0;
 for(let y=0;y<160;y++)for(let x=0;x<128;x++){
  const c=p[y*128+x]??0;
  // Transform address order into the fixed portrait panel before its mounting rotation.
  let px=ctl&0x40?127-x:x,py=ctl&0x80?159-y:y;
  if(ctl&0x20){[px,py]=[py,px];}
  const dx=py,dy=127-px;if(dx<0||dx>=160||dy<0||dy>=128)continue;
  const i=(dy*160+dx)*4,r=((c>>>11)&31)*255/31,g=((c>>>5)&63)*255/63,b=(c&31)*255/31;
  // D578 panel native colour order is BGR (confirmed by user comparison).
  rgba[i]=ctl&8?r:b;rgba[i+1]=g;rgba[i+2]=ctl&8?b:r;rgba[i+3]=255;
 }
 return rgba;
}
