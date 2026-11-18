# Datenschemata (Stand 1.6.3-AP6)

## results/szenarien/<Szenario_ID>/

| Datei | Inhalt |
|---|---|
| `Verteilung.csv` | Zustand, 43 200 Zeilen, `;`-getrennt, UTF-8 mit BOM |
| `Kennwerte.csv` | Kennwerte im Langformat (Schema unten) |
| `Herkunftskohorten.csv` | Flächen je Herkunftskohorte |
| `Szenario.xlsx` | Tabellenübersicht inkl. Energiekennwerte (falls berechnet) |
| `laufprotokoll.json` | Zustands-ID, Eingaben mit Prüfsummen (projektrelativ), Software, Energiestatus, Vergleichsbasis, SHA-256 aller Ausgaben (`ausgaben`) |
| `eingaben/` | Kopien der verwendeten Eingabedateien und aufgelöste Annahmen |

### Verteilung.csv

`Szenario, Jahr, Archetype, geometry, quality, energy, pv, flex, weather, mass, NGF_m2, BGF_m2, Flaechenanteil` (Archetype = Merkmale mit `|` verbunden). Prüfungen beim Wiederladen: vollständiger Katalog, keine Doppelungen, keine negativen oder nichtendlichen Werte, Anteile summieren zu 1, ein Szenario und ein Jahr, Ausgabehashes laut Laufprotokoll.

### Kennwerte.csv

| Spalte | Bedeutung |
|---|---|
| `Szenario_ID`, `Zustand_ID`, `Jahr` | Zuordnung |
| `Bereich` | `Gesamt`, `Haushalte`, `Nichtwohnen` |
| `Gruppe` | `Fläche`, `Typen`, Merkmal (z. B. `Qualität`) oder `Energie: …` |
| `Kennwert` | z. B. `NGF`, `NGF-Anteil`, `Positiv belegte Typen`, Energiekennwert |
| `Kategorie` | Merkmalsausprägung bzw. Energieträger (leer bei Summen) |
| `Wert`, `Einheit` | Zahlenwert; fehlende Werte bleiben leer, nie 0 |
| `Bezugsflaeche` | `NGF`, `BGF` oder leer |
| `Abdeckung_pct` | Flächenabdeckung des Kennwerts |
| `Status` | `OK`, `UNVOLLSTAENDIG`, `KEINE_FLAECHE`, `NICHT_AUSGEFUEHRT`, `KENNWERT_FEHLT` |
| `Vergleichsbasis_ID` | `F-…` für Flächen-, `E-…` für Energiekennwerte. Gleiche ID = gleiche Definition, Kategorien und Abgrenzung; Grundlage für AP2 |

## results/vergleiche/<Vergleich_ID>/

| Datei | Inhalt |
|---|---|
| `Kennwerte_Alle_Szenarien.csv` | gemeinsame Kennwerttabelle (Spalten wie `Kennwerte.csv`, alle Szenarien untereinander) |
| `Vergleichbarkeit.csv` | je Kennwert (`Bereich`, `Gruppe`, `Kennwert`, `Kategorie`, `Einheit`) Status je Szenario gegenüber der Referenz, Gesamtstatus (schlechtester), Hinweis |
| `Referenzvergleich.csv` | je Kennwert und Szenario: `Wert_Referenz`, `Wert_Szenario`, `Delta`, `Relative_Aenderung_pct`, `Delta_pp`, `Netto_pro_Jahr`, `Jahre`, `Status`, `Hinweis` |
| `Paarvergleich.csv` | Kategorien je Merkmal: NGF A/B, Δ, Anteile, Δ pp, Flächeneffekt, Struktureffekt, Nettoänderung pro Jahr |
| `Typenvergleich.csv` | wie Paarvergleich je vollständigem Typenschlüssel |
| `Vergleich.xlsx` | Blätter Szenarien, Status, Uebersicht, Vergleichbarkeit, Referenzvergleich, Paar_* |
| `Vergleich.html` | Statusübersicht und Grafiken |
| `vergleichsprotokoll.json` | Auswahl, Mindestabdeckung, Eingabedateien mit SHA-256 (projektrelativ), Szenariometadaten, Regeln, Paarkontrollen, Software, Modul-Hash, SHA-256 aller Ausgaben |

Statusregeln (je Kennwert, Szenario gegen Referenz):

