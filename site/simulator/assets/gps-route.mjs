/* Synthetic ground track, great-circle arcs on a sphere of mean radius.
 * This supplies NMEA inputs; it does not calculate a radio/GNSS firmware fix. */
export const EARTH_RADIUS_M=6371008.8;
const RAD=Math.PI/180,DEG=180/Math.PI,clamp=x=>Math.max(-1,Math.min(1,x));
export function point(latitude,longitude){latitude=Number(latitude);longitude=Number(longitude);if(!Number.isFinite(latitude)||Math.abs(latitude)>90||!Number.isFinite(longitude)||Math.abs(longitude)>180)throw Error('Coordonnées du trajet invalides');return {latitude,longitude};}
export function inverse(a,b){const p=a.latitude*RAD,q=b.latitude*RAD,d=(b.longitude-a.longitude)*RAD,s=Math.sin((q-p)/2)**2+Math.cos(p)*Math.cos(q)*Math.sin(d/2)**2;return {distance:2*EARTH_RADIUS_M*Math.asin(Math.sqrt(Math.max(0,Math.min(1,s)))),course:(Math.atan2(Math.sin(d)*Math.cos(q),Math.cos(p)*Math.sin(q)-Math.sin(p)*Math.cos(q)*Math.cos(d))*DEG+360)%360};}
export function direct(a,course,distance){const p=a.latitude*RAD,l=a.longitude*RAD,c=course*RAD,s=distance/EARTH_RADIUS_M,q=Math.asin(clamp(Math.sin(p)*Math.cos(s)+Math.cos(p)*Math.sin(s)*Math.cos(c))),n=l+Math.atan2(Math.sin(c)*Math.sin(s)*Math.cos(p),Math.cos(s)-Math.sin(p)*Math.sin(q));return {latitude:q*DEG,longitude:((n*DEG+540)%360)-180};}
export function squareRoute(origin,side){const east=direct(origin,90,side),south=direct(east,180,side),west=direct(south,270,side);return [origin,east,south,west,origin];}
function bounded(v,lo,hi,label){v=Number(v);if(!Number.isFinite(v)||v<lo||v>hi)throw Error(label+' hors plage');return v;}
export function compileMotion(c){const origin=point(c.latitude,c.longitude),kind=c.motion??'static',speedKmh=bounded(c.speedKmh??36,0,1000,'Vitesse'),course=bounded(c.course??90,0,360,'Cap')%360,delay=bounded(c.startDelaySeconds??2,0,3600,'Attente initiale');
 if(!['static','line','square','route'].includes(kind))throw Error('Mouvement GPS inconnu');
 let points=[origin],segments=[],duration=0;
 if(kind==='line'){if(speedKmh<=0)throw Error('Le mouvement exige une vitesse positive');duration=bounded(c.durationSeconds??12,0.1,86400,'Durée');if(speedKmh/3.6*duration>2000000)throw Error('Ligne GPS : distance maximale 2 000 km');points.push(direct(origin,course,speedKmh/3.6*duration));segments=[{a:origin,b:points[1],course,distance:speedKmh/3.6*duration,start:0,end:duration}];}
 if(kind==='square'||kind==='route'){
  if(speedKmh<=0)throw Error('Le trajet exige une vitesse positive');points=kind==='square'?squareRoute(origin,bounded(c.sideMeters??30,1,100000,'Côté du carré')):c.route;
  if(!Array.isArray(points)||points.length<2||points.length>256)throw Error('Trajet : 2 à 256 points');points=points.map(p=>point(p.latitude,p.longitude));
  for(let i=1;i<points.length;i++){const g=inverse(points[i-1],points[i]);if(g.distance<0.001||g.distance>2000000)throw Error('Segment GPS : distance 0,001 m à 2 000 km');const end=duration+g.distance/(speedKmh/3.6);segments.push({a:points[i-1],b:points[i],...g,start:duration,end});duration=end;}
 }
 return {kind,origin:points[0],points,segments,speedKmh,course,delay,duration};
}
export function motionAt(m,seconds){const elapsed=Math.max(0,seconds-m.delay),active=m.kind!=='static'&&seconds>=m.delay&&elapsed<m.duration;
 if(m.kind==='static'||seconds<m.delay)return {...m.origin,speedKmh:0,course:0,phase:m.kind==='static'?'stationary':'waiting',elapsedSeconds:seconds};
 if(!active)return {...m.points.at(-1),speedKmh:0,course:m.segments.at(-1)?.course??m.course,phase:'finished',elapsedSeconds:seconds};
 const s=m.segments.find(s=>elapsed<s.end),distance=Math.min(s.distance,(elapsed-s.start)*m.speedKmh/3.6),p=direct(s.a,s.course,distance),course=inverse(p,s.b).course;
 return {...p,speedKmh:m.speedKmh,course,phase:'moving',elapsedSeconds:seconds};
}
