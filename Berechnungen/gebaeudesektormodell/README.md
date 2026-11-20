# Gebäudesektormodell: Konsolidierung und Analyse

## Einstieg
`Gebaeudesektormodell_Analyse.ipynb` erklärt und berechnet den gelieferten Stand Schritt für Schritt. Von oben nach unten ausführen. `SZENARIEN` wählt die tatsächlich berechneten Szenarien, `DETAILSZENARIO` die vertiefte Darstellung. Benötigt werden die Pakete aus `Gebaeudesektor_konsolidiert/requirements.txt` sowie matplotlib.

## Datenfluss
Statistik und Szenario-Verteilungen → kalibrierte Typenflächen → Simulationen → sektorale Summen und virtueller Zielabstand.

Die Flächenbildung verwendet den Rechenkern des Kollegen in `Gebaeudesektor_konsolidiert/modell`. Das Analyse-Notebook zeigt Eingaben, Herkunftskohorten, Kalibrierziele und bedingte Verteilungen. Es verbindet die Typenflächen mit dem Parquet und rekonstruiert Energiesummen unabhängig im Notebook.

Die mitgelieferten aufgelösten Verteilungen werden unverändert verwendet. Eine erneute Ableitung von Prioren und die Rekonstruktion von Flächenströmen bleiben Aufgaben der Notebooks `01_Szenario.ipynb` und `03_Flaechenstroeme.ipynb` im Modellpaket. Achtung: In der gelieferten Fassung von 01 sind Berechnung, Prior-Ableitung, Export und Ersetzen aktiviert, obwohl der Einleitungstext etwas anderes sagt. Vor Ausführung die Steuerzelle lesen.

## Bewertung
`PEI_balance` ist der virtuelle Zielabstand mit bereits enthaltenem Dichtefaktor; Zielerfüllung bei mindestens null. Alle Typen bleiben unverändert. Die erste Konsolidierung verwendet die simulierte GFZ (`FSI`). Das Dashboard ergänzt eine getrennte GFZ-Kohortenanalyse: unveränderter PEI_saldo_project gegenüber dem aus den Simulationsparametern berechneten Dichteziel. Diese Diagnose verändert keine Strombilanz.

## Ergebnisse
`outputs/konsolidierung/` enthält `typenflaechen.parquet`, `szenariosummen.csv`, `summenabgleich.csv`, `szenariovergleich.png` und `herkunft.json`. Vorhandene Ergebnisse des Kollegen und historische Analyseexporte werden nicht überschrieben. Das Notebook zeigt, ob die unabhängige Summenbildung mit dem Rechenkern übereinstimmt; frühere Exporte des Kollegen waren nicht mitgeliefert.

## Website und Dashboard
`Internes_Kalibrierungsdashboard.ipynb` verwendet die konsolidierten Typenflächen; Startansicht ist `Transition_2040`. Es bietet Szenarioauswahl, Typenfilter, Gruppenbeiträge, empirische GFZ-Kohorten je Geometrie, getrennte PV70/PV90-Zielanalyse, Szenarienvergleich und nationale Bedarf-/Deckungsgrafik. Die alte PEQ-Zielersetzung ist entfernt. Filter ändern keine Annahmen; die nationale PV-Allokation verändert nur die Top-down-Referenz.

Ausführen: `python Berechnungen/gebaeudesektormodell/execute_notebook.py --dashboard` aus dem Repository. Eigenständiges Dashboard: `outputs/dashboard/index.html`. Die interne Quarto-Navigation bindet das Notebook bereits ein. Die GFZ-Verteilung 2021 wird vorläufig auf die Szenarioflächen übertragen. NGF-Umschichtungen zwischen PV-Varianten bleiben ein künftiger Schritt im vorgeschalteten Notebook. Die übrigen Berichtskapitel sind noch zu aktualisieren. Eine Veröffentlichung wurde mit diesem Arbeitsschritt nicht durchgeführt.
