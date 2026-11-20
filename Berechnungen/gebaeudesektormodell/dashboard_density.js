const root=document.getElementById('sector-dashboard');
const el=id=>root.querySelector('#sd-'+id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=x=>Number.isFinite(x)?new Intl.NumberFormat('de-DE',{maximumFractionDigits:2}).format(x):'–';
const names={geometry:'Geometrie',quality:'Qualität / Baualter',energy:'Versorgung',pv:'PV-Ausstattung',flex:'Flexibilität',weather:'Wetter',mass:'Gebäudemasse',FSI:'Simulierte GFZ'};
const dims=Object.keys(names).filter(k=>k!=='FSI'), idx=Object.fromEntries(S.columns.map((k,i)=>[k,i]));
const at=(r,k)=>r[idx[k]];
const total=rows=>rows.reduce((a,r)=>{const f=at(r,'NGF_m2'),pe=at(r,'PEI_balance');a.area+=f;a.pe+=f*pe;a.pass+=pe>=0?f:0;a.pv+=f*at(r,'PV_total');a.demand+=f*at(r,'Strombedarf_ohne_Mobilitaet');return a;},{area:0,pe:0,pass:0,pv:0,demand:0});
const mean=a=>a.area?a.pe/a.area:NaN, share=a=>a.area?100*a.pass/a.area:NaN;
const table=(headers,rows)=>`<table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>'<tr>'+row.map(x=>`<td>${esc(x)}</td>`).join('')+'</tr>').join('')}</tbody></table>`;
const option=(v,t=v)=>`<option value="${esc(v)}">${esc(t)}</option>`;
el('scenario').innerHTML=Object.keys(S.scenarios).map(k=>option(k,k.replaceAll('_',' '))).join('');el('scenario').value=S.start;

el('filters').innerHTML=dims.map(k=>`<label>${names[k]}<select id="sd-${k}" aria-label="${names[k]}"></select></label>`).join('');
let filtered=[];
function refreshFilters(){const rows=S.scenarios[el('scenario').value];for(const k of dims){el(k).innerHTML=option('','Alle')+[...new Set(rows.map(r=>at(r,k)))].sort((a,b)=>String(a).localeCompare(String(b),'de',{numeric:true})).map(v=>option(v)).join('');}}
function grouped(rows,k){const m=new Map();for(const r of rows){const v=at(r,k);if(!m.has(v))m.set(v,[]);m.get(v).push(r);}return [...m].map(([key,rs])=>({key,...total(rs)})).sort((a,b)=>b.area-a.area);}
function groupTable(groups){return table(['Gruppe','NGF Mio. m²','NGF-Anteil %','Zielabstand kWh PE/(m² NGF·a)','Beitrag PJ PE/a','Ziel erfüllt %'],groups.map(g=>[g.key,fmt(g.area/1e6),fmt(total(filtered).area?100*g.area/total(filtered).area:NaN),fmt(mean(g)),fmt(g.pe*3.6e-9),fmt(share(g))]));}
function bars(groups){if(!groups.length)return '<p>Keine Treffer für diese Filter.</p>';const w=920,h=groups.length*30+35,zero=555,span=300,max=Math.max(...groups.map(g=>Math.abs(g.pe*3.6e-9)),1e-9);return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Absolute Beiträge zum virtuellen Zielabstand"><line x1="${zero}" y1="0" x2="${zero}" y2="${h-20}" stroke="#738b97"/>${groups.map((g,i)=>{const v=g.pe*3.6e-9,l=Math.abs(v)/max*span,y=i*30+8;return `<text x="4" y="${y+15}" font-size="12">${esc(g.key)}</text><rect x="${v<0?zero-l:zero}" y="${y}" width="${l}" height="20" fill="${v<0?'#b75a46':'#198375'}"><title>${esc(g.key)}: ${fmt(v)} PJ PE/a</title></rect><text x="${v<0?zero+5:zero-5}" text-anchor="${v<0?'start':'end'}" y="${y+15}" font-size="12">${fmt(v)}</text>`;}).join('')}<text x="${zero}" y="${h-3}" text-anchor="middle" font-size="12">0 · virtuelles Ziel</text></svg>`;}
function target(gfz){const c=S.density;return Math.min(c.cfd_fPE*(c.cfd_A/(gfz+c.cfd_dx)-c.cfd_EUI),c.cfd_cutoff);}
function diagnosis(rows){const a=total(rows);a.project=rows.reduce((v,r)=>v+at(r,'NGF_m2')*at(r,'PEI_saldo_project'),0);a.target=rows.reduce((v,r)=>v+at(r,'NGF_m2')*at(r,'GFZ_Zielmittel'),0);a.pe=a.project-a.target;a.pass=rows.reduce((v,r)=>v+at(r,'NGF_m2')*at(r,'GFZ_Zielerfuellung'),0);return a;}
function national(){
 const name=el('scenario').value,a=total(S.scenarios[name]),p=Number(el('pv-share').value)/100,g=S.national_full.g,d=S.national_full.d;
 const tdPV=g.pv*p,tdD=d.gebaeude,miv=d.verkehr*Number(el('miv').value)/100,buPV=a.pv*3.6e-9,buD=a.demand*3.6e-9;
 el('pv-label').textContent=fmt(p*100)+' %';el('miv-label').textContent=fmt(Number(el('miv').value))+' %';
 const others=d.industrie+d.landwirtschaft+d.verbrauch_sektor_energie+d.transportverluste+d.umwandlungseinsatz;
 const central=g.hydro+g.wind+g.biomass+g.geothermal+g.hydrogen_electricity+g.fossil+g.pv*(1-p);
 const credit=central-others-(d.verkehr-miv)-5;
 el('national').innerHTML=table(['Strom [PJ/a]','Bottom-up','Top-down','Bottom-up − Top-down'],[['Gebäude-PV',fmt(buPV),fmt(tdPV),fmt(buPV-tdPV)],['Gebäudebedarf',fmt(buD),fmt(tdD),fmt(buD-tdD)],['Gebäudesaldo',fmt(buPV-buD),fmt(tdPV-tdD),fmt((buPV-buD)-(tdPV-tdD))],['MIV-Bedarf (Allokation)',fmt(miv),fmt(miv),'0'],['Zentrale Restdeckung (Allokation)',fmt(credit),fmt(credit),'0'],['Saldo Gebäude + MIV + Restdeckung',fmt(buPV+credit-buD-miv),fmt(tdPV+credit-tdD-miv),fmt(buPV-buD-tdPV+tdD)]]);
 const palette={'Gebäude':'#437caa','MIV':'#9563b1','Übriger Verkehr':'#b39cc5','Industrie':'#64798d','Landwirtschaft':'#a9a653','Energiebranche':'#84846c','Netzverluste':'#bd8a63','Umwandlung':'#9d735d','Nettoexport':'#b1bbc2','Gebäude-PV':'#e4b936','Freiflächen-PV':'#b5952d','Wasserkraft':'#3994bb','Wind':'#67b7b2','Biomasse':'#7c9a4b','Geothermie':'#bb795b','H₂-Strom':'#9bc7cb','Fossil':'#5e6169','Zentrale Restdeckung':'#63a47c','Zentraler Fehlbetrag':'#b75a46'};
 const cols=[{name:'Top-down Bedarf',items:[['Gebäude',tdD],['MIV',miv],['Übriger Verkehr',d.verkehr-miv],['Industrie',d.industrie],['Landwirtschaft',d.landwirtschaft],['Energiebranche',d.verbrauch_sektor_energie],['Netzverluste',d.transportverluste],['Umwandlung',d.umwandlungseinsatz],['Nettoexport',5]]},{name:'Top-down Deckung',items:[['Gebäude-PV',tdPV],['Wasserkraft',g.hydro],['Wind',g.wind],['Biomasse',g.biomass],['Geothermie',g.geothermal],['H₂-Strom',g.hydrogen_electricity],['Fossil',g.fossil],['Freiflächen-PV',g.pv*(1-p)]]},{name:'Bottom-up Bedarf',items:[['Gebäude',buD],['MIV',miv],['Zentraler Fehlbetrag',Math.max(-credit,0)]]},{name:'Bottom-up Deckung',items:[['Gebäude-PV',buPV],['Zentrale Restdeckung',Math.max(credit,0)]]}];
 const max=Math.max(...cols.map(c=>c.items.reduce((v,x)=>v+x[1],0)))*1.12,y=v=>390-v/max*350;
 let svg='<svg viewBox="0 0 960 640" role="img" aria-label="Nationale Strombilanz und Bottom-up-Gebäudesektor">';
 for(let v=0;v<=max;v+=100)svg+=`<line x1="50" x2="890" y1="${y(v)}" y2="${y(v)}" stroke="#dbe4e7"/><text x="42" y="${y(v)+4}" text-anchor="end" font-size="12">${v}</text>`;
 const xs=[100,300,570,770];cols.forEach((c,i)=>{let sum=0;for(const [label,v] of c.items){if(v<=0)continue;svg+=`<rect x="${xs[i]}" y="${y(sum+v)}" width="110" height="${v/max*350}" fill="${palette[label]}"><title>${label}: ${fmt(v)} PJ/a</title></rect>`;sum+=v;}svg+=`<text x="${xs[i]+55}" y="${y(sum)-10}" text-anchor="middle" font-size="14">${fmt(sum)}</text><text x="${xs[i]+55}" y="415" text-anchor="middle" font-size="13">${c.name}</text>`;});
 for(const [v,x1,x2,color] of [[tdD,100,680,palette.Gebäude],[tdD+miv,100,680,palette.MIV],[tdPV,300,880,palette['Gebäude-PV']]])svg+=`<line x1="${x1}" x2="${x2}" y1="${y(v)}" y2="${y(v)}" stroke="${color}" stroke-dasharray="5 4"/>`;
 svg+='<text x="50" y="20" font-size="13">PJ Strom/a · gleicher Maßstab</text>';
 Object.entries(palette).forEach(([label,color],i)=>{const x=55+(i%4)*225,yy=455+Math.floor(i/4)*29;svg+=`<rect x="${x}" y="${yy}" width="12" height="12" fill="${color}"/><text x="${x+18}" y="${yy+11}" font-size="12">${label}</text>`;});el('national-chart').innerHTML=svg+'</svg>';
 const natSupply=cols[1].items.reduce((s,x)=>s+x[1],0),natDemand=cols[0].items.reduce((s,x)=>s+x[1],0);
 el('national-note').textContent=(name==='Bestand_2024'?'Bestand 2024 gegenüber Zukunftsreferenz 2040. ':'')+`Nationaler Modellrest: ${fmt(natSupply-natDemand)} PJ/a; Modellannahme 5 PJ Nettoexport, Quelle 7 PJ. Bottom-up-Gebäudesaldo: ${fmt(buPV-buD)} PJ/a. Abstand zum Gebäudeziel: ${fmt(buPV-buD-tdPV+tdD)} PJ/a. Die zentrale Restdeckung ist ein zugeordnetes Budget, keine zusätzliche nationale Erzeugung. Typenfilter und GFZ-Zielanalyse ändern diese Bilanz nicht.`;
}
function gfzView(){
 const geo=el('gfz-geometry').value,bins=S.bins.filter(b=>b.Geometrie===geo).sort((a,b)=>a.GFZ-b.GFZ),rows=filtered.filter(r=>at(r,'geometry')===geo&&['PV70','PV90'].includes(at(r,'pv')));
 if(!bins.length||!rows.length){el('gfz-curve').innerHTML='<p>Keine belegten PV70/PV90-Typen für diese Auswahl.</p>';el('gfz-area').innerHTML='';el('gfz').innerHTML='';return;}
 const ps=['PV70','PV90'].map(pv=>{const rr=rows.filter(r=>at(r,'pv')===pv);return {pv,rows:rr,...diagnosis(rr)};}).filter(a=>a.area>0),colors={PV70:'#198375',PV90:'#815cad'};
 const xmax=Math.max(...bins.map(b=>b.GFZ)),ymin=Math.min(...bins.map(b=>target(b.GFZ)),...ps.map(a=>a.project/a.area),0)-10,ymax=Math.max(...bins.map(b=>target(b.GFZ)),...ps.map(a=>a.project/a.area),0)+10;
 const x=v=>70+v/xmax*780,y=v=>290-(v-ymin)/(ymax-ymin)*240;
 let svg='<svg viewBox="0 0 940 350" role="img" aria-label="GFZ-Zielkurve und konstante Projektsalden">';
 for(let v=Math.ceil(ymin/25)*25;v<=ymax;v+=25)svg+=`<line x1="70" x2="850" y1="${y(v)}" y2="${y(v)}" stroke="#dbe4e7"/><text x="62" y="${y(v)+4}" text-anchor="end" font-size="11">${fmt(v)}</text>`;
 svg+=`<polyline points="${bins.map(b=>`${x(b.GFZ)},${y(target(b.GFZ))}`).join(' ')}" fill="none" stroke="#243746" stroke-width="3"/>`;
 for(const a of ps){const v=a.project/a.area;svg+=`<line x1="70" x2="850" y1="${y(v)}" y2="${y(v)}" stroke="${colors[a.pv]}" stroke-width="2"/><text x="855" y="${y(v)+4}" font-size="12" fill="${colors[a.pv]}">${a.pv}</text>`;}
 for(let v=0;v<=xmax;v+=Math.max(1,Math.ceil(xmax/10)))svg+=`<text x="${x(v)}" y="310" text-anchor="middle" font-size="11">${v}</text>`;
 svg+='<text x="70" y="20" font-size="13">kWh PE/(m² NGF·a) · dunkel: Dichteziel; farbig: mittlerer Projektsaldo</text><text x="460" y="337" text-anchor="middle" font-size="12">GFZ · gesamte Verteilung</text></svg>';el('gfz-curve').innerHTML=svg;
 const maxarea=Math.max(...bins.map(b=>b.s*ps.reduce((s,a)=>s+a.area,0))),bw=Math.max(1,780/bins.length*.8);
 let area='<svg viewBox="0 0 940 180" role="img" aria-label="NGF-Verteilung auf GFZ-Kohorten"><text x="70" y="20" font-size="13">Zugeordnete NGF · höchste Säule '+fmt(maxarea/1e6)+' Mio. m²</text>';
 for(const b of bins){let base=145;for(const a of ps){const h=b.s*a.area/maxarea*100;area+=`<rect x="${x(b.GFZ)-bw/2}" y="${base-h}" width="${bw}" height="${h}" fill="${colors[a.pv]}"><title>GFZ ${fmt(b.GFZ)} · ${a.pv}: ${fmt(b.s*a.area/1e6)} Mio. m² NGF</title></rect>`;base-=h;}}el('gfz-area').innerHTML=area+'</svg>';
 const tr=[];for(const b of bins)for(const a of ps){const pass=a.rows.reduce((s,r)=>s+(at(r,'PEI_saldo_project')>=target(b.GFZ)?at(r,'NGF_m2'):0),0)/a.area;tr.push([fmt(b.GFZ),a.pv,fmt(b.s*a.area/1e6),fmt(a.project/a.area),fmt(target(b.GFZ)),fmt(a.project/a.area-target(b.GFZ)),fmt(pass*100)]);}
 el('gfz').innerHTML=table(['GFZ','PV','NGF Mio. m²','Projektsaldo','Zielsaldo','Abstand','NGF erfüllt %'],tr);
}
function render(){
 const rows=S.scenarios[el('scenario').value],q=el('search').value.trim().toLowerCase();filtered=rows.filter(r=>dims.every(k=>!el(k).value||String(at(r,k))===el(k).value)&&(!q||at(r,'Archetype').toLowerCase().includes(q)));
 const a=total(filtered),all=total(rows);el('scope').textContent=`${el('scenario').value.replaceAll('_',' ')} · ${filtered.length.toLocaleString('de-DE')} von ${rows.length.toLocaleString('de-DE')} belegten Typen · ${fmt(100*a.area/all.area)} % der Szenario-NGF`;
 el('cards').innerHTML=[['Betrachtete NGF',fmt(a.area/1e6),'Mio. m²'],['PV-Erzeugung',fmt(a.pv*3.6e-9),'PJ Strom/a'],['Gebäudestrombedarf',fmt(a.demand*3.6e-9),'PJ Strom/a'],['Stromsaldo',fmt((a.pv-a.demand)*3.6e-9),'PJ Strom/a']].map(([label,v,u])=>`<div class="card">${label}<strong>${v}</strong><span class="muted">${u}</span></div>`).join('');
 const high=filtered.filter(r=>['PV70','PV90'].includes(at(r,'pv'))),m=new Map();for(const r of high){const k=at(r,'geometry')+' / '+at(r,'pv');if(!m.has(k))m.set(k,[]);m.get(k).push(r);}const groups=[...m].map(([key,rr])=>({key,...diagnosis(rr)})).sort((a,b)=>a.key.localeCompare(b.key,'de',{numeric:true}));
 el('bars').innerHTML=bars(groups);el('groups').innerHTML=table(['Geometrie / PV','NGF Mio. m²','Projekt kWh PE/(m² NGF·a)','GFZ-Zielmittel','Abstand','NGF erfüllt %'],groups.map(a=>[a.key,fmt(a.area/1e6),fmt(a.project/a.area),fmt(a.target/a.area),fmt(mean(a)),fmt(share(a))]));
 const previous=el('gfz-geometry').value,geos=[...new Set(high.map(r=>at(r,'geometry')))];el('gfz-geometry').innerHTML=geos.map(g=>option(g)).join('');el('gfz-geometry').value=geos.includes(previous)?previous:(geos[0]||'');gfzView();
 el('types').innerHTML=table(['Typ','NGF m²','Simulations-GFZ','Projektsaldo','GFZ-Zielmittel','GFZ-Zielabstand'],[...filtered].sort((a,b)=>at(b,'NGF_m2')-at(a,'NGF_m2')).slice(0,100).map(r=>[at(r,'Archetype'),fmt(at(r,'NGF_m2')),fmt(at(r,'FSI')),fmt(at(r,'PEI_saldo_project')),fmt(at(r,'GFZ_Zielmittel')),fmt(at(r,'GFZ_Zielabstand'))]));national();
}
// Cross-check the browser aggregation against the notebook, before displaying results.
for(const ref of S.reference){const a=total(S.scenarios[ref.Szenario]);for(const [actual,expected] of [[a.area,ref.NGF_m2],[a.pe,ref.PE_kWh],[a.pass,ref.Ziel_m2],[a.pv,ref.PV_kWh],[a.demand,ref.Bedarf_kWh]])if(Math.abs(actual-expected)>Math.max(.01,Math.abs(expected)*1e-10))throw Error('Aggregationsabweichung: '+ref.Szenario);}
el('comparison').innerHTML=table(['Szenario','NGF Mio. m²','PV PJ/a','Bedarf PJ/a','Stromsaldo PJ/a'],Object.entries(S.scenarios).map(([name,rows])=>{const a=total(rows);return[name.replaceAll('_',' '),fmt(a.area/1e6),fmt(a.pv*3.6e-9),fmt(a.demand*3.6e-9),fmt((a.pv-a.demand)*3.6e-9)];}));
el('sources').textContent=S.sources.map(s=>`${s.Quelle}, ${s.Fundstelle}: ${s.Wert_PJ} PJ/a (${s.Datei})`).join(' · ');
el('audit').textContent=JSON.stringify({data_sha256:S.data_sha256,...S.provenance},null,2);
el('scenario').onchange=()=>{refreshFilters();el('search').value='';render();};el('gfz-geometry').onchange=gfzView;el('miv').oninput=national;el('search').oninput=render;for(const k of dims)el(k).onchange=render;el('pv-share').oninput=national;el('reset').onclick=()=>{refreshFilters();el('search').value='';render();};
el('export').onclick=()=>{const csv='\ufeff'+[S.columns,...filtered].map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(';')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=el('scenario').value+'_Typenfilter.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
refreshFilters();render();
