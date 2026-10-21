"""Validate normalized scenario data and retained published residuals (stdlib only)."""
from sektorenmodell.model import validate


if __name__ == '__main__':
    for r in validate():
        print(r['scenario'] + ': ' + '; '.join(f'{k}={v:+g} PJ' for k, v in r.items() if k != 'scenario'))
    print('Tabellen, Energiegrößen, Quellen, Schlüssel, Legacy-Gutschriften und Bilanzreste OK.')
