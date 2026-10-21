# Sektorale Szenarien und Allokationsstruktur

Stand 21.10.2026. Die geltende Streicher-basierte Kalibrierung 2023 bleibt erhalten. Transition 2040 ist eine laufende Rekalibrierung. Dieses Modul stellt Daten, Kontrollen und eine parametrische Sankey-Struktur bereit; es berechnet keine neue Mobilitätsgutschrift.

## Reproduktion

Vom Repository-Wurzelverzeichnis, Python 3 (nur Standardbibliothek):

```powershell
python Berechnungen/check_scenarios.py
python -m unittest Berechnungen.sektorenmodell.test_model -v
python Berechnungen/sektorenmodell/generate.py
python Berechnungen/sektorenmodell/generate.py --check
quarto render --to html
```

CSV-Masterdaten liegen unter `Daten/sektorenmodell/`. Sie stammen aus dem Handoff `Redaktion/transitionsszenarien/Daten/`; keine UBA-Werte wurden nachträglich aus anderen Tabellen ergänzt oder verändert. Präzisiert wurden ausschließlich Fundstellen und Hinweise. Der Generator erstellt aus derselben Basis die Quarto-Stromtabellen, den separaten Endenergievergleich, den Prüfbericht und `sankey_structure.json`. `--check` meldet veraltete generierte Dateien als Fehler. Das vorhandene `Berechnungen/allokation.py` bleibt unverändert.

Die Endenergie aller Energieträger ist ein separater Sektorausweis in `Daten/sektorenmodell/endenergie_vergleich.md`. Sie wird entsprechend Handoff nicht als zusätzliche Allokationstabelle im Quarto-Kapitel geführt. Der Entwurf wurde in Kapitel 3 integriert; kein zweites Kapitel wurde angelegt.

## Datenvertrag

- Eindeutiger Schlüssel: `scenario`, `year`, `metric`. PJ/a; `energy_basis` unterscheidet Endenergie, Strombedarf und Stromerzeugung/Nettoimporte. Die beiden elektrischen Kategorien können als PJ_el verglichen werden, Endenergie darf nicht hinzuaddiert werden.
- `source_id` verweist auf `sources.csv` mit BibKey und URL; `source_location` enthält Tabelle und gedruckte Seite. Bei lokalen Originalen ist der Fundort im Methodenstand dokumentiert.
- `generation_published_total`, `electricity_demand_published_total` und `eev_published_total` bleiben eigenständige publizierte Werte. Sie werden nicht durch Summen der gerundeten Teilwerte ersetzt.
- `scenario_validation.json` enthält Komponenten-minus-Gesamt-Reste und die Bilanz Erzeugung + Nettoimport − Bedarf. Der Checker validiert nicht nur Toleranzen, sondern auch den mitgelieferten dokumentierten Rest je Szenario. Neue Abweichungen erfordern eine bewusste Aktualisierung der Dokumentation.
- Nettoimporte dürfen negativ sein; Sankey-Ausgaben bilden sie dann als positiven Exportfluss ab. Fehlend ist nicht null. Striche bei zwei Technologien in WEM/WAM 2023 wurden bereits im Handoff als null normiert; diese Konvention ist kenntlich gemacht.
- `legacy_operationalisierung_2023.csv` und `legacy_gutschriften_nutzungen.csv` behalten ihre ursprünglichen Einheiten. Prozentwerte der Zielfahrten sind gerundet und summieren sich zu 101 %, sie werden nicht nachträglich normiert. Die publizierten Gutschriften werden nicht aus den gerundeten Budgets neu berechnet.

## Parametrisierung und Sankey

`allocation_parameters.json` führt für alle sechs Szenarien dieselben Parameter. Standardmäßig sind sämtliche normativen Parameter `null`. Ein expliziter Anteil muss zwischen 0 und 1 liegen und eine `parameter_source` besitzen. Null bedeutet offen, null Prozent ist dagegen ein gesetzter Wert. Das wird getestet.

Beispiel einer **nicht freigegebenen Parameterstudie**: `central_generation_share.pv = 0` bedeutet 100 % dezentrale PV. Sie lässt die physischen Erzeugungs-/Bedarfsdaten unverändert und erzeugt ausschließlich entsprechend bezeichnete Allokationslinks. Sie schließt weder die übrige Zuordnung noch berechnet sie einen Mobilitätsbonus. Der Fall wird im Test geprüft und nicht in der Standardkonfiguration gespeichert.

`sankey_structure.json` enthält gemeinsame `nodes`, szenariospezifische `links`, Quellen, Horizonte, Status und getrennte Ebenen:

1. `physical` / `electricity`: publizierte Stromerzeugung, Nettohandel, sektorale Bedarfe, Energiebranche, Transportverluste und Umwandlung. `plotly_physical` ist eine unmittelbar verwendbare Plotly-Sankey-Trace-Struktur ausschließlich dieser Ebene. Keine künstlichen Ausgleichsflüsse. Die ausgewiesenen Residuen müssen in einer späteren Anzeige sichtbar bleiben.
2. `normative_allocation` / `electricity`: zentrale/dezentrale Anteile und MIV-/übriger-Verkehr-Anteile können erst mit expliziten Parametern berechnet werden. Priorisierte Bedarfsdeckung ist vorbereitet, aber bleibt offen. Ein Pool enthält nicht automatisch nur erneuerbare oder berechtigte Erzeugung.
3. `virtual_credit` / `primary_energy`: Legacy-Budget 10,68 TWh PE/a entspricht 38,448 PJ PE/a (reine Einheitenumrechnung). Kein Link verbindet es mit dem elektrischen Pool. Bei Transition und WEM/WAM bleibt die neue Gutschrift null/unbestimmt.

Prioritätsregeln, Importberechtigung und PE-Faktoren sind benannte offene Schnittstellen, noch keine implementierten Bewertungsregeln. Nicht-null-Werte für diese Felder werden abgewiesen statt stillschweigend ignoriert. Auch nach Setzen einzelner Anteile bleibt `normative_allocation_complete=false`.

Für Legacy fehlen vollständig vergleichbare nationale Stromtabellen: `physical_data_complete=false`, keine erfundenen physischen Breiten. Die belegten historischen Teilwerte sind als Metadaten verfügbar. Alle Energiearten der Folie einschließlich Wärme zusammenzurechnen ist ausdrücklich ausgeschlossen.

Im Bericht wird zunächst das statische, nicht maßstäbliche SVG-Schema verwendet. Ein interaktives Plotly-Dropdown ist optional und wird in dieser Iteration nicht in das Buch eingebunden. Das SVG funktioniert ohne JS auch für weitere Ausgabeformate; PDF/Word wurden hier nicht gebaut.

Quellenprüfung, Widersprüche und offene Entscheidungen: [METHODENSTAND.md](METHODENSTAND.md).
