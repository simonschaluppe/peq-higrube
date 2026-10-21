"""Visualize the published legacy allocation in one energy basis: TWh PE/year."""
import argparse
import json
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
from .model import ROOT, rows
from .sankey import translucent


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--static',action='store_true'); args=parser.parse_args()
    records=rows('legacy_gutschriften_nutzungen.csv')
    # Published budget values, not the rounded per-area credits, determine flow widths.
    amounts=[float(r['budget_twh_pe']) for r in records]
    names={'wohnen':'Wohnen','buero_gewerbe':'Büro / Gewerbe','bildung':'Bildung','handel_sonstige':'Handel / Sonstige'}
    labels=[names[r['usage']] for r in records]
    colors=['#d39736','#487fa8','#739c40','#7857a5']
    assert abs(sum(amounts)-10.68)<1e-9
    fig=go.Figure(go.Sankey(arrangement='snap',node=dict(
        label=['Mobilitätsbudget<br>10,68 TWh PE/a']+[f'{s}<br>{v:g} TWh PE/a' for s,v in zip(labels,amounts)],
        x=[.01,.99,.99,.99,.99],y=[.5,.08,.36,.59,.83],pad=18,thickness=14,
        color=['#687787']+colors),link=dict(source=[0]*4,target=[1,2,3,4],value=amounts,
        color=[translucent(c) for c in colors],hovertemplate='%{value:.2f} TWh PE/a<extra></extra>')))
    fig.update_layout(width=850,height=440,margin=dict(l=8,r=8,t=20,b=20),font=dict(family='Arial',size=12))
    payload=fig.to_json()
    html='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mobilitätsbudget 2023</title><style>*{box-sizing:border-box}body{margin:0;padding:8px;font:13px Arial}#chart{width:100%;min-width:0}p{overflow-wrap:anywhere}</style>
<div id="chart"></div><p>Quelle: Schneider et al. (2023), Tabelle 9, S. 16. Virtuelle Primärenergie-Zuordnung; keine physischen Stromflüsse. Gutschriften unverändert.</p><script>'''+get_plotlyjs()+'''</script><script>
const f='''+payload+''';delete f.layout.width;f.layout.autosize=true;
Plotly.newPlot('chart',f.data,f.layout,{responsive:true,displayModeBar:false});
</script></html>'''
    (ROOT/'Abbildungen/mobilitaetsbudget_sankey.html').write_text(html,encoding='utf-8')
    if args.static: fig.write_image(ROOT/'Abbildungen/mobilitaetsbudget_sankey.png',scale=2)


if __name__=='__main__':main()