1. Kennwert fehlt, Wert nicht endlich oder Status `NICHT_AUSGEFUEHRT`/`KENNWERT_FEHLT`/`KEINE_FLAECHE` → `KENNWERT_FEHLT`.
2. Einheit, Bezugsfläche oder `Vergleichsbasis_ID` verschieden → `NICHT_VERGLEICHBAR`.
3. Abdeckung fehlt oder unter `mindestabdeckung_pct` → `NICHT_VERGLEICHBAR`.
4. Abdeckung unter 100 % oder Kennwertstatus nicht `OK` → `BEDINGT_VERGLEICHBAR`.
5. sonst `VERGLEICHBAR`.

Summenzeilen ohne eigene Abdeckung erhalten im Vergleich die kleinste Abdeckung ihrer Einzelwerte. Flächen- und Energiekennwerte werden unabhängig bewertet. Zerlegung im Paarvergleich: Δ = (NGF_B − NGF_A)·(a_A + a_B)/2 + (NGF_A + NGF_B)/2·(a_B − a_A) mit Anteilen a.

## results/flaechenstroeme/<Rekonstruktion_ID>/

| Datei | Inhalt |
|---|---|
| `Machbarkeit.csv` | Diagnose: Konflikte je Ebene (`Gesamt`, `Merkmal`, `Block`, `Numerik`; ab 1.6.2 `Fehlmengen A`/`Fehlmengen B` mit Typenschlüssel bei Solverstatus 2), `Eigenschaft` (ab 1.6.2 `Kombination` für Konflikte mehrerer Merkmale), Kategorie, Defizit m², ggf. `Solverstatus` (1 Zeitlimit, 2 unzulässig, 4 numerisch); leer bei `MACHBAR` |
| `Kontrollen.csv` | je gelöstem Block: NGF, zulässige/belegte Kanten, max. Herkunfts-/Zielfehler, numerische Zielkorrektur |
| `Pruefungen.csv` | Pflichtprüfungen `Pruefung;Status;Detail` (Status `OK`, `FEHLER`, `HINWEIS`) |
| `Erlaubte_Uebergaenge.csv` | Regeltabelle je Merkmal |
| `uebergaenge_verwendet.json` | verwendete Regeln samt Paar |
| `Bestandsbilanz.csv` | Bilanztabelle T_A, D, T_A − D, N, Soll, Ist, Netto mit Eingabeart, Vorgabe, Anteil und %/a (falls Bestandsentwicklung konfiguriert) |
| `Neubau.csv`, `Abriss.csv` | nur bei `MACHBAR` mit Bruttovorgaben: `Ziel_Typ` bzw. `Herkunft_Typ`, `post_*` bzw. `pre_*`, `NGF_m2` (explizite externe Flüsse, keine Gebäudetypen) |
| `Fluesse.csv` | nur bei `MACHBAR` (Bestandsflüsse ohne Neubau/Abriss): `Herkunft_Typ`, `Ziel_Typ`, `NGF_m2`, `pre_*`, `post_*`, `Aenderung_*` je Merkmal, `Unveraendert` |
| `Flussanalyse.xlsx`, `Sankey_*.html` | nur bei `MACHBAR`: Kontrollen, Bestandsbilanz, Aenderungsanteile, ggf. Neubau, Abriss, Zusammensetzung_Qualitaet/_Versorgung; Aggregationen, Matrizen, Sankey-Grafiken (Qualität, Versorgung, Qualität × Versorgung, PV × Flex, Auswahl) mit externen Knoten „Neubau (Zeitraum)“/„Abriss (Zeitraum)“ |
| `Massnahmenraten.csv` | nur bei `MACHBAR` (ab AP5): `Bereich` (`Bestand`/`Extern`), `Ebene` (`Rate`, `davon`, `Rückwärts`, `Summe`), `Massnahme` (ab 1.6.1 zusätzlich `Dekarbonisierungsrate` mit `davon fossil → <Gruppe>`, `davon aus Erdgas`/`Oel` und `Wechsel erneuerbar → fossil`), `Flaeche_m2` (Periodenfläche), `Anteil_Ausgangs_NGF_pct`, `Rate_pct_pro_Jahr` (leer bei „ohne Änderung“), `Flaechenbasis` |
| `Massnahmenkombinationen.csv` | nur bei `MACHBAR` (ab AP5): `Kombination`, `Anzahl_Massnahmen`, Flags `Sanierung`, `Versorgungswechsel`, `PV_Ausbau`, `Flexibilisierung`, `Sonstige_Aenderung` (Rückwärtsentwicklung bzw. nicht klassifiziert), `Flaeche_m2`, `Anteil_Ausgangs_NGF_pct`, `Rate_pct_pro_Jahr` (leer bei „keine Maßnahme“); Summe = Bestandsflüsse |
| `Fossilbilanz.csv` | nur bei `MACHBAR` (ab 1.6.1): `Bereich` (`Fossilbilanz`), `Teil` (`Ausgangszustand`, `Verbleib F_A`, `Herkunft F_B`, `Zielzustand`, `Saldo`), `Position`, `Flaeche_m2`, `Anteil_Ausgangs_NGF_pct`, `Rate_pct_pro_Jahr` (nur für Ströme), `Anteil_fossile_Ausgangsflaeche_pct`, `Rate_fossil_pct_pro_Jahr`; geschlossen: F_A = Abriss + Dekarbonisierung + innerhalb fossil + unverändert, F_B = innerhalb fossil + unverändert + erneuerbar → fossil + Neubau fossil |
| `massnahmen_verwendet.json` | verwendete Maßnahmendefinition (Kopie von `massnahmen.json`); SHA-256 des sortierten JSON-Inhalts im Protokoll als `massnahmen_sha256` |
| `KEINE_FLUESSE.txt` | sonst: Status und Bedeutung |
| `flussprotokoll.json` | Status, Paar, Jahre, `extern` (Neubau/Abriss m², Freigaben, Bilanztoleranz, Datei und SHA-256 der Bestandsentwicklung), `bilanzstatus`, Eingaben (projektrelative Datei, SHA-256 von `Verteilung.csv` und `laufprotokoll.json`, Zustands-ID), Regel-Hash, Methode, `zielwerte` (ab 1.5.1: `zielfunktion`, `stufe2_geloest`, geänderte Fläche und Versorgungswechsel nach Stufe 1 und Stufe 2 in m²), Modul-Hash, Softwareversionen (ab 1.6.0 mit Python und `projektfassung`), ab 1.6.0 `module_sha256` (flaechenstroeme, bestandsbilanz, massnahmen, fassung), bei `MACHBAR` `raten` (Nenner T_A in m², Zeitspanne, Formel) und `energiestatus` je Zustand unter `eingaben`, `ausgaben` (SHA-256 aller Dateien) |

