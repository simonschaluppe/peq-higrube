# Hintergrundbericht: Klimaneutrale Plus-Energie-Quartiere

Arbeitsrepository für die wissenschaftlichen Grundlagen des österreichischen klimaaktiv Standards. Leitfrage: **Was heißt klimaneutral bauen – und wie viel ist genug?**

Der Bericht erklärt die nationale Herleitung der Anforderungen und ihre Anwendung auf Quartiere. Er ergänzt Broschüre und Tool-Handbuch. Die vorhandenen Texte sind Entwürfe, keine freigegebene Nachweisgrundlage.

## Wo anfangen?

- **Nächste inhaltliche Entscheidungen:** [Redaktioneller Vorschlag](Redaktion/arbeitsplan.md).
- **Offene methodische Fragen:** [Offene Punkte](Redaktion/offene-punkte.md).
- **Quellen und belastbare Fundorte:** [Quellenübersicht](Redaktion/quellenuebersicht.md).
- **Projektauftrag:** [Projektbrief/Handoff](Redaktion/projektbrief-handoff.qmd). Der übernommene Brief liegt als `.qmd`, nicht als `.md` vor; Dateinamen und Versionsangaben darin sind teilweise historisch.

## Struktur und Bearbeitung

| Ort | Inhalt |
|---|---|
| `index.qmd` | Einstieg und Arbeitsstand |
| `executive_summary.qmd` | Bestehende Kurzfassung |
| `Kapitel/` | Führende Berichtstexte; derzeit Kapitel 1 und 2 |
| `references.bib`, `references.qmd` | Zentrale Bibliografie und Literaturverzeichnis |
| `Abbildungen/` | Künftig freigegebene Abbildungen mit Quellen und Alternativtexten |
| `Redaktion/` | Projektbrief, Quellenprüfung, Arbeitsplan und Entscheidungen |
| `Redaktion/Primärquellen/` | Unveränderte Ausgangsdokumente |
| `_book/` | Generierte Ausgabe; nicht versionieren |
| `.local/` | Lokale Extrakte, Sicherungen und Prüfdateien; nicht versionieren |

Textänderungen erfolgen ausschließlich in den `.qmd`-Quellen. Rückmeldungen aus PDF oder Word werden dort eingearbeitet. Neue Kapitel erst nach inhaltlicher Bearbeitung in `_quarto.yml` aufnehmen. Kein Gerüst voller leerer Kapitel veröffentlichen.

## Vorschau und Ausgabe

Voraussetzung: Quarto (lokal vorgefunden: 1.10.19). Befehle **im Ordner mit dieser README und `_quarto.yml`** ausführen; im vorliegenden Workspace liegt dieser eine Ebene unter dem geöffneten Ordner.

```powershell
quarto preview --to html
quarto render --to html
```

Der Einstieg liegt anschließend unter `_book/index.html`. HTML enthält Navigation und Volltextsuche. Die Kapitelreihenfolge ist in `_quarto.yml` ausdrücklich festgelegt. Redaktion und Primärquellen sind vom Kopieren als Ressourcen ausgeschlossen.

Für eine PDF-Arbeitsfassung ist LuaLaTeX mit den benötigten Paketen erforderlich:

```powershell
quarto render --to pdf
```

Die PDF-Konfiguration ist eine Arbeitsgrundlage, kein Ministeriums-Layout und kein Nachweis von PDF/UA-Konformität. Den tatsächlich geprüften Buildstand dokumentiert der [Arbeitsplan](Redaktion/arbeitsplan.md#technischer-stand).

## Quellen- und Versionsregeln

1. Jede tragende Zahl und Gleichung bekommt einen passenden Beleg mit Seite, Tabelle oder Gleichung. Ein allgemeines Literaturverzeichnis ersetzt diese Einzelbelege nicht.
2. Wissenschaftliche Herleitung, normative Festlegung, Modellannahme und Softwareimplementierung ausdrücklich unterscheiden.
3. Szenariojahr, Bilanzzeitraum und Softwareversion getrennt angeben. Historische Parameter nicht stillschweigend aktualisieren.
4. Toolwerte erst nach Festlegung einer konkreten Version beziehungsweise eines Commits übernehmen. Annex A dokumentiert Schema 1.11.4; das ist kein Nachweis des aktuellen Tools.
5. Unklarheiten in `Redaktion/offene-punkte.md` erfassen. Bestehende Prüfvermerke erst nach fachlicher Klärung auflösen.

Die Primärquellen bleiben als Arbeitsmaterial im Repository. Daraus folgt keine Freigabe zur Weiterveröffentlichung: Insbesondere der Leitfaden von 2023 trägt einen Weitergabevorbehalt. Vor einer öffentlichen Bereitstellung des gesamten Repositories ist dessen Quellenbestand gesondert zu prüfen. Für die spätere Berichtspublikation ausschließlich die geprüfte Ausgabe bereitstellen.

## Review mit wenig Aufwand

Pro Arbeitspaket gibt es einen kurzen Entscheidungsvermerk mit Empfehlung, Beleg, Alternative und Auswirkung. Fachliches Review konzentriert sich auf Zielwerte, Grenzen, Interpretation und Freigaben. Rechtschreibung, Quarto, Literaturformat und Verweise werden redaktionell erledigt. Maximal drei fachliche Entscheidungen pro Runde; keine parallelen Fassungen in Word und Quarto.
