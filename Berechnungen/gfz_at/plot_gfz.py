"""Erstellt drei Berichtsdiagramme aus den Ergebnissen des GFZ-Sektormodells.

Benötigte Dateien im Ergebnisordner:
- gfz_distribution_austria_by_use.csv
- gfz_distribution_by_province.csv
- allocation_audit.csv

Aufruf:
    python plot_gfz_annotiert.py /pfad/zu/ergebnissen --out /pfad/zu/plots
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Bilder ohne grafische Benutzeroberfläche erzeugen
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import pandas as pd


# Feste Farben und Stapelreihenfolge je Gebäudeklasse.
# An die Farben und Klassenreihenfolge des Referenz-Histogramms angelehnt.
# Die Reihenfolge bestimmt auch die Reihenfolge in der Legende (unten -> oben).
NUTZUNGSFARBEN = {
    'Groß- und Einzelhandelsgebäude': '#abd7e7',  # hellblau
    'Büronutzung': '#81c9e6',                      # türkisblau
    'Hotels o.Ä.': '#3e82b8',                      # mittelblau
    'Industrie und Lagerung': '#405d77',          # dunkelblau
    'Ein- und Zweifamilienhäuser': '#ff9800',     # orange
    'Mehrfamilienhaus': '#ff5c48',                # korallrot
    'EZFH Nebenwohnsitz': '#ff947d',              # hellkorall
    'Gemeinschaftsgebäude': '#dca51b',            # ocker
    'Sondernutzung, konditioniert': '#19c52c',    # grün
    'Kultur, Freizeit, Bildung und Gesundheit': '#92009a',  # violett
    'Sondernutzung, nicht konditioniert': '#737373',        # dunkelgrau
    'Verkehrs- und Nachrichtenwesen': '#a4a4a4',            # grau
    'keine Info': '#cecece',                       # hellgrau
}
GFZ_KLASSENBREITE = 0.1  # BGF je GFZ-Intervall von 0,1


def make_figures(result_dir: Path, plot_to: Path, gfz_cutoff: float = 8) -> None:
    plot_to.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        'font.size': 10,
        'axes.spines.top': False,
        'axes.spines.right': False,
    })
    data = pd.read_csv(result_dir / 'gfz_distribution_austria_by_use.csv')
    audit = pd.read_csv(result_dir / 'allocation_audit.csv')
    regional = pd.read_csv(result_dir / 'gfz_distribution_by_province.csv')

    def save(fig, name):
        fig.savefig(plot_to / (name + '.png'), dpi=180, bbox_inches='tight')
        plt.close(fig)

    # 1. Gebäudebestand Österreich: gestapelte BALKEN statt Flächendiagramm.
    # Jede Zeile steht für ein GFZ-Intervall, jede Spalte für eine Hauptnutzung.
    # pivot_table mit sum ist robust, falls mehrere Datenzeilen dieselbe
    # Kombination aus GFZ und Nutzung enthalten.
    wide = (
        data.loc[data.GFZ.between(0, gfz_cutoff)]
        .pivot_table(index='GFZ', columns='GWR_Nutzung', values='BGF_m2',
                     aggfunc='sum', fill_value=0)
        .sort_index()
        / 1e6  # m² -> Mio. m² je 0,1 GFZ
    )
    if wide.empty:
        raise ValueError('Keine GFZ-Daten zwischen 0 und dem gewählten GFZ-Cutoff.')

    # Einheitliche Farben, unabhängig davon, welche Klassen im Datensatz
    # vorhanden sind. Unbekannte Klassen werden am Schluss ergänzt.
    ordered = [name for name in NUTZUNGSFARBEN if name in wide.columns]
    extras = sorted(set(wide.columns) - set(ordered))
    ordered += extras
    fallback_colors = plt.get_cmap('tab20')

    fig, ax = plt.subplots(figsize=(14, 6), layout='constrained')
    x = wide.index.to_numpy(dtype=float)
    bottom = pd.Series(0.0, index=wide.index)

    for i, name in enumerate(ordered):
        color = NUTZUNGSFARBEN.get(name, fallback_colors(i % 20))
        ax.bar(
            x, wide[name].to_numpy(), bottom=bottom.to_numpy(),
            width=GFZ_KLASSENBREITE * 0.96,  # schmale Trennfuge zwischen Balken
            align='edge',                     # Intervall beginnt am GFZ-Wert
            color=color, edgecolor='none', label=name,
            zorder=2,
        )
        bottom += wide[name]

    # X-Achse exakt ab GFZ 0. Große Teilstriche bei ganzen GFZ-Werten,
    # kleine Teilstriche alle 0,1 GFZ wie im Referenz-Histogramm.
    ax.set_xlim(left=0, right=gfz_cutoff + GFZ_KLASSENBREITE)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_locator(MultipleLocator(1.0))
    ax.xaxis.set_minor_locator(MultipleLocator(GFZ_KLASSENBREITE))
    ax.tick_params(axis='x', which='major', length=6, width=1)
    ax.tick_params(axis='x', which='minor', length=3, width=0.7)
    ax.set_axisbelow(True)
    ax.grid(axis='x', which='major', color='#bbbbbb', linewidth=0.65)

    ax.set(
        xlabel='Geschossflächenzahl (GFZ)',
        ylabel='BGF [Mio. m² je 0,1 GFZ]',
        title='Österreichischer Gebäudebestand 2021: modellierte Dichteverteilung',
    )
    # Die Legende liegt rechts oben auf dem weitgehend freien Bereich
    # hoher GFZ-Werte; der eigentliche Plot bleibt dadurch breit.
    ax.legend(title='Hauptnutzung', loc='upper right', fontsize=9,
              title_fontsize=11, frameon=True, framealpha=0.95)
    save(fig, 'gfz_oesterreich_nutzung')

    # 2. Vergleich der Bundesländer: Originaldarstellung unverändert.
    fig, ax = plt.subplots(figsize=(9, 4.5), layout='constrained')
    for region, color in [('Wien', '#955196'), ('Salzburg', '#007c83')]:
        values = regional.loc[regional.Bundesland == region].set_index('GFZ').BGF_m2
        (100 * values.loc[values.index <= gfz_cutoff] / values.sum()).plot(ax=ax, label=region, color=color)
    ax.set(xlabel='Geschossflächenzahl (GFZ)', ylabel='Anteil der Landes-BGF [% je 0,1 GFZ]', title='Wien und Salzburg: hochgerechnete Landesverteilungen 2021')
    ax.legend()
    save(fig, 'gfz_wien_salzburg')

    # 3. Modellabdeckung/Ersatzschätzungen: Originaldarstellung unverändert.
    audit['Ersatzschätzung'] = audit.BGF_target_m2.where(audit.status != 'reference-exact', 0)
    totals = audit.groupby('Bundesland')[['BGF_target_m2', 'Ersatzschätzung']].sum()
    totals.loc['Österreich'] = totals.sum()
    shares = 100 * totals['Ersatzschätzung'] / totals.BGF_target_m2
    fig, ax = plt.subplots(figsize=(9, 5), layout='constrained')
    ax.barh(shares.index, 100 - shares, color='#007c83', label='Primäre Referenz')
    ax.barh(shares.index, shares, left=100-shares, color='#df9c38', label='Ersatzschätzung')
    for i, value in enumerate(shares):
        ax.text(101, i, f'{value:.2f} %', va='center', fontsize=9)
    ax.set(xlim=(0, 114), xlabel='Anteil der BGF [%] · rechts: Ersatzanteil', title='Statistische Modellabdeckung nach Bundesland')
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.16), ncol=2)
    ax.invert_yaxis()
    save(fig, 'fallback_bundeslaender')


if __name__ == '__main__':
    print("hel")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('result_dir', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--gfz-cutoff', type=float, default=8)
    args = p.parse_args()
    make_figures(args.result_dir, args.out or args.result_dir, args.gfz_cutoff)