Beim Laden (`lade_flussergebnis`) werden alle Ausgabehashes geprüft; ein Ergebnis gilt nur, wenn die Eingabehashes zu den aktuell gespeicherten Zuständen A/B passen. Ordner ohne `ausgaben` (vor AP3) werden nicht verwendet. Mit Neubau/Abriss gilt ein Ergebnis zusätzlich nur bei gleichen Mengen und Freigaben (inhaltlicher Fingerabdruck `extern_signatur`). Ein `MACHBAR`-Ergebnis gilt nur mit der aktuellen Zielfunktion (`zielwerte.zielfunktion`; ältere Ergebnisse neu rekonstruieren). Statusbedeutungen: `docs/BEDIENUNG.md`.

## Zuordnung zu Abschnitt 10 des Arbeitsauftrags

| Arbeitsauftrag | Umsetzung | Grund |
|---|---|---|
| Szenarioordner `Verteilung.csv`, `Kennwerte.csv`, `Szenario.xlsx`, `laufprotokoll.json`, `eingaben/` | wie vorgegeben, zusätzlich `Herkunftskohorten.csv` | – |
| Vergleichsordner (7 Dateien) | wie vorgegeben, zusätzlich `Typenvergleich.csv` | – |
| `Diagnose.csv` | `Machbarkeit.csv` | Name seit AP3 in Tests und gespeicherten Ergebnissen; Inhalt = Diagnose |
| `Aenderungsraten.csv` | `Massnahmenraten.csv` (Raten je Maßnahme); Änderungsanteile je Merkmal im Blatt `Aenderungsanteile` von `Flussanalyse.xlsx` | Unterscheidung Maßnahmenrate / Merkmalsänderung (AP5) |
| `Sankey.html` | `Sankey_Auswahl.html` sowie `Sankey_Qualitaet`, `_Versorgung`, `_Qualitaet_Versorgung`, `_PV_Flex` | eine Datei je Ansicht |
| weitere | `Pruefungen.csv`, `Erlaubte_Uebergaenge.csv`, `Bestandsbilanz.csv`, `massnahmen_verwendet.json`, `KEINE_FLUESSE.txt` | Nachvollziehbarkeit |

