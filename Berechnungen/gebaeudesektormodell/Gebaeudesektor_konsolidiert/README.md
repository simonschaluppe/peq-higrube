# Gebäudesektormodell

Gewichtete Abbildung des österreichischen Gebäudesektors über 43 200 Gebäudetypen (Geometrie × Qualität × Versorgung × PV × Flexibilität × Wetter × Speichermasse). Zustände werden aus Excel-Verteilungen gebildet, geprüft, optional energetisch bewertet, gespeichert und verglichen. Die zielgeführte Optimierung ist zurückgestellt und unter `archiv/zielgefuehrte_entwicklung/` versioniert abgelegt.

Registrierte Szenarien: `Bestand_2024`, `Transition_2040`, `Transition_2040_Wachstum` (950 Mio. m² NGF, illustrativ).

## Schnellstart

1. Python-Umgebung einrichten: `pip install -r requirements.txt`
2. Jupyter im Projektordner starten und `notebooks/00_Start.ipynb` ausführen (prüft Pfade und Pakete, rechnet nichts).
3. `notebooks/01_Szenario.ipynb`: Szenario wählen, Schalter bewusst auf `True` setzen, ausführen.
4. `notebooks/02_Szenarienvergleich.ipynb`: Mehrszenarienvergleich gespeicherter Ergebnisse (Übersicht, Referenzvergleich, Paarvergleich); `notebooks/03_Flaechenstroeme.ipynb`: Flächenströme zwischen zwei gespeicherten Zuständen mit Maßnahmenraten und -kombinationen (Standard: nur vorhandene Flüsse lesen; Rekonstruktion nur mit `MODUS='Rekonstruktion'` und `REKONSTRUIEREN=True`). Beide rechnen keine Zustände neu.

Alle Notebooks haben dieselbe Startzelle. Sie sucht den Projektordner über `config/projekt.json`, sodass der Ordner verschoben oder kopiert werden kann. Sie lädt die Module immer frisch aus `modell/` und prüft die Notebook-Fassung (aktuell `1.6.3-AP6`). Nach einer Aktualisierung der Dateien geöffnete Notebooks ohne Speichern schließen und neu öffnen (siehe `docs/BEDIENUNG.md`).

## Struktur

| Ordner | Inhalt |
|---|---|
| `config/` | Projektpfade (`projekt.json`), Szenarioregister, Vergleiche, Übergangsregeln und Rekonstruktionen |
| `modell/` | Rechenlogik (`gebaeudesektor.py`, `distribution_to_json.py`, `szenarienvergleich.py`, `flaechenstroeme.py`, `bestandsbilanz.py` – nur Bilanz Bestand/Neubau/Abriss, `massnahmen.py` – Maßnahmenraten aus gültigen Flüssen, `fassung.py` – Projekt- und Notebook-Fassung, `abnahme.py` – Abnahmestand und Wiederholbarkeit, nur lesen, `prioren.py` – optionale Ableitung leerer Prior-Zellen aus globalen Zielen und Erreichbarkeitsprüfung, Vorstufe ohne eigenen Rechenkern) |
| `notebooks/` | Bedienung 00–03 |
| `data/eingaben/` | fachliche Eingaben (Verteilungen, Annahmen, später Bestandsentwicklung) |
| `data/referenz/` | Statistik und Typologiekatalog |
| `data/simulation/` | Simulationsergebnisse (`scenarios.parquet`), Pfad zentral in `config/projekt.json` |
| `results/` | ausschließlich Ergebnisse (Szenarien, Vergleiche, Flächenströme) |
| `tests/` | automatische Tests mit Referenzdaten in `tests/daten/` |
| `docs/` | Bedienung, Datenschemata, offene Punkte, Prüfprotokolle je Arbeitspaket |
| `archiv/` | Sicherungen und zurückgestellte Entwicklungsstände (nicht aktiv) |

## Tests

Im Projektordner: `python -m unittest discover -s tests -v`
Selbsttest der Excel-Einlesung: `python modell/distribution_to_json.py self-test`

Weitere Hinweise: `docs/BEDIENUNG.md`, `docs/DATENSCHEMATA.md`, `docs/OFFENE_PUNKTE.md`, `CHANGELOG.md`.
