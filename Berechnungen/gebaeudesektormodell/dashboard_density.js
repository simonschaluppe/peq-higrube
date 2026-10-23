// Interaktive Entsprechung der GFZ-Referenzrechnung im Notebook.
let selectedTypes=new Set(S.types.filter(k=>k.default_selected).map(k=>k.Archetype));
let densityReferenceChecked=false;
el('selection-note').textContent=S.selection_note;
function showTypeOptions(){
 const query=el('type-search').value.toLowerCase();
 el('type-options').replaceChildren();
 for(const k of S.types.filter(k=>k.Archetype.toLowerCase().includes(query))){
  const label=document.createElement('label');
  label.style.cssText='display:flex;flex-wrap:nowrap;font-size:11px;overflow-wrap:anywhere;align-items:start';
  const input=document.createElement('input');input.type='checkbox';input.checked=selectedTypes.has(k.Archetype);
  input.style.cssText='width:auto;flex:none;margin:3px 6px 0 0';
  input.title=`${k.Archetype}: ${fmt(k.BGF/1e6)} Mio. m² BGF. Auswahl aktiviert nur die virtuelle Dichtebewertung; Bedarf und PV bleiben enthalten.`;
  input.setAttribute('aria-label',k.Archetype);
  input.onchange=()=>{input.checked?selectedTypes.add(k.Archetype):selectedTypes.delete(k.Archetype);render();};
  label.append(input,document.createTextNode(k.Archetype));el('type-options').append(label);
 }
}
el('type-search').oninput=showTypeOptions;
for(const [id,filter] of [['types-default',k=>k.default_selected],['types-all',()=>true],['types-none',()=>false]]){
 el(id).onclick=()=>{selectedTypes=new Set(S.types.filter(filter).map(k=>k.Archetype));showTypeOptions();render();};
}
showTypeOptions();
function renderDensity(r,virtual){
 const areas={};let selectedArea=0;
 for(const k of S.types)if(selectedTypes.has(k.Archetype)){areas[k.Geometrie]=(areas[k.Geometrie]||0)+k.BGF;selectedArea+=k.BGF;}
 const totalArea=S.geometry.reduce((s,k)=>s+k.BGF,0);
 el('type-summary').textContent=`${selectedTypes.size} von ${S.types.length} flächengewichteten Typen · ${fmt(selectedArea/1e6)} Mio. m² BGF · ${fmt(selectedArea/totalArea*100)} % der Szenariofläche. Suchfilter verändert die Auswahl nicht.`;
 const xs=[...new Set(S.use_bins.map(b=>b.GFZ))].sort((a,b)=>a-b), index=new Map(xs.map((x,i)=>[x,i]));
 const uses=Object.keys(S.use_colors), series=Object.fromEntries(uses.map(u=>[u,{P:xs.map(()=>0),D:xs.map(()=>0),C:xs.map(()=>0)}]));
 const geometry=Object.fromEntries(S.geometry.map(k=>[k.Geometrie,k]));
 for(const b of S.use_bins){
  const k=geometry[b.Geometrie];if(!k)continue;
  const a=series[b.GWR_Nutzung],j=index.get(b.GFZ);
  a.P[j]+=k.P*p.ngf_bgf*p.pv_scale*b.s;
  a.D[j]+=k.D*p.ngf_bgf*(1-p.saving)*b.s;
  a.C[j]+=(areas[b.Geometrie]||0)*b.s*(-Math.min(p.density_f_res/(b.GFZ+p.density_dx)-p.density_f_ed,p.density_cutoff))*3.6e-9;
 }
 const sum=arr=>arr.reduce((a,b)=>a+b,0);
 const P=xs.map((_,i)=>sum(uses.map(u=>series[u].P[i]))),D=xs.map((_,i)=>sum(uses.map(u=>series[u].D[i]))),C=xs.map((_,i)=>sum(uses.map(u=>series[u].C[i])));
 const accumulate=arr=>{let total=0;return arr.map(v=>total+=v);};
 const physical=accumulate(P.map((v,i)=>v-D[i])),corrected=accumulate(P.map((v,i)=>v-D[i]+C[i]));
 const base=physical.at(-1),evaluated=corrected.at(-1),difference=base-r.balance;
 if(!densityReferenceChecked){
  for(const [key,value] of Object.entries({demand:sum(D),pv:sum(P),virtual:sum(C),balance:base,corrected:evaluated}))
   if(Math.abs(value-S.gfz_reference[key])>1e-7)throw Error('GFZ-Referenzabweichung Python/Browser: '+key);
  densityReferenceChecked=true;
 }
 for(const [a,b] of [[sum(P),r.pv],[sum(D),r.demand],[sum(C),virtual],[base,r.balance]])if(Math.abs(a-b)>1e-7)throw Error('GFZ-Aggregation verletzt Flächen-/Energieerhaltung');
 last.gfz_comparison={direct_bgf_balance:r.balance,gfz_balance:base,virtual_selected:virtual,corrected_balance:evaluated,aggregation_difference:difference,selected_bgf_m2:selectedArea};
 const tile=(title,value,unit,tip)=>`<div class="card" tabindex="0" title="${esc(tip)}">${esc(title)} ⓘ<strong>${fmt(value)}</strong><small>${unit}</small></div>`;
 el('gfz-totals').innerHTML=tile('Direkte BGF-Bilanz',r.balance,'PJ Strom/a','PV − Strombedarf aller Typen, direkt über ihre BGF gewichtet. Ohne Mobilität.')+
 tile('GFZ ohne Korrektur',base,'PJ Strom/a','Summe über sämtliche GFZ- und Nutzungsklassen. Muss die direkte BGF-Bilanz reproduzieren; Endpunkt der ersten Linie.')+
 tile('GFZ mit Korrektur',evaluated,'PJ-Äquivalent/a',`GFZ-Saldo ${fmt(base)} + virtuelle Korrektur ${fmt(virtual)} = ${fmt(evaluated)}. Nur ausgewählte Typen werden korrigiert; Endpunkt der zweiten Linie.`)+
 `<div class="row-title small">Virtuelle Korrektur: ${fmt(virtual)} PJ-Äquivalent/a · Prüfdifferenz GFZ − BGF: ${difference.toExponential(1)} PJ/a.</div>`;
 if(!window.Plotly)return;
 const pos=P.map((v,i)=>v+sum(uses.map(u=>Math.max(series[u].C[i],0)))),neg=D.map((v,i)=>-v+sum(uses.map(u=>Math.min(series[u].C[i],0))));
 const yrange=[Math.min(0,...neg)*1.08,Math.max(0,...pos)*1.08];
 const ymin=Math.min(0,...physical,...corrected),ymax=Math.max(0,...physical,...corrected),pad=Math.max((ymax-ymin)*.08,1);
 for(const [id,includeCorrection,line] of [['gfz-physical',false,physical],['gfz-corrected',true,corrected]]){
  const traces=[];
  for(const u of uses){
   for(const [field,label,sign] of [['P','PV-Erzeugung',1],['D','Strombedarf',-1],...(includeCorrection?[['C','Virtuelle Korrektur',1]]:[])]){
    traces.push({type:'bar',x:xs,y:series[u][field].map(v=>sign*v),width:.095,
     name:u,legendgroup:u,showlegend:field==='P',marker:{color:S.use_colors[u],...(field==='C'?{pattern:{shape:'/',solidity:.35}}:{})},
     customdata:series[u][field],hovertemplate:`${esc(u)}<br>${label}<br>GFZ-Klasse: %{x:.2f} ± 0,05<br>%{customdata:.4f} ${field==='C'?'PJ-Äquivalent/a':'PJ Strom/a'}<extra></extra>`});
   }
  }
  if(includeCorrection)traces.push({type:'bar',x:[null],y:[null],name:'Schraffur: virtuelle Korrektur',marker:{color:'#a259a4',pattern:{shape:'/'}}});
  traces.push({type:'scatter',mode:'lines',x:xs,y:line,yaxis:'y2',name:'Kumulierter Saldo (rechts)',line:{color:'#243746',width:2.5},hovertemplate:`Bis GFZ %{x:.2f}<br>Kumulierter Saldo: %{y:.3f} ${includeCorrection?'PJ-Äquivalent/a':'PJ Strom/a'}<extra></extra>`});
  Plotly.react(el(id),traces,{barmode:'relative',template:'plotly_white',autosize:true,height:620,
   margin:{l:65,r:72,t:20,b:245},font:{size:11},separators:',.',
   xaxis:{title:'GFZ (BGF / Grundstücksfläche)',range:[0,Math.max(...xs)+.05]},
   yaxis:{title:{text:includeCorrection?'Klassenbeitrag [PJ-Äquivalent/a]':'Klassenbeitrag [PJ Strom/a]'},range:yrange,zeroline:true},
   yaxis2:{title:{text:'Kumulierter Saldo [PJ'+(includeCorrection?'-Äquivalent':' Strom')+'/a]'},overlaying:'y',side:'right',range:[ymin-pad,ymax+pad],showgrid:false},
   legend:{orientation:'h',x:0,y:-.25,font:{size:10},itemclick:false,itemdoubleclick:false},hovermode:'closest'},
   {responsive:true,displaylogo:false,toImageButtonOptions:{format:'svg'}});
 }
}
// Gemeinsame lokale Plotly-Bibliothek, kein externer CDN-Aufruf.
if(!window.Plotly){const script=document.createElement('script');script.src='../../Abbildungen/methodik/plotly.min.js';script.onload=()=>render();script.onerror=()=>{el('gfz-physical').textContent='Plotly konnte nicht geladen werden. Die Bilanzwerte darüber bleiben verfügbar.';};document.head.append(script);}
