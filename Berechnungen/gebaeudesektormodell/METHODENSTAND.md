# Methodenstand – 19.11.2026

Die erste Konsolidierung steht in `Gebaeudesektormodell_Analyse.ipynb`. Grundlage ist das vom Kollegen gelieferte konsolidierte Paket mit 43.200 simulierten Typen und vier registrierten Flächenszenarien: Bestand 2024, Transition 2040, Wachstum und ambitioniert.

- Die Szenarioauswahl steuert die Berechnung. Die gelieferten aufgelösten Verteilungen werden verwendet; ihre Prior-Ableitung wird nicht neu durchgeführt.
- Das Notebook dokumentiert Statistikzuordnung, Qualitätskalibrierung, bedingte Verteilungen und Flächenbildung. Die bestehenden Modellmodule werden wiederverwendet.
- Kennwerte werden über vollständige Typenschlüssel verbunden und mit NGF gewichtet. Summen werden unabhängig vom Rechenkern aggregiert und für PV sowie PE-Projektsaldo abgeglichen.
- Zentrale Bewertungsgröße ist `PEI_balance`, der Abstand zum virtuellen Ziel einschließlich Dichtefaktor. Kein zusätzlicher GFZ-Zielabzug und keine vorab ausgewählte PED-Teilmenge.
- Das Dashboard verteilt Typenflächen für eine separate Analyse auf die empirische GFZ-Verteilung 2021 je Geometrie. Es vergleicht den unveränderten PEI_saldo_project mit dem negativen Dichtefaktor der Kohorte, insbesondere für PV70/PV90. Parameter stammen aus dem Parquet; Zielwerte und Projektsalden beziehen sich auf NGF. Die Strombilanz bleibt unverändert.
- Flächenkalibrierung ist keine empirische Validierung der Energieperformance. Die wissenschaftliche Aufbereitung benötigt Quellenbegründung, Unsicherheits- und Sensitivitätsanalyse sowie eine dokumentierte Übertragung der GFZ-Verteilung.
- Das interne Dashboard verwendet nun die konsolidierten Daten mit Transition 2040 als Startansicht. Es zeigt PEI_balance, Szenario-/Typenvergleiche und den nationalen Stromvergleich; die alte Zielersetzung ist entfernt. Die nationale Stromgrafik mit Bedarf/Deckung, MIV-Allokation und zentraler Restdeckung ist wiederhergestellt. Die übrigen Website-Kapitel bleiben offen.

---

## Historischer Stand vom 09.11.2026 (überholt)



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

## Nächster Kalibrierungsschritt
NGF zwischen PV-Varianten bei sonst gleichen Typmerkmalen umverteilen, Gesamtfläche erhalten und als eigenes Szenario neu auswerten. Die Anteilsänderung gehört zunächst ins vorgeschaltete Notebook; sie ist noch kein Dashboard-Regler. Ziel ist ein nachvollziehbarer Abgleich von Bottom-up-Strombilanz und Top-down-Allokation.
