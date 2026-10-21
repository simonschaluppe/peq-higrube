"""Reproduce report figures from model outputs (no building microdata needed)."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def make_figures(result_dir: Path, plot_to: Path, gfz_cutoff: float = 8) -> None:
    plot_to.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    data = pd.read_csv(result_dir / 'gfz_distribution_austria_by_use.csv')
    audit = pd.read_csv(result_dir / 'allocation_audit.csv')
    regional = pd.read_csv(result_dir / 'gfz_distribution_by_province.csv')

    def save(fig, name):
        fig.savefig(plot_to / (name + '.png'), dpi=180, bbox_inches='tight')
        plt.close(fig)

    wide = data.loc[data.GFZ <= gfz_cutoff].pivot(index='GFZ', columns='GWR_Nutzung', values='BGF_m2').fillna(0) / 1e6
    fig, ax = plt.subplots(figsize=(12, 6), layout='constrained')
    wide.plot.area(ax=ax, linewidth=0, cmap='tab20')
    ax.set(xlabel='Geschossflächenzahl (GFZ)', ylabel='BGF [Mio. m² je 0,1 GFZ]', title='Österreichischer Gebäudebestand 2021: modellierte Dichteverteilung')
    ax.legend(title='Hauptnutzung', loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=8)
    save(fig, 'gfz_oesterreich_nutzung')

    fig, ax = plt.subplots(figsize=(9, 4.5), layout='constrained')
    for region, color in [('Wien', '#955196'), ('Salzburg', '#007c83')]:
        values = regional.loc[regional.Bundesland == region].set_index('GFZ').BGF_m2
        (100 * values.loc[values.index <= gfz_cutoff] / values.sum()).plot(ax=ax, label=region, color=color)
    ax.set(xlabel='Geschossflächenzahl (GFZ)', ylabel='Anteil der Landes-BGF [% je 0,1 GFZ]', title='Wien und Salzburg: hochgerechnete Landesverteilungen 2021')
    ax.legend()
    save(fig, 'gfz_wien_salzburg')

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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('result_dir', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--gfz-cutoff', type=float, default=8)
    args = p.parse_args()
    make_figures(args.result_dir, args.out or args.result_dir, args.gfz_cutoff)
