# Gebäudesektormodell Österreich 2040

Erster wissenschaftlicher Modellstand vom 23.10.2026. Das ausführbare Notebook ist das Modell: Gewichtung, nationale Energieaggregation, GFZ-Verknüpfung, Dichte-Erwartungswerte, PE-Bilanz und Bilanzkontrollen stehen unmittelbar in seinen Zellen. `utils.py` enthält ausschließlich Import-, Hash- und Tabellenformatierungshilfen.

## Daten und Dateien

- `data/Building-Sector_Pool_1.xlsx`: unveränderte Kopie der aktualisierten Lieferung `Redaktion/sektormodell/Building-Sector_Pool 1.xlsx`. SHA256: `b032c1bd7148b0bdac8541196a1eaa7fc58f538f87912e1f2714af88ac80a7cd`. Die Originalformeln bleiben erhalten.
- `daten_gebauedesektor.xlsx`: editierbare Reinschrift der gespeicherten Kennwerte, Anwendungen, GFZ-Zuordnungen und Parameter. Sie ersetzt nicht die Originalsimulation. Ein einziges Eingabearbeitsbuch, keine konkurrierenden Gebaeudedaten-Versionen.
- `Gebaeudesektormodell.ipynb`: wissenschaftlicher Quarto-Anhang, ausgeführt und mit Ergebnissen gespeichert.
- `outputs/`: CSV-Ergebnisse, komprimierte Typologie-GFZ-Matrix, vier Abbildungen und `validation.json` mit Eingabe-Hashes. Quarto-Includes werden zusätzlich nach `Kapitel/_generated/gebaeude-*.qmd` geschrieben.

`Strombed_estim` enthält 900 eindeutige Archetypen; 603 haben positive BGF 2040. `Tabelle2` enthält die passenden Anwendungen und die NGF-Einheiten. `zuordnung_gfz!A:F` liefert 70 Nutzungs-/Geschosszeilen. Die rechts daneben liegenden Hilfsbereiche sind keine zusätzlichen Zuordnungen. `reduced` wird ausschließlich als abweichender älterer Flächenstand geprüft. `save` ist kein zweiter additiver Datensatz.

## Ausführen

Im Repository-Stamm, getestet mit Python 3.13:

```powershell
python -m pip install -r Berechnungen/gebaeudesektormodell/requirements.txt
python Berechnungen/gebaeudesektormodell/execute_notebook.py
quarto render --to html
```

Alternativ Kernel neu starten und alle Notebook-Zellen ausführen. Bei eingeschränktem Windows-Tempverzeichnis `TEMP`, `TMP` und `IPYTHONDIR` auf beschreibbare lokale Ordner setzen. Der Runner speichert das Notebook erst nach erfolgreichem Abschluss. Das Notebook arbeitet mit versionierten Dateien und braucht keine Dateien aus `Redaktion/` oder persönliche OneDrive-Pfade.

Änderungen an Eingaben erfolgen in `daten_gebauedesektor.xlsx`; anschließend das Notebook neu ausführen. Tabellen und Grafiken aktualisieren sich. Die interpretierenden Zahlen im QMD-Fließtext beschreiben den dokumentierten Lieferstand und sind bei einem Szenariowechsel redaktionell abzugleichen. Die Originalquelle wird weiterhin separat gegen ihre gespeicherten Simulationsergebnisse geprüft.

Die technische Reinschrift kann über `prepare_inputs.py` und den Artifact-Tool-Builder `build_inputs.mjs` erzeugt werden. Dies ist ein bewusster Neuimport und überschreibt die Reinschrift; **nicht nach manuellen Ergänzungen ohne Sicherung ausführen**. `prepare_inputs.py` lehnt eine abweichende bereits vorhandene Quellkopie ab, damit ein neuer Lieferstand ausdrücklich versioniert wird. Es führt keine wissenschaftliche Aggregation aus. Der Builder benötigt die bereitgestellte Bibliothek `@oai/artifact-tool`, die JSON-Datei `.local/building-inputs.json` und den Ordner `.local/building-artifacts/` für Prüfbilder. Alle eigentlichen Modellrechnungen bleiben im Notebook.

## Ergebnisse des Lieferstands

| Größe 2040 | Ergebnis |
|---|---:|
| BGF | 1.126,579 Mio. m² |
| NGF bei NGF/BGF = 0,8 | 901,263 Mio. m² |
| Strombedarf einschließlich PV-Direktverbrauch | 137,493 PJ/a |
| PV-Erzeugung | 78,245 PJ/a |
| Betrieblicher Stromsaldo | −59,248 PJ/a |
| Gas / Öl | 76,673 / 58,512 PJ/a |
| PE-Export minus PE-Import, gelieferter Bewertungsstand | −409,364 PJ PE/a |
| Abstand zum vorläufigen elektrischen Top-down-Beispiel | −100,248 PJ/a |

Die MIV-Zuordnung wird beim Vergleich auf beiden Seiten identisch angesetzt und ändert die Differenz nicht. Virtuelle Dichtewerte sind keine physische Erzeugung. Ein negativer Stromsaldo ist ebenso wenig eine vollständige THG-Bilanz wie ein positiver Saldo ein Nachweis der PEQ-Konformität.

## Bestätigte Regeln und vorläufige Annahmen

- **Bestätigt am 23.10.2026:** Eine GFZ-Zielklasse bedeutet 100 %. Die zweite Zielspalte dient nur der Aufteilung. Die aktualisierte Quelle enthält alle Anteile explizit. Die sechs 50/50-Zeilen bleiben erhalten; zusammengefasste Statistiknutzungen werden nicht doppelt gezählt.
- NGF/BGF = 0,8 aus der bestehenden GFZ-Analyse bleibt eine vorläufige einheitliche Modellannahme.
- Die bedingten GFZ-Verteilungen 2021 werden als räumliches Muster der 2040-Typen verwendet; keine neue Dichteprognose.
- Die historische elektrische Dichte-Referenzkurve verwendet 30,4, 26,4, dx = 0,15 und cutoff = 62. Die gemischte EE-/PE-Beschriftung der Publikation ist dokumentiert; keine endgültige Neukalibrierung.
- Gelieferte PEI werden ohne Kontextgutschriften aggregiert. Faktorversion/Bezugsjahr bleiben zu bestätigen. Es werden keine neuen Faktoren oder Absenkpfade erfunden.

## Eingaben für die Fortschreibung

„Heute“ benötigt ein Bezugsjahr; BGF 2020 ist als leere Spalte vorbereitet. Ebenso sind PEQ-Anteile, Quellen/Unsicherheiten und jahresbezogene PE-Faktoren ergänzbar. Wichtig sind außerdem die Definition der Bestands-/Neubau-/Sanierungsanteile, der Abbau fossiler Versorgung 2040 und Kennwerte für alternative PV-/Flexibilitätsvarianten. Siehe `METHODENSTAND.md` und den Notebook-Ausblick. Keine Optimierungsschleife und keine automatische Anpassung an UBA.
