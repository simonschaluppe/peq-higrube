# GFZ-Verteilung Österreich

Bundeslandweise, BGF-gewichtete Hochrechnung des Bestands mit Statistikbezug 2021. Enthalten sind Rechenmodul, Notebook, Tests, Ergebnistabellen und Berichtsgrafiken. Die nationale Kalibrierung 2040 ist ein nachfolgender Arbeitsschritt.

## Ausführen

Aus diesem Verzeichnis, mit Python 3.13 (getestet):

```powershell
python -m pip install -r requirements.txt
python -m unittest -v test_gfz_hydrator.py
python gfz_hydrator.py --buildings data/rohdaten_python.xlsx --statistics data/GFZ_Analyse_AT.xlsx --out outputs/recalculated --fallback vienna
python compare_results.py
python plot_gfz.py outputs/recalculated --out ../../Abbildungen/gfz_at
```

Die Originaldateien bleiben unverändert. Lokale Kopien liegen in `data/`, das von Git ausgeschlossen ist. Benötigt werden `rohdaten_python.xlsx` (Blatt `Rohdaten`) und `GFZ_Analyse_AT.xlsx` (Blatt `python`). `statistics.xlsx` ist eine ergänzende historische Quelle, kein zweiter additiver Flächeneingang. CSV-Extrakte mit denselben Spalten werden ebenfalls unterstützt.

Falls eine eingeschränkte Windows-Umgebung das System-Tempverzeichnis nicht beschreiben kann, vor den Tests `TEMP` und `TMP` auf ein beschreibbares lokales Verzeichnis setzen. Dies ändert keine Modellparameter.

Ohne Rohdaten lassen sich die gelieferten Tabellen prüfen und die Grafiken reproduzieren:

```powershell
python rebuild_results.py
python plot_gfz.py outputs --out ../../Abbildungen/gfz_at
```

Dieser zweite Weg führt keine erneute KDE aus. Die Originalanlieferung liegt unter `outputs/`, der Lauf aus Original-Excel unter `outputs/recalculated/`. Vergleichsdaten werden dadurch nicht überschrieben.

## Methode und Freigabe

- Primäre Referenz: Wien für Wien, Salzburg für jedes der acht übrigen Bundesländer.
- Neun Nutzungsgruppen und sieben Geschossklassen. `6 bis 10` und `6-10` werden vereinheitlicht, kleine/große Mehrfamilienhäuser zusammengeführt.
- BGF-gewichtete gaußsche KDE mit Scott-Bandbreite; GFZ-Raster 0–20, Schritt 0,1, Mitten 0,05–19,95. Normierung auf Summe eins; Ziel-BGF = statistische NGF / 0,8. Alternative Histogrammmethode im Code vorhanden, in dieser Sitzung keine Sensitivitätsrunde.
- Mindestumfang fünf Gebäude. Bei fehlender Referenz zuerst Wien mit gleicher Nutzung/Geschossklasse, danach die nächstgelegene Geschossklasse derselben Nutzung in der primären Region, zuletzt Wien. Nähe meint den Abstand in der geordneten Liste der sieben Klassen. Bei gleichem Abstand entscheidet die vorhandene lexikografische Sortierung. Jede Zuordnung steht im Audit.
- **Die bestehende Ersatzregel wurde vom Auftraggeber am 21.10.2026 ausdrücklich freigegeben.** Sie betrifft 1,696 % der modellierten BGF. Begründung für ihre Verwendung im Arbeitsstand: weitgehend vollständige primäre Flächenabdeckung, Erhalt der statistischen Ziel-Flächen und transparente Kennzeichnung der kleinen Ersatzanteile. Eine unabhängige Bestätigung der räumlichen Repräsentativität wird damit nicht behauptet.
- Der CLI-Standard `--fallback error` bleibt als strenger Diagnosemodus erhalten; der freigegebene Produktionsaufruf verwendet ausdrücklich `--fallback vienna`.
- `AT`-Zeilen dienen ausschließlich der Bilanzkontrolle. Acht historische Summenzeilen (`Alles`, `AT ohne Wien und Salzburg`) der Originaldatei werden explizit ausgeschlossen und im Prüfbericht gezählt. Unbekannte Regionen bleiben Fehler.

## Tabellenvertrag

CSV: UTF-8, kommasepariert, Dezimalpunkt. Flächen in m²; GFZ dimensionslos. Summierung über `BGF_m2`, niemals Mittelwertbildung über Flächen.

| Datei | Inhalt und Schlüssel |
|---|---|
| `gfz_distribution_by_province_use_storeys.csv` | Hauptdatensatz: Bundesland × GK × GWR_Nutzung × GFZ, mit BGF_m2 und cell_id |
| `allocation_audit.csv` | Je positive Zielkombination: NGF, Ziel-/Ergebnis-BGF, Differenz, Referenzregion/-klasse, Fallzahl, Ersatzstatus, Schätzmethode |
| `reference_coverage.csv` | Primäre Stichprobengröße und ausreichende Abdeckung je positiver Zielkombination |
| `gfz_distribution_by_province.csv` | BGF je Bundesland und GFZ |
| `gfz_distribution_austria_by_use.csv` | Nationale BGF je GFZ und Nutzung |
| `province_totals.csv` | Ziel-/Ergebnis-BGF und Differenz je Bundesland |
| `recalculated/validation.json` | Originaldatenlauf: Eingabe-Hashes, Parameter, ausgeschlossene Zeilen, Summen und Ersatzanteile |
| `validation_delivered.json` | Prüfung der übergebenen Ergebnisse, keine unabhängige Rohdatenvalidierung |
| `category_checks.csv`, `province_checks.csv` | Aus gelieferten GFZ-Bins neu summierte Flächen und Differenzen |
| `comparison.json` | Vergleich Originaldatenlauf mit übergebenen Ergebnissen |

Leere statistische Zielzellen werden nicht als positive Audit-/Verteilungszeilen exportiert. Fehlende statistische Werte behandelt der übernommene Import derzeit wie null; diese Einschränkung ist in `METHODENSTAND.md` dokumentiert. Fehlende Referenzgruppen mit positiver Ziel-Fläche werden niemals stillschweigend verworfen.

## Bericht und Grenzen

`plot_gfz.py` erzeugt drei PNGs unter `Abbildungen/gfz_at/`: nationale Nutzungsverteilung, normierte Landesverteilungen Wien/Salzburg und Modellabdeckung. Das Methodikschema steht als Mermaid direkt in `Kapitel/03-allokation.qmd`. Kurven zeigen GFZ bis 8, die Summen umfassen das gesamte Raster bis 20.

Phase 2 wird gemäß Auftrag nur dokumentiert. Inhaltliche Mängel und kleinere Abweichungen lösen keine weitere Arbeitsschleife aus. Befunde, die Zuordnung der falsch benannten Anlieferung und der Unterschied zur alten Implementierung stehen in `METHODENSTAND.md`. Die 2040-Allokation und bestehenden PEQ-Zielwerte werden durch diesen Modellstand nicht neu kalibriert.
