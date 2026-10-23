"""Gemeinsame Farben und Formatierung aller Plotly-Energiediagramme.

Nach Änderungen: python -m Berechnungen.methodik_plots und die beiden
wissenschaftlichen Notebooks ausführen. Farben kennzeichnen Träger bzw. Sektoren;
Schraffuren kennzeichnen virtuelle Bewertungskomponenten.
"""
COLORS = dict(
    hydro='#287bb5', wind='#159a98', pv='#dca51d', biomass='#609c42',
    geothermal='#ce603b', hydrogen_electricity='#8b63b7', fossil='#626b76',
    verkehr='#7857a5', gebaeude='#397eaf', industrie='#486781', landwirtschaft='#739c40',
    verbrauch_sektor_energie='#ad6977', transportverluste='#90969b', umwandlungseinsatz='#569da0',
    miv='#7857a5', oepnv='#af90ce', mobility_credit='#18a28b', density='#a259a4',
    free_pv='#f1c75b', saldo='#283f50', target='#b26326', net_imports='#72858a',
    generation_residual='#159a98', demand_residual='#397eaf', balance_residual='#7857a5',
    wohnen='#d39736', buero_gewerbe='#487fa8', bildung='#739c40', handel_sonstige='#7857a5')


def format_figure(fig, title, unit='PJ Strom/a', height=590):
    fig.update_layout(template='plotly_white', title=dict(text=title, font=dict(size=18)),
                      autosize=True, height=height, font=dict(family='Arial, sans-serif',size=13),
                      margin=dict(l=65,r=25,t=85,b=150),
                      legend=dict(orientation='h',y=-.25,x=0),
                      yaxis_title=unit, separators=',.', hovermode='closest')
    fig.update_yaxes(zeroline=True,zerolinecolor='#58636a')
    return fig


def save_figure(fig, path):
    """Offline HTML; eine gemeinsame Plotly-Datei je Ausgabeordner."""
    from pathlib import Path
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fig.write_html(path, include_plotlyjs='directory', full_html=True,
                   config={'responsive':True,'displaylogo':False,'toImageButtonOptions':{'format':'svg'}})
    html=path.read_text(encoding='utf-8').replace('<head>', '<head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0;overflow-x:hidden} .plotly-graph-div{max-width:100%}</style>')
    path.write_text(html,encoding='utf-8')

# Nutzungsfarben identisch zum GFZ-Analyseanhang.
GFZ_USE_COLORS = {
    'Groß- und Einzelhandelsgebäude': '#abd7e7', 'Büronutzung': '#81c9e6',
    'Hotels o.Ä.': '#3e82b8', 'Industrie und Lagerung': '#405d77',
    'Ein- und Zweifamilienhäuser': '#ff9800', 'Mehrfamilienhaus': '#ff5c48',
    'Gemeinschaftsgebäude': '#dca51b',
    'Kultur, Freizeit, Bildung und Gesundheit': '#92009a',
    'Verkehrs- und Nachrichtenwesen': '#a4a4a4',
}
