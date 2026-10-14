# Quellenübersicht und Befund der Sichtung

**Internes Quellenregister:** Die folgenden Abgleiche und Konflikte dienen der Redaktion. Sie werden nicht in den Bericht übertragen. Eigene Publikationen belegen die direkt dargestellte Methodik; Übernahmen und Abbildungsplatzhalter sind zulässig. Maßgeblich ist die Perspektive im [Redaktionsmemo](arbeitsplan.md).

Stand: 14.10.2026. Alle neun Dateien in `Primärquellen/` wurden textuell erschlossen und nach ihrer Funktion gesichtet. Vertieft gelesen wurden die methodischen Kernabschnitte der Dissertation, die Originalbeiträge 2023 und 2025 in Annex B, die Broschüre sowie die widersprüchlichen Stellen in Handbuch und Präsentationen. Das ist eine redaktionelle Bestandsaufnahme, noch keine vollständige Prüfung sämtlicher Formeln, Tabellen, Abbildungen und Softwareparameter. Die mehrhundertseitigen Anhänge sind gezielt ausgewertet, nicht vollständig fachlich auditiert.

PDF-Seiten bezeichnen hier den Zähler der Datei; gedruckte Seiten sind ausdrücklich als solche bezeichnet. Bei DOCX werden Abschnitte statt ungesicherter Seitenzahlen genannt. Lokale Textauszüge liegen ausschließlich unter `.local/quellen/`.

## Maßgeblicher Stand nach fachlicher Rückmeldung

Festlegung vom 14.10.2026: Die Dissertation und ihre zugehörigen Publikationen bilden den inhaltlichen Letztstand. Andere Unterlagen, insbesondere der alte Leitfaden und überholte Veröffentlichungen, sind nachrangig. Die unten protokollierten Abweichungen bleiben als Befund der ersten Sichtung erhalten; ihre Bearbeitungsentscheidungen stehen in [Entscheidungen und offene Punkte](offene-punkte.md).

Die Rückmeldung klärt insbesondere die 50-jährige Bewertung bis 2075 bei angenommener Dekarbonisierung ab 2050 sowie die davon unabhängige Bedeutung von GWP100. Sie bestätigt die Sanierungsgutschrift als normative Setzung ohne quantitative Absicherung. PEExcel 1.13.1 ist als künftige Implementierungsreferenz gewählt, aber noch nicht als fertiger Parameterstand geprüft. Die Broschüre bleibt eine Kommunikationsquelle; bei inhaltlichen Widersprüchen führt der oben genannte wissenschaftliche Letztstand.

## Quellen nach Funktion

