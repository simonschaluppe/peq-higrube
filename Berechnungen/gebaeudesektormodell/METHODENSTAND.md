# Methodenstand – 09.11.2026

## Aktueller Ablauf
Modellierung (noch leere Vorlage des Kollegen) → vollständige Typenflächen in Excel →
Analyse mit lokalem scenarios.parquet → bestand.parquet für heute/2040 → virtuelle
PEQ-Auswahl im Kalibrierungsdashboard.

Die lokale Typologie enthält 43.200 Simulationen. Die vollständige Flächentabelle steht
noch aus. Die derzeitige Excel enthält 900 alte PV30/noFlex-Schlüssel ohne Wetter und Masse.
Damit liegt noch kein neu berechneter Bestand nach diesem Ablauf vor.

## Fachliche Abgrenzung
- Keine Flächenallokationsregeln und kein 20-%-PEQ-Ziel in der Analyse.
- Keine synthetischen PV0-Varianten: ausschließlich gelieferte Simulationen.
- Flächen in BGF, Kennwerte je NGF; Flächenbezug im Notebook sichtbar prüfen.
- Heute bleibt ohne bestätigtes Kalenderjahr; keine Umbenennung in 2020.
- Strom-/Endenergie sowie PE-Import/Export/Projektsaldo sind die betriebliche Betrachtung.
- GFZ-/PEQ-Kontext ist eine getrennte virtuelle Bewertung; keine zusätzliche reale Erzeugung.
- Nationale Referenz 2040 und heutiger Bestand sind nicht zeitgleich.

## Prüfungen und Nachvollziehbarkeit
Wenige Eingangsprüfungen: eindeutige und vollständige Typenzuordnung, Flächenerhalt und
Einheiten. Keine separate Testsuite für die Flächenregeln, da diese hier nicht mehr
implementiert sind. Wissenschaftliche Herleitung und Zwischenresultate stehen im Notebook.

## Historischer Stand
Die am 05.11. veröffentlichte Rechnung bleibt in outputs und archiv/2026-11-05 erhalten.
Ihre Testgewichte und Ergebnisse sind keine aktuelle Flächenlieferung. Neue Ergebnisse
werden getrennt unter outputs/analyse abgelegt. Die Website wurde durch dieses Refactoring
noch nicht verändert.