Externe Sankey-Knoten „Neubau (Zeitraum)“ und „Abriss (Zeitraum)“ stellen nur die expliziten externen Flüsse dar. Neubau und Abriss stehen in eigenen Dateien, nie als Gebäudetypen.

## Dokumentation in jedem Export

| Angabe (Abschnitt 10) | Szenario (`laufprotokoll.json`) | Vergleich (`vergleichsprotokoll.json`) | Flüsse (`flussprotokoll.json`) |
|---|---|---|---|
| Eingabe- und Zustands-IDs | Zustands-ID, Eingaben mit SHA-256 | Szenariometadaten mit Zustands-ID, Eingabedateien mit SHA-256 | `eingaben` A/B mit SHA-256 und Zustands-ID, Bestandsentwicklung mit SHA-256 |
| verwendete Regeln | Bilanzdefinition | Vergleichsregeln, Mindestabdeckung | `regeln`, `regel_sha256`, `uebergaenge_verwendet.json`, `massnahmen_sha256` |
| Modell- und Softwareversionen | `software` (inkl. `modellversion` des Rechenkerns), `modellsoftware` (SHA-256) | `software` mit `projektfassung`, `modul_sha256` | `software` mit `projektfassung`, `modul_sha256`, `module_sha256` |
| Solverstatus und Optionen | – (keine Optimierung) | – | `status`, `methode`, `solver` (Verfahren, Toleranzen, Zeitlimit; ab 1.6.0), `solver_toleranz` (tatsächlich verwendet, mit Neubau/Abriss), `zielwerte` |
| technische Toleranzen | Kalibrierung | Mindestabdeckung | `regeln.toleranz_m2`, `extern.bilanztoleranz_m2` |
| Rate, Nenner, Zeitspanne | – | `Jahre`, `Netto_pro_Jahr` (Nettoänderung) | `raten`, Spalten in `Massnahmenraten.csv` |
| Ausführungsstatus der Energieanalyse | `energieanalyse.status` | Energiestatus je Szenario | `eingaben.A/B.energiestatus` (ab 1.6.0) |

`modellversion` in `laufprotokoll.json` bezeichnet die Fassung des Rechenkerns `gebaeudesektor.py` (unverändert seit AP3, deshalb weiter `1.3.0-AP3`). Die Projektfassung steht in `modell/fassung.py`.

## Nachweisstärke von Referenzen

- **Stark (Inhalt):** SHA-256 über Dateiinhalte, und zwar für Eingabedateien, Ausgaben, Zustände, Regeln, Maßnahmendefinition, Bestandsentwicklung und Module. Jede Änderung wird erkannt.
- **Inhaltlicher Fingerabdruck:** `extern_signatur` (Neubau-/Abrissmengen und Freigaben) und der Regel-Hash über das sortierte JSON. Formatänderungen ohne inhaltliche Änderung bleiben folgenlos.
- **Schwach (Pfad/Größe):** `scenarios.parquet` (mehrere GB) wird nur über Name und Dateigröße nachgewiesen. Eine inhaltliche Änderung bei gleicher Größe würde nicht erkannt. Wer die Simulationsdaten ersetzt, sollte deshalb die Szenarien in 01 neu speichern.

## config/flaechenstroeme/

- `uebergaenge.json`: nur Regeln (unveränderliche Merkmale, Gruppen-/Aufstiegsregeln, Toleranz).
- `massnahmen.json` (Schema 1.1 ab 1.6.1, vorher 1.0; ab AP5): `nenner` (`ausgangs_ngf`), `thermische_sanierung.verbesserungen` (Liste von `pre`/`post`-Qualitätslisten; Abweichungen von den zulässigen Qualitätswechseln in `uebergaenge.json` werden in 03 als `HINWEIS` gemeldet), `versorgungswechsel.gruppen` (jede Versorgungskategorie genau einer Gruppe), `dekarbonisierung.fossil` und `.erneuerbar` (ab 1.1; zusammen jede Versorgungskategorie genau einmal, beide nicht leer), `pv.folge` und `flex.folge` (Rangfolge für Ausbau/Rückbau), je Abschnitt `bezeichnung` und `erlaeuterung`. Ungültige Definitionen (Schema, Nenner, unbekannte Kategorien, unvollständige Gruppen, falsche Rangfolge) werden mit Meldung abgelehnt.
- `rekonstruktionen.json`: Paare `szenario_a`/`szenario_b` (Szenario-IDs), `beschreibung`, Regeldatei, optional `flussdatei` (projektrelativ; semantisch mit `Herkunft_Typ`, `Ziel_Typ`, `NGF_m2` oder ID-basiert mit `systemordner`) für die geprüfte Übernahme vorhandener Flüsse.

