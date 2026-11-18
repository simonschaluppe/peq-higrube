# Änderungsprotokoll

## 1.6.3-AP6 – 17.11.2026

Szenarioeingabe über globale Ziele (Stufe A) und Erreichbarkeitsprüfung (Stufe B).

- Neu `modell/prioren.py` (Methode 1.0): Vorstufe zur Zustandsbildung, kein zweiter Szenariorechenkern. Eine Eingabe-Excel mit ZIEL-Zeilen und leeren Prior-Zellen wird zu einer vollständigen Verteilungsdatei unter `data/eingaben/verteilungen/abgeleitet/` ergänzt (gemeinsame Transportmatrix Qualität × Versorgung und PV-Transport vom gespeicherten Basiszustand zu den Zielen nach `uebergaenge.json` und Bestandsentwicklung; Maximum-Entropie mit bevorzugtem Verbleib, Wechselgewicht 0,05; LP-Vorprüfung und Trägerbestimmung). Eingegebene Werte haben Vorrang. Blätter `Ableitung` und `Herkunft` dokumentieren Methode, Prüfsummen und Herkunft jeder Zelle; Datei bytegleich reproduzierbar. Status `AKTUELL`/`VERALTET`/`FEHLT`/`NICHT_KONFIGURIERT`.
- `erreichbarkeit`: Blockdiagnose eines gebildeten Zustands gegen die gespeicherten Gegenzustände aller registrierten Paare (nur lesen, kein Solver).
- Szenarioprofil: optionales Feld `prioren` (`eingabe`, `basis`, optional `rekonstruktion`, `wechselgewicht`). Profile ohne dieses Feld unverändert.
- Notebook 00: Abschnitt „Abgeleitete Prioren“ (nur lesen). Notebook 01: Schalter `PRIOREN_ABLEITEN=False`, Abschnitte „Prioren aus globalen Zielen“ und „Erreichbarkeit“; Speichern warnt bei Konflikten. Fassung 1.6.3-AP6 in allen Notebooks.
- Vorlage `data/eingaben/verteilungen/Vorlage_Verteilung_nur_Ziele.xlsx`.
- Tests: `test_prioren` (9), Notebook-Sicherheit um den neuen Schalter erweitert.
- `gebaeudesektor.py`, `distribution_to_json.py`, `flaechenstroeme.py`, `bestandsbilanz.py`, `massnahmen.py`, Eingaben und Regeln unverändert: Zustands-IDs und gespeicherte Ergebnisse bleiben gültig.

## 1.6.2-AP6 – 17.11.2026

Diagnose von Kombinationskonflikten (Anlass: Wachstumsszenario nach Änderung 17.11.2026 mit Solverstatus 2 bei 0 Konflikten in der Blockdiagnose).

- `flaechenstroeme.py`: neu `_kombinations_konflikte` – notwendige Bedingung für Kombinationen veränderlicher Merkmale (Produkte vorgänger- bzw. nachfolgerabgeschlossener Kategoriemengen; B_T ≤ A_T + N_frei,T, A_U ≤ B_U + D_frei,U), nur minimale Kombinationen; eingebunden in `blockdiagnose` (konstanter Bestand und mit Neubau/Abriss) und in die Vorprüfung der Rekonstruktion mit Neubau/Abriss (Konflikt → `NICHT_MACHBAR` ohne Solver). Neu `_fehlmengen`: bei Solverstatus 2 Fehlmengen-LP und Ausgabe der Typen mit nicht zuordenbarer Fläche (Ebene `Fehlmengen A/B`). Rechenweg zulässiger Fälle unverändert (Ergebnisse identisch).
- Notebook 03: Text der Blockdiagnose ergänzt; Fassung 1.6.2-AP6 in allen Notebooks.
- Tests: `test_bestandsbilanz.Kombinationsdiagnose` (5).
- `gebaeudesektor.py`, `bestandsbilanz.py`, `massnahmen.py`, Eingaben und Regeln unverändert: Zustands-IDs und gespeicherte Ergebnisse bleiben gültig.

## 1.6.1-AP6 – 17.11.2026

Fachliche Ergänzung Dekarbonisierungsrate (Entscheidung 17.11.2026) und Vorbereitung AP7.