| Lokale Datei unter `Primärquellen/` | Verwendung und zentrale Fundorte | Einschränkung |
|---|---|---|
| `PhD Thesis.pdf` | Kap. 3.1–3.2, gedruckte S. 43–60 / PDF 65–82: Definition als Gestaltungsaufgabe, normative Allokation, Dichte, Mobilität, THG. Kap. 3.3, S. 61–68 / PDF 83–90: Modell und Grenzen. Kap. 3.4–3.5: Anwendungen und kommunale Perspektive. Kap. 4.2: Forschungsbedarf. | Übergreifende wissenschaftliche Struktur; einzelne Implementierungsbehauptungen brauchen Versionsabgleich. |
| `PhD Annexes.pdf` | Annex A, PDF 1–76: Variablen/Formeln, ausdrücklich Schema 1.11.4. Annex B.1, Artikel 2023: besonders PDF 88–93. Annex B.11, Artikel 2025: besonders PDF 332–334, 353–357. | Historisches Schema, kein aktueller Preset-Katalog. Abgedruckte Originalartikel direkt zitieren. |
| `Broschüre korr.pdf` | Gedruckte S. 8–14 / PDF 10–16: Stufen, Gewichtung, Kontextfaktoren. S. 15–19 / PDF 17–21: RUGInnovation. | Autoritative Kommunikationsquelle für die Stufen; keine vollständige quantitative Herleitung. Freigabestatus dieser lokalen Korrekturfassung noch festhalten. |
| `Handbuch Nachweisführung PEQ-Tool_1-2026.pdf` | PDF 4–6: Nachweisprozess. PDF 69–70: THG-Abgrenzung. Kapitel zu Eingaben und Ergebnissen: Nachvollziehbarkeit der Bedienung. | PDF 5 nennt 100 Jahre; später Budget bis 2050 und teils jährliche Einheit. Keine führende Quelle für die Budgetherleitung. |
| `Hintergrundbericht klimaaktiv Plus-Energie-Quartiere.docx` | Gliederung „Nationales Allokationsmodell“ / „Quartier: Systemgrenzen und Bilanzierung“; offene Fragen; 32 extrahierte Tabellen mit vielen Presets. | Stark skizzenhaft, gemischte Vorlagendaten 2024/2026, Platzhalter. Preset-Tabellen teilweise leer oder auffällig zugeordnet; nicht ungeprüft übernehmen. |
| `Leitfaden PEQ Definition und Operationalisierung_StandJuni2023.docx` | „Methodik“, „Kontext“, Zielwertableitung und Beispiele: ausführliche Vorgeschichte und deutschsprachiges Argumentationsmaterial. | Historische Alpha/Beta/Omega-Terminologie, damaliger Budgetansatz; ausdrücklicher Weitergabevorbehalt auf dem Titelblatt. |
| `PEQ-Standard im Überblick_6_2026.pptx` | Folien 20–26: Allokation, Kontext, THG. 28–35: Beispiele. 37: „Auf dem Weg“. | Gemischte Zeitstände. Folien 25–26: 2025–2075 versus „LZ-Bilanz bis 2050“. Aussagen zu Prozess und Praxis nicht als freigegebene Regeln behandeln. |
| `PEQ Nachweistool 2026-07-05.pptx` | Folien 4–7: Zweck und Modellvereinfachung. 19–20: physische Mobilitätsflüsse versus Zielverkehrsbilanz. 22–24: THG. | Titelfolie datiert 26.5.2026 trotz Dateiname Juli; Abbildungsquelle mit genauem Dateistand dokumentieren. |
| `PEQ Nachweistool 2026-10-14.pdf` | PDF 4: Zeithorizonte; PDF 7: zwei thermische Zonen; spätere Folien: Eingabe, Audit und Toolstruktur. | Aktuellstes lokales Präsentationsdatum, aber keine benannte freigegebene Toolversion. PDF 33 enthält einen Audit-Screenshot mit `#FEHLER`; daraus keine Defaults ableiten. |

## Befunde, die die Redaktion steuern

**Die Verteilung der Anforderungen ist eine normative Entscheidung auf wissenschaftlicher Grundlage.** Der Artikel 2023 erklärt die Dichteparameter ausdrücklich als Stellgrößen der Lastenverteilung; die Kurve ist kein technisches Potenzialmaximum (Artikel S. 12–14, Annex-PDF 89–91). Die nationale Kalibrierung setzt Anteile verschiedener Gebäudetypen und Sanierungsqualitäten voraus. Der Bericht muss diese Annahmen zeigen, statt allein „wissenschaftlich hergeleitet“ zu schreiben.

**320 ist ein bedingter Grenzwert.** Artikel 2025, §2.3 und Tabelle 2 (S. 6–7, Annex-PDF 332–333): L1 = 72, L2 = 196, L3 = 320 kg CO₂e/m² BGF. L3 setzt 1 t CO₂e pro Person und Jahr an natürlichen Senken voraus; der Anteil Gebäude plus MIV beträgt 50 %. Diese L-Werte sind Budgetvarianten innerhalb der THG-Bewertung und dürfen nicht mit den drei PEQ-Qualitätsstufen verwechselt werden. Tabelle A1 (S. 30, Annex-PDF 356) dokumentiert die Ausgangsgrößen. Die rechnerische Reproduktion steht aus.

