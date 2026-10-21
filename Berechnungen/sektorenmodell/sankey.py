"""Source-linked annual electricity comparison and separate final-energy savings.

No primary-energy credit is calculated. Changes in annual generation are not MW.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
from .model import ROOT, DATA, GEN, DEMAND, EEV, LABELS, NAMES, load, rows, values


def baseline(year, basis):
    records = [r for r in rows('baseline_energy.csv') if int(r['year']) == year and r['energy_basis'] == basis]
    if not records or len({r['metric'] for r in records}) != len(records):
        raise ValueError('Missing or duplicate baseline data')
    return {r['metric']: float(r['value_pj']) for r in records}


def fraction(value, name):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'{name} must be finite and between 0 and 1')


def calculation(scenario='transition_2040', baseline_year=2020, pv_decentral_share=None,
                transport_split=None, savings=None, assumption_source=None):
    if pv_decentral_share is not None:
        fraction(pv_decentral_share, 'PV share')
    if transport_split is not None:
        if set(transport_split) != {'miv', 'ov'}:
            raise ValueError('Provide MIV and public-transport shares; remainder is other transport')
        for key, v in transport_split.items():
            fraction(v, key)
        if sum(transport_split.values()) > 1 + 1e-12:
            raise ValueError('MIV + public transport cannot exceed 100 percent')
    savings = savings or {}
    for key, value in savings.items():
        if key not in DEMAND:
            raise ValueError('Unknown electricity demand category')
        fraction(value, key)
    sensitivity = pv_decentral_share is not None or transport_split is not None or any(savings.values())
    if sensitivity and not assumption_source:
        raise ValueError('A variant must explicitly document assumption_source')
    g = values(load('stromerzeugung_2040.csv'), scenario)
    original_demand = values(load('strombedarf_2040.csv'), scenario)
    d = {k: original_demand[k] * (1-savings.get(k, 0)) for k in DEMAND}
    bgen, bdemand, bend = (baseline(baseline_year, b) for b in ['electricity_generation','electricity_demand','energetic_final'])
    end = values(load('endenergie_2040.csv'), scenario)
    comparison = []
    for basis, keys, now, target in [('electricity_generation', GEN, bgen, g), ('electricity_demand', DEMAND, bdemand, d), ('energetic_final', EEV, bend, end)]:
        for key in keys:
            comparison.append(dict(scenario=scenario,baseline_year=baseline_year,energy_basis=basis,metric=key,
                                   baseline_pj=now[key],target_pj=target[key],change_pj=target[key]-now[key],
                                   increase_pj=max(0,target[key]-now[key]),reduction_pj=max(0,now[key]-target[key])))
    return dict(scenario=scenario, baseline_year=baseline_year, generation=g, demand=d,
                original_demand=original_demand, baseline_generation=bgen, baseline_demand=bdemand,
                baseline_endenergy=bend, endenergy=end, comparison=comparison,
                pv_decentral_share=pv_decentral_share, transport_split=transport_split, savings=savings, sensitivity=sensitivity,
                assumption_source=assumption_source,
                electricity_residual_pj=g['generation_published_total'] + g['net_imports'] - sum(d.values()),
                published_electricity_residual_pj=g['generation_published_total']+g['net_imports']-original_demand['electricity_demand_published_total'],
                new_mobility_credit=None)


def flow_trace(nodes, links, domain):
    ids = list(nodes)
    return go.Sankey(domain=domain, arrangement='snap', node=dict(
        label=[nodes[k][0] for k in ids], x=[nodes[k][1] for k in ids], y=[nodes[k][2] for k in ids],
        color=[nodes[k][3] for k in ids], pad=12, thickness=13, line=dict(width=.3,color='#526575')),
        link=dict(source=[ids.index(l[0]) for l in links],target=[ids.index(l[1]) for l in links],
                  value=[l[2] for l in links],color=[l[3] for l in links],
                  customdata=[l[4] for l in links],hovertemplate='%{customdata}<br>%{value:.2f} PJ/a<extra></extra>'))


def figure(result):
    r = result; year = r['baseline_year']; g = r['generation']; d = r['demand']; bg = r['baseline_generation']
    teal, amber, purple, grey = '#007c83','#dba03a','#8650a1','#748795'
    links=[]; nodes={}
    def node(key,label,x,y,color=teal): nodes[key]=(label,x,y,color)
    def link(a,b,v,desc,color='rgba(0,124,131,0.32)'):
        if v > 1e-9: links.append((a,b,v,color,desc))
    node('current',f'Ertrag {year}',.01,.20,grey); node('growth','Zusätzlicher Jahresertrag',.01,.66,amber)
    node('retirement','Entfallender Ertrag',.25,.97,grey)
    for i,key in enumerate(GEN):
        node(key,f"{NAMES[key].replace('¹','')}: {g[key]:g}",.25,.03+i*.125)
        link('current',key,min(bg[key],g[key]),f'{key}: rechnerisch fortgeführter Jahresertrag {year} → 2040')
        link('growth',key,max(0,g[key]-bg[key]),f'{key}: zusätzlicher Jahresertrag bis 2040; keine installierte Leistung','rgba(219,160,58,.42)')
        link('current','retirement',max(0,bg[key]-g[key]),f'{key}: entfallender Jahresertrag','rgba(116,135,149,.3)')
    node('system','Stromsystem 2040',.58,.43)
    pv = r['pv_decentral_share']
    if pv is not None:
        node('pv_local','PV dezentral',.43,.75,amber); node('pv_central','PV zentral',.43,.91,purple)
        for k,share in [('pv_local',pv),('pv_central',1-pv)]:
            link('pv',k,g['pv']*share,'Explizite PV-Zuordnungsannahme; keine sektorale Deckungspriorität')
            link(k,'system',g['pv']*share,'Rückführung in dieselbe physische Strombilanz')
    for key in GEN:
        if key != 'pv' or pv is None:
            link(key,'system',g[key],f'{key}: UBA-Stromerzeugung 2040, zentral/dezentral offen')
    if g['net_imports'] > 0:
        node('imports','Nettoimport',.43,.02,grey); link('imports','system',g['net_imports'],'UBA-Nettoimport 2040')
    elif g['net_imports'] < 0:
        node('exports','Nettoexport',.98,.96,grey); link('system','exports',-g['net_imports'],'UBA-Nettoexport 2040')
    demand_nodes = [(key,NAMES[key],d[key]) for key in DEMAND]
    if r['transport_split'] is not None:
        split = r['transport_split']
        demand_nodes = [(k,label,d['verkehr']*share) for k,label,share in [
            ('miv','MIV (Annahme)',split['miv']),('ov','ÖV (Annahme)',split['ov']),
            ('other','Übriger Verkehr',max(0,1-sum(split.values())))]] + demand_nodes[1:]
    for i,(key,label,value) in enumerate(demand_nodes):
        node('d_'+key,f'{label}: {value:g}',.98,.02+i*.84/len(demand_nodes))
        link('system','d_'+key,value,f'{label} 2040'+(' – Parametervariante' if r['sensitivity'] else ' – UBA'))
    fig = go.Figure(flow_trace(nodes,links,dict(x=[0,.68],y=[.43,.96])))
    if r['transport_split'] is not None:
        split = r['transport_split']; rest=max(0,1-sum(split.values()))
        fig.add_annotation(x=.35,y=.38,xref='paper',yref='paper',showarrow=False,font_size=12,
            text=f"Verkehrsannahme: MIV {split['miv']*d['verkehr']:.1f}, ÖV {split['ov']*d['verkehr']:.1f}, übriger Verkehr {rest*d['verkehr']:.1f} PJ_el/a. Keine neue Gutschrift.")
    labels=[NAMES[k] for k in DEMAND]
    custom=[[d[k]-r['baseline_demand'][k], max(0,r['baseline_demand'][k]-d[k])] for k in DEMAND]
    fig.add_trace(go.Bar(x=[r['baseline_demand'][k] for k in DEMAND],y=labels,orientation='h',name=str(year),marker_color=grey,
                        hovertemplate='%{y}: %{x:.1f} PJ_el/a<extra>Ausgangsjahr</extra>'))
    fig.add_trace(go.Bar(x=[d[k] for k in DEMAND],y=labels,orientation='h',name='2040',marker_color=teal,customdata=custom,
        hovertemplate='%{y}: %{x:.1f} PJ_el/a<br>Änderung: %{customdata[0]:+.1f}<br>Minderung: %{customdata[1]:.1f}<extra>2040</extra>'))
    # Independent final-energy accounting: never connected to the electricity nodes.
    enodes={}; elinks=[]
    for i,k in enumerate(EEV):
        current=r['baseline_endenergy'][k]; target=r['endenergy'][k]
        enodes[k]=(f'{NAMES[k]} {year}: {current:g}',.01,.05+i*.24,grey)
        enodes[k+'_target']=(f'{NAMES[k]} 2040: {target:g}',.62,.05+i*.24,teal)
        elinks.append((k,k+'_target',min(current,target),'rgba(0,124,131,.32)',f'{NAMES[k]}: verbleibender Endenergiebedarf'))
        if current>target:
            elinks.append((k,'saved',current-target,'rgba(219,160,58,.45)',f'{NAMES[k]}: Endenergieminderung {year} → 2040'))
        elif target>current:
            enodes['added']=('Mehrbedarf',.01,.98,amber)
            elinks.append(('added',k+'_target',target-current,'rgba(219,160,58,.45)',f'{NAMES[k]}: Endenergie-Mehrbedarf'))
    saved=sum(max(0,r['baseline_endenergy'][k]-r['endenergy'][k]) for k in EEV)
    enodes['saved']=(f'Minderung (Komponenten): {saved:g} PJ_end/a',.99,.48,amber)
    fig.add_trace(flow_trace(enodes,elinks,dict(x=[0,.99],y=[0,.27])))
    annual_change=g['generation_published_total']-bg['published_total']
    demand_change=r['original_demand']['electricity_demand_published_total']-r['baseline_demand']['published_total']
    reduction=r['baseline_endenergy']['published_total']-r['endenergy']['eev_published_total']
    title=f"{LABELS[r['scenario']]} · Ausgangsjahr {year} → 2040"
    if r['sensitivity']: title+=' · PARAMETERVARIANTE'
    annotations=[dict(x=0,y=1.075,text=f'<b>{title}</b>',font_size=22),
        dict(x=0,y=1.025,text=f'Jahresstromerzeugung Δ {annual_change:+g} PJ_el/a · publizierter Strombedarf Δ {demand_change:+g} PJ_el/a · Endenergie Δ {reduction*-1:+g} PJ_end/a'),
        dict(x=0,y=.995,text='<b>Strom: Ausgangsertrag und Ausbau → Erzeugung → Stromsystem → Bedarf</b>'),
        dict(x=.78,y=.995,text='<b>Bedarf heute / Ziel</b>'),
        dict(x=0,y=.335,text=f'<b>Separater Endenergievergleich {year} → 2040 (alle Energieträger)</b>'),
        dict(x=0,y=-.065,text=f"Strom: publizierter Bilanzrest {r['published_electricity_residual_pj']:+g} PJ; Rest gegenüber Bedarfskomponenten/Variante {r['electricity_residual_pj']:+g} PJ. Kein künstlicher Ausgleich."),
        dict(x=0,y=-.105,text='Ausbau = zusätzlicher jährlicher Ertrag, nicht MW oder Bruttoinvestition. Jahresbilanz ist kein Nachweis stündlicher Versorgung.'),
        dict(x=0,y=-.145,text='Quellen: REP-0880 Tab. A/15/16; WEM/WAM: REP-0882 Tab. 12 + Zusammenfassung B/D; REP-0995 Tab. B/E/18. Details im Datenmodell.')]
    for a in annotations:
        a.update(xref='paper',yref='paper',showarrow=False,xanchor='left',yanchor='bottom')
    if year==2023:
        annotations[-1]['text']='2023: REP-0995 Tab. E/18 enthält widersprüchliche Ausgangswerte (u.a. Nettoimport/Verluste); kein harmonisierter Basisstromsaldo.'
    fig.update_layout(width=1700,height=1100,font=dict(family='Arial',size=11,color='#263b47'),paper_bgcolor='white',plot_bgcolor='white',
        margin=dict(l=25,r=35,t=100,b=140),barmode='group',legend=dict(x=.8,y=.42,orientation='h'),
        xaxis=dict(domain=[.81,.99],anchor='y',title='PJ_el/a',showgrid=True,gridcolor='#e3e9ed'),
        yaxis=dict(domain=[.43,.96],anchor='x',autorange='reversed',tickfont_size=10),annotations=annotations)
    return fig


def export_comparison(result, path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(result['comparison'][0]));writer.writeheader();writer.writerows(result['comparison'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--static',action='store_true');args=parser.parse_args()
    scenarios=['transition_2040','wem_2025','wam_2025','wem_2023','wam_2023']
    configs={}
    for year in [2020,2023]:
        for sid in scenarios:
            result=calculation(sid,year)
            configs[f'{sid}_{year}']=json.loads(figure(result).to_json())
    default='transition_2040_2020'
    html='''<!doctype html><html lang="de"><meta charset="utf-8"><title>UBA Szenarien: Ausbau und Bedarf</title>
<style>body{margin:12px;font:15px Arial;color:#263b47}label{margin-right:20px}select{padding:6px}#chart{width:100%;min-width:1100px}p{max-width:1200px}</style>
<label>Szenario <select id="scenario">'''+''.join(f'<option value="{s}">{LABELS[s]}</option>' for s in scenarios)+'''</select></label>
<label>Ausgangsjahr <select id="year"><option>2020</option><option>2023</option></select></label>
<p>Standard: konsistente Transition-Ausgangsbilanz 2020. Stellschrauben für PV, MIV/ÖV und zusätzliche Strombedarfsminderung im begleitenden Notebook. Keine neue Mobilitätsgutschrift.</p>
<div id="chart"></div><script>'''+get_plotlyjs()+'''</script><script>
const figures='''+json.dumps(configs,ensure_ascii=False)+''';
function draw(){const f=figures[document.getElementById('scenario').value+'_'+document.getElementById('year').value]; Plotly.react('chart',f.data,f.layout,{responsive:true,displaylogo:false});}
document.getElementById('scenario').onchange=draw;document.getElementById('year').onchange=draw;draw();
</script></html>'''
    out=ROOT/'Abbildungen/transition_sankey.html';out.write_text(html,encoding='utf-8')
    result=calculation();export_comparison(result,DATA/'transition_2020_2040_comparison.csv')
    if args.static:
        figure(result).write_image(str(ROOT/'Abbildungen/transition_sankey.png'),width=1700,height=1100,scale=1.5)
    print(out)


if __name__=='__main__':main()
