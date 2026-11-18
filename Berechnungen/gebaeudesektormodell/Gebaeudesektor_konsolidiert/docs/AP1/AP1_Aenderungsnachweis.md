# AP1 – Änderungsnachweis

## Neu oder geändert

| Datei | Herkunft | Änderung |
|---|---|---|
| `config/projekt.json` | neu | zentrale Pfade (Konfiguration, Dateien, Ergebnisse), relativ |
| `config/szenarien.json` | aus `szenarien.json` | Pfade der Verteilungen projektrelativ, Szenariotyp ergänzt |
| `config/vergleiche.json` | neu | Platzhalter für AP2 |
| `config/flaechenstroeme/uebergaenge.json` | aus `uebergaenge.json` | nur Regeln; Szenariopaar und Ausgabe entfernt |
| `config/flaechenstroeme/rekonstruktionen.json` | neu | Paar Bestand_2024 → Transition_2040 |
| `modell/gebaeudesektor.py` | `gebaeudesektor.py` (13.11.) | Projektfunktionen, relative Quellen, ortsunabhängige Zustands-ID, Energie nur auf Anforderung, Kennwerte, geprüftes Speichern/Wiederladen, kein `mkdtemp`, Szenariotyp aus Register statt fest verdrahtet; Rechenkern (Flächenbildung, Kalibrierung, Energiebilanzen) unverändert |
| `modell/distribution_to_json.py` | unverändert | – |
| `modell/flaechenstroeme.py` | `Integration_2_2/flaechenstroeme.py` | Projektfunktionen, relative Protokollpfade, kein `mkdtemp`; Rekonstruktionslogik unverändert |
| `notebooks/00_Start.ipynb` | neu | Projektprüfung, nur lesen |
| `notebooks/01_Szenario.ipynb` | ersetzt `Gebaeudesektor_Szenario.ipynb` | Schalter, Abschnittserläuterungen, Wiederladen |
| `notebooks/02_Szenarienvergleich.ipynb` | aus `Gebaeudesektor_Szenarienvergleich.ipynb` | Startzelle, Projektpfade, Export standardmäßig aus, automatische Flusszelle entfernt, relative Protokollpfade |
| `notebooks/03_Flaechenstroeme.ipynb` | ersetzt `Gebaeudesektor_Flaechenstroeme.ipynb` | Lesemodus als Standard, öffentliche Blockdiagnose statt privater Funktionen, Ausgabe nur nach `results/` |
| `tests/*` | ersetzt `tests/test_regression.py` | neue Tests, aktuelle Referenzen, Energiereferenzen |
| `README.md`, `CHANGELOG.md`, `requirements*.txt`, `docs/*`, `data/simulation/README_Datenpfad.md` | neu bzw. ersetzt | Dokumentation |

## Verschoben (Inhalt unverändert)

| alt | neu |
|---|---|
| `data/Verteilungen_Gebaeudesektor.xlsx` | `data/eingaben/verteilungen/Verteilung_Bestand_2024.xlsx` |
| `data/Verteilungen_Transition_2040.xlsx` | `data/eingaben/verteilungen/Verteilung_Transition_2040.xlsx` |
| `data/annahmen.json` | `data/eingaben/annahmen.json` |
| `data/Statistik_Austria_2024.xlsx` | `data/referenz/statistik/` |
| `data/typologien_43200.csv` | `data/referenz/` |
| `data/scenarios.parquet` | `data/simulation/` |

## Archiviert

- Bisherige Dateien des Projektordners → `archiv/vor_AP1_20261116/`.
- `Integration_2_2/` (zielgeführte Entwicklung) → `archiv/zielgefuehrte_entwicklung/Integration_2_2_20261116/`.
- Nichts gelöscht; Sicherungen aus AP0 unter `archiv/sicherungen/`.
