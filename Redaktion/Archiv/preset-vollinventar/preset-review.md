# Fachprüfung der Presets und Defaults

Arbeitsgrundlage: Anhang der HTML-Lesefassung, Tabellen T01–T26 und Ergänzungen E01–E08. Entwicklungsschema 1.13.1_dev, Eingabeschema 8, Exportdatum 18.08.2026. Noch keine Defaultfreigabe.

## Auftrag an die Kollegen

Bitte zuerst für euren Fachbereich prüfen: Fehlen Tabellen, Parameter oder sinnvolle Presets? Dann: Welche vorhandenen Werte können bleiben, welche sind zu ändern? Welche Quellen und Anwendungsgrenzen tragen die Werte? Welches Preset soll für Deklarationen Standard sein, welche Varianten sind nur für Studien geeignet?

Ihr müsst keine Tabellen abschreiben. Änderungen mit Tabellen-ID, Parameterkennung und Preset-ID angeben. Beispiel T04.R05 / T04.PE = plugloads!E5. Werte in der angegebenen Einheit nennen; Quelle mit Ausgabe/Jahr und Seite/Tabelle ergänzen. Bei einer Ergänzung neue Bezeichnung und Zuordnung vorschlagen. Ein unverändert gelassener Wert gilt nicht als freigegeben.

Die QMD-Tabellen sind der lesbare Schemaauszug. Rückmeldungen hier sammeln; fachliche Änderungen werden danach in den Bericht und abgestimmt in PEExcel übernommen. Das Quellschema bleibt unverändert. Der Generator ersetzt die abgeleiteten QMD-Dateien und darf nach manuellen Änderungen dort nicht ungeprüft erneut laufen.

## Zuständigkeit und Vollständigkeit

| ID | Bereich | Verantwortlich | Tabellen/Presets vollständig? | Empfohlener Standard | Status |
|---|---|---|---|---|---|
| T01 | Sanierungsanteile (`renovation`) | offen | ungeprüft | festzulegen | offen |
| T02 | Gebäudetypen und Bauteilmengen (`geometry`) | offen | ungeprüft | festzulegen | offen |
| T03 | Bilanzumfang der Qualitätsstufen (`declaration_type`) | offen | ungeprüft | festzulegen | offen |
| T04 | Nutzerstrom (`plugloads`) | offen | ungeprüft | festzulegen | offen |
| T05 | Warmwasserwärmebedarf (`dhw_demand`) | offen | ungeprüft | festzulegen | offen |
| T06 | Wärmeschutz der Gebäudehülle (`hulls`) | offen | ungeprüft | festzulegen | offen |
| T07 | Luftdichtheit (`air_tightness`) | offen | ungeprüft | festzulegen | offen |
| T08 | Wirksame Speichermasse (`building_mass`) | offen | ungeprüft | festzulegen | offen |
| T09 | Geometrische Einstrahlungsfaktoren (`shading_geometry`) | offen | ungeprüft | festzulegen | offen |
| T10 | Beweglicher Sonnenschutz (`mobile_shading`) | offen | ungeprüft | festzulegen | offen |
| T11 | Wärmeerzeugung (`heating_system`) | offen | ungeprüft | festzulegen | offen |
| T12 | Wärme- und Kälteabgabe (`emission_system`) | offen | ungeprüft | festzulegen | offen |
| T13 | Heizperioden (`heating_period`) | offen | ungeprüft | festzulegen | offen |
| T14 | Kälteerzeugung (`cooling_system`) | offen | ungeprüft | festzulegen | offen |
| T15 | Anteile aktiv gekühlter Nutzungen (`cooling_modes`) | offen | ungeprüft | festzulegen | offen |
| T16 | Kühlperioden (`cooling_period`) | offen | ungeprüft | festzulegen | offen |
| T17 | Warmwasserbereitung und Verteilung (`dhw_system`) | offen | ungeprüft | festzulegen | offen |
| T18 | Lüftungstechnik und Wärmerückgewinnung (`ventilation_system`) | offen | ungeprüft | festzulegen | offen |
| T19 | Anteile mechanisch belüfteter Nutzungen (`vent_modes`) | offen | ungeprüft | festzulegen | offen |
| T20 | Nachtauskühlung (`vent_night_modes`) | offen | ungeprüft | festzulegen | offen |
| T21 | Photovoltaikbelegung (`PV_system`) | offen | ungeprüft | festzulegen | offen |
| T22 | Batteriespeicher (`battery_system`) | offen | ungeprüft | festzulegen | offen |
| T23 | Nutzung erneuerbarer Überschüsse (`flexibility_system`) | offen | ungeprüft | festzulegen | offen |
| T24 | Thermische Flexibilität (`flexibility_thermal`) | offen | ungeprüft | festzulegen | offen |
| T25 | Mobilitätsregionen (`mobility`) | offen | ungeprüft | festzulegen | offen |
| T26 | Bauweisen und Bauteilzuordnungen (`construction_type`) | offen | ungeprüft | festzulegen | offen |
| E01 | Allgemeinstrom und Abgrenzung zum Nutzerstrom | offen | ungeprüft | festzulegen | offen |
| E02 | Beleuchtung und Tageslicht | offen | ungeprüft | festzulegen | offen |
| E03 | Innere Wärmegewinne | offen | ungeprüft | festzulegen | offen |
| E04 | Flächenumrechnung und Belegung | offen | ungeprüft | festzulegen | offen |
| E05 | Wetter, Ertrag und externe Signale | offen | ungeprüft | festzulegen | offen |
| E06 | Weitere Mobilitätsannahmen | offen | ungeprüft | festzulegen | offen |
| E07 | Datensätze und Quellen | offen | ungeprüft | festzulegen | offen |
| E08 | Fehlende Tabellen ergänzen | offen | ungeprüft | festzulegen | offen |