**Auch die wissenschaftliche Hauptquelle enthält redaktionelle Spannungen.** Artikel 2025 verwendet in §2.4 den Zeitraum 2025–2075; im Schluss auf S. 28 steht hingegen „budget to 2050“ und „next 25 years“. §2.3 nennt 2050 als Bezugsjahr der Flächenstatistik, Tabelle A1 nennt 2040. Fachliche Klarstellung vom 14.10.2026: Ableitung und Flächenprognose beziehen sich auf 2040; 2050 ist der vorsorglich spätere Dekarbonisierungszeitpunkt. Die unterschiedliche Funktion der Zeitangaben wird im Kapitel erläutert; eine spätere Fortschreibung der Flächenprognose ist damit nicht vorweggenommen.

**Die Bilanz hat definierte Ausschlüsse.** Artikel 2025, Tabelle 3 und §2.4.1 (S. 7–9, Annex-PDF 333–335): u. a. B7 ausgeschlossen, A4/A5 abhängig von Datenverfügbarkeit; PV-Herstellung auf nationaler Sektorebene behandelt. „Alle Emissionen“ wäre zu weitgehend. §4.2 benennt die Abhängigkeit vom konsistenten nationalen Allokationsmodell ausdrücklich.

**Planungseignung ist keine Messvalidierung.** Thesis §3.3.1 beschreibt ein vereinfachtes Modell für Variantenvergleiche; §4.2 benennt Betriebsmonitoring und Abgleich mit Messdaten als weitere Arbeit. Kommunale Allokation wird in §3.5.1 als zusätzliche Perspektive beschrieben, ausdrücklich noch nicht als formaler Kontextfaktor der Deklaration implementiert.

**Beispieldaten brauchen einen gemeinsamen Stand.** RUGInnovation hat in der Broschüre 223 kg CO₂e/m² BGF (S. 19), in der Überblickspräsentation 228,6 (Folie 33). Broschüre S. 15 und Präsentation Folie 28 nennen unterschiedliche Baujahre; die Thesis-Tabelle 5 nennt GFZ 1,14, die Broschüre 2,1. Das können unterschiedliche Abgrenzungen oder Szenarien sein. Nicht aus verschiedenen Dokumenten zu einem scheinbar einheitlichen Beispiel zusammensetzen.

## Bestehende Berichtstexte

Kurzfassung, Startseite und Kapitel 1–3 wurden nach der ersten Durchsicht redaktionell überarbeitet. Kapitel 3 erklärt die eigene Methodik direkt; Rundungsabgleiche und Quellenkonflikte sind im internen Reviewvermerk gesichert. Kapitel 2 nennt die Zeit- und Senkenannahmen und verweist auf die Budgetherleitung. Der Sprachfehler in der Zielgruppenbeschreibung ist korrigiert. Weitere Straffung der Wiederholungen erfolgt mit dem Ausbau der Methodenkapitel.

## Ergänzende öffentliche Orientierung

Die aktuelle [klimaaktiv-Publikationsseite](https://www.klimaaktiv.at/publikationen/plus-energie-quartiere) bestätigt die Rolle eines allgemeinverständlichen Einstiegs. Die [Seite zu Siedlungen und Quartieren](https://www.klimaaktiv.at/gemeinden/energie-bau/siedlungen-quartiere) bietet bereits kommunale Arbeitsmittel. Der neue Bericht sollte daran anschließen und seine quantitative Vertiefung klar ausweisen. Sichtung: 14.10.2026; keine umfassende Recherche zu Rechtslage oder Förderinstrumenten.

Die MDPI-Webseiten waren bei direktem Abruf nicht erreichbar (HTTP 429); die oben genannten Artikel wurden aus den lokal vorhandenen Originalabdrücken in Annex B gelesen. Der aktuelle PEExcel-Repository-Stand wurde in dieser Bestandsaufnahme nicht verifiziert.