- `config/flaechenstroeme/massnahmen.json` Schema 1.1: neuer Abschnitt `dekarbonisierung` mit `fossil` (Erdgas, Öl) und `erneuerbar` (Wärmepumpen, Fernwärme, Biomasse, Strom direkt); Validierung: beide nicht leer, zusammen jede Versorgungskategorie genau einmal.
- `massnahmen.py`: Merkmale `Dekarbonisierung` (fossil → erneuerbar) und `Refossilisierung`; in `massnahmenraten` die Rate `Dekarbonisierungsrate` (Teilmenge der Versorgungswechsel) mit `davon fossil → <Gruppe>`, `davon aus Erdgas`/`Oel` und getrennt `Wechsel erneuerbar → fossil`; neu `fossilbilanz` (Verbleib von F_A: Abriss, Dekarbonisierung, innerhalb fossil, unverändert; Herkunft von F_B; Saldo; zusätzlich bezogen auf F_A); drei neue Kontrollen (Dekarbonisierung ≤ Versorgungswechsel, Fossilbilanz Verbleib und Herkunft geschlossen). Keine Optimierung, Rekonstruktion unverändert.
- Export (`flaechenstroeme.exportiere`): `Fossilbilanz.csv` und Excel-Blatt `Fossilbilanz`. Gespeicherte Ergebnisse 1.5.1 bleiben ladbar und werden vollständig neu ausgewertet; die Datei entsteht beim nächsten Export.
- Neu `modell/abnahme.py` (nur lesen): `abnahmestand` (Integrität, Zugehörigkeit, Wiederauswertung der gespeicherten Maßnahmenraten), `wiederholbarkeit` (neue Rekonstruktion gegen gespeichertes Ergebnis; Toleranz max(1 m², 1e-7 · T_A)). Prüfumgebung: beide Paare bitgleich wiederholt (Transition 28 s, Wachstum 101 s).
- Notebooks: 00 neuer Abschnitt „Abnahmestand (AP7)“ (`ABNAHMESTAND_PRUEFEN=False`); 03 Abschnitt 8 mit Dekarbonisierung und Fossilbilanz, neuer Abschnitt 9 „Wiederholbarkeit“, Speichern jetzt Abschnitt 10; Formeln in Abschnitt 8 werden wieder als Formel dargestellt (doppelte Maskierung seit 1.5.0 behoben). Fassung 1.6.1-AP6.
- `rekonstruktionen.json`: veraltete Beschreibung des Wachstumspaares („ohne externe Flüsse NICHT_MACHBAR“) ersetzt; nicht im Fingerprint.
- Neu `docs/AP7/AP7_Abnahmeprotokoll.md` (Vorlage der lokalen Gesamtprüfung mit Referenzwerten); `BEDIENUNG.md`, `DATENSCHEMATA.md` (auch Ebene `Summe` statt `Gesamt` korrigiert), `OFFENE_PUNKTE.md`, `README.md` ergänzt.
- Tests: `test_massnahmen.Dekarbonisierung` (4), Validierungsfälle; neu `test_abnahme` (6); `test_notebook_sicherheit` (Standardwert `ABNAHMESTAND_PRUEFEN`, Verbot `ab._`); `test_flaechenstroeme` (`Fossilbilanz.csv` im Export).
- `gebaeudesektor.py`, `bestandsbilanz.py`, `distribution_to_json.py`, Eingaben und Regeln unverändert: Zustands-IDs und gespeicherte Ergebnisse bleiben gültig.

## 1.6.0-AP6 – 17.11.2026

Notebook-Texte, Export und Bedienung finalisiert (Standardworkflow).

