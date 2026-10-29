# Sektorale Szenarien und Allokationsstruktur

Stand 29.10.2026. Die historische PE-Kalibrierung 2023 bleibt erhalten; die elektrische Transition-Allokation verwendet die dokumentierten Modellannahmen vom 29.10.2026.

## Wissenschaftlicher Allokationsanhang

`allokation.ipynb` enthält die fachliche Rechnung. Freiflächen-PV gehört zu den zentralen Großkraftwerken; 4 PJ H₂ und 1 PJ fossiler Strom sind vollständig enthalten. Der Nettoexport wird im Modell mit 5 statt 7 PJ/a angesetzt. Die CSV-Quelldaten bleiben unverändert; Quellrest −2 und Modellrest 0 werden separat dokumentiert.

Bei 80 % MIV und 0 % Freiflächen-PV ergeben sich 31 PJ/a zentrale Restdeckung und 0 PJ/a Top-Down-Saldo Gebäude + MIV: 108 + 72 = 149 + 31. Die gesamte Restdeckung wird ohne MIV-Obergrenze zugeordnet. Negative zentrale Reste werden als Fehlbetrag sichtbar und durch Gebäude-PV ausgeglichen. PV- und Verkehrsanteile bleiben Modellvarianten.

```powershell
python -m Berechnungen.sektorenmodell.execute_notebook --notebook allokation
python -m unittest Berechnungen.sektorenmodell.test_allocation -v
quarto render --to html --no-execute
```

`outputs/allokation/allokation.json` verwendet Schema 2: `central_credit_pj` ersetzt das bisherige gekappte `miv_budget_pj`. `available_credit_pj` und `central_shortfall_pj` sind die nichtnegativen Anzeigegrößen. Alte Anrechnungsparameter werden abgewiesen; H₂-/Fossilanrechnung ist fest. Annahmen, Quellen-Hashes und beide Bilanzreste werden exportiert. Die abhängigen Gebäude-Notebooks sind anschließend neu auszuführen. Ein heutiger PE-Faktorensatz und eine neue nutzungsbezogene PE-Gutschrift bleiben offen.

Die folgenden Abschnitte beschreiben die ursprüngliche Quellaufbereitung und deren separate Szenario-/Sankey-Schnittstellen; deren Quellenwerte bleiben unverändert.

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

Im Bericht ergänzt das interaktive Plotly-Sankey das schematische Zuordnungsbild. Standard ist die ausdrücklich gewählte Ausgangsbilanz 2020; 2023 bleibt als mit Quellenproblemen gekennzeichneter Vergleich auswählbar. Strom und Endenergie bleiben getrennte Flussbilder. Eine neue PE-Gutschrift wird nicht berechnet. PNG dient als Fallback für weitere Ausgabeformate; PDF/Word wurden hier nicht gebaut.

## Reproduzierbare Grafik und Notebook

```powershell
python -m unittest Berechnungen.sektorenmodell.test_model Berechnungen.sektorenmodell.test_sankey
python Berechnungen/check_scenarios.py
python -m Berechnungen.sektorenmodell.sankey --static
python -m Berechnungen.sektorenmodell.mobility_sankey --static
python -m Berechnungen.sektorenmodell.execute_notebook
quarto render --to html
quarto preview --render html --profile redaktion --no-browser
```

`sankey.py` benötigt Plotly; PNG zusätzlich Kaleido und einen von Kaleido unterstützten lokalen Browser. Geprüft mit Python 3.13 und Plotly 6.5.2. Bei gesperrtem System-Temp-Verzeichnis `TEMP` und `TMP` auf ein beschreibbares lokales Verzeichnis setzen. HTML enthält Plotly eingebettet und benötigt kein CDN.

Das ausgeführte Notebook liegt in `Redaktion/transitionsszenarien/Berechnungen/Transition_2040.ipynb`. Es benötigt zusätzlich pandas, nbformat, nbclient, ipykernel und ipywidgets. Seine Oberfläche nutzt dieselben Rechenfunktionen wie die Berichtsgrafik; Exporte landen mit Zeitstempel in `.local/transition-varianten/`, einschließlich Annahmen, Zahlen und offlinefähiger Grafik. PV- und Verkehrsaufteilung sind standardmäßig nicht gesetzt. Einsparungen verändern nur den Ziel-Strombedarf; Endenergie und Quelltabellen werden nicht mitverändert. Die PV-Aufteilung ist eine Klassifizierung, keine Prioritätsregel der Versorgung.

`baseline_energy.csv` ergänzt die Zieldaten um Quellenzeilen für 2020/2023. `transition_2020_2040_comparison.csv` enthält daraus berechnete Änderungen, Mehrbedarfe und Minderungen, getrennt nach Energiegröße. Das Quarto-Profil `redaktion` ergänzt das Fachreview; der normale HTML-Build enthält dieses Review nicht.

Quellenprüfung, Widersprüche und offene Entscheidungen: [METHODENSTAND.md](METHODENSTAND.md).

Die HTML-Sankeys passen sich der verfügbaren Breite an. Unter 1.200 px werden Stromfluss, Bedarfsvergleich und Endenergievergleich untereinander angeordnet; horizontales Scrollen ist nicht erforderlich. Erzeugungstechnologien und Bedarfssektoren haben feste Farben. Das separate Mobilitäts-Sankey zeigt ausschließlich die publizierte Verteilung der 10,68 TWh PE/a, ohne elektrische und primärenergetische Flüsse zu verbinden.
