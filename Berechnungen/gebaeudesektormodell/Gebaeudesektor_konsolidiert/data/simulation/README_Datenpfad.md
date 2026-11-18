# Simulationsdaten

`scenarios.parquet` enthält die Simulationsergebnisse je Gebäudetyp und wird nur für die energetische Auswertung (`ENERGIE_BERECHNEN=True` in `01_Szenario.ipynb`) benötigt. Die Flächenanalyse funktioniert ohne diese Datei.

Der Pfad steht zentral in `config/projekt.json` unter `dateien.parquet`:

- Standard: `data/simulation/scenarios.parquet` (relativ zum Projektordner)
- Große Dateien dürfen außerhalb des Projekts liegen; dann dort einen absoluten Pfad eintragen. Im Modellcode stehen keine Pfade.

Nachweis: Für das Parquet wird aus Zeitgründen kein Inhaltshash gebildet. Die Zustands-ID verwendet Dateiname und Dateigröße; das Laufprotokoll dokumentiert zusätzlich den Zeitstempel und kennzeichnet den Nachweis als „schwach“. Lesen erfordert `pyarrow`.