- Neu `modell/fassung.py`: Projektfassung `1.6.0-AP6` und erwartete Notebook-Fassungen; `pruefe_notebook(name, fassung)` bricht mit Abhilfe ab, wenn ein Notebook nicht zur Modellfassung passt. Getrennt von `gebaeudesektor.py`, damit Zustands-IDs gültig bleiben.
- Einheitliche Startzelle aller vier Notebooks: entfernt vor dem Import alle bereits geladenen Module aus `modell/` (kein veralteter Kernelstand nach einer Aktualisierung) und prüft die Notebook-Fassung, bevor das Projekt geladen wird. Anlass: Am 17.11.2026 wurde lokal die alte Zelle „Blockdiagnose“ (ohne Bilanz) aus einem noch geöffneten Notebook-Fenster ausgeführt; dabei erschienen erneut 300 Scheinkonflikte.
- `flaechenstroeme.blockdiagnose`: Ohne gültige Bruttovorgaben bei ungleicher NGF kommt jetzt genau eine Meldung „nur Nettoänderung bekannt“ statt Scheinkonflikten je Block (Grundlage `keine (NGF A ≠ NGF B ohne Bruttovorgaben)`). Bei gleicher NGF und mit `BILANZ_OK` bleibt sie unverändert.
- `flussprotokoll.json` (neue Exporte): `software` mit Python und Projektfassung, `module_sha256` (flaechenstroeme, bestandsbilanz, massnahmen, fassung), `raten` (Nenner T_A in m², Zeitspanne, Formel) und `energiestatus` von A und B. `vergleichsprotokoll.json`: `software.projektfassung`. Gespeicherte Ergebnisse bleiben ladbar.
- CSV-Einlesung der Flussergebnisse: `float_precision='round_trip'` nur noch bei pandas < 3.1 (dort nötig für bitgenaues Einlesen; ab 3.1 Standard und veraltet). Die Veraltungswarnung entfällt.
- Notebooks: 00 mit den Abschnitten „Zweck und Grenzen des Modells“, „Standardworkflow“ und „Nach einer Aktualisierung“; 01 ohne interne Hilfsfunktion (`gs._relativ` ersetzt); 03 Blockdiagnose-Text. Rechenzellen, Schalter und Standardwerte unverändert.
- Dokumentation: `BEDIENUNG.md` mit Standardworkflow, Aktualisierung und Fehlermeldungen samt Abhilfe; `DATENSCHEMATA.md` mit der Zuordnung der Dateinamen aus Abschnitt 10 und der Nachweisstärke; `OFFENE_PUNKTE.md` bereinigt.
- Tests: `test_notebook_sicherheit` (Fassung je Notebook, vollständige Abschnittstexte, keine privaten Modulfunktionen, Zweck/Workflow in 00, Abbruch bei abweichender Fassung, Startzelle verwirft veraltete Module); `test_bestandsbilanz` (Blockdiagnose ohne Bilanz: eine Meldung; Protokollangaben).
- `gebaeudesektor.py`, `bestandsbilanz.py`, `massnahmen.py`, `distribution_to_json.py`, alle Eingaben und Regeln unverändert: Zustands-IDs und gespeicherte Ergebnisse 1.5.1 bleiben gültig.

## 1.5.1-AP5 – 17.11.2026

Nachtrag zu AP5 nach den Entscheidungen vom 17.11.2026.

- Zielfunktion zweistufig (`flaechenstroeme.ZIELFUNKTION`): Stufe 1 maximale vollständig unveränderte Bestandsfläche, Stufe 2 bei gleicher unveränderter Fläche (Toleranz `toleranz_m2`) minimale Bestandsfläche mit Versorgungswechsel; für das Block-LP und das gemeinsame LP mit Neubau/Abriss. Zielwerte beider Stufen im Ergebnis und Protokoll (`zielwerte`); neue Pflichtprüfungen „Zielwerte = Flüsse“ und „Zweite Zielstufe“ (`HINWEIS`, falls Stufe 2 nicht lösbar). Gespeicherte `MACHBAR`-Ergebnisse mit älterer Zielfunktion werden nicht mehr geladen (`EINGABEN_UNGUELTIG`). Wirkung (Prüfumgebung): Versorgungswechsel Transition 460,65 → 409,71 Mio. m², Wachstum 423,93 → 374,33 Mio. m²; unveränderte Fläche gleich.
- `Bestandsentwicklung.xlsx`: Freigaben bestätigt und erweitert – Abriss zusätzlich 1990-99; Neubau zusätzlich Biomasse und Strom direkt (Elektro); Erdgas/Öl weiter gesperrt. Erläuterungen aktualisiert. Abriss als Bilanzrest bestätigt. Die `extern_signatur` ändert sich; das Wachstumspaar ist neu zu rekonstruieren.
- `blockdiagnose(a, b, cfg, bilanz=None)`: mit Bruttovorgaben dieselben notwendigen Bedingungen wie vor dem gemeinsamen LP (Neubau/Abriss innerhalb der Freigaben); `attrs['grundlage']`, `attrs['bloecke']`. Bisher wurden Neubau/Abriss ignoriert, beim Wachstumspaar entstanden dadurch 300 Scheinkonflikte (60 Blöcke × 5 Meldungen); jetzt 0.
- `notebooks/03_Flaechenstroeme.ipynb`: Blockdiagnose mit Bilanz und Grundlage; Zielfunktion in Regeln und Abschnitt 4–5; Texte Abschnitt 7/8 angepasst. `massnahmen.HINWEIS` nennt die Zuordnungsregel.
- Tests: `test_massnahmen.Zielstufe` (2 Tests, Block-LP und gemeinsames LP); `test_bestandsbilanz.Wachstumspaar` (Diagnose mit/ohne Bilanz, neue Freigaben, Zielwerte, Abweisung älterer Zielfunktion).

