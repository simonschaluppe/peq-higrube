"""Darstellung geprüfter Szenariotabellen und Notebook-Ergebnisse; keine Kalibrierung."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from styles.plotly_formatting import COLORS, format_figure, save_figure
from Berechnungen.sektorenmodell.model import ROOT, DATA, GEN, DEMAND, LABELS, NAMES, SCENARIOS

OUT=ROOT/'Abbildungen/methodik'


def national_figures():
    scenarios=SCENARIOS[1:]
    gs=pd.read_csv(DATA/'stromerzeugung_2040.csv').pivot(index='scenario',columns='metric',values='value_pj')
    ds=pd.read_csv(DATA/'strombedarf_2040.csv').pivot(index='scenario',columns='metric',values='value_pj')
    for name,table,keys,title,total in [
        ('stromerzeugung',gs,GEN,'Stromerzeugung 2040 nach Energieträger','generation_published_total'),
        ('strombedarf',ds,DEMAND,'Strombedarf 2040 nach Sektor','electricity_demand_published_total')]:
        fig=go.Figure()
        for k in keys:
            fig.add_bar(name=NAMES[k],x=[LABELS[s] for s in scenarios],y=table.loc[scenarios,k],marker_color=COLORS[k])
        fig.add_scatter(name='Publizierte Gesamtsumme',x=[LABELS[s] for s in scenarios],y=table.loc[scenarios,total],
                        mode='markers',marker=dict(symbol='diamond-open',color=COLORS['saldo'],size=12))
        if name=='stromerzeugung':
            fig.add_bar(name='Nettoimport (+) / Export (−)',x=[LABELS[s] for s in scenarios],y=table.loc[scenarios,'net_imports'],marker_color=COLORS['net_imports'])
        fig.update_layout(barmode='relative')
        save_figure(format_figure(fig,title),OUT/f'{name}.html')
    fig=make_subplots(rows=3,cols=1,vertical_spacing=.13,subplot_titles=[
        'Erzeugung: Komponenten (+) und Gesamtsumme (−)',
        'Bedarf: Komponenten (+) und Gesamtsumme (−)',
        'Gesamterzeugung (+), Nettoimport und Gesamtbedarf (−)'])
    identities=[[(gs[GEN].sum(axis=1),'Erzeugungskomponenten','wind'),(-gs.generation_published_total,'Erzeugung gesamt (−)','fossil')],
                [(ds[DEMAND].sum(axis=1),'Bedarfskomponenten','gebaeude'),(-ds.electricity_demand_published_total,'Bedarf gesamt (−)','industrie')],
                [(gs.generation_published_total,'Erzeugung gesamt','wind'),(gs.net_imports,'Nettoimport','net_imports'),(-ds.electricity_demand_published_total,'Bedarf gesamt (−)','industrie')]]
    for i,terms in enumerate(identities,1):
        for series,label,c in terms:
            fig.add_trace(go.Bar(name=label,x=[LABELS[s] for s in scenarios],y=series.loc[scenarios],marker_color=COLORS[c],showlegend=False),row=i,col=1)
        rest=sum(t[0] for t in terms).loc[scenarios]
        fig.add_trace(go.Scatter(name='Rest',x=[LABELS[s] for s in scenarios],y=rest,
            mode='markers+text',text=[f'Rest: {v:+g}' for v in rest],textposition='top center',
            marker=dict(color=COLORS['saldo'],size=8),showlegend=False),row=i,col=1)
    fig.update_layout(barmode='relative')
    format_figure(fig,'Drei Bilanzidentitäten: Stapel und resultierender Rest',height=820)
    fig.update_yaxes(title_text='PJ Strom/a')
    save_figure(fig,OUT/'bilanzreste.html')


def allocation_figures(variants, central_steps):
    fig=go.Figure(go.Waterfall(x=list(central_steps),y=list(central_steps.values()),
        measure=['absolute']+['relative']*(len(central_steps)-2)+['total'],
        decreasing=dict(marker_color=COLORS['gebaeude']),increasing=dict(marker_color=COLORS['wind']),
        totals=dict(marker_color=COLORS['mobility_credit']),textposition='outside'))
    fig.update_xaxes(tickangle=-30)
    save_figure(format_figure(fig,'Von zentralen Großkraftwerken zur Restdeckung'),OUT/'zentraler_pool.html')
    def short_label(label):
        return label.replace('20 % Freiflächen-PV','20 %<br>Freiflächen-PV').replace('40 % MIV: Konflikt','40 % MIV:<br>Konflikt').replace('H₂ vollständig angerechnet','H₂ vollständig<br>angerechnet')
    x=[(short_label(row['Variante']),side) for row in variants for side in ['Bedarf','Deckung']]
    fig=go.Figure()
    for key,label,color,side in [('Gebäude','Gebäudestrombedarf','gebaeude','Bedarf'),('MIV','MIV-Strombedarf','miv','Bedarf'),
                               ('PV Gebäude','Gebäude-PV','pv','Deckung'),('Verfügbare Restdeckung','Zentrale Restdeckung','mobility_credit','Deckung'),('Zentraler Fehlbetrag','Zentraler Fehlbetrag','target','Bedarf')]:
        fig.add_bar(name=label,x=[[a for a,b in x],[b for a,b in x]],
                    y=[row[key] if s==side else 0 for row in variants for s in ['Bedarf','Deckung']],marker_color=COLORS[color])
    fig.update_layout(barmode='stack')
    save_figure(format_figure(fig,'Gebäude und MIV: Bedarf und zugeordnete Deckung',height=660),OUT/'allokation_deckung.html')
    fig=go.Figure()
    fig.add_bar(name='Saldo Deckung − Bedarf',x=[short_label(r['Variante']) for r in variants],y=[r['Saldo'] for r in variants],marker_color=COLORS['saldo'])
    fig.add_bar(name='Zentraler Fehlbetrag',x=[short_label(r['Variante']) for r in variants],y=[r['Zentraler Fehlbetrag'] for r in variants],marker_color=COLORS['target'])
    fig.update_layout(barmode='group')
    save_figure(format_figure(fig,'Saldo und zentrale Unterdeckung je Variante'),OUT/'allokation_saldo.html')


def building_figures(types, comparison):
    # Vollständige Typenliste: Geometrie wählen, horizontale Plotachse zoomen.
    geometries=sorted(types.Geometrie.unique()); buttons=[]
    fig=go.Figure()
    for gi,geom in enumerate(geometries):
        t=types.loc[types.Geometrie.eq(geom)]
        labels=t.Archetype.str.split('|',regex=False).str[1:3].str.join(' / ')
        for col,name,c,pattern in [('Bedarf_BGF','Strombedarf (negativ)','gebaeude',''),('PV_BGF','PV-Erzeugung','pv',''),('c_D_EE_BGF','Virtueller Dichtewert','density','/')]:
            vals=-t[col] if col=='Bedarf_BGF' else t[col]
            fig.add_bar(name=name,x=labels,y=vals,marker=dict(color=COLORS[c],pattern_shape=pattern),visible=gi==0,
                        customdata=t[['Archetype','Nationale BGF 2040']],
                        hovertemplate='%{customdata[0]}<br>%{y:.2f} kWh/(m² BGF a)<br>BGF 2040: %{customdata[1]:,.0f} m²<extra>%{fullData.name}</extra>')
        mask=[False]*(len(geometries)*3)
        mask[gi*3:gi*3+3]=[True]*3
        buttons.append(dict(label=geom,method='update',args=[{'visible':mask},{'xaxis.range':[-.5,14.5]}]))
    fig.update_layout(barmode='relative',updatemenus=[dict(buttons=buttons,x=0,y=1.05,yanchor='bottom')],
                      xaxis=dict(range=[-.5,14.5],tickangle=-65,rangeslider=dict(visible=True,thickness=.06)))
    format_figure(fig,'Typenvergleich: Strom und virtuelle Dichtekorrektur','kWh EE/(m² BGF·a)',820)
    fig.update_layout(margin=dict(t=130,b=240),legend=dict(y=-.49))
    save_figure(fig,OUT/'typen_deckung.html')
    fig=go.Figure()
    for col,label,c,pattern in [('Bedarf','Gebäude + MIV: Bedarf','gebaeude',''),('Deckung','Gebäude-PV + zentrale Restdeckung','pv',''),
                              ('Dichte','Virtuelle Dichtekorrektur','density','/'),('Saldo','Saldo einschließlich ausgewiesener Korrektur','saldo','')]:
        fig.add_bar(name=label,x=comparison.Modell,y=comparison[col],marker=dict(color=COLORS[c],pattern_shape=pattern))
    fig.update_layout(barmode='group')
    save_figure(format_figure(fig,'Top-down, Bottom-up und Dichte-Bewertung','PJ bzw. PJ EE-Äquivalent/a',height=660),OUT/'sektorvergleich.html')


if __name__=='__main__':
    national_figures()
