// Interaktive Entsprechung der GFZ-Referenzrechnung im Notebook.
let selectedTypes=new Set(S.types.filter(k=>k.default_selected).map(k=>k.Archetype));
let densityReferenceChecked=false;
let groupReferenceChecked=false;
el('selection-note').textContent=S.selection_note;
const typeAttributes=k=>{const [geometry,age,heat,pv,flex]=k.Archetype.split('|');return {geometry,age,heat,pv,flex,heat_family:heat.startsWith('WP_')?'Wärmepumpe':heat};};
const attributes=new Map(S.types.map(k=>[k.Archetype,typeAttributes(k)]));
const filters=[['geometry','Geometrie'],['age','Baualter / Hülle'],['pv','PV-Ausstattung'],['flex','Flexibilität'],['heat_family','Heizungsfamilie / WP'],['heat','Heizung im Detail']];
for(const [key,label] of filters){
 const l=document.createElement('label');l.htmlFor='filter-'+key;l.textContent=label;
 const select=document.createElement('select');select.id='filter-'+key;select.multiple=true;select.size=3;select.style.cssText='width:100%;font-size:12px';
 select.title='Mehrfachauswahl mit Strg/Cmd. Keine markierte Option = alle Werte. Innerhalb eines Merkmals gilt ODER, zwischen Merkmalen UND. Filter ändern die Auswahl erst über die Schaltflächen.';
 for(const v of [...new Set([...attributes.values()].map(a=>a[key]))].sort()){const o=document.createElement('option');o.value=v;o.textContent=v;select.append(o);}
 select.onchange=showTypeOptions;el('type-filters').append(l,select);
}
function matchedTypes(){
 const query=el('type-search').value.toLowerCase();
 const rules=filters.map(([key])=>[key,new Set([...el('filter-'+key).selectedOptions].map(o=>o.value))]);
 return S.types.filter(k=>k.Archetype.toLowerCase().includes(query)&&rules.every(([key,values])=>!values.size||values.has(attributes.get(k.Archetype)[key])));
}
function showTypeOptions(){
 const root=el('type-options'),open=new Set([...root.querySelectorAll('details[open]')].map(d=>d.dataset.group));root.replaceChildren();
 const matches=matchedTypes();
 el('type-filter-count').textContent=`${matches.length} Treffer; ${matches.filter(k=>selectedTypes.has(k.Archetype)).length} davon ausgewählt. Filter allein ändern keine PEQ-Zuordnung.`;
 const makeGroup=(name,items,key,byAge)=>{
  const detail=document.createElement('details');detail.dataset.group=key;const summary=document.createElement('summary');
  summary.textContent=`${name} (${items.filter(k=>selectedTypes.has(k.Archetype)).length}/${items.length})`;detail.append(summary);
  const content=document.createElement('div');detail.append(content);
  const populate=()=>{
   if(content.childElementCount)return;
   for(const [text,choose] of [['Gruppe auswählen',true],['Gruppe abwählen',false]]){const button=document.createElement('button');button.type='button';button.textContent=text;button.title='Wirkt auf die '+items.length+' angezeigten Treffer dieser Gruppe; andere Typen bleiben unverändert.';button.onclick=()=>{for(const k of items)choose?selectedTypes.add(k.Archetype):selectedTypes.delete(k.Archetype);showTypeOptions();render();};content.append(button);}
   if(byAge){for(const age of [...new Set(items.map(k=>attributes.get(k.Archetype).age))].sort())content.append(makeGroup(age,items.filter(k=>attributes.get(k.Archetype).age===age),key+'/'+age,false));}
   else for(const k of items){const label=document.createElement('label');label.style.cssText='display:flex;font-size:11px;overflow-wrap:anywhere';const input=document.createElement('input');input.type='checkbox';input.checked=selectedTypes.has(k.Archetype);input.style.cssText='width:auto;flex:none;margin-right:6px';input.setAttribute('aria-label',k.Archetype);input.title=`${fmt(k.BGF/1e6)} Mio. m² BGF; Auswahl setzt den Saldo auf den GFZ-Zielwert.`;input.onchange=()=>{input.checked?selectedTypes.add(k.Archetype):selectedTypes.delete(k.Archetype);showTypeOptions();render();};label.append(input,document.createTextNode(k.Archetype));content.append(label);}
  };
  detail.ontoggle=()=>{if(detail.open)populate();};if(open.has(key)){detail.open=true;populate();}return detail;
 };
 for(const geo of [...new Set(matches.map(k=>k.Geometrie))].sort())root.append(makeGroup(geo,matches.filter(k=>k.Geometrie===geo),geo,true));
}
el('type-search').oninput=showTypeOptions;
for(const [id,choose] of [['types-matched-add',true],['types-matched-remove',false]])el(id).onclick=()=>{for(const k of matchedTypes())choose?selectedTypes.add(k.Archetype):selectedTypes.delete(k.Archetype);showTypeOptions();render();};
el('types-clear-filters').onclick=()=>{el('type-search').value='';for(const [key] of filters)for(const o of el('filter-'+key).options)o.selected=false;showTypeOptions();};
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
 el('gfz-totals').innerHTML=tile('Top-Down',r.target,'PJ Strom/a',`Nationale Gebäude-PV ${fmt(S.g.pv*(1-p.free_pv))} − Gebäudestrombedarf ${fmt(S.d.gebaeude)}. Ohne MIV und ohne Mobilitätsgutschrift.`)+
 tile('Typologisch',base,'PJ Strom/a','PV − Strombedarf aller Typen. Die GFZ-Aggregation reproduziert die direkte BGF-Bilanz. Ohne Mobilität.')+
 tile('Mit Dichteausgleich',evaluated,'PJ-Äquivalent/a',`Typologischer Saldo ${fmt(base)} + PEQ-Anpassung ${fmt(virtual)} = ${fmt(evaluated)}. Ausgewählte Typen erreichen ihren GFZ-Zielsaldo.`)+
 `<div class="row-title small">Abstand zum Top-Down-Ziel: typologisch ${fmt(base-r.target)}, mit Dichteausgleich ${fmt(evaluated-r.target)} PJ/a. PEQ-Anpassung: ${fmt(virtual)} PJ/a. Kontrolle GFZ − direkte BGF-Bilanz: ${difference.toExponential(1)} PJ/a.</div>`;
 last.gfz_comparison.top_down_building_balance=r.target;
 last.gfz_comparison.gap_to_top_down=evaluated-r.target;
 if(!window.Plotly)return;
 renderNationalComparison(r);
 renderTargetDistribution();
 const green='#238b45';
 const classRows=S.geometry.map(k=>{
  const chosen=selected[k.Geometrie]||{P:0,D:0},area=areas[k.Geometrie]||0,rest=k.BGF-area;
  const selectedBalance=(chosen.P*p.pv_scale-chosen.D*(1-p.saving))*p.ngf_bgf;
  const allBalance=(k.P*p.pv_scale-k.D*(1-p.saving))*p.ngf_bgf;
  const targetMean=S.bins.filter(b=>b.Geometrie===k.Geometrie).reduce((s,b)=>s+b.s*Math.min(p.density_f_res/(b.GFZ+p.density_dx)-p.density_f_ed,p.density_cutoff),0);
  return {geometry:k.Geometrie,non_peq_bgf_m2:rest,peq_bgf_m2:area,
   non_peq:rest>1e-6?(allBalance-selectedBalance)/(rest*3.6e-9):null,
   peq_typological:area>1e-6?selectedBalance/(area*3.6e-9):null,
   peq_target:area>1e-6?targetMean:null};
 });
 last.specific_group_balances={unit:'kWh/(m² BGF·a)',denominator:'BGF der jeweiligen Gruppe innerhalb der Geometrieklasse',rows:classRows};
 if(!groupReferenceChecked){
  for(const row of classRows){const ref=S.group_balance_reference.find(k=>k.geometry===row.geometry);
   for(const key of ['non_peq','peq_typological','peq_target'])if(row[key]===null?ref[key]!==null:ref[key]===null||Math.abs(row[key]-ref[key])>1e-7)throw Error('Gruppensaldo weicht von Notebook ab: '+row.geometry+' / '+key);
  }groupReferenceChecked=true;
 }
 const reconstruct=classRows.reduce((s,k)=>s+((k.non_peq||0)*k.non_peq_bgf_m2+(k.peq_typological||0)*k.peq_bgf_m2)*3.6e-9,0);
 const reconstructTarget=classRows.reduce((s,k)=>s+((k.non_peq||0)*k.non_peq_bgf_m2+(k.peq_target||0)*k.peq_bgf_m2)*3.6e-9,0);
 if(Math.abs(reconstruct-base)>1e-7||Math.abs(reconstructTarget-evaluated)>1e-7)throw Error('Spezifische Gruppenbilanz rekonstruiert Sektorsaldo nicht');
 const classTraces=[];
 for(const [key,name,color,pattern,areaKey] of [
  ['non_peq','1 · Nicht-PEQ: typologisch','#487fa8','', 'non_peq_bgf_m2'],
  ['peq_typological','2 · PEQ: typologisch',green,'','peq_bgf_m2'],
  ['peq_target','3 · PEQ: Dichteziel',green,'/','peq_bgf_m2']]){
  classTraces.push({type:'bar',orientation:'h',y:classRows.map(k=>k.geometry),x:classRows.map(k=>k[key]),name,
   marker:{color,pattern:{shape:pattern}},customdata:classRows.map(k=>k[areaKey]/1e6),
   hovertemplate:'%{y}<br>%{fullData.name}<br>Saldo: %{x:.2f} kWh/(m² BGF·a)<br>Bezugsfläche dieser Gruppe: %{customdata:.3f} Mio. m² BGF<extra></extra>'});
 }
 Plotly.react(el('dash-geometry'),classTraces,{barmode:'group',height:720,autosize:true,margin:{l:80,r:15,t:15,b:100},
  xaxis:{title:{text:'Saldo [kWh/(m² BGF·a)]'},zeroline:true},yaxis:{autorange:'reversed'},
  legend:{orientation:'h',y:-.12,font:{size:10},traceorder:'normal'},font:{size:11},separators:',.'},
  {responsive:true,displaylogo:false});
 el('class-empty-note').textContent=classRows.filter(k=>k.non_peq===null||k.peq_target===null).map(k=>`${k.geometry}: ${k.non_peq===null?'keine Nicht-PEQ-Fläche':'keine ausgewählte PEQ-Fläche'}`).join(' · ')||'Alle dargestellten Gruppen besitzen positive Bezugsflächen.';
 last.schema_version='peq-dashboard-2';
 last.density_curve={definition:'target(gfz) = min(f_RES / (gfz + dx) - f_ED, cutoff)',
  unit:'kWh EE/(m² BGF·a)',gfz_definition:'BGF / Grundstücksfläche',parameters:{f_RES:p.density_f_res,f_ED:p.density_f_ed,dx:p.density_dx,cutoff:p.density_cutoff},
  application:'Ausgewählte Typen erhalten flächengewichtet den Zielsaldo. Anpassung = Zielsaldo minus typologischer Saldo. Nicht ausgewählte Typen bleiben unverändert.',
  distribution:S.use_bins,distribution_weight:'s = BGF-Anteil von Nutzung und GFZ innerhalb der Geometrieklasse; Summe je Geometrie = 1',display_gfz_range:[0,5],calculation:'vollständige GFZ-Verteilung'};
 last.type_definitions=S.types.map(k=>({id:k.Archetype,attributes:attributes.get(k.Archetype),bgf_m2:k.BGF,
  electricity_demand_kwh_m2_ngf_a:k.D/(k.BGF*3.6e-9),pv_generation_kwh_m2_ngf_a:k.P/(k.BGF*3.6e-9),
  peq_selected:selectedTypes.has(k.Archetype),source_file:S.xlsx,source_area_column:S.area_column}));
 last.type_selection={selected_ids:[...selectedTypes],default_note:S.selection_note,search:el('type-search').value,
  filters:Object.fromEntries(filters.map(([key])=>[key,[...el('filter-'+key).selectedOptions].map(o=>o.value)])),
  semantics:'ODER innerhalb eines Attributs, UND zwischen Attributen; Filter sind Ansicht, selected_ids ist die maßgebliche Auswahl.'};
 last.national_inputs={generation:S.g,demand:S.d,scenario:S.scenario};
 const pos=P.map((v,i)=>Math.max(v,C[i])),neg=D.map((v,i)=>Math.min(-v,C[i]));
 const yrange=[Math.min(0,...neg)*1.08,Math.max(0,...pos)*1.08];
 const ymin=Math.min(0,...physical,...corrected),ymax=Math.max(0,...physical,...corrected),pad=Math.max((ymax-ymin)*.08,1);
 for(const [id,includeCorrection,line] of [['gfz-physical',false,physical],['gfz-corrected',true,corrected]]){
  const traces=[];
  const shortNames={'Groß- und Einzelhandelsgebäude':'Handel','Büronutzung':'Büro','Hotels o.Ä.':'Hotels','Industrie und Lagerung':'Industrie / Lager','Ein- und Zweifamilienhäuser':'EFH / ZFH','Mehrfamilienhaus':'Mehrfamilienhaus','Gemeinschaftsgebäude':'Gemeinschaft','Kultur, Freizeit, Bildung und Gesundheit':'Bildung / Kultur','Verkehrs- und Nachrichtenwesen':'Verkehr','PEQ (ausgewählt)':'PEQ (ausgewählt)'};
  for(const u of uses){
   for(const [field,label,sign] of [['P','PV-Erzeugung',1],['D','Strombedarf',-1],...[]]){
    traces.push({type:'bar',x:xs,y:series[u][field].map(v=>sign*v),width:.095,
     name:shortNames[u],legendgroup:u,showlegend:field==='P',marker:{color:(u==='PEQ (ausgewählt)'?'#238b45':S.use_colors[u]),...(field==='C'?{pattern:{shape:'/',solidity:.35}}:{})},
     customdata:series[u][field],hovertemplate:`${esc(u)}<br>${label}<br>GFZ-Klasse: %{x:.2f} ± 0,05<br>%{customdata:.4f} ${field==='C'?'PJ-Äquivalent/a':'PJ Strom/a'}<extra></extra>`});
   }
  }
  if(includeCorrection)traces.push({type:'bar',x:xs,y:C,base:0,width:.095,opacity:.75,name:'PEQ-Anpassung',marker:{color:'#238b45',pattern:{shape:'/',solidity:.35}},hovertemplate:'GFZ %{x:.2f}<br>Anpassung: %{y:.4f} PJ/a<br>Positiv: mehr Saldo gefordert<br>Negativ: geringere Anforderung<extra></extra>'});
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
function renderNationalComparison(r){
 const g=S.g,d=S.d,col=S.energy_colors,traces=[],shapes=[],annotations=[];
 const miv=d.verkehr*p.miv,pv=g.pv*(1-p.free_pv);
 const bar=(name,key,x,value)=>{if(value!==0)traces.push({type:'bar',x:[x],y:[value],width:.65,name,marker:{color:col[key]||'#72858a'},hovertemplate:'%{fullData.name}: %{y:.2f} PJ Strom/a<extra></extra>'});};
 bar('Gebäudebedarf','gebaeude',0,d.gebaeude);
 bar('MIV-Bedarf','miv',0,miv);
 bar('ÖPNV','oepnv',0,d.verkehr*(1-p.miv-p.other_transport));
 bar('Übriger Verkehr','verkehr',0,d.verkehr*p.other_transport);
 for(const [key,name] of [['industrie','Industrie'],['landwirtschaft','Landwirtschaft'],['verbrauch_sektor_energie','Energiebranche'],['umwandlungseinsatz','Umwandlung'],['transportverluste','Netzverluste']])bar(name,key,0,d[key]);
 bar('Nettoexport','net_imports',0,Math.max(-g.net_imports,0));
 bar('Gebäude-PV','pv',1,pv);
 for(const [key,name] of [['hydro','Wasserkraft'],['wind','Wind'],['biomass','Biomasse'],['geothermal','Geothermie'],['hydrogen_electricity','H₂-Strom'],['fossil','Fossil']])bar(name,key,1,g[key]);
 bar('Freiflächen-PV','free_pv',1,g.pv*p.free_pv);
 bar('Nettoimport','net_imports',1,Math.max(g.net_imports,0));
 for(const [name,key,x,v] of [['Gebäudebedarf','gebaeude',3,r.demand],['MIV-Bedarf','miv',3,miv],['Gebäude-PV','pv',4,r.pv],['Mobilitätsgutschrift','mobility_credit',4,r.budget]]){
  if(v!==0){bar(name,key,x,v);traces.at(-1).showlegend=name==='Mobilitätsgutschrift';}
 }
 const total=x=>traces.filter(t=>t.x[0]===x).reduce((s,t)=>s+t.y[0],0);
 const nationalDemand=total(0),nationalSupply=total(1);
 if(Math.abs(nationalSupply-nationalDemand-S.residual)>1e-7)throw Error('Nationale Säulenbilanz verletzt Quellrest');
 if(Math.abs(total(4)-total(3)-r.extended)>1e-7)throw Error('Bottom-Up-Säulenbilanz verletzt');
 const line=(x0,x1,y,color,dash='dot')=>shapes.push({type:'line',x0,x1,y0:y,y1:y,line:{color,width:1,dash}});
 line(-.35,3.4,d.gebaeude,col.gebaeude);line(.65,4.4,pv,col.pv);
 line(-.35,3.4,d.gebaeude+miv,col.miv);line(.65,4.4,pv+r.budget,col.mobility_credit);
 const bracket=(x,a,b,text,color)=>{shapes.push({type:'line',x0:x,x1:x,y0:a,y1:b,line:{color,width:2}});line(x-.08,x+.08,a,color,'solid');line(x-.08,x+.08,b,color,'solid');annotations.push({x,y:(a+b)/2,text,showarrow:true,ax:22,ay:0,font:{size:9,color},bgcolor:'rgba(255,255,255,.9)'});};
 bracket(.45,d.gebaeude+miv,pv+r.budget,`TD: ${fmt(r.target_extended)}`,col.target);
 bracket(3.5,r.demand+miv,r.pv+r.budget,`BU: ${fmt(r.extended)}`,col.saldo);
 for(const [x,v] of [[0,nationalDemand],[1,nationalSupply],[3,total(3)],[4,total(4)]])annotations.push({x,y:v,text:fmt(v),showarrow:false,yshift:12,font:{size:11}});
 Plotly.react(el('dash-balance'),traces,{barmode:'stack',height:650,autosize:true,margin:{l:50,r:20,t:35,b:220},font:{size:11},separators:',.',
  xaxis:{tickvals:[0,1,3,4],ticktext:['Top-Down<br>Bedarf','Top-Down<br>Deckung','Bottom-Up<br>Bedarf','Bottom-Up<br>Deckung'],range:[-.6,4.6]},
  yaxis:{title:{text:'Jährliche Strommenge [PJ/a]'},rangemode:'tozero'},legend:{orientation:'h',y:-.22,font:{size:10}},shapes,annotations},
  {responsive:true,displaylogo:false,toImageButtonOptions:{format:'svg'}});
 el('national-comparison-note').textContent=`National: Deckung ${fmt(nationalSupply)} − Bedarf einschließlich Export ${fmt(nationalDemand)} = ${fmt(nationalSupply-nationalDemand)} PJ/a (Quellrest). Vergleich Gebäude + MIV: Top-Down ${fmt(r.target_extended)}, Bottom-Up ${fmt(r.extended)} PJ/a. Unterschied BU − TD: Bedarf ${fmt(r.demand-d.gebaeude)}, Deckung ${fmt(r.pv-pv)}, Saldo ${fmt(r.gap)} PJ/a. Klammern beziehen sich auf Gebäude + MIV, nicht auf die nationale Gesamtsumme.`;
}
function renderTargetDistribution(){
 const rows=S.geometry.map(k=>{
  const bins=S.bins.filter(b=>b.Geometrie===k.Geometrie).map(b=>({v:Math.min(p.density_f_res/(b.GFZ+p.density_dx)-p.density_f_ed,p.density_cutoff),w:b.s})).sort((a,b)=>a.v-b.v);
  const weight=bins.reduce((s,b)=>s+b.w,0);
  const quantile=q=>{let cum=0;for(const b of bins){cum+=b.w/weight;if(cum+1e-14>=q)return b.v;}return bins.at(-1).v;};
  return {name:k.Geometrie,lo:quantile(.1),q1:quantile(.25),median:quantile(.5),q3:quantile(.75),hi:quantile(.9),mean:bins.reduce((s,b)=>s+b.v*b.w,0)/weight};
 });
 last.target_distribution=rows;
 const traces=[];
 for(const r of rows){
  const hover=`${r.name}<br>BGF-gewichtet: P10 ${fmt(r.lo)}, P25 ${fmt(r.q1)}<br>Median ${fmt(r.median)}, P75 ${fmt(r.q3)}, P90 ${fmt(r.hi)}<br>Mittelwert ${fmt(r.mean)} kWh/(m² BGF·a)<extra></extra>`;
  traces.push({type:'scatter',mode:'lines',x:[r.lo,r.hi],y:[r.name,r.name],line:{color:'#8dc89e',width:5},showlegend:false,hovertemplate:hover});
  traces.push({type:'scatter',mode:'lines',x:[r.q1,r.q3],y:[r.name,r.name],line:{color:'#238b45',width:12},showlegend:false,hovertemplate:hover});
 }
 for(const [key,name,symbol,color] of [['median','Median','diamond','#145a2b'],['mean','Mittelwert','circle','#243746']])traces.push({type:'scatter',mode:'markers',x:rows.map(r=>r[key]),y:rows.map(r=>r.name),name,marker:{symbol,color,size:9},hovertemplate:'%{y}<br>'+name+': %{x:.2f} kWh/(m² BGF·a)<extra></extra>'});
 Plotly.react(el('dash-density'),traces,{height:420,autosize:true,margin:{l:80,r:20,t:15,b:85},xaxis:{title:{text:'PEQ-Zielsaldo [kWh/(m² BGF·a)]'},zeroline:true},yaxis:{autorange:'reversed'},legend:{orientation:'h',y:-.2},font:{size:11},separators:',.'},{responsive:true,displaylogo:false});
}
// Gemeinsame lokale Plotly-Bibliothek, kein externer CDN-Aufruf.
if(!window.Plotly){const script=document.createElement('script');script.src='../../Abbildungen/methodik/plotly.min.js';script.onload=()=>render();script.onerror=()=>{el('gfz-physical').textContent='Plotly konnte nicht geladen werden. Die Bilanzwerte darüber bleiben verfügbar.';};document.head.append(script);}
