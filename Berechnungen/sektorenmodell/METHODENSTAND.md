# Quellenprüfung und offene Entscheidungen

## Ergänzung 23.10.2026: quantitative sektorale Allokation

Der aktuelle Teilauftrag umfasst ausschließlich `allokation.ipynb` als ausführbaren wissenschaftlichen Anhang und die QMD-Ergebnisdarstellung. Die Gebäudesektormodellierung wartet auf die aktualisierte Typologie-Excel. Die unten dokumentierten älteren offenen Schnittstellen bleiben als Historie erhalten; das neue Notebook rechnet nun explizite, vorläufige Zuordnungsfälle, ohne die früheren normativen JSON-Parameter oder die historischen PE-Gutschriften zu überschreiben.

Die vollständige Rechnung steht im Notebook, nicht in einem Hilfsmodul. Der Basisfall verwendet 0 % andere PV, 80 % MIV und 20 % ÖPNV. Diese Werte sind redaktionelle Rechenannahmen. Für Wasserstoff-Rückverstromung werden 0 % und 100 % Budgetfähigkeit verglichen; Geothermie/sonstige wird vorläufig voll zugeordnet. Der zentrale Pool trägt Industrie, Landwirtschaft, Energiebranche, Umwandlung, Verluste und Nettoexport sowie ÖPNV/übrigen Verkehr. Die Priorität ist zu bestätigen. Andere PV und nicht budgetfähige Erzeugung bleiben eigene Restpositionen. Keine zusätzliche Anrechnung von Elektrolyse als Erzeugung, keine doppelte Verwendung des MIV-Budgets.

Ergebnisse im Basisfall: 303 PJ budgetfähige nicht-PV-Erzeugung, 261 PJ feste prioritäre Positionen, 18 PJ ÖPNV, 24 PJ MIV-Budget, −7 PJ Gebäudesaldo einschließlich MIV. Nach voller H2-Anrechnung: 28 PJ MIV-Budget und −3 PJ Gebäudesaldo. Der Bilanzrest bleibt −2 PJ gegenüber den publizierten Bedarfskomponenten. Vollständige Primärenergie- und nutzungsbezogene Gutschriftenrechnung bleibt mangels freigegebener Faktoren und Ziel-Flächen offen. Die Tabelle im Hauptkapitel ist ein generiertes Ergebnis; die interpretierenden Textzahlen beschreiben explizit den dokumentierten Basisfall.

Stand: 21.10.2026. Auftrag: Handoff `Redaktion/transitionsszenarien`, erweitert durch die direkte Anweisung, keine unbelegte Zuordnung oder neue Gutschrift zu erfinden. Die Formulierung im Handoff, MIV/ÖV pro rata zu skalieren, wurde daher als offener Vorschlag und nicht als genehmigte Parameterfestlegung behandelt.

## Geprüfte Quellen

