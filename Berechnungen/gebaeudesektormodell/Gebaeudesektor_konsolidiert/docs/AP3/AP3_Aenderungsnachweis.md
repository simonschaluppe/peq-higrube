# AP3 – Änderungsnachweis

| Datei | Art | Änderung |
|---|---|---|
| `modell/flaechenstroeme.py` | geändert | Statuswerte und -bedeutung, `analysiere_rekonstruktion` (einheitlich, immer mit Status), `pruefe_eingaben`, `pruefe_fluesse`, `lade_zustaende_geprueft`, `lade_flussergebnis`, `matrix`, `aenderungsanteile` (vorläufig), `zusammenfassung`, `registrierte_rekonstruktionen`, `speichere_ergebnis`; Zeitlimit; strikte Zeitreihenfolge; Export mit `Pruefungen.csv`, Ausgabehashes, bereinigten Eingaben; Altfunktionen entfernt |
| `modell/gebaeudesektor.py` | geändert | Szenarioregister nicht im Fingerprint; `MODELLVERSION = '1.3.0-AP3'` (alle Zustands-IDs ändern sich einmalig) |
| `config/szenarien.json` | geändert | Szenario `Transition_2040_Wachstum` |
| `config/vergleiche.json` | geändert | Vergleich `Bestand_Transition_Wachstum_2040` |
| `config/flaechenstroeme/rekonstruktionen.json` | geändert | Paar `Bestand_2024__Transition_2040_Wachstum`, Beschreibungen, Hinweis |
| `notebooks/03_Flaechenstroeme.ipynb` | ersetzt | Ablauf 1–8 nach Arbeitsauftrag, nur Modulaufrufe, neue Schalter |
| `tests/test_flaechenstroeme.py` | ersetzt | 12 Tests (Regelfälle synthetisch, Projektablauf, Notebook 03) |
| `tests/test_szenario.py` | geändert | +2 Tests (Register/ID, drittes Szenario) |
| `tests/test_notebook_sicherheit.py` | geändert | `test_03_nur_modulfunktionen` |
| `README.md`, `CHANGELOG.md` | geändert | AP3-Stand |
| `docs/BEDIENUNG.md`, `docs/DATENSCHEMATA.md`, `docs/OFFENE_PUNKTE.md` | geändert | Schalter und Status 03, Ergebnisordner Flächenströme, offene Punkte |
| `docs/AP3/*` | neu | Prüfprotokoll, Änderungsnachweis, Testlauf |

Nicht geändert: `modell/distribution_to_json.py`, `modell/szenarienvergleich.py`, Notebooks 00–02, `config/flaechenstroeme/uebergaenge.json`, alle Eingaben unter `data/`.

Vorherige Fassungen von `notebooks/03_Flaechenstroeme.ipynb`, `modell/flaechenstroeme.py` und `modell/gebaeudesektor.py` liegen unter `archiv/vor_AP3_20261116/`.
