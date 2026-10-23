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
  input.title=`${k.Archetype}: ${fmt(k.BGF/1e6)} Mio. m² BGF. Auswahl setzt den Saldo auf den GFZ-Zielwert. Grüne Schraffur zeigt Ziel minus typologischen Saldo; keine Vorgabe zur Aufteilung auf Effizienz und PV.`;
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
 const areas={},selected={};let selectedArea=0;
 for(const k of S.types)if(selectedTypes.has(k.Archetype)){areas[k.Geometrie]=(areas[k.Geometrie]||0)+k.BGF;selectedArea+=k.BGF;selected[k.Geometrie]??={P:0,D:0};selected[k.Geometrie].P+=k.P;selected[k.Geometrie].D+=k.D;}
 const totalArea=S.geometry.reduce((s,k)=>s+k.BGF,0);
 el('type-summary').textContent=`${selectedTypes.size} von ${S.types.length} flächengewichteten Typen · ${fmt(selectedArea/1e6)} Mio. m² BGF · ${fmt(selectedArea/totalArea*100)} % der Szenariofläche. Suchfilter verändert die Auswahl nicht.`;
 const xs=[...new Set(S.use_bins.map(b=>b.GFZ))].sort((a,b)=>a-b), index=new Map(xs.map((x,i)=>[x,i]));
 const uses=[...Object.keys(S.use_colors),'PEQ (ausgewählt)'], series=Object.fromEntries(uses.map(u=>[u,{P:xs.map(()=>0),D:xs.map(()=>0),C:xs.map(()=>0)}]));
 const geometry=Object.fromEntries(S.geometry.map(k=>[k.Geometrie,k]));
 for(const b of S.use_bins){
  const k=geometry[b.Geometrie];if(!k)continue;
  const a=series[b.GWR_Nutzung],j=index.get(b.GFZ);
  const sel=selected[b.Geometrie]||{P:0,D:0},peq=series['PEQ (ausgewählt)'];
  a.P[j]+=(k.P-sel.P)*p.ngf_bgf*p.pv_scale*b.s;
  a.D[j]+=(k.D-sel.D)*p.ngf_bgf*(1-p.saving)*b.s;
  peq.P[j]+=sel.P*p.ngf_bgf*p.pv_scale*b.s;
  peq.D[j]+=sel.D*p.ngf_bgf*(1-p.saving)*b.s;
  const target=(areas[b.Geometrie]||0)*b.s*Math.min(p.density_f_res/(b.GFZ+p.density_dx)-p.density_f_ed,p.density_cutoff)*3.6e-9;
  peq.C[j]+=target-(sel.P*p.pv_scale-sel.D*(1-p.saving))*p.ngf_bgf*b.s;
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
 tile('GFZ mit PEQ-Ziel',evaluated,'PJ-Äquivalent/a',`GFZ-Saldo ${fmt(base)} + Anpassung zur PEQ-Zielerreichung ${fmt(virtual)} = ${fmt(evaluated)}. Ausgewählte Typen erreichen exakt ihren Zielsaldo; Endpunkt der zweiten Linie.`)+
 `<div class="row-title small">PEQ-Anpassung: ${fmt(virtual)} PJ-Äquivalent/a · Prüfdifferenz GFZ − BGF: ${difference.toExponential(1)} PJ/a.</div>`;
 if(!window.Plotly)return;
 const classes=S.geometry.map(k=>k.Geometrie), green='#238b45';
 const groupSeries=(field,chosen)=>S.geometry.map(k=>{const v=(selected[k.Geometrie]||{P:0,D:0})[field];return (chosen?v:k[field]-v)*p.ngf_bgf*(field==='P'?p.pv_scale:1-p.saving)*(field==='P'?1:-1);});
 const changes=S.geometry.map(k=>{let target=0;for(const b of S.bins)if(b.Geometrie===k.Geometrie)target+=(areas[k.Geometrie]||0)*b.s*Math.min(p.density_f_res/(b.GFZ+p.density_dx)-p.density_f_ed,p.density_cutoff)*3.6e-9;const sel=selected[k.Geometrie]||{P:0,D:0};return target-(sel.P*p.pv_scale-sel.D*(1-p.saving))*p.ngf_bgf;});
 const balances=S.geometry.map(k=>(k.P*p.pv_scale-k.D*(1-p.saving))*p.ngf_bgf);
 const classTraces=[];
 for(const chosen of [false,true])for(const field of ['P','D'])classTraces.push({type:'bar',orientation:'h',y:classes,x:groupSeries(field,chosen),name:(chosen?'PEQ: ':'Übrige: ')+(field==='P'?'PV':'Bedarf'),marker:{color:chosen?green:field==='P'?'#dca51d':'#487fa8'},hovertemplate:'%{y}<br>%{fullData.name}: %{x:.3f} PJ/a<extra></extra>'});
 classTraces.push({type:'bar',orientation:'h',y:classes,x:changes,name:'PEQ-Anpassung',marker:{color:green,pattern:{shape:'/'}},hovertemplate:'%{y}<br>Zielsaldo minus typologischer PEQ-Saldo:<br>%{x:.3f} PJ-Äquivalent/a<extra></extra>'});
 for(const adjusted of [false,true])classTraces.push({type:'scatter',mode:'markers',y:classes,x:balances.map((v,i)=>v+(adjusted?changes[i]:0)),name:adjusted?'Saldo mit PEQ-Ziel':'Typologischer Saldo',marker:{color:adjusted?green:'#243746',size:9,symbol:adjusted?'diamond':'circle'},hovertemplate:'%{y}<br>%{fullData.name}: %{x:.3f} PJ/a<extra></extra>'});
 Plotly.react(el('dash-geometry'),classTraces,{barmode:'relative',height:440,autosize:true,margin:{l:80,r:15,t:15,b:100},xaxis:{title:{text:'Bedarf ← 0 → PV / Anpassung [PJ/a]'},zeroline:true},yaxis:{autorange:'reversed'},legend:{orientation:'h',y:-.2,font:{size:10}},font:{size:11},separators:',.'},{responsive:true,displaylogo:false});

 const pos=P.map((v,i)=>v+sum(uses.map(u=>Math.max(series[u].C[i],0)))),neg=D.map((v,i)=>-v+sum(uses.map(u=>Math.min(series[u].C[i],0))));
 const yrange=[Math.min(0,...neg)*1.08,Math.max(0,...pos)*1.08];
 const ymin=Math.min(0,...physical,...corrected),ymax=Math.max(0,...physical,...corrected),pad=Math.max((ymax-ymin)*.08,1);
 for(const [id,includeCorrection,line] of [['gfz-physical',false,physical],['gfz-corrected',true,corrected]]){
  const traces=[];
  const shortNames={'Groß- und Einzelhandelsgebäude':'Handel','Büronutzung':'Büro','Hotels o.Ä.':'Hotels','Industrie und Lagerung':'Industrie / Lager','Ein- und Zweifamilienhäuser':'EFH / ZFH','Mehrfamilienhaus':'Mehrfamilienhaus','Gemeinschaftsgebäude':'Gemeinschaft','Kultur, Freizeit, Bildung und Gesundheit':'Bildung / Kultur','Verkehrs- und Nachrichtenwesen':'Verkehr','PEQ (ausgewählt)':'PEQ (ausgewählt)'};
  for(const u of uses){
   for(const [field,label,sign] of [['P','PV-Erzeugung',1],['D','Strombedarf',-1],...(includeCorrection&&u==='PEQ (ausgewählt)'?[['C','PEQ-Anpassung',1]]:[])]){
    traces.push({type:'bar',x:xs,y:series[u][field].map(v=>sign*v),width:.095,
     name:shortNames[u],legendgroup:u,showlegend:field==='P',marker:{color:(u==='PEQ (ausgewählt)'?'#238b45':S.use_colors[u]),...(field==='C'?{pattern:{shape:'/',solidity:.35}}:{})},
     customdata:series[u][field],hovertemplate:`${esc(u)}<br>${label}<br>GFZ-Klasse: %{x:.2f} ± 0,05<br>%{customdata:.4f} ${field==='C'?'PJ-Äquivalent/a':'PJ Strom/a'}<extra></extra>`});
   }
  }
  if(includeCorrection)traces.push({type:'bar',x:[null],y:[null],name:'PEQ-Anpassung',marker:{color:'#238b45',pattern:{shape:'/'}}});
  traces.push({type:'scatter',mode:'lines',x:xs,y:line,yaxis:'y2',name:'Saldo (kumuliert)',line:{color:'#243746',width:2.5},hovertemplate:`Bis GFZ %{x:.2f}<br>Kumulierter Saldo: %{y:.3f} ${includeCorrection?'PJ-Äquivalent/a':'PJ Strom/a'}<extra></extra>`});
  Plotly.react(el(id),traces,{barmode:'relative',template:'plotly_white',autosize:true,height:370,
   margin:{l:48,r:48,t:45,b:48,autoexpand:false},font:{size:11},separators:',.',
   xaxis:{title:{text:'GFZ (BGF / Grundstücksfläche)'},range:[0,5]},
   updatemenus:[{type:'buttons',direction:'right',x:0,xanchor:'left',y:1.13,buttons:[
    {label:'GFZ 0–5',method:'relayout',args:[{'xaxis.range':[0,5]}]},
    {label:'Gesamte GFZ',method:'relayout',args:[{'xaxis.range':[0,Math.max(...xs)+.05]}]}]}],
   yaxis:{title:{text:includeCorrection?'Klassenbeitrag [PJ-Äquivalent/a]':'Klassenbeitrag [PJ Strom/a]'},range:yrange,zeroline:true},
   yaxis2:{title:{text:'Kumulierter Saldo [PJ'+(includeCorrection?'-Äquivalent':' Strom')+'/a]'},overlaying:'y',side:'right',range:[ymin-pad,ymax+pad],showgrid:false},
   legend:{tracegroupgap:0,x:.99,y:.99,xanchor:'right',yanchor:'top',bgcolor:'rgba(255,255,255,.85)',font:{size:9},itemclick:false,itemdoubleclick:false},hovermode:'closest'},
   {responsive:true,displaylogo:false,toImageButtonOptions:{format:'svg'}});
 }
}
// Gemeinsame lokale Plotly-Bibliothek, kein externer CDN-Aufruf.
if(!window.Plotly){const script=document.createElement('script');script.src='../../Abbildungen/methodik/plotly.min.js';script.onload=()=>render();script.onerror=()=>{el('gfz-physical').textContent='Plotly konnte nicht geladen werden. Die Bilanzwerte darüber bleiben verfügbar.';};document.head.append(script);}
