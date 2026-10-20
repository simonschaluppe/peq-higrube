# Codex-Brief: Siedlungs-Check 2027 – Proof of Concept

## 1. Ziel und Ausgangslage

Entwickle einen interaktiven Designprototyp der zukünftigen **klimaaktiv Siedlungs-Check-Plattform**.

Grundlage ist das bereitgestellte Dokument **„Pflichtenheft Siedlungs-Check 2027.pdf“**.

Der Proof of Concept soll die vier Module des Pflichtenhefts in einer gemeinsamen Website präsentieren:

1. Qualitätsprüfung Siedlungen und Quartiere
2. Plus-Energie
3. New European Bauhaus (NEB)
4. Wissensplattform

**Priorität hat die gemeinsame Plattform mit integrierten bestehenden PEQ-Inhalten und einem funktionierenden interaktiven Plus-Energie-Quick-Check.**

Die beiden anderen Qualitätsprüfungen werden zunächst nur als statische Designplatzhalter umgesetzt.

Es handelt sich um einen **Designprototyp, nicht um eine produktionsreife Bewertungsplattform**.

## 2. Repositories und neue Projektstruktur

Verwende drei eigenständige Repositories:

| Repository                           | Aufgabe                                                    |
| ------------------------------------ | ---------------------------------------------------------- |
| `simonschaluppe/siedlungs-check-poc` | Neues übergeordnetes Quarto-Website-Projekt                |
| `simonschaluppe/peq-higrube`         | Wissenschaftlicher Hintergrundbericht, Quarto Book         |
| `simonschaluppe/peexcel`             | Bestehende PEExcel-Website, Dokumentation und Nachweistool |

Bestehende Websites:

- [https://simonschaluppe.github.io/peq-higrube/](https://simonschaluppe.github.io/peq-higrube/)
- [https://simonschaluppe.github.io/peexcel/](https://simonschaluppe.github.io/peexcel/)
- PEExcel-Build: [https://github.com/simonschaluppe/peexcel/tree/gh-pages](https://github.com/simonschaluppe/peexcel/tree/gh-pages)

**Wichtig: PEExcel besitzt bereits eine vollständige Quarto-Pages-Website. Keine zweite Dokumentationswebsite erstellen.**

Untersuche zunächst, wo die PEExcel-Quelldateien gepflegt werden und wie der bestehende `gh-pages`-Build erzeugt wird. Die veröffentlichte Ausgabe ist nicht automatisch die Quelle.

Das neue Repository darf zunächst lokal angelegt werden. Ein Remote-Repository erst nach ausdrücklicher Zustimmung erstellen.

## 3. Arbeitsweise – verpflichtende Abstimmungen

**Arbeite nicht autonom über mehrere große Entwicklungsphasen hinweg.**

Vor jedem wesentlichen Arbeitsschritt kurz erläutern:

> Ich würde als Nächstes [konkrete Änderung] durchführen. Betroffen sind [Dateien/Repositories]. Dafür würde ich [Tools/Agenten] verwenden. Erwartetes Ergebnis: [Ergebnis]. Ist das so in Ordnung?

Warte auf meine Bestätigung.

### Wann ausdrücklich nachfragen?

- Vor dem Anlegen oder Verändern eines GitHub-Repositories.
- Vor Änderungen in `peq-higrube` oder `peexcel`.
- Vor größeren Änderungen an Quarto-Konfiguration, Navigation oder CSS.
- Vor der Verwendung zusätzlicher Agenten, Subagenten oder spezialisierter Tools, die eigenständig umfangreiche Änderungen vornehmen.
- Vor neuen technischen Abhängigkeiten oder einem Wechsel des vorgeschlagenen Stacks.
- Vor umfangreichen Refactorings und erneuten Überarbeitungsschleifen.
- Vor Commits, Pushes, Pull Requests und Veröffentlichungen.
- Bei fachlichen Unklarheiten im Pflichtenheft.
- Bevor zusätzliche Features außerhalb des vereinbarten Umfangs implementiert werden.

Gewöhnliche Lesezugriffe, kleine lokale Prüfungen und unmittelbar vereinbarte Tests benötigen keine wiederholte Rückfrage.

### Effizienter Umgang mit Agenten und Tokens

- Bevorzuge kurze, gezielte Arbeitsschritte.
- Keine parallelen Subagenten ohne Zustimmung.
- Keine umfassenden Codebase-Analysen, wenn wenige gezielte Dateiinspektionen ausreichen.
- Vor umfangreicher Recherche erst den konkreten Informationsbedarf benennen.
- Bestehende Komponenten wiederverwenden, bevor neue geschrieben werden.
- Nach einem erfolgreichen Arbeitsschritt kurz Ergebnis und offene Fragen nennen.
- Maximal eine gezielte Korrekturrunde ohne erneute Abstimmung.
- Keine zusätzlichen Verbesserungen nur deshalb durchführen, weil noch Zeit oder Tokens verfügbar sind.

**Die Kontrolle über Umfang, Aufwand und Reihenfolge bleibt bei mir.**

## 4. Zielarchitektur der Website

```text
Siedlungs-Check – gemeinsame Plattform
│
├── Startseite
│
├── Qualitätsprüfung
│   └── Siedlungs-Check [Platzhalter]
│
├── New European Bauhaus
│   └── NEB-Check [Platzhalter]
│
├── Plus-Energie
│   ├── PEQ-Standard
│   ├── Quick-Check [interaktiv]
│   ├── Hintergrundbericht [peq-higrube]
│   └── PEExcel [bestehende Pages]
│
└── Wissensplattform
    └── Dokumentenübersicht
```

### Einheitliches Plattformgefühl

Die Website soll über alle Bereiche hinweg dieselben Gestaltungselemente verwenden:

- Header und Hauptnavigation
- Typografie und Farben
- Seitenbreiten und Abstände
- Sidebar-Navigation
- Buttons und Formularfelder
- Tabellen, Abbildungen und Callouts
- Footer

Die Benutzer sollen den Übergang zwischen Plattform, Hintergrundbericht und PEExcel möglichst nicht als Wechsel zu einer anderen Website wahrnehmen.

**Keine reine Sammlung externer Links.**

Die eingebundenen Websites sollen idealerweise unter gemeinsamen Pfaden erreichbar sein:

```text
/qualitaetspruefung/
/neb/
/plusenergie/quickcheck/
/plusenergie/hintergrundbericht/
/plusenergie/peexcel/
/wissen/
```

### Technische Umsetzung

Bevorzugt:

- Quarto Website
- Bootstrap / SCSS / CSS
- JavaScript für Formulare
- Plotly.js für Diagramme
- GitHub Pages
- Reproduzierbarer statischer Build

Kein Backend, keine Datenbank, kein Login.

Prüfe zunächst eine einfache Integrationsstrategie:

1. Bestehende Quarto-Websites separat bauen beziehungsweise ihren vorhandenen Build verwenden.
2. Die HTML-Ausgaben in die Plattform unter den vorgesehenen Pfaden integrieren.
3. Gemeinsame Navigation und Gestaltung sicherstellen.
4. Relative Links, Assets, Suche und Quarto-Funktionen prüfen.

**Vermeide iframes**, sofern eine praktikable Integration der gerenderten Websites möglich ist.

Wenn die Integration tiefgreifende Änderungen an Quarto oder den bestehenden Projekten erfordern würde: **Stopp, Alternativen und Aufwand kurz darstellen und Rückfrage stellen.**

Keine fragilen manuellen Änderungen an generierten HTML-Dateien, die beim nächsten Build verloren gehen. Falls Anpassungen an der HTML-Ausgabe nötig sind, müssen sie reproduzierbar automatisiert sein.

Die bestehenden Projekte müssen weiterhin eigenständig publizierbar bleiben.

## 5. Priorität 1 – Plattform und PEQ-Integration

### 5.1 Startseite

Erstelle eine moderne, responsive Startseite mit vier Modulkacheln:

- Siedlungs-Check
- New European Bauhaus
- Plus-Energie
- Wissensplattform

Der Plus-Energie-Bereich soll bereits vollständig zugänglich sein.

Verwende kurze, ausdrücklich gekennzeichnete Platzhaltertexte:

> [PLATZHALTER: Allgemeine Einführung zum klimaaktiv Siedlungs-Check]

Keine umfangreichen selbst erfundenen Fach- oder Marketingtexte.

Orientiere die Gestaltung am bestehenden klimaaktiv-Auftritt und den Screenshots im Pflichtenheft.

### 5.2 PEQ-Standard

Erstelle eine kompakte Einstiegsseite mit:

- Vorstellung der drei PEQ-Qualitätsstufen
- Vorhandenen beziehungsweise vorläufigen Abbildungen
- Direktem Einstieg zum Quick-Check
- Verweis auf den Hintergrundbericht
- Verweis auf das vollständige PEExcel-Nachweistool

Die methodischen Inhalte dürfen nicht neu interpretiert werden. Verwende bestehende, geeignete Quellen und kennzeichne fehlende Inhalte.

### 5.3 Hintergrundbericht

Integriere die bestehende Quarto-Book-Ausgabe aus `peq-higrube`.

Erhalte:

- Kapitel und Unterkapitel
- Literatur und Querverweise
- Abbildungen
- Navigationsstruktur
- Eigenständige PDF-Ausgabe

Fachliche Inhalte bleiben unverändert.

### 5.4 PEExcel

Integriere die bereits bestehende PEExcel-Pages-Website vollständig.

Die vorhandenen Bereiche einschließlich Dokumentation, Tutorials, Downloads und Illustrationen sollen erhalten bleiben.

Keine erneute Implementierung der PEExcel-Dokumentation.

Erlaubt sind minimale Änderungen an Navigation, Styling und Quarto-Konfiguration, **aber erst nach Rückfrage**.

## 6. Priorität 2 – Interaktiver Plus-Energie-Quick-Check

Dies ist die zentrale interaktive Demonstration.

Orientiere dich am bestehenden Eingabeformular und an der gewünschten Primärenergie-Ergebnisdarstellung auf **Seite 4 des Pflichtenhefts**.

### 6.1 Beispiel-Eingabeformular

Mindestens:

- Standortgemeinde
- Bruttogrundfläche
- Grundstücksfläche, sofern für die Demo benötigt
- Nutzungsflächen für Wohnen, Büro und Schule
- Art des Vorhabens: Neubau / Sanierung
- Bauweise
- Wärmeversorgung
- Stromversorgung
- PV-Fläche beziehungsweise PV-Leistung

Stelle geeignete Dummy-Startwerte bereit.

Die Felder müssen tatsächlich bedienbar sein.

### 6.2 Beispielberechnung

Änderungen der Eingaben sollen unmittelbar Auswirkungen auf das Diagramm haben.

Beispielsweise:

- Mehr PV verbessert die dargestellte Erzeugungsbilanz.
- Mehr Nutzfläche erhöht den demonstrativen Energiebedarf.
- Eine andere Wärmeversorgung verändert den dargestellten Energiebedarf.
- Unterschiedliche Nutzungsanteile verändern die Bedarfszusammensetzung.

Verwende ausschließlich **einfache, dokumentierte Demo-Formeln**.

**Keine reale PEQ-Bewertung, keine erfundenen offiziellen Grenzwerte oder Kontextfaktoren.**

Die Demo-Berechnung soll in einer kleinen, klar isolierten JavaScript-Funktion liegen, damit sie später ersetzt werden kann.

### 6.3 Plotly-Ergebnisgrafik

Erstelle ein interaktives, vorzugsweise gestapeltes Säulendiagramm der Primärenergiebilanz.

Darzustellen sind:

- Energiebedarf
- Erneuerbare Energieaufbringung
- Kontextkomponenten als Dummy-Werte
- Gesamtbilanz / Saldo

Anforderungen:

- Dynamische Aktualisierung
- Hover-Informationen
- Legende
- Achsenbeschriftung und Einheiten
- Sinnvolle Farben
- Reset auf Beispielwerte
- Responsive Darstellung

**Sichtbarer Hinweis:**

> Demonstrationsberechnung mit vereinfachten Annahmen und Beispielwerten. Kein gültiger PEQ-Nachweis.

Verzichte auf eine verbindliche Aussage, ob das Projekt den klimaaktiv Standard erfüllt.

### 6.4 Weitere Seitenelemente

Ergänze passende Bild- und Callout-Platzhalter:

- Qualitätsstufen
- Schematische PEQ-Bilanz
- Energieversorgung und PV
- Vom Quick-Check zur vollständigen Nachweisführung

Fehlende Abbildungen dürfen keinen Build-Fehler verursachen.

## 7. Priorität 3 – Wissensplattform

Erstelle zunächst eine gestaltete Übersichtsseite mit beispielhaften Dokumentenkarten.

Beispielkategorien:

- Kriterienkataloge
- Handbücher
- Wissenschaftliche Grundlagen
- Nachweistools
- Praxisbeispiele

Verwende bestehende Dokumente aus den beiden Projekten, wo sinnvoll.

Jede Karte soll Titel, Beschreibung, Kategorie und Link enthalten.

Zusätzlich Platzhalter für zukünftige Dokumente.

**Nicht umsetzen:**

- Dokumentenupload
- Administrationsoberfläche mit echter Funktionalität
- Datenbank
- Benutzerkonten
- Berechtigungsverwaltung

Der künftige Upload durch das Programmmanagement darf lediglich als Designidee gekennzeichnet werden.

## 8. Siedlungs- und NEB-Check – vorerst statisch

### Siedlungs-Check

Zeige die sechs Hauptkategorien aus dem Pflichtenheft:

| Kategorie                          | Punkte |
| ---------------------------------- | -----: |
| A. Management                      |    155 |
| B. Kommunikation und Partizipation |    100 |
| C. Städtebau und Soziales          |    300 |
| D. Gebäude                         |    150 |
| E. Versorgung                      |    140 |
| F. Mobilität                       |    155 |

Ergänze einen statischen, klar gekennzeichneten Platzhalter für das spätere Formular **A. Management**.

### NEB-Check

Zeige die vier Hauptkategorien:

| Kategorie                     | Punkte |
| ----------------------------- | -----: |
| A. Prozessqualität            |    200 |
| B. Ökologische Nachhaltigkeit |    300 |
| C. Ästhetik                   |    350 |
| D. Inklusion                  |    150 |

Ergänze einen statischen Platzhalter für das spätere Formular **A. Prozessqualität**.

Die Screenshots und die Struktur des Pflichtenhefts dienen als gestalterische Orientierung.

**Noch keine echten Formulare, Berechnungen oder Plotly-Radardiagramme implementieren.**

Bekannte Unklarheiten der Kriterien und Punkte dokumentieren, nicht eigenständig berichtigen.

### Erst nach ausdrücklicher Abnahme

Nur wenn ich zustimme und noch ausreichend Entwicklungsbudget verfügbar ist:

- Siedlungs-Check: A. Management mit A.1–A.4 interaktiv
- NEB-Check: A. Prozessqualität mit A.1–A.4 interaktiv
- Je ein Plotly-Spinnendiagramm mit Demonstrationswerten

Der restliche Kriterienkatalog bleibt Platzhalter.

## 9. Verbindliche Arbeitsetappen

### Etappe 1 – Bestandsaufnahme

Untersuche gezielt:

- Quarto-Konfiguration von `peq-higrube`
- Bestehende PEExcel-Pages
- Herkunft und Build der PEExcel-Quelldateien
- Möglichkeiten der gemeinsamen Navigation und Veröffentlichung

Liefere eine kurze Bestandsaufnahme mit maximal zwei Architekturvarianten und einer Empfehlung.

**Stopp und Rückfrage.**

### Etappe 2 – Plattformgerüst

Nach Freigabe:

- Neues lokales Quarto-Projekt
- Hauptnavigation
- Startseite
- Gemeinsames Design
- Alle Modul-Seiten als Grundgerüst

Zeige eine funktionierende Vorschau.

**Stopp und Rückfrage.**

### Etappe 3 – Integration der PEQ-Websites

Nach Freigabe:

- Hintergrundbericht integrieren
- PEExcel-Pages integrieren
- Navigation und CSS angleichen
- Interne Links und Assets prüfen

Zeige die Integration im Browser.

**Stopp und Rückfrage.**

### Etappe 4 – Quick-Check

Nach Freigabe:

- Eingabeformular
- Dummy-Berechnung
- Dynamische Plotly-Ergebnisse
- Demo-Hinweise und Platzhalter

Teste die Interaktivität mit mehreren Eingabeänderungen.

**Stopp und Rückfrage.**

### Etappe 5 – Abschluss PoC

Nach Freigabe:

- Wissensplattform
- Statische Siedlungs- und NEB-Seiten
- Responsive Überprüfung
- Build- und Linktests
- README und Dokumentation

Bereite die GitHub-Pages-Veröffentlichung vor.

**Keine Veröffentlichung ohne meine Freigabe.**

## 10. Abnahmekriterien

Der PoC gilt als fertig, wenn:

- [ ] Die Plattform als Quarto-Website funktioniert.
- [ ] Alle vier Module erreichbar sind.
- [ ] Eine gemeinsame Navigation und Gestaltung vorhanden ist.
- [ ] `peq-higrube` als bestehender Bericht integriert ist.
- [ ] Die bestehende PEExcel-Website integriert ist.
- [ ] Beide Projekte eigenständig funktionsfähig bleiben.
- [ ] Der PEQ Quick-Check tatsächlich interaktiv ist.
- [ ] Plotly auf Eingabeänderungen reagiert.
- [ ] Demo-Werte klar gekennzeichnet sind.
- [ ] Die Wissensplattform Dokumentenkarten zeigt.
- [ ] Siedlungs- und NEB-Seiten als Platzhalter vorhanden sind.
- [ ] Desktop- und Mobilansicht funktionieren.
- [ ] Der Quarto-Build reproduzierbar ist.
- [ ] Die Dokumentation Build und Veröffentlichung erklärt.
- [ ] Keine fachlichen Inhalte oder Berechnungsmodelle unerlaubt geändert wurden.

## 11. Git und Dokumentation

- Arbeite mit eigenen Branches.
- Keine Force-Pushes.
- Keine Änderungen am Hauptbranch ohne Zustimmung.
- Keine Bearbeitung der Excel- oder Python-Berechnungsmodelle.
- Bestehende Komponenten und Abbildungen wiederverwenden.
- Erstelle eine kurze README mit Entwicklungs- und Buildanleitung.
- Dokumentiere Änderungen an jedem Repository getrennt.
- Formuliere technische Entscheidungen und Einschränkungen knapp und nachvollziehbar.

## 12. Erste Aktion

**Beginne ausschließlich mit Etappe 1: Bestandsaufnahme.**

Führe noch keine Änderungen an Dateien oder Repositories durch.

Prüfe insbesondere die vorhandenen Quarto-Pages von PEExcel und die Möglichkeit, diese zusammen mit dem Hintergrundbericht unter einer gemeinsamen Plattformadresse einzubinden.

Gib danach eine kurze Empfehlung mit Aufwand, Risiken und dem konkret vorgeschlagenen nächsten Schritt.

**Frage mich ausdrücklich, ob du mit Etappe 2 beginnen sollst.**