## data/eingaben/bestandsentwicklung/Bestandsentwicklung.xlsx (Schema 1.0)

| Blatt | Spalten | Regeln |
|---|---|---|
| `Erlaeuterung` | Text | nur Dokumentation |
| `Parameter` | `Parameter`, `Wert`, `Einheit`, `Erläuterung` | `schema_version` = 1.0; `bilanztoleranz_m2` > 0 und ≤ 10 000 |
| `Verbindungen` | `Verbindung_ID`, `Szenario_A`, `Szenario_B`, `Groesse` (`Neubau`/`Abriss`), `Eingabeart` (`Rate_pct_pro_Jahr`/`Periodenflaeche_m2`/`Bilanzrest`), `Wert`, `Einheit`, `Quelle`, `Bemerkung` | je Verbindung und Größe höchstens eine Zeile; `Wert` endlich und ≥ 0 (leer bei `Bilanzrest`); `Verbindung_ID` = Rekonstruktions-ID |
| `Freigaben` | `Art` (`Neubau`/`Abriss`), `Merkmal`, `Kategorie`, `Freigegeben` (0/1) | je Art und Merkmal jede Kategorie genau einmal, mindestens eine freigegeben; Versorgung auf Planebene (`FW_*` = `DH`) |

Die Datei wird nur gelesen (`bestandsbilanz.lade_bestandsentwicklung`); sie ist nicht Teil des Zustands-Fingerprints (Pfad unter `konfiguration`, nicht unter `dateien`), damit Zustands-IDs unverändert bleiben. Ihre Prüfsumme steht im Flussprotokoll.

## Abgeleitete Prioren (ab 1.6.3, `modell/prioren.py`)

Szenarioprofil (`config/szenarien.json`), optional:

| Feld | Bedeutung |
|---|---|
| `prioren.eingabe` | projektrelative Eingabe-Excel (Aufbau wie jede Verteilung; ZIEL-Zeilen Pflicht, Prior-Zellen dürfen leer sein) |
| `prioren.basis` | ID eines gespeicherten Zustands (Ausgangsflächen und wirksame Verteilungen) |
| `prioren.rekonstruktion` | optional: Paar für Neubau/Abriss aus `Bestandsentwicklung.xlsx`; sonst registriertes Paar Basis → Szenario; ohne Paar nur bei gleicher NGF (dann N = D = 0) |
| `prioren.wechselgewicht` | optional, (0, 1], Standard 0,05 |
| `verteilungen` | abgeleitete Datei, üblich `data/eingaben/verteilungen/abgeleitet/Verteilung_<ID>.xlsx`; muss von `prioren.eingabe` verschieden sein |

Abgeleitete Datei: Blätter wie die Eingabe (vollständig befüllt, vom Kern gelesen) und zusätzlich

- `Hinweise`: Herkunft der Datei, Warnung vor Handänderungen.
- `Ableitung`: Angabe/Wert – Methode, Szenario, Basis und Basis-Zustands-ID, SHA-256 von Eingabe, Regeln und Bestandsentwicklung, Paar, N und D (m²), Ziel-NGF, Wechselgewicht, Iterationen, Restfehler, Zahl erzwungener Nullflüsse, SHA-256 der Werte (`werte_sha256`, erkennt Handänderungen).
- `Herkunft`: je Blatt, Zeile und Kategorie Wert und Herkunft: `eingegeben`, `abgeleitet` (Transport; bei teilweise befüllten Zeilen Rest im Verhältnis der abgeleiteten Werte) oder `Basis` (Geometrie, Speichermasse, Flexibilitaet aus dem Basiszustand). Abgeleitete Werte 0 sind strukturelle Nullzellen (keine zulässige Herkunft).

Die Datei ist bei gleichen Eingaben bytegleich (feste Zeitstempel). Sie ist Teil des Zustands-Fingerprints wie jede Verteilungsdatei; die Eingabedatei selbst nicht.