## 1.5.0-AP5 – 16.11.2026

Änderungsraten und Maßnahmenkombinationen mit einheitlichem Nenner und überschneidungsfreier Zählung. Festlegungen vom 16.11.2026: thermische Sanierung = alle zulässigen Qualitätswechsel (E7), Nenner = Ausgangs-NGF (E8), Begriff „Versorgungswechselrate“ statt „Kesseltauschrate“ (E9).

- Neu `config/flaechenstroeme/massnahmen.json` (Schema 1.0): Abgrenzung der Maßnahmen (Sanierungsklassifikation vor1919 … 1980-89 → Neu_20cm/Neu_30cm, Versorgungsgruppen, PV- und Flex-Rangfolge, Erläuterungen). `config/projekt.json`: `konfiguration.massnahmen` (nicht im Zustands-Fingerprint).
- Neu `modell/massnahmen.py` (reine Auswertung gültiger Flüsse, kein Solver, kein zweiter Rechenkern): `lade_definition`/`validiere_definition`, `pruefe_gegen_regeln`, `merkmale`, `massnahmenraten` (Rate = 100 · A_M / (T_A · Jahre); Sanierung nach Zielqualität, Versorgungswechsel nach Ziel- und Herkunftsgruppe, PV-Ausbau mit Erstausstattung, Flexibilisierung; Rückwärtsentwicklungen getrennt; „mindestens eine Änderung“ ohne Doppelzählung; Neubau-/Abrissrate als Bereich `Extern`), `massnahmenkombinationen` (jede Bestandsfläche genau einmal), `versorgungswechsel_matrix`, `extern_merkmale` (Merkmale von Neubau/Abriss), `kontrollen` (Nenner, Abdeckung, Überschneidung, unveränderliche Merkmale, Zeitspanne). Aussagegrenze als `HINWEIS` an jeder Tabelle.
- `flaechenstroeme.py`: Bei `MACHBAR` wird die Maßnahmendefinition zum Ergebnis geladen; Export schreibt `Massnahmenraten.csv`, `Massnahmenkombinationen.csv`, `massnahmen_verwendet.json` und Excel-Blätter `Massnahmenraten`, `Massnahmenkombinationen`, `Versorgungswechsel_Gruppen`, `Massnahmen_Kontrollen`, `Neubau_Merkmale`, `Abriss_Merkmale`; `massnahmen_sha256` im Protokoll; Abbruch bei fehlgeschlagener Maßnahmenkontrolle. Rekonstruktion selbst unverändert.
- `notebooks/03_Flaechenstroeme.ipynb`: Abschnitt 7 (Änderungsanteile) nicht mehr vorläufig; neuer Abschnitt 8 „Maßnahmenraten und Maßnahmenkombinationen“ (nur Modulaufrufe, liest nur); Speichern jetzt Abschnitt 9. Schalter unverändert.
- Tests: neu `tests/test_massnahmen.py` (9 Tests: konstruierte Fälle mit bekannten Raten, Überschneidung, Rückwärtsentwicklung, Neubau/Abriss getrennt, Definition/Validierung); `test_flaechenstroeme.py` und `test_bestandsbilanz.py` (Maßnahmendateien im Export, Gleichheit nach Wiederladen, Neubau-/Abrissrate); `test_notebook_sicherheit.py` (Import `ms`, Verbot `ms._`).
- `gebaeudesektor.py` und `bestandsbilanz.py` unverändert: Zustands-IDs bleiben gültig. Gespeicherte Flussergebnisse aus AP4 bleiben ladbar; die Maßnahmendateien entstehen beim nächsten Export.

## 1.4.0-AP4 – 16.11.2026

