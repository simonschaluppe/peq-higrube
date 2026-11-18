# AP5 – Änderungsnachweis

Stand 16.11.2026. SHA-256 (erste 12 Zeichen) der gelieferten Fassung. Sicherung der Vorfassungen auf dem Gerät: `archiv/vor_AP5_20261116/` (Pfadtrenner als `__`).

| Datei | Art | Änderung |
|---|---|---|
| `modell/massnahmen.py` | neu | Maßnahmendefinition laden/prüfen, Raten, Kombinationen, Versorgungsmatrix, Neubau-/Abrissmerkmale, Kontrollen; nur Auswertung |
| `config/flaechenstroeme/massnahmen.json` | neu | Abgrenzung E7/E8/E9 (Schema 1.0) |
| `config/projekt.json` | geändert | `konfiguration.massnahmen` |
| `modell/flaechenstroeme.py` | geändert | Definition bei `MACHBAR` zum Ergebnis; Export der Maßnahmendateien und Excel-Blätter; `massnahmen_sha256`; Docstring `aenderungsanteile` |
| `notebooks/03_Flaechenstroeme.ipynb` | geändert | Abschnitt 8 neu, Abschnitt 7 nicht mehr vorläufig, Speichern = 9; 00–02 unverändert |
| `tests/test_massnahmen.py` | neu | 9 Tests |
| `tests/test_flaechenstroeme.py`, `tests/test_bestandsbilanz.py`, `tests/test_notebook_sicherheit.py` | geändert | Maßnahmendateien, Raten nach Wiederladen, Import-/Verbotsregeln |
| `README.md`, `CHANGELOG.md`, `docs/BEDIENUNG.md`, `docs/DATENSCHEMATA.md`, `docs/OFFENE_PUNKTE.md` | geändert | Dokumentation AP5 |
| `docs/AP5/*` | neu | Prüfprotokoll, Änderungsnachweis, Testlauf |

Unverändert: `gebaeudesektor.py` (Zustands-IDs gültig), `bestandsbilanz.py`, `szenarienvergleich.py`, `distribution_to_json.py`, Notebooks 00–02, Regeln, Szenarien, Eingabedaten.

## Hashes

| Datei | SHA-256 (12) |
|---|---|
| `modell/massnahmen.py` | A3DB4681A91F |
| `modell/flaechenstroeme.py` | 37C30C5B4097 |
| `config/flaechenstroeme/massnahmen.json` | 4B868514D7F4 |
| `config/projekt.json` | C2313E560BD9 |
| `notebooks/03_Flaechenstroeme.ipynb` | E4061B23F6E4 |
| `tests/test_massnahmen.py` | A012B8E4F037 |
| `tests/test_flaechenstroeme.py` | 0EA85EC5AD95 |
| `tests/test_bestandsbilanz.py` | D9242F8C2EBD |
| `tests/test_notebook_sicherheit.py` | 741C9ED03CDB |
| `README.md` | 6C6FF652D4C8 |
| `CHANGELOG.md` | C82B4DDA73AA |
| `docs/BEDIENUNG.md` | 48DFE2031679 |
| `docs/DATENSCHEMATA.md` | DFD20162A806 |
| `docs/OFFENE_PUNKTE.md` | CF2BEF5FA035 |
| `docs/AP5/AP5_Testlauf.txt` | F3C3E8A1F6CE |
| `docs/AP5/AP5_Pruefprotokoll.md` | 732EEDBE0E34 |


## Nachtrag 17.11.2026 (1.5.1)

Sicherung der Vorfassungen auf dem Gerät: `archiv/vor_AP51_20261117/` (Pfadtrenner als `__`). Die Hashes oben (1.5.0) sind für die folgenden Dateien überholt.

| Datei | Art | Änderung |
|---|---|---|
| `modell/flaechenstroeme.py` | geändert | zweite Zielstufe (bei maximal unveränderter Fläche minimaler Versorgungswechsel), `zielwerte` im Ergebnis, neue Kontrollen, Abweisung von Ergebnissen mit älterer Zielfunktion, `blockdiagnose(..., bilanz)` berücksichtigt Neubau/Abriss |
| `modell/massnahmen.py` | geändert | nur Hinweistext zur Zielfunktion |
| `data/eingaben/bestandsentwicklung/Bestandsentwicklung.xlsx` | geändert | Freigaben: Abriss 1990-99; Neubau Biomasse und Elektro |
| `notebooks/03_Flaechenstroeme.ipynb` | geändert | Ausgabe der Zielfunktion, Blockdiagnose mit Bilanz, Texte Abschnitte 4/5/7/8; 00–02 unverändert |
| `tests/test_massnahmen.py` | geändert | Klasse `Zielstufe` (2 Tests), jetzt 11 Tests |
| `tests/test_bestandsbilanz.py` | geändert | Blockdiagnose mit/ohne Bilanz, Freigaben, `zielwerte`, Abweisung |
| `CHANGELOG.md`, `docs/BEDIENUNG.md`, `docs/DATENSCHEMATA.md`, `docs/OFFENE_PUNKTE.md` | geändert | Dokumentation 1.5.1 |
| `docs/AP5/*` | geändert | Prüfprotokoll-Nachtrag, Testlauf, dieser Nachweis |

Unverändert: `massnahmen.json`, `projekt.json`, `bestandsbilanz.py`, `gebaeudesektor.py`, `szenarienvergleich.py`, `distribution_to_json.py`, Notebooks 00–02, `test_flaechenstroeme.py`, `test_notebook_sicherheit.py`, `README.md`.

| Datei | SHA-256 (12) |
|---|---|
| `modell/flaechenstroeme.py` | CECD8EB9A214 |
| `modell/massnahmen.py` | E307D2D58DC7 |
| `data/eingaben/bestandsentwicklung/Bestandsentwicklung.xlsx` | 0B8834F8B000 |
| `notebooks/03_Flaechenstroeme.ipynb` | 57A1CE73D3C5 |
| `tests/test_massnahmen.py` | 837C5BDDEDFB |
| `tests/test_bestandsbilanz.py` | F14546739262 |
| `CHANGELOG.md` | EEED8BB2DA6A |
| `docs/BEDIENUNG.md` | BBC78F7A31CB |
| `docs/DATENSCHEMATA.md` | C49090B76258 |
| `docs/OFFENE_PUNKTE.md` | 1DAC411E93E8 |
| `docs/AP5/AP5_Testlauf.txt` | 684171D9722A |
| `docs/AP5/AP5_Pruefprotokoll.md` | 8828A6BB6C14 |

Der Hash des Änderungsnachweises selbst steht im Abschlussbericht.
