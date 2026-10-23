# Methodenstand und fachliche Befunde

Stand 23.10.2026, aktualisierte Quelle nach Ergänzung der GFZ-Anteile.

## Prüfergebnisse

Die Kennwert- und Simulationstabellen besitzen jeweils 900 eindeutige, übereinstimmende Schlüssel. Sämtliche übernommenen Kennwerte aus `Strombed_estim` stimmen mit den referenzierten gespeicherten Werten aus `Tabelle2` überein. Eine unabhängig wiederholte PEExcel-Simulation ist nicht Bestandteil dieses Modells. Fehlerwerte in anderen, nicht übernommenen Simulationsspalten werden dadurch nicht als repariert ausgegeben.

Die alte `reduced`-NGF summiert sich auf 696,615 Mio. m². Das neue Kennwertblatt nennt 1.112,341 Mio. m² BGF heute und 1.126,579 Mio. m² BGF 2040. Nach NGF/BGF = 0,8 sind das 889,873 bzw. 901,263 Mio. m² NGF. Die Differenz verschwindet also nicht durch korrekte Umrechnung. `flaechenvergleich_kern.csv` vergleicht zusätzlich Geometrie/Hülle/Heizung unter Zusammenfassung alter PV-/Flexibilitätsvarianten. Keine dieser Summen wird nachträglich auf eine andere nationale Gesamtsumme skaliert.

Alle 603 positiv gewichteten 2040-Archetypen haben eine GFZ-Verteilung. MFH_2G bleibt mangels Gewicht und Zuordnung ohne Erwartungswert. Die 70 Quellzeilen werden nach Prüfung identischer Zuordnungen für Ein-/Zweifamilienhäuser auf die neun Statistiknutzungen und sieben Geschossklassen abgebildet. Jede GFZ-Referenzfläche wird insgesamt genau einmal verteilt. Die nationale Typenfläche und jede positive Archetypenfläche bleiben in der exportierten GFZ-Matrix erhalten.

Die ursprünglich zwölf leeren Einzelzielanteile wurden vom Auftraggeber in der Quelle auf 100 % ergänzt. Am 23.10.2026 wurde zudem ausdrücklich bestätigt: Einzelziel = 100 %, zweites Ziel nur bei Aufteilung. Diese Frage ist **erledigt**, keine offene Annahme. Der neue Quellhash steht in README und validation.json.

Strombedarf = Netzbezug + PV-Direktverbrauch; PV-Erzeugung = Direktverbrauch + Export. Beide Saldoformulierungen sind identisch. Die sieben Stromanwendungen summieren sich auf den Bedarf; Heiz-/WW-Hilfsstrom wird nicht doppelt gezählt. Thermische Anwendungsgrößen summieren sich jeweils auf ihren Energieträger. PE-Import ist konsistent mit Netzstrom-PE plus den thermischen PE-Komponenten. Jahresenergie wird mit 3,6e−9 PJ/kWh umgerechnet.

## Inhaltliche Grenzen ohne weitere Optimierungsschleife

1. **Kein bereits klimaneutrales Szenario:** Im 2040-Pool bleiben 76,67 PJ/a Gas und 58,51 PJ/a Öl. Zudem sind ausschließlich PV30/noFlex-Varianten ausgewertet. Die −100,25 PJ/a Differenz des Stromsaldos zu UBA ist wesentlich und kein akzeptierter kleiner Rundungsrest. Die Ursache wird ausgewiesen, nicht durch eine freie Gutschrift geschlossen.
2. **Flächenentwicklung:** Der Nettozuwachs beträgt nur 14,238 Mio. m² BGF; gleichzeitig sind 320,354 Mio. m² als Neubauanteil klassifiziert. Ohne zeitliche Definition/Übergangsmatrix kann daraus keine Neubau- oder Abbruchrate abgeleitet werden. Die Sanierungsfläche beträgt 26,696 Mio. m², nicht 90 Typen mit pauschal 100 %.
3. **Jahre und Flächenbezüge:** „Heute“ ist in der Quelle nicht datiert. 2020 bleibt offen. BGF/NGF = 1/0,8 ist ein Referenzansatz, keine Messung aller Typen. Eine kleine Variation 0,75/0,80/0,85 ist dokumentiert; keine Optimierung.
4. **GFZ:** Verwendet wird das vollständige Raster 0,05–19,95 der vorhandenen Hochrechnung 2021. Der räumliche Transfer auf 2040 ist eine Annahme. Energievarianten derselben Geometrie erhalten dieselbe bedingte Verteilung. Der Erwartungswert wird über die Funktion je Bin gebildet, nicht durch Einsetzen der mittleren GFZ.
5. **Dichtefunktion:** Schneider et al. (2023), Gl. 7/Tab. 5, ist der historische Referenzstand. Tabelle und Gleichung weisen gemischte EE-/PE-Einheiten aus. Die verwendete elektrische Tabellenlesart (30,4; 26,4; 0,15; 62, BGF-Bezug) wird ausdrücklich als vorläufig geführt. Keine Übernahme der bereits PE-gewichteten Einzelsimulations-Kontextwerte als EE und keine neue endgültige Kalibrierung.
6. **Primärenergie:** Gelieferte PEI erlauben eine nachvollziehbare Import-/Exportaggregation. Effektive Netzfaktoren sind typabhängig; die normative Faktorversion und das Bezugsjahr fehlen. Die Reinschrift bereitet neue belegte Faktorensätze vor, wendet aber keine erfundenen Jahreswerte an.
7. **PEQ und Sanierung:** Das Standardfeld ist leer und die Anspruchsberechtigung nicht geklärt. Die erzeugte Dichtematrix ist eine Kalibriereingabe. Die Dichtewerte werden nicht unterschiedslos als Guthaben sämtlicher Flächen addiert. Der PEQ-Anteil bleibt leer, statt aus Presetnamen oder Strompositivität abgeleitet zu werden.
8. **Systemgrenze:** Bruttostrom enthält lokalen PV-Verbrauch; externe Endenergielieferung verwendet nur Netzbezug. Umweltwärme ist nicht als zusätzliche Lieferung in den Trägerkennwerten enthalten. Elektrische Saldendifferenzen ersetzen keinen Vergleich aller Energieträger und keine THG-Bilanz.

## Abnahme des ersten Entwurfs

Versionierte Quelle und Reinschrift, direkt ausführbares wissenschaftliches Notebook, Flächenaudit, Strom-/Endenergie-/PE-Aggregation, GFZ-Erwartungswerte, exportierte Typologie-Dichte-Matrix und QMD-Integration sind vorhanden. Offen bleiben die fachlichen Fortschreibungsparameter, keine versteckte numerische Optimierung. Die endgültige PEQ-Neukalibrierung ist ein eigener Folgeschritt.