Neubau-/Abrissbilanz für Szenarien und Rekonstruktion (\(T_B = T_A - D + N\)); Bruttoflüsse explizit, keine Netto-Identifikation.

- Neu `modell/bestandsbilanz.py` (nur Bilanzierung, kein Szenariorechenkern): liest `Bestandsentwicklung.xlsx` mit strenger Prüfung, rechnet Raten (%/a, Bezug NGF A, linear) in Periodenflächen um, unterstützt einen ausdrücklich gewählten `Bilanzrest`, prüft gegen die Gesamtflächen der gespeicherten Zustände (`BILANZ_OK`, `NUR_NETTO`, `WIDERSPRUCH`, `UNVOLLSTAENDIG`), stellt Freigaben für Neubau-/Abrisstypen bereit; `szenariobilanz` für alle registrierten Paare (nur lesen).
- Neu `data/eingaben/bestandsentwicklung/Bestandsentwicklung.xlsx` (Schema 1.0): Verbindung `Bestand_2024__Transition_2040_Wachstum` mit Neubau 80 000 000 m² (Periodenfläche) und Abriss als Bilanzrest (= 19 872 558 m²; die genannten 19,9 Mio. m² widersprächen der Bilanz um 27 442 m²). Standardfreigaben (Annahme, zu bestätigen): Abriss nur Qualitäten vor1919 bis 1980-89; Neubau nur Neu_20cm/Neu_30cm mit WP oder Fernwärme.
- `config/projekt.json`: `konfiguration.bestandsentwicklung` (nicht unter `dateien`, damit die Zustands-IDs unverändert bleiben).
- `flaechenstroeme.py`: mit `BILANZ_OK` ein gemeinsames LP über alle Blöcke mit Variablen für Bestandsflüsse, Abriss (nur freigegebene A-Typen) und Neubau (nur freigegebene B-Typen); vorab notwendige Bedingungen ohne Solver (Bilanz, Kapazitäten, Blockbilanz, Merkmalshüllen); `pruefe_eingaben(..., bilanz)`: ungleiche NGF ohne Bruttoangaben → FEHLER („nur Nettoänderung bekannt“, vorher HINWEIS); `pruefe_fluesse` mit Randsummen inkl. Neubau/Abriss, Vorgaben und Freigaben; Export `Neubau.csv`, `Abriss.csv`, `Bestandsbilanz.csv`, zusätzliche Excel-Blätter; Sankey mit externen Knoten; `aenderungsanteile` mit Nenner T_A und gesonderten Zeilen für Neubau/Abriss; neu `zusammensetzung`; gespeicherte Ergebnisse nur gültig bei gleichen Neubau-/Abrissvorgaben; Flussdatei-Übernahme mit Neubau/Abriss vorerst gesperrt.
- `config/flaechenstroeme/uebergaenge.json`: Versorgungsregeln Bio → WP und Erdgas/Öl → Elektro ergänzt (Entscheidung 16.11.2026). `Bestand_2024__Transition_2040` ist damit `MACHBAR` (46,25 % unverändert).
- `notebooks/03_Flaechenstroeme.ipynb`: Abschnitt Bestandsbilanz (Übersicht, Freigaben, Bilanztabelle des Paares), Zusammensetzung je Qualität/Versorgung, Neubau-/Abrisssummen; weiterhin nur Modulaufrufe, Schalter unverändert.
- Tests: neu `tests/test_bestandsbilanz.py` (13 Tests; Wachstumspaar mit Standardfreigaben `MACHBAR`, eingeschränkte Neubaufreigabe `NICHT_MACHBAR`); `test_szenario.py`: Szenario 3 ohne Zuwachs bei 1990-99/Neu_10cm; `test_flaechenstroeme.py` angepasst (Paar jetzt machbar; Nettofall FEHLER); `test_notebook_sicherheit.py` (+ Verbot `bb._`, `.to_excel`).
- Szenario 3 angepasst (Entscheidung 16.11.2026: im Wachstumsszenario bzw. für Neubau keine zusätzliche Fläche für 1990-99 und Neu_10cm): neue Verteilungsdatei `data/eingaben/verteilungen/Verteilung_Transition_2040_Wachstum.xlsx` (Kopie von Transition 2040; nur Zielzeile Qualität und Hinweise geändert): 1990-99 und Neu_10cm absolut wie im Bestand (Anteil = Bestandsfläche / 950 Mio. m²), frei werdende ≈0,97 %-Punkte anteilig (33,65 : 30) auf Neu_20cm/Neu_30cm. `config/szenarien.json` verweist darauf. Die Zustands-ID von `Transition_2040_Wachstum` ändert sich; Szenario 3 muss in `01_Szenario` neu gespeichert werden. Das Wachstumspaar ist damit mit den Standardfreigaben `MACHBAR`.
- `flaechenstroeme.py`: Meldet HiGHS bei der strengen Toleranz (1e-10, skaliert) „unzulässig“, folgt ein zweiter Lauf mit der aus `toleranz_m2` abgeleiteten Toleranz (`toleranz_m2/SKALA_M2/10`, hier 1e-7 ≙ 0,001 m²). Grund: Kalibrierte Zustände treffen Zielsummen nur bis auf Rundungsreste (hier +0,001 m² bei 1990-99). Die Rand- und Bilanzprüfungen bleiben unverändert gegen `toleranz_m2`; die verwendete Toleranz steht im Protokoll (`solver_toleranz`).
- `gebaeudesektor.py` unverändert: gespeicherte Zustände und Zustands-IDs von Bestand 2024 und Transition 2040 bleiben gültig.

