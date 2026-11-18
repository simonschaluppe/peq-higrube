# AP2 – Änderungsnachweis

| Datei | Art | Änderung |
|---|---|---|
| `modell/szenarienvergleich.py` | neu | Mehrszenarienvergleich: Register, Laden mit Integritätsprüfung, Vergleichbarkeit, Übersicht, Referenz- und Paarvergleich, Grafiken, Export, Wiederladen |
| `config/vergleiche.json` | geändert | `mindestabdeckung_pct` (95), Hinweis, `beschreibung` für `Bestand_2024__Transition_2040` |
| `notebooks/02_Szenarienvergleich.ipynb` | ersetzt | modulbasiert; neue Schalter; Schalter `EXPORT_ERSETZEN` heißt jetzt `ERSETZEN` |
| `tests/test_vergleich.py` | neu | 12 Tests |
| `tests/test_notebook_sicherheit.py` | geändert | Standardwerte 02, Test `test_02_nur_modulfunktionen` |
| `README.md`, `CHANGELOG.md`, `requirements_getestet.txt` | geändert | AP2-Stand, lokale Umgebung |
| `docs/BEDIENUNG.md`, `docs/DATENSCHEMATA.md`, `docs/OFFENE_PUNKTE.md` | geändert | Schalter 02, Lesart, Vergleichsordner, Statusregeln, offene Punkte |
| `docs/AP2/*` | neu | Prüfprotokoll, Änderungsnachweis, Testlauf |

Nicht geändert: `modell/gebaeudesektor.py`, `modell/distribution_to_json.py`, `modell/flaechenstroeme.py`, Notebooks 00, 01, 03, alle Eingaben und Ergebnisse. Die gespeicherten Zustands-IDs bleiben gültig.

Die bisherige Fassung von Notebook 02 (AP1, vorläufig) liegt unter `archiv/vor_AP2_20261116/02_Szenarienvergleich.ipynb`.
