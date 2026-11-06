(function () {
  'use strict';
  const models = window.OpenD578Models || {};
  const docs = window.OpenD578Docs || [];
  const photoData = window.OpenD578Photos || {};
  const S = 'http://www.w3.org/2000/svg';
  const proof = {
    physical:'Materiel observe',
    oem_trace:'Trace du firmware constructeur',
    emulator:'Observation du modèle OEM (GPIO à recouper si non tracé)',
    datasheet:'Documentation constructeur',
    hypothesis:'Affectation physique ou inter-version à confirmer',
    unknown:'Broches du segment non encore attribuées'
  };
  const $ = (id) => document.getElementById(id);
  const text = (tag, value, cls) => {
    const el=document.createElement(tag);
    if (cls) el.className=cls;
    el.textContent=value;
    return el;
  };
  const link = (url, value) => {
    const a=text('a',value);
    a.href=url;
    return a;
  };
  const svgEl = (tag, attr={}) => {
    const el=document.createElementNS(S,tag);
    Object.keys(attr).forEach(k=>el.setAttribute(k,String(attr[k])));
    return el;
  };
  function normalize(str) {
    return String(str||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  }
  function docUrl(path) {return 'doc/'+path.replace(/\.md$/i,'.html');}
  function compUrl(variant,id) {return 'component/'+encodeURIComponent(variant)+'/'+encodeURIComponent(id)+'.html';}
  function edgeUrl(variant,id) {return 'connection/'+encodeURIComponent(variant)+'/'+encodeURIComponent(id)+'.html';}

  function initSearch() {
    const input=$('docs-search'), out=$('search-results'), count=$('search-count');
    if (!input||!out) return;
    const items=docs.slice().sort((a,b)=>a.category.localeCompare(b.category)||a.title.localeCompare(b.title));
    function update() {
      const terms=normalize(input.value).split(/\s+/).filter(Boolean);
      const found=items.filter(d=>terms.every(t=>normalize(d.title+' '+d.path+' '+d.body).includes(t)));
      out.replaceChildren();
      count.textContent=found.length+' document(s) sur '+items.length;
      found.forEach(d=>{
        const c=document.createElement('article'); c.className='doc-card';
        c.append(text('small',d.category,'muted'));
        const h=text('h2',''); h.append(link(d.url,d.title)); c.append(h);
        c.append(text('p',d.path,'path'));
        const act=document.createElement('div'); act.className='doc-card-actions';
        act.append(link(d.url,'Lecture integree'));
        act.append(link('https://github.com/Telectroboy/OpenD578/blob/main/'+d.path,'Source GitHub'));
        c.append(act); out.append(c);
      });
    }
    input.addEventListener('input',update);
    update();
  }

  function initPhotos() {
    const out=$('photo-gallery');
    if (!out) return;
    let count=0;
    Object.keys(photoData).forEach(variant=>{
      const photos=photoData[variant].photos||[];
      photos.forEach(p=>{
        count++;
        const card=document.createElement('article'); card.className='doc-card';
        card.append(text('h2',p.title||p.file));
        card.append(text('p',variant+' / '+(p.side||'face non precisee'),'muted small'));
        const frame=document.createElement('div'); frame.className='photo-frame';
        const img=document.createElement('img'); img.loading='lazy'; img.alt=p.title||'Photographie de PCB';
        img.src='photos/'+encodeURIComponent(variant)+'/'+encodeURIComponent(p.file);
        frame.append(img);
        (p.hotspots||[]).forEach(h=>{
          const a=link(compUrl(variant,h.node),'');
          a.className='hotspot'; a.title='Ouvrir fiche '+h.node;
          a.setAttribute('aria-label','Ouvrir fiche '+h.node);
          for (const k of ['x','y','w','h']) {
            a.style[({x:'left',y:'top',w:'width',h:'height'})[k]]=h[k]+'%';
          }
          frame.append(a);
        });
        card.append(frame);
        if (p.note) card.append(text('p',p.note));
        if (p.source && /^https?:\/\//.test(p.source)) card.append(link(p.source,'Source et provenance'));
        out.append(card);
      });
    });
    if (!count) {
      const empty=document.createElement('div'); empty.className='panel';
      empty.append(text('h2','Aucune photo de la revision GD32 encore annotee'));
      empty.append(text('p','Les vues externes de reference sont accessibles ci-dessous. Pour activer des photos cliquables, ajouter les images et les zones verifiees au manifest JSON.'));
      out.append(empty);
    }
  }

  function initExplorer() {
    const svg=$('hardware-svg');
    if (!svg) return;
    const vsel=$('variant-select'), gsel=$('group-filter'), ssel=$('status-filter'), input=$('part-filter'), inspector=$('inspector');
    let currentModel=null, currentSelection=null;
    const allowed = ['facade','logique','peripheriques','radio'];

    function activeId() {return currentModel.id;}
    function selected(type,id) {return currentSelection && currentSelection.type===type && currentSelection.id===id;}
    function open(type,id) {currentSelection={type,id}; draw(); details();}
    function attachKey(el,fn) {
      el.addEventListener('click',fn);
      el.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();fn();}});
    }
    function nodeMatch(n) {
      const term=normalize(input.value).trim();
      if (!term) return true;
      let extra='';
      currentModel.edges.filter(e=>e.source===n.id||e.target===n.id).forEach(e=>{
        extra+=' '+e.label+' '+e.bus+' '+e.pins.map(p=>p.from_pin+' '+p.to_pin).join(' ');
      });
      return normalize(n.label+' '+n.subtitle+' '+n.description+' '+extra).includes(term);
    }
    function geometry(a,b) {
      const ax=a.x+a.w/2, ay=a.y+a.h/2, bx=b.x+b.w/2, by=b.y+b.h/2;
      const dx=Math.abs(bx-ax), dy=Math.abs(by-ay);
      if(dx>50) return `M ${ax} ${ay} C ${ax+(bx-ax)*.43} ${ay}, ${bx-(bx-ax)*.43} ${by}, ${bx} ${by}`;
      return `M ${ax} ${ay} C ${ax} ${ay+Math.sign(by-ay)*Math.max(dy*.5,55)}, ${bx} ${by-Math.sign(by-ay)*Math.max(dy*.5,55)}, ${bx} ${by}`;
    }
    function draw() {
      const m=currentModel;
      const nodeMap=Object.fromEntries(m.nodes.map(n=>[n.id,n]));
      svg.replaceChildren();
      const diagramHeight=Math.max(824,...m.nodes.map(n=>n.y+n.h+70));
      const diagramWidth=m.layout_width||1280;
      svg.setAttribute('viewBox','0 0 '+diagramWidth+' '+diagramHeight);
      const bg=svgEl('g'); svg.append(bg);
      const groups=m.layout_groups||m.groups.map((g,i)=>({...g,x:16+i*320,w:298}));
      for (const g of groups) {
        bg.append(svgEl('rect',{x:g.x,y:20,width:g.w,height:diagramHeight-39,rx:4,class:'svg-group-bg'+(g.id==='central'?' svg-center-bg':'')}));
        const t=svgEl('text',{x:g.x+12,y:46,class:'svg-group-label'});
        t.textContent=g.label;bg.append(t);
      }
      const selectedGroup=gsel.value,selectedStatus=ssel.value;
      const edgesLayer=svgEl('g'); svg.append(edgesLayer);
      m.edges.forEach(e=>{
        const a=nodeMap[e.source],b=nodeMap[e.target];
        const dim=(selectedGroup!=='all' && !(a.group===selectedGroup||b.group===selectedGroup)) ||
                  (selectedStatus!=='all' && e.status!==selectedStatus) ||
                  (!nodeMatch(a) && !nodeMatch(b));
        const d=geometry(a,b);
        const line=svgEl('path',{d,class:'edge-line '+e.status+(dim?' dimmed':'')+(selected('edge',e.id)?' selected':'')});
        edgesLayer.append(line);
        const hit=svgEl('path',{d,class:'edge-hit',tabindex:0,role:'button','aria-label':'Connexion '+e.label});
        const etitle=svgEl('title'); etitle.textContent=e.label+' ('+proof[e.status]+')'; hit.append(etitle);
        attachKey(hit,()=>open('edge',e.id)); edgesLayer.append(hit);
      });
      const nodesLayer=svgEl('g'); svg.append(nodesLayer);
      m.nodes.forEach(n=>{
        const dim=(selectedGroup!=='all'&&n.group!==selectedGroup)||!nodeMatch(n);
        const g=svgEl('g',{class:'node '+n.confidence+((n.id==='mcu'||n.id==='mcu_plus')?' central-mcu':'')+(selected('node',n.id)?' selected':'')+(dim?' dimmed':''),role:'button',tabindex:0,'aria-label':'Composant '+n.label});
        const ntitle=svgEl('title'); ntitle.textContent=n.description; g.append(ntitle);
        g.append(svgEl('rect',{x:n.x,y:n.y,width:n.w,height:n.h,rx:3}));
        const label=svgEl('text',{x:n.x+12,y:n.y+25,class:'node-label'}); label.textContent=n.label; g.append(label);
        const sub=svgEl('text',{x:n.x+12,y:n.y+44,class:'node-sub'});
        const s=n.subtitle||'';
        sub.textContent=s.length>37?s.slice(0,34)+'...':s;
        g.append(sub);
        const stat=svgEl('text',{x:n.x+n.w-10,y:n.y+n.h-9,'text-anchor':'end',class:'node-status'});
        stat.textContent={identified:'fonction ou composant établi',partial:'liaisons à préciser',candidate:'référence candidate'}[n.confidence]; g.append(stat);
        attachKey(g,()=>open('node',n.id)); nodesLayer.append(g);
      });
      const note=svgEl('text',{x:20,y:diagramHeight-15,fill:'#666','font-size':12}); note.textContent='Fonction OEM validée ≠ piste du PCB mesurée. Cliquer sur un trajet pour les broches et traces.'; svg.append(note);
    }
    function references(dest,items) {
      const ul=document.createElement('ul');
      (items||[]).forEach(p=>{
        const li=document.createElement('li');
        li.append(link(docUrl(p),p.split('/').slice(-1)[0]));
        ul.append(li);
      });
      dest.append(ul);
    }
    function detailLinks(dest,type,item) {
      const div=document.createElement('div');div.className='inspector-links';
      div.append(link(type==='node'?compUrl(activeId(),item.id):edgeUrl(activeId(),item.id),'Ouvrir fiche complete'));
      dest.append(div);
    }
    function details() {
      inspector.replaceChildren();
      const m=currentModel;
      if (!currentSelection) {
        inspector.append(text('h2','Selection'));
        inspector.append(text('p','Cliquez sur un composant ou une liaison du diagramme.'));
        inspector.append(text('p','Les fonctions OEM du poste sont opérationnelles; les traits distinguent les traces de programmation et les pistes physiques relevées.','muted small'));
        return;
      }
      const n=m.nodes.find(n=>currentSelection.type==='node'&&n.id===currentSelection.id);
      if(n) {
        inspector.append(text('h2',n.label));
        inspector.append(text('p',n.subtitle,'muted small'));
        inspector.append(text('p',n.description));
        inspector.append(text('p','Identification : '+n.confidence,'muted small'));
        detailLinks(inspector,'node',n);
        inspector.append(text('h3','Connexions'));
        const links=document.createElement('div'); links.className='edge-list';
        m.edges.filter(e=>e.source===n.id||e.target===n.id).forEach(e=>{
          const b=text('button',e.label+' - '+proof[e.status]); b.type='button';
          b.onclick=()=>open('edge',e.id);links.append(b);
        }); inspector.append(links);
        inspector.append(text('h3','Documents source')); references(inspector,n.docs);
        return;
      }
      const e=m.edges.find(e=>e.id===currentSelection.id);
      if(!e)return;
      const a=m.nodes.find(n=>n.id===e.source),b=m.nodes.find(n=>n.id===e.target);
      inspector.append(text('h2',e.label));
      inspector.append(text('p',a.label+' - '+b.label));
      inspector.append(text('p',e.bus+' | '+proof[e.status],'muted small'));
      inspector.append(text('p',e.details));
      detailLinks(inspector,'edge',e);
      inspector.append(text('h3','Broches / signaux'));
      if(e.pins.length) {
        const t=document.createElement('table'); t.className='pins';
        const hd=document.createElement('tr'); ['Source','Destination'].forEach(k=>hd.append(text('th',k)));t.append(hd);
        e.pins.forEach(p=>{const tr=document.createElement('tr');tr.append(text('td',p.from_pin));tr.append(text('td',p.to_pin));t.append(tr);});
        inspector.append(t);
      } else inspector.append(text('p','Protocole ou fonction documenté; aucun numéro de broche supplémentaire n’est publié pour ce segment. Voir la notice et les preuves associées.')); 
      inspector.append(text('h3','Documents justificatifs')); references(inspector,e.docs);
      const back=document.createElement('div');back.className='edge-list';
      [a,b].forEach(node=>{const btn=text('button','Composant : '+node.label);btn.onclick=()=>open('node',node.id);back.append(btn);});
      inspector.append(back);
    }
    function changeVariant() {
      currentModel=models[vsel.value]||Object.values(models)[0];
      const intro=$('model-intro');
      if(intro) intro.textContent='Vue eclatee documentaire : '+currentModel.title+'.';
      currentSelection=null;draw();details();
    }
    vsel.addEventListener('change',changeVariant);
    [gsel,ssel,input].forEach(el=>el.addEventListener(el===input?'input':'change',draw));
    changeVariant();
  }
  function init() {initSearch();initPhotos();initExplorer();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
