# Hintergrundbericht: Klimaneutrale Plus-Energie-Quartiere

Arbeitsrepository für die wissenschaftlichen Grundlagen des österreichischen klimaaktiv Standards. Leitfrage: **Was heißt klimaneutral bauen – und wie viel ist genug?**

Der Bericht erklärt die nationale Herleitung der Anforderungen und ihre Anwendung auf Quartiere. Er ergänzt Broschüre und Tool-Handbuch. Die vorhandenen Texte sind Entwürfe, keine freigegebene Nachweisgrundlage.

## Wo anfangen?

- **Nächste inhaltliche Entscheidungen:** [Internes Redaktionsmemo](Redaktion/arbeitsplan.md).
- **Neue Kapitel:** [Bilanzregeln bis Weiterentwicklung](Kapitel/04-bilanzregeln.qmd), mit [kapitelweisem Konsistenz- und Planungsreview](Redaktion/review-kapitel-04-08.md).
- **Methodischer Einstieg:** [Kapitel 3 – nationale Allokation](Kapitel/03-allokation.qmd), mit [dokumentiertem Reviewstand](Redaktion/review-kapitel-03.md).
- **Fachliche Festlegungen und ausstehende Zuarbeiten:** [Entscheidungen und offene Punkte](Redaktion/offene-punkte.md).
- **Quellen und belastbare Fundorte:** [Quellenübersicht](Redaktion/quellenuebersicht.md).
- **Projektauftrag:** [Projektbrief/Handoff](Redaktion/projektbrief-handoff.qmd). Der übernommene Brief liegt als `.qmd`, nicht als `.md` vor; Dateinamen und Versionsangaben darin sind teilweise historisch.

## Struktur und Bearbeitung

| Ort | Inhalt |
|---|---|
| `index.qmd` | Einstieg und Arbeitsstand |
| `executive_summary.qmd` | Bestehende Kurzfassung |
| `Kapitel/` | Führende Berichtstexte; Kapitel 1 bis 8 und Methodenanhang |
| `Berechnungen/` | Reproduzierbare Rechnungen; unabhängig vom Text-Build |
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

Für die Veröffentlichung auf GitHub Pages zuerst ausschließlich HTML rendern und nur bei erfolgreichem Rendern veröffentlichen:

```powershell
quarto render --to html
if ($LASTEXITCODE -eq 0) {
    quarto publish gh-pages --no-render
}
```

So benötigt die Website keine PDF- oder Word-Werkzeuge. `Redaktion/` bleibt lokal erhalten und wird von Git ignoriert; die oben verlinkten Redaktionsunterlagen sind nur lokal verfügbar.

Für eine PDF-Arbeitsfassung sind LuaLaTeX mit den benötigten Paketen und `rsvg-convert` für SVG-Abbildungen erforderlich:

```powershell
quarto render --to pdf
```

Die PDF-Konfiguration ist eine Arbeitsgrundlage, kein Ministeriums-Layout und kein Nachweis von PDF/UA-Konformität. Den tatsächlich geprüften Buildstand dokumentiert der [Arbeitsplan](Redaktion/arbeitsplan.md#technischer-stand).

## Redaktionelle Perspektive

Der Bericht ist die zusammenhängende Primärdarstellung unserer Methodik. Eigene Publikationen werden als Belege zitiert. Rückrechnungen, Rundungsdifferenzen und Quellenkonflikte bleiben in `Redaktion/`; fachliche Annahmen und Grenzen stehen im Bericht. Tabellen und Grafiken können mit Beleg übernommen oder zunächst als Platzhalter definiert werden. Vollständige Reproduktion ist keine Voraussetzung für die Textfassung.

## Quellen- und Versionsregeln

Inhaltlich führen die Dissertation und die zugehörigen Publikationen im dokumentierten Letztstand. Ältere Leitfäden, Handbücher, Broschüren und Präsentationen sind nachrangig; die [fachlichen Entscheidungen vom 14.10.2026](Redaktion/offene-punkte.md) ergänzen die Quellenlage.

1. Jede tragende Zahl und Gleichung bekommt einen passenden Beleg mit Seite, Tabelle oder Gleichung. Ein allgemeines Literaturverzeichnis ersetzt diese Einzelbelege nicht.
2. Wissenschaftliche Herleitung, normative Festlegung, Modellannahme und Softwareimplementierung ausdrücklich unterscheiden.
3. Szenariojahr, Bilanzzeitraum und Softwareversion getrennt angeben. Historische Parameter nicht stillschweigend aktualisieren.
4. Geplante Implementierungsreferenz ist PEExcel **1.13.1**, derzeit in Arbeit. Presets und Defaults erst nach fachlicher Freigabe mit Commit, Arbeitsmappe und Freigabestand übernehmen. Annex A dokumentiert Schema 1.11.4 und ersetzt diese Tabellen nicht.
5. Unklarheiten in `Redaktion/offene-punkte.md` erfassen. Bestehende Prüfvermerke erst nach fachlicher Klärung auflösen.

Publikationsform: druckfähiger Bericht als PDF und navigierbare Online-Fassung. Rechte liegen laut Auftraggeber bei der FH Technikum Wien, Forschungsteam Climate-fit Buildings and Districts. Autor:innenliste und Impressum werden vervollständigt. Die Primärquellen bleiben Arbeitsmaterial; veröffentlicht wird die geprüfte Berichtsausgabe, nicht automatisch der gesamte Quellenbestand.

## Zweigeteilter Anhang

- [Annahmen der Zielwertberechnung](Kapitel/anhang-methodenstand.qmd): nationale Energiebilanzen, Flächen- und Dichteallokation, Mobilitätsbudget, THG-Budget und Absenkpfade.
- [Annahmen der Quartiersbilanzierung](Kapitel/anhang-quartiersbilanzierung.qmd): Nutzungsbedarfe, Beleuchtung, innere Wärmegewinne, Mobilität und gemeinsame Modellbedingungen.

Beide Teile sind als Berichtstext nach außen formuliert. Fehlende Angaben sind direkt markiert; Projektwerte werden von vorläufigen Referenzwerten unterschieden. Das vollständige Presetinventar bleibt als Quellenarbeit unter `Redaktion/Archiv/preset-vollinventar/` erhalten und wird nicht veröffentlicht. Die frühere einzelne HTML-Prüffassung ist überholt; maßgeblich ist die neu gerenderte Buchfassung.

## Review mit wenig Aufwand

Pro Arbeitspaket gibt es einen kurzen Entscheidungsvermerk mit Empfehlung, Beleg, Alternative und Auswirkung. Fachliches Review konzentriert sich auf Zielwerte, Grenzen, Interpretation und Freigaben. Rechtschreibung, Quarto, Literaturformat und Verweise werden redaktionell erledigt. Maximal drei fachliche Entscheidungen pro Runde; keine parallelen Fassungen in Word und Quarto.