## Werte, Quellen und Entscheidungen

| Tabelle / Parameter / Preset | Vorschlag (Wert, Einheit oder neuer Name) | Fachquelle mit Fundstelle | Gültigkeit / Begründung | Entscheidung / Person / Datum |
|---|---|---|---|---|
| einzutragen | einzutragen | einzutragen | einzutragen | offen |

## Zusätzliche Tabellen oder Presets

| Fachlicher Zweck | Neue Tabelle / Parameter | Varianten und Einheiten | Quelle / Zuständigkeit |
|---|---|---|---|
| einzutragen | einzutragen | einzutragen | einzutragen |

## Auffälligkeiten für die erste Runde

- Nutzerstrom: Preset-Zeile 4 nennt kWh/m²NGFa, IN nennt kWh/m²NFA ohne Jahreszeichen. Zeit- und Flächenbezug ausdrücklich bestätigen; im Anhang gilt die Preseteinheit.
- Warmwasserbedarf: OIB-Varianten sind noch nicht befüllt. Normtitel im Presetnamen nicht als geprüfte Quelle übernehmen.
- Batterie: Kapazitätswerte stehen teils auf 0, während die Anzeigen eine Ableitung je PV-kWp nennen. Ableitungsregel und Defaultwert gemeinsam prüfen.
- PV: Belegungsvarianten über 100 % benötigen eine eindeutige Flächen-/Ertragsdefinition.
- Mobilität: Export enthält Gemeindezuordnung, keinen vollständigen regionalen Mobilitätsdatensatz. Fehlendes Label wurde nur im Lesetext aus IN ergänzt, nicht im Schema geändert.
- Bauweise: Live-, Auswahl- und Testspalten gesondert entscheiden; Bauteilnamen benötigen zugehörige LCA-Datensätze.
- Schemaeinheiten und fehlende IN-Zuordnungen sind im Anhang offen markiert; keine Einheiten aus Variablennamen erfunden.

## Freigabe

Je Fachgruppe: freigegebene Tabellen/Presets, ausgeschlossene Varianten, Quellenstand, verantwortliche Person und Datum dokumentieren. Offene Werte bleiben offen. Eine Gesamtfreigabe setzt auch die ergänzenden Profile und Bewertungsdaten voraus.

## Technischer Prüfstand

26 Presetgruppen vollständig zugeordnet; 6.218 Wertefelder einschließlich Leerstellen unabhängig gegen die Quelldatei abgeglichen. Darstellung rundet auf acht signifikante Stellen und normalisiert Rand-Leerzeichen; Null, leer und boolesche Werte bleiben unterscheidbar. SHA-256-Prüfung bestätigt unveränderte Quelldatei. 20 Buchseiten erfolgreich gerendert, lokale Links und Anker geprüft. Die separate HTML-Prüffassung enthält ihre Darstellungsressourcen eingebettet. Keine fachliche Freigabe der Entwicklungswerte und keine visuelle Browserprüfung behauptet.