## 1.3.0-AP3 – 16.11.2026

Flussrekonstruktion für konstanten Bestand abgesichert; drittes Szenario.

- Neues Szenario `Transition_2040_Wachstum` (Verteilung wie Transition 2040, Ziel-NGF 950 Mio. m², illustrativ) in `config/szenarien.json`; Vergleich `Bestand_Transition_Wachstum_2040` (drei Szenarien, Referenz Bestand 2024, Paar Transition/Wachstum) in `config/vergleiche.json`.
- `gebaeudesektor.py`: Szenarioregister nicht mehr im Eingabe-Fingerprint (vorher änderte jedes neu registrierte Szenario die Zustands-IDs aller anderen). `MODELLVERSION = 1.3.0-AP3`. **Alle Zustands-IDs ändern sich dadurch einmalig**; Flächen und Kennwerte sind unverändert.
- `flaechenstroeme.py`: Statuswerte `NICHT_AUSGEFUEHRT`, `EINGABEN_UNGUELTIG`, `MACHBAR`, `NICHT_MACHBAR`, `NICHT_ABSCHLIESSEND_GELOEST`, `BERECHNUNGSFEHLER` mit Bedeutung; `analysiere_rekonstruktion(..., modus, rekonstruieren, exportieren, ersetzen, zeitlimit_s)` liefert immer einen Status; Zustände A/B werden mit Integritätsprüfung geladen und per Dateihash vor/nach dem Lauf als unverändert nachgewiesen; `pruefe_eingaben` (Regeln, Zustände, Integrität, Zeitreihenfolge, Gesamtbilanz) und `pruefe_fluesse` (17 Pflichtprüfungen); Laden gespeicherter Ergebnisse mit Hashprüfung (`lade_flussergebnis`) ohne Solver; Zeitlimit; `matrix`, `aenderungsanteile` (vorläufig), `zusammenfassung`, `registrierte_rekonstruktionen`, `speichere_ergebnis`. Export mit `Pruefungen.csv`, Ausgabehashes im Protokoll, `KEINE_FLUESSE.txt` mit Statusbedeutung. Alte Funktion `analysiere_fluesse` und die doppelte AP1-Fassung von `analysiere_rekonstruktion` entfernt.
- `config/flaechenstroeme/rekonstruktionen.json`: Paar `Bestand_2024__Transition_2040_Wachstum`, Beschreibungen.
- `notebooks/03_Flaechenstroeme.ipynb` neu, nur Modulaufrufe; Ablauf nach Arbeitsauftrag (A/B, Zeitspanne/Bilanz, Regeln, Laden oder ausdrückliche Rekonstruktion, Status/Kontrollen, Matrizen/Sankey, Änderungsanteile, optional Speichern); Schalter `REKONSTRUKTION`, `MODUS`, `REKONSTRUIEREN`, `ZEITLIMIT_S`, `EXPORTIEREN`, `ERSETZEN`.
- `config/flaechenstroeme/uebergaenge.json`: Versorgungsregel Erdgas/Öl → Bio ergänzt (fachliche Entscheidung 16.11.2026).
- Tests: `test_flaechenstroeme.py` neu gefasst (12 Tests), `test_szenario.py` (+2), `test_notebook_sicherheit.py` (+1).