- REP-0880: [Original](https://www.umweltbundesamt.at/fileadmin/site/publikationen/rep0880.pdf), Tabelle A S. 7, Tabelle 15 S. 60, Tabelle 16 S. 63. Modellgeneration/Titelseite 2023; das online vorliegende PDF trägt im Impressum © 2024. Auf ausdrücklichen redaktionellen Wunsch wird die Ausgabe mit 2024 geführt und der abweichende Titelblattstand ausdrücklich genannt; der BibTeX-Schlüssel bleibt stabil.
- Streicher et al. (2010): *Energieautarkie für Österreich 2050*, Feasibility Study Endbericht, Dezember 2010, Projekt B068644. Vom Nutzer bereitgestellte Primärquelle aus Zotero, Zusammenfassung S. iii–v geprüft. Jährliche Nettoautarkie und Wachstum der Energiedienstleistungen sind von Klimaneutralität und Bevölkerungswachstum zu unterscheiden. Schneider (2020) bleibt der Beleg der nachfolgenden lokalen Operationalisierung.

## Redaktionelle Erweiterung: Grafik, Notebook und getrennte Zielwertseiten

Ausgangsjahr ist auf ausdrückliche Auswahl des Nutzers **2020**. Zieljahr und Vergleichsdaten bleiben 2040. Quelltabellen werden nicht durch interaktive Varianten verändert. Die aktuelle Operationalisierung 2026 umfasst Datenmodell, Berechnungen und Visualisierung; eine neue normative Mobilitätsgutschrift bleibt offen. Das Notebook stellt Anteile für zentrale/dezentrale PV, elektrischen MIV/ÖV/übrigen Verkehr sowie zusätzliche Stromminderungen gegenüber 2040 bereit. Die Primärenergiegutschriften 2023 bleiben unverändert.

Die Methodik folgt der Reihenfolge allgemeines Prinzip → sektorales Energiezielbild → Kontextfaktoren Dichte, Mobilität und Sanierung → Zielwert THG → Systemgrenze des Quartiers. `03-allokation.qmd` enthält das sektorale Zielbild; die frühere Kontextseite bleibt unter ihrer URL als Dichteseite erhalten. Gemeinsame Kontextgleichungen stehen einmalig in `03-methodik.qmd`. Die THG-Seite enthält Flächenstände, eine Struktur für zusätzliche Bestandsdaten und die bestehende Abbildung der THG-Absenkpfade. Numerische PE-Zeitreihen und vollständige THG-Stützwerte fehlen noch und werden nicht interpoliert. Fachfragen und Antworten stehen in `Redaktion/transitionsszenarien/Review_Zielwerte_2026.qmd`, erreichbar über das lokale Quarto-Profil `redaktion`. Quellendifferenzen und inhaltliche Grenzen bleiben dokumentiert; keine weitere GFZ-Phase-2-Schleife.
- REP-0882: [Hauptbericht](https://www.umweltbundesamt.at/fileadmin/site/publikationen/rep0882.pdf), Tabelle 12 S. 39; [barrierefreie Zusammenfassung](https://www.umweltbundesamt.at/fileadmin/site/publikationen/rep0882_bfz.pdf), Tabelle B S. 5 und D S. 8.
- REP-0995: [Original](https://www.umweltbundesamt.at/fileadmin/site/publikationen/rep0995.pdf), Tabelle B S. 10, E S. 12, 18 S. 62 und 19 S. 64. Die übergebenen Daten stammen für die Erzeugung aus Tabelle E, nicht aus Tabelle 19. Die vormals mehrdeutige Angabe „D/E bzw. 19“ wurde präzisiert, ohne Zahlen auszutauschen. Tabelle D ist in TWh und wurde nicht zur Rückrechnung der gerundeten PJ-Angaben verwendet.
- Schneider, Zelger, Klauda (2020): bereitgestelltes Original `Redaktion/transitionsszenarien/Referenzen/Schneider2020_original.pdf`, zehn Seiten. Auswahl/Anpassung von Streicher in Abschnitt 3.1, Allokation zentral/dezentral und historische Pro-Kopf-Gutschrift in Abschnitt 3.1.4 und 5.1. Diese Pro-Kopf-Endenergiegutschrift wird nicht mit der PE-Flächengutschrift von 2023 gleichgesetzt.
- Schneider et al. (2023), [DOI](https://doi.org/10.3390/buildings13051210): Originalartikel als Bestandteil der lokal vorhandenen `Redaktion/Primärquellen/PhD Thesis.pdf` geprüft (PDF-Seiten 228–231, Originalseiten 13–16). Tabellen 6, 8 und 9 bestätigen 114,8/137,6 PJ, 6,30 TWh Strom, 0,36 TWh Biomasse, 10,68 TWh PE sowie alle vier Mobilitätsgutschriften. Der direkte Verlagsabruf war zeitweise blockiert; die lokale Primärfassung wurde verwendet.
- [Öffentlicher klimaaktiv-Leitfaden 2026](https://www.klimaaktiv.at/publikationen/plus-energie-quartiere) und verlinktes PDF, S. 10: Mobilitätskontextfaktor bestätigt. Das bereitgestellte Handbuch vom 19.01.2026, Version 1.08, S. 66 bestätigt nutzungsabhängige virtuelle Deckung und den Wohnwert 14,11. Eine vollständige Prüfung der gegenwärtig produktiven Toolversion oder sämtlicher interner Presets liegt damit nicht vor. Die vier publizierten Werte werden gemäß Auftrag bewahrt.
- Folienreferenz und eingebettetes Rasterbild im bestehenden `nationales_bilanzmodell.svg` visuell kontrolliert. Die Folie mischt Strom, Solarthermie, Umweltwärme und Abwärme und zeigt eine schematische 60/40-Aufteilung. Das ist kein datengetreues UBA-Strom-Sankey. Die Bildunterschrift wurde präzisiert und die fehlerhafte Breitenangabe korrigiert. Die historische Grafik wurde nicht neu gezeichnet.

Original-PDFs und Extrakte bleiben in ignorierten lokalen Verzeichnissen, nicht im PR. Der neue Quellenindex und die BibTeX-Einträge sind versioniert. EEV-Tabellen bleiben im Datenmodell und werden nicht als Stromallokation im Quarto-Kapitel ausgegeben.

## Befunde und Abweichungen

| Befund | Umgang |
|---|---|
| WEM 2025 EEV: Komponenten 1.002 PJ, publiziert 1.003 PJ | Publizierte 1.003 PJ bewahrt; −1 PJ ausgewiesen. |
| Transition Strombedarf: Komponenten 452 PJ, publiziert 450 PJ | +2 PJ offen ausgewiesen; keine erfundene Verlustposition. |
| WEM/WAM 2025 Strombilanz: +1/+2 PJ | Bilanzreste ausgewiesen, nicht nachträglich geschlossen. |
| REP-0995 Tabelle E versus 19 | Für WEM 2040: Wasser 167/170, PV 53/51, Wind 65/64 PJ. Für WAM: fossil 15/14, Biomasse 21/20, Gesamterzeugung 406/403 PJ. Das ist ein interner Quellenwiderspruch, nicht pauschal durch Rundung erklärt. Tabelle E bleibt die gelieferte Masterbasis. |
| Transition REP-0880 versus REP-0882-Zusammenfassung | 457 PJ Erzeugung und −7 PJ Nettoimport in REP-0880 gegenüber 456/−6 PJ in der Zusammenfassung. Für Transition wird ausschließlich REP-0880 verwendet; Ursache nicht abschließend geklärt. |
| Kategorie Geothermie | Bei Transition ausdrücklich Geothermie. Vergleichsquellen verwenden „Umgebungswärme etc.“. Gemeinsamer technischer Schlüssel bleibt, die breitere Quellbedeutung wird erklärt. |
| Striche WEM/WAM 2023 | Geothermie/sonstige und Wasserstoff im Handoff auf null normiert. Als Konvention dokumentiert; keine zusätzliche beobachtete Genauigkeit behauptet. |
| Legacy-Daten unvollständig gegenüber UBA-Abgrenzung | Keine nationalen Totale erfunden; Legacy bleibt separates historisches Referenzmodell mit dokumentierten Teilwerten. |
| Gerundete Legacy-Anteile und Budgets | Anteile der Zielfahrten ergeben 101 %, Teilflächen 547,7 statt publiziert 547,8 Mio. m². Gutschriften nicht aus gerundeten Zwischenwerten neu berechnet. |

## Offene normative Entscheidungen

1. Definition zentral/dezentral je Technologie, Gebäude-PV versus Freifläche, Anlagenmaßstab und räumliche Grenze. Der PV-Fall 100 % dezentral ist eine mögliche Parameterstudie, kein genehmigter Default.
2. Trennung MIV/ÖV/Güterverkehr und Abgrenzung sonstiger Verkehrsbedarfe; keine Übertragung historischer Anteile ohne explizite Festlegung.
3. Reihenfolge und Deckungsquote der priorisierten Sektoren. Berechtigung von Erzeugung, fossilen Resten, Biomasse, importiertem Strom und Wasserstoff-Rückverstromung für einen erneuerbaren Pool.
4. Import-/Exportkonvention, Speicher- und Konversionsverluste, Zeitauflösung und nachvollziehbare PE-Faktoren. Ein elektrischer Saldo ist noch kein PE-Budget.
5. Zuordnung des neuen Budgets zu Nutzungen und konsistenter Flächenbezug. Kein pro-rata Skalieren des Legacy-Budgets.
6. Auflösung des Widerspruchs zwischen Tabelle E und Tabelle 19 vor einer verbindlichen Kalibrierung. Die vorliegende Fassung eignet sich zum Vergleich, nicht zur Freigabe neuer Anforderungen.

## Abnahme dieser Iteration

Der Checker prüft Tabellenstruktur, Vollständigkeit, eindeutige Schlüssel, Einheiten/Energiegrößen, Quellenangaben, dokumentierte Bilanzreste und unveränderte Legacy-Gutschriften. Vier erfolgreiche Tests sichern fehlende Parameter, getrennte PE-/Stromebenen, Exportrichtung sowie den ausdrücklich gesetzten PV-Fall. Generierte Tabellen und Sankey-Struktur wurden mit `generate.py --check` gegen die CSV-Masterdaten geprüft. Auch die bestehende `allokation.py` läuft unverändert erfolgreich. Der vollständige Quarto-HTML-Build aller 15 Kapitel ist erfolgreich; neue Tabellen und Abbildungs-IDs erscheinen im HTML jeweils genau einmal. Eine zusätzliche Browseransicht der lokalen Datei war durch die Browser-URL-Richtlinie gesperrt; daraus wird keine erfolgte visuelle HTML-Prüfung abgeleitet. Kein Merge, kein Deployment, keine neue Gutschrift.
