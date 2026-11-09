# Gebäudesektormodell: zwei Arbeitsschritte

## 1. Modellierung – Kollege
`Gebaeudesektor_Modellierung.ipynb` ist eine bewusst noch nicht ausgefüllte Vorlage.
Hier werden später Statistik, Annahmen und Regeln der Flächenzuordnung erläutert.
Ergebnis ist die vollständige Flächentabelle in `data/Building-Sector_Pool_1.xlsx`.

## 2. Analyse
`Gebaeudesektormodell_Analyse.ipynb` liest ausschließlich:
- `data/scenarios.parquet`: aktuelle Simulationen (derzeit 43.200 Varianten).
- `data/Building-Sector_Pool_1.xlsx`: fertige Typenflächen und GFZ-Zuordnung.

Blatt `Strombed_estim`: `Archetype` entspricht exakt `scenario_name` im Parquet,
`Nationale BGF heute` und `Nationale BGF 2040` sind m² BGF. Bei mehrfach vorkommenden Szenarionamen zusätzlich
`batch`. Für nicht belegte Typen ausdrücklich 0 eintragen. Keine automatische Verteilung
fehlender Wetter-, Masse-, PV- oder Flexvarianten in der Analyse.
Optional bleiben Bestand/Neubau/Sanierung und Energetischer Standard erhalten.
`zuordnung_gfz!A:F` bleibt die geometrische Zuordnung.

**Die neue vollständige Flächentabelle folgt noch.** Die aktuelle 900-Zeilen-Tabelle ist
historisch; die Analyse stoppt deshalb verständlich vor der Berechnung. Es wird kein
Ersatzbestand erfunden. Alle fachlichen Rechenschritte stehen direkt im Notebook.

## Übergabe ans Dashboard
Die Analyse erzeugt `outputs/analyse/bestand.parquet` mit einer Zeile je Szenario und Typ:
`Szenario` (heute/2040), `batch`, `scenario_name`, `Archetype`, `BGF_m2`, Merkmale und Kennwerte.
Tabellen und Grafiken liegen ebenfalls unter `outputs/analyse/`.

Im `Internes_Kalibrierungsdashboard.ipynb` wählt `BESTAND` genau einen Bestand.
Die PEQ-Bewertungsflächen werden erst dort ausgewählt; keine erzwungene 20-%-Vorauswahl.
Der nationale Referenzfall ist 2040. Bei heute ist dies ausdrücklich eine Zukunftsreferenz.

## Ausführen
Notebooks von oben nach unten ausführen; Jupyter genügt. Optional dient
`execute_notebook.py` nur als technischer Starter (mit `--dashboard` für das Dashboard).
Es enthält keine fachliche Rechnung. `dashboard_template.html` und `dashboard_density.js`
sind die Browserdarstellung; `requirements.txt` nennt die Python-Abhängigkeiten.

## Historie und Aufräumen
`archiv/2026-11-05/` enthält den bisherigen gemischten Rechenweg einschließlich
vorläufiger Variantenregeln, Tests und Excel-Reinschrift. Er ist nicht Teil des aktiven
Ablaufs. `outputs/` außerhalb `analyse/` ist der historische publizierte Ergebnisstand.
Er bleibt erhalten, bis der neue Bestand vollständig berechnet und redaktionell übernommen ist.
Keine historische Ergebnisdatei als aktuelle Lieferung verwenden.

Veröffentlichung erst nach neuer Flächenlieferung und fachlicher Durchsicht.