## 1.2.0-AP2 – 16.11.2026

Mehrszenarienvergleich vereinheitlicht.

- Neu `modell/szenarienvergleich.py`: liest nur gespeicherte Ergebnisse (mit Integritätsprüfung); gemeinsame Kennwerttabelle aller gewählten Szenarien; Vergleichbarkeit je Kennwert (`VERGLEICHBAR`, `BEDINGT_VERGLEICHBAR`, `NICHT_VERGLEICHBAR`, `KENNWERT_FEHLT`); Übersicht, Referenzvergleich, Paarvergleich (Merkmale, Typen, Flächen-/Struktureffekt, minimale Umverteilung, Qualität × Versorgung); Grafiken; Export mit Arbeitsordner, Ersetzungsschutz, Ausgabehashes; `lade_vergleich`.
- `config/vergleiche.json`: `mindestabdeckung_pct` (95 %, Annahme), `beschreibung`.
- `notebooks/02_Szenarienvergleich.ipynb` neu, nur Modulaufrufe; Schalter `VERGLEICH`, `SZENARIEN`, `REFERENZ`, `PAAR`, `MINDESTABDECKUNG_PCT`, `EXPORTIEREN`, `ERSETZEN` (vorher `EXPORT_ERSETZEN`).
- Tests neu: `tests/test_vergleich.py` (drei Szenarien, Statusregeln, Differenzregeln, gleichjährig ohne Jahresrate, Zerlegungsidentität, Export/Schutz/Wiederladen, Standardlauf 02 schreibt nichts); `test_notebook_sicherheit.py` angepasst.
- Rechenkern `gebaeudesektor.py` unverändert (Zustands-IDs der gespeicherten Ergebnisse bleiben gültig).

## 1.1.0-AP1 – 16.11.2026

Zielstruktur mit projektrelativen Pfaden; Szenario-API und Notebooks konsolidiert.

- Neue Ordnerstruktur `config/`, `modell/`, `notebooks/`, `data/{eingaben,referenz,simulation}/`, `results/`, `tests/`, `docs/`, `archiv/`.
- `config/projekt.json` als einzige Quelle aller Pfade; `finde_projektwurzel`, `lade_projekt`, `pruefe_projekt`.
- `gebaeudesektor.py`: `lade_szenario(name, projekt)` mit projektrelativen Quellen; Zustands-ID unabhängig vom Speicherort; Energieanalyse nur auf Anforderung (`analysiere_zustand(..., energie=True)`); `bilanzkontrollen`, `kennwerttabelle` (Kennwerte.csv), `speichere_szenario` mit Ausgabehashes, `lade_gespeichertes_szenario` mit Integritätsprüfung, `ergebnisuebersicht`, `registrierte_szenarien`, `zeige_eingaben`.
- Arbeitsordner ohne `tempfile.mkdtemp` (Ursache der gesperrten Ergebnisordner unter Windows).
- `flaechenstroeme.py` (Basis Integration 2.2): `lade_rekonstruktion`, `lade_zustaende`, `analysiere_rekonstruktion`; Regeln (`uebergaenge.json`) und Paare (`rekonstruktionen.json`) getrennt; projektrelative Protokollpfade; ohne `mkdtemp`.
- Notebooks 00–03 mit einheitlicher Startzelle, sicheren Standardwerten und Erläuterung vor jedem Abschnitt. 02 und 03 vorläufig bis AP2/AP3.
- Tests neu: `test_szenario.py`, `test_notebook_sicherheit.py`, `test_flaechenstroeme.py`; Referenzen aus dem gültigen Stand (Transition mit Bio 0,18).
- Verteilungsdateien umbenannt: `Verteilungen_Gebaeudesektor.xlsx` → `Verteilung_Bestand_2024.xlsx`, `Verteilungen_Transition_2040.xlsx` → `Verteilung_Transition_2040.xlsx` (Inhalt unverändert).
- Vorherige Dateien unter `archiv/vor_AP1_20261116/`, Integration 2.2 unter `archiv/zielgefuehrte_entwicklung/Integration_2_2_20261116/`.

## 1.0 – bis 13.11.2026

Stand vor der Finalisierung; siehe `docs/AP0/AP0_Bestandsaufnahme.md`.
