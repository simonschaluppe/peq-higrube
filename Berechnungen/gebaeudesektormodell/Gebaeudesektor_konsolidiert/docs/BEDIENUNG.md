# Bedienung

## Grundsätze

- Jede Berechnung, jeder Export und jedes Ersetzen muss im Notebook ausdrücklich eingeschaltet werden. Standard ist immer `False`.
- Laden, Analysieren und Vergleichen vorhandener Ergebnisse startet keine Neuberechnung und keine Optimierung.
- Eingaben (`data/`, `config/`) und Ergebnisse (`results/`) sind getrennt. Ergebnisse werden zuerst in einen Arbeitsordner neben dem Ziel geschrieben und erst nach vollständiger Erstellung veröffentlicht. Vorhandene Ergebnisse werden nur mit `ERSETZEN=True` ersetzt.
- Logik liegt in `modell/`; Notebooks enthalten Schalter, Aufrufe und Anzeigen.

## Standardworkflow

| Schritt | Notebook | Einstellungen | Ergebnis |
|---|---|---|---|
| 1 | `00_Start` | keine | Pfade, Pakete, Szenarioregister, Status vorhandener Ergebnisse (nur lesen) |
| 2 | `01_Szenario` | je Szenario `SZENARIO`, dann `BERECHNEN`, `ENERGIE_BERECHNEN`, `EXPORTIEREN` = `True` (bei vorhandenem Ergebnis `ERSETZEN=True`) | `results/szenarien/<ID>/` |
| 3 | `02_Szenarienvergleich` | `VERGLEICH` (registriert) oder eigene `SZENARIEN`; optional `EXPORTIEREN` | `results/vergleiche/<ID>/` |
| 4 | `03_Flaechenstroeme` | `REKONSTRUKTION`; Standard liest vorhandene Flüsse. Neu rekonstruieren: `MODUS='Rekonstruktion'`, `REKONSTRUIEREN=True`, `EXPORTIEREN=True` (ggf. `ERSETZEN=True`) | `results/flaechenstroeme/<ID>/` |

Jeder Schritt liest nur gespeicherte Ergebnisse des vorherigen. Ändert sich ein Zustand (Schritt 2), gelten gespeicherte Vergleiche und Flüsse, die auf ihm beruhen, nicht mehr: Flüsse werden dann mit `EINGABEN_UNGUELTIG` abgewiesen, der Vergleich ist neu zu exportieren. Änderungen an `Bestandsentwicklung.xlsx` (Mengen, Freigaben) betreffen nur Schritt 4.

Nach einem Lauf von 01 bis 03 ohne geänderte Schalter (alle `False`) entsteht keine Datei und es läuft keine Optimierung.

## Nach einer Aktualisierung der Projektdateien

Werden Dateien in `modell/` oder `notebooks/` ersetzt, während Jupyter läuft:

1. Geöffnete Notebooks **ohne Speichern schließen**. Sonst überschreibt Jupyter die neue Datei mit dem alten Inhalt.
2. Notebook aus `notebooks/` neu öffnen und den Kernel neu starten.

Die Startzelle schützt doppelt (ab 1.6.0): Sie entfernt alle bereits geladenen Module aus `modell/` und lädt sie neu. Außerdem vergleicht sie die Fassung des Notebooks mit `modell/fassung.py` und bricht bei einer Abweichung mit einem Hinweis ab. Ältere Notebook-Fassungen (vor 1.6.0) haben diese Prüfung noch nicht.

## Fehlermeldungen und Abhilfe

| Meldung (Auszug) | Ursache | Abhilfe |
|---|---|---|
| `Projektordner nicht gefunden` | Notebook liegt nicht unter `notebooks/` des Projekts | Notebook im Projektordner öffnen |
| `Notebook … hat Fassung …, das Modell … erwartet …` | Notebook-Fenster mit altem Inhalt oder altes Notebook | siehe „Nach einer Aktualisierung“ |
| `… existiert bereits. Zum Ersetzen ERSETZEN = True setzen.` | Ersetzungsschutz | bewusst `ERSETZEN=True` setzen |
| Status `FEHLERHAFT` in 00 (Spalte `Hinweis`) | Ergebnis im Altformat, Dateien fehlen oder verändert | Szenario in 01 neu speichern |
| Status `NICHT_LESBAR (Zugriffsrechte)` in 00 | Ordnerrechte (siehe Windows-Besonderheit) | Rechte prüfen bzw. neu speichern |
| `Gespeichertes … verändert oder unvollständig` | Ausgabehash weicht ab | neu berechnen und speichern; Ergebnisdateien nicht von Hand ändern |
| `EINGABEN_UNGUELTIG … gehört nicht zu den aktuellen Zuständen` bzw. `… älteren Zielfunktion` | Zustand A/B, Neubau-/Abrissvorgaben oder Zielfunktion haben sich geändert | in 03 neu rekonstruieren und exportieren |
| Bilanzstatus `NUR_NETTO` bei ungleicher NGF | keine Bruttovorgaben für das Paar | Neubau und Abriss in `Bestandsentwicklung.xlsx` eintragen |
| Bilanzstatus `WIDERSPRUCH` / `UNVOLLSTAENDIG` | Vorgaben passen nicht zu A/B bzw. fehlen | Vorgaben korrigieren (nichts wird ausgeglichen) |
| Blockdiagnose: „nur Nettoänderung bekannt“ | ungleiche NGF ohne `BILANZ_OK` | wie `NUR_NETTO`; mit `BILANZ_OK` erscheint die Meldung nicht |
| `NICHT_MACHBAR` | Regeln/Freigaben lassen A → B nicht zu | Diagnose lesen; Regeln, Freigaben oder Zustände bewusst ändern |
| `NICHT_MACHBAR`, Diagnose „Kombination“ | eine Merkmalskombination in B fehlt in A (bzw. umgekehrt), typischerweise durch Prioren der Excel-Verteilung | Prior der Kombination in der Verteilung auf 0 setzen, Ziel ändern oder zusätzlichen Übergang bzw. Freigabe bewusst erlauben |
| `NICHT_MACHBAR`, Solverstatus 2, Ebene „Fehlmengen“ | Konflikt höherer Ordnung, von der Blockdiagnose nicht erfasst | genannte Typen prüfen; Vorgehen wie bei „Kombination“ |
| `NICHT_ABSCHLIESSEND_GELOEST` | Zeitlimit erreicht | `ZEITLIMIT_S=None` oder größer; kein Unmachbarkeitsnachweis |
| Energiestatus `Nicht ausgeführt` | Energieanalyse nicht angefordert oder Parquet fehlt | in 01 `ENERGIE_BERECHNEN=True`; `scenarios.parquet` und `pyarrow` prüfen (00) |

## Notebooks

| Notebook | Zweck | Standardlauf |
|---|---|---|
| `00_Start` | Projektprüfung, registrierte Szenarien, vorhandene Ergebnisse, optional Abnahmestand | nur lesen |
| `01_Szenario` | Zustand erstellen, Bilanzkontrollen, Eigenschaften, optional Energie, speichern, wiederladen | zeigt Eingaben, lädt vorhandenes Ergebnis |
| `02_Szenarienvergleich` | Mehrszenarienvergleich gespeicherter Zustände: Übersicht, Vergleichbarkeit, Referenzvergleich, optional Paarvergleich | liest gespeicherte Ergebnisse, rechnet Differenzen, kein Export, keine Flüsse |
| `03_Flaechenstroeme` | Flächenströme zwischen zwei gespeicherten Zuständen (konstanter Bestand oder mit Neubau/Abriss): Bestandsbilanz, Pflichtprüfungen, Regeln, Blockdiagnose, vorhandene Flüsse laden oder Rekonstruktion, Matrizen, Sankey, Änderungsanteile, Maßnahmenraten | `MODUS='VorhandeneFluesse'`: lädt registrierte Flussdatei oder gespeichertes Ergebnis, kein Solver, kein Export |

## Schalter in 01_Szenario

| Schalter | Wirkung |
|---|---|
| `SZENARIO` | registrierte ID aus `config/szenarien.json` |
| `BERECHNEN` | Zustand aus Excel-Verteilung bilden, Bilanzkontrollen und Eigenschaften |
| `ENERGIE_BERECHNEN` | zusätzlich energetische Auswertung über `scenarios.parquet` |
| `EXPORTIEREN` | Ergebnis nach `results/szenarien/<SZENARIO>/` speichern |
| `ERSETZEN` | vorhandenes Ergebnis ersetzen |
| `PRIOREN_ABLEITEN` | (ab 1.6.3) nur für Szenarien mit `prioren` im Profil: abgeleitete Verteilungsdatei schreiben, wenn sie fehlt oder veraltet ist. Mit `BERECHNEN=True` und nicht aktueller Datei bricht 01 ab |

### Szenario nur über globale Ziele (ab 1.6.3)

1. Vorlage `data/eingaben/verteilungen/Vorlage_Verteilung_nur_Ziele.xlsx` kopieren, ZIEL-Zeilen (Qualitaet, Versorgung, PV) eintragen. Prior-Zellen leer lassen oder nur die bekannten Zellen bzw. Zeilen eintragen; eingetragene Werte haben Vorrang.
2. Profil in `config/szenarien.json`: `"verteilungen"` auf die abgeleitete Datei setzen, Feld `"prioren"` ergänzen, z. B.
   `"verteilungen": "data/eingaben/verteilungen/abgeleitet/Verteilung_<ID>.xlsx", "prioren": {"eingabe": "data/eingaben/verteilungen/<Eingabe>.xlsx", "basis": "Bestand_2024"}`.
   Optional `"rekonstruktion"` (Paar für Neubau/Abriss, sonst das registrierte Paar Basis → Szenario) und `"wechselgewicht"` (0–1, Standard 0,05; kleiner = mehr Verbleib).
3. Basis in 01 gespeichert? Dann 01 mit `PRIOREN_ABLEITEN=True` (schreibt nur die abgeleitete Datei), danach wie gewohnt `BERECHNEN=True`.
4. Abschnitt „Erreichbarkeit“ prüft den Zustand ohne Solver gegen die Gegenzustände der registrierten Paare: `KEINE_KONFLIKTE` (notwendige Bedingungen erfüllt), `KONFLIKTE` (Tabelle nennt Typen und Defizit), `NUR_NETTO`, `GEGENZUSTAND_FEHLT`, `FEHLER`. Die Machbarkeit weist erst die Rekonstruktion in 03 nach.

Die abgeleitete Datei wird bei geänderter Eingabe, Basis-ID, Regeln, Bestandsentwicklung, Ziel-NGF oder Wechselgewicht als `VERALTET` gemeldet, ebenso nach Handänderungen. Ziele, die mit Regeln und Freigaben nicht erreichbar sind, werden mit den größten Fehlmengen abgewiesen. Die abgeleiteten Prioren sind eine regelkonforme Startverteilung, keine Prognose.

## Schalter in 02_Szenarienvergleich

| Schalter | Wirkung |
|---|---|
| `VERGLEICH` | registrierte Vergleichs-ID aus `config/vergleiche.json`; zugleich Name des Exportordners |
| `SZENARIEN` | `None` = Registrierung; sonst eigene Liste (mindestens zwei gespeicherte Szenarien) |
| `REFERENZ` | `None` = Registrierung bzw. erstes Szenario |
| `PAAR` | zwei Szenarien für den Detailvergleich; `None` = Registrierung (bei eigener Liste: kein Paar) |
| `MINDESTABDECKUNG_PCT` | `None` = Registrierung (Standard 95 %) |
| `EXPORTIEREN` | Vergleich nach `results/vergleiche/<VERGLEICH>/` speichern |
| `ERSETZEN` | vorhandenen Vergleich ersetzen |

Neuen Vergleich registrieren: Eintrag unter `vergleiche` in `config/vergleiche.json` mit `szenarien`, `referenz`, optional `paar`, `beschreibung`, `mindestabdeckung_pct`. Alle Szenarien müssen zuvor in `01_Szenario` gespeichert sein (Format ab AP1 mit `Kennwerte.csv`).

### Lesart der Vergleichsergebnisse

- Differenzen werden nur für `VERGLEICHBAR` und `BEDINGT_VERGLEICHBAR` ausgewiesen.
- Relative Änderung nur bei Referenzwert ≠ 0; Prozentpunkte nur für Anteile (`% NGF`).
- `Netto_pro_Jahr` ist die mittlere Nettoänderung zwischen zwei Zuständen, keine Sanierungs-, Neubau- oder Abrissrate. Nur bei positiver Zeitspanne; gleichjährige Alternativszenarien erhalten keine Jahresrate.
- Fehlende oder nicht vergleichbare Energiewerte sperren den Flächenvergleich nicht.
- Die minimale Umverteilung im Paarvergleich ist eine Untergrenze der verschobenen Fläche (nur bei gleicher Gesamt-NGF), keine Flussrekonstruktion.

## Schalter in 03_Flaechenstroeme

| Schalter | Wirkung |
|---|---|
| `REKONSTRUKTION` | registrierte ID aus `config/flaechenstroeme/rekonstruktionen.json` (Paar A/B) |
| `MODUS` | `'VorhandeneFluesse'` (Standard, nur lesen) oder `'Rekonstruktion'` |
| `REKONSTRUIEREN` | startet die lineare Optimierung, nur zusammen mit `MODUS='Rekonstruktion'` |
| `ZEITLIMIT_S` | optionales Zeitlimit (Sekunden; je Block bzw. für das gemeinsame LP mit Neubau/Abriss); Überschreitung ergibt `NICHT_ABSCHLIESSEND_GELOEST` |
| `EXPORTIEREN` | Ergebnis nach `results/flaechenstroeme/<REKONSTRUKTION>/` speichern (auch `NICHT_MACHBAR` mit Diagnose) |
| `ERSETZEN` | vorhandenes Ergebnis ersetzen |

Im Modus `VorhandeneFluesse` gilt: Ist eine `flussdatei` registriert, wird sie gegen A/B geprüft und übernommen. Sonst wird ein gespeichertes Ergebnis geladen, sofern seine Ausgabehashes stimmen und es zu den aktuellen Zuständen A/B gehört. Andernfalls `NICHT_AUSGEFUEHRT`.

### Status der Flussrekonstruktion

| Status | Bedeutung |
|---|---|
| `NICHT_AUSGEFUEHRT` | nichts gestartet bzw. nichts geladen |
| `EINGABEN_UNGUELTIG` | Zustand fehlt oder verändert, ungültige Typen, Regeln, Zeitreihenfolge oder Flussdatei; nichts gelöst |
| `MACHBAR` | gültige Flüsse; alle Pflichtprüfungen bestanden |
| `NICHT_MACHBAR` | nachweislich keine zulässige Zuordnung (Randsummen-, Block- oder Merkmalshüllenkonflikt, Neubau-/Abrisskapazität oder Solver: unzulässig) |
| `NICHT_ABSCHLIESSEND_GELOEST` | Zeit- oder Iterationslimit; **kein** Unmachbarkeitsnachweis |
| `BERECHNUNGSFEHLER` | numerischer oder technischer Fehler; Ergebnis nicht verwendbar |

Die Rekonstruktion arbeitet zweistufig (Entscheidung 17.11.2026): Stufe 1 maximiert die vollständig unveränderte Fläche; Stufe 2 wählt unter allen Lösungen mit dieser unveränderten Fläche (Toleranz `toleranz_m2` je Block bzw. insgesamt) diejenige mit der kleinsten Bestandsfläche mit Versorgungswechsel. Die Pflichtprüfung „Zweite Zielstufe“ zeigt beide Werte; ist Stufe 2 numerisch nicht lösbar, wird die Stufe-1-Lösung mit `HINWEIS` verwendet. Gespeicherte Ergebnisse mit älterer Zielfunktion (vor 1.5.1) gelten nicht mehr und werden mit `EINGABEN_UNGUELTIG` abgewiesen. Die Rekonstruktion kalibriert nicht nach, gleicht Gesamtflächen nicht aus, ergänzt keine Übergänge und verändert das Ziel nicht. Bei `NICHT_MACHBAR` zeigt die Blockdiagnose, welche Merkmalsflächen mit den Regeln nicht erreichbar sind; Abhilfe ist eine bewusste Änderung der Regeln oder Zustände.

Die Zelle „Blockdiagnose“ in 03 prüft dieselben notwendigen Bedingungen wie die Rekonstruktion, ohne Solver. Mit Bruttovorgaben (`BILANZ_OK`) gehören Neubau und Abriss innerhalb der Freigaben dazu. Bei gleicher NGF ohne Bruttovorgaben wird für konstanten Bestand geprüft. Bei ungleicher NGF ohne Bruttovorgaben gibt es seit 1.6.0 nur eine Meldung „nur Nettoänderung bekannt“. Die Zeile „Grundlage“ zeigt, was geprüft wurde. Ab 1.6.2 prüft sie auch Kombinationen veränderlicher Merkmale (Eigenschaft „Kombination“, z. B. „Qualität: 1990-99 × Versorgung: Oel“): Kann jedes Merkmal für sich erreicht werden, eine Kombination aber nicht (etwa weil 1990-99 nur aus 1990-99 und Öl nur aus Öl entsteht, A diese Kombination im Block aber nicht enthält), meldet die Zelle das Defizit vor dem Solver. Gemeldet werden nur minimale Kombinationen. Die Bedingungen bleiben notwendig, nicht hinreichend; scheitert die Rekonstruktion trotzdem mit Solverstatus 2, nennt die Diagnose in Abschnitt 4–5 die Typen mit nicht zuordenbarer Fläche (Ebene „Fehlmengen A/B“). Hintergrund: Bis 1.5.0 ließ die Zelle Neubau und Abriss außer Acht. Beim Wachstumspaar erschienen deshalb 300 Meldungen (60 Blöcke × 5), obwohl die Rekonstruktion `MACHBAR` war. Erscheinen sie noch, wurde eine alte Notebook-Fassung ausgeführt (siehe „Nach einer Aktualisierung“).

Die Änderungsanteile in Abschnitt 7 beziehen sich auf die Ausgangs-NGF (Festlegung E8) und beschreiben eine zulässige Mindestzuordnung, keine beobachteten Maßnahmen. Die Maßnahmenraten stehen in Abschnitt 8 (siehe unten).

### Neubau und Abriss (Bestandsbilanz, ab AP4)

Grundlage ist \(T_B = T_A - D + N\) mit Abriss \(D\) und Neubau \(N\) im Zeitraum. Aus den Zuständen A und B allein ist nur \(N - D\) bekannt; Neubau und Abriss werden deshalb **nur** aus ausdrücklichen Bruttovorgaben übernommen. Die Vorgaben stehen in `data/eingaben/bestandsentwicklung/Bestandsentwicklung.xlsx` (Pfad in `config/projekt.json` → `konfiguration.bestandsentwicklung`):

- Blatt `Verbindungen`: je Rekonstruktions-ID (`Verbindung_ID`) eine Zeile für `Neubau` und eine für `Abriss` mit `Eingabeart`:
  - `Rate_pct_pro_Jahr`: Periodenfläche = Rate/100 · NGF A · (Jahr B − Jahr A) (lineare mittlere Rate, Bezug Ausgangs-NGF);
  - `Periodenflaeche_m2`: Fläche im gesamten Zeitraum;
  - `Bilanzrest`: Größe ergibt sich aus der Bilanz (ausdrücklich gewählte Annahme; höchstens eine Größe je Verbindung).
- Blatt `Freigaben`: welche Kategorien je Merkmal abgerissen bzw. neu gebaut werden dürfen (1/0). Ein Typ ist freigegeben, wenn alle sieben Merkmale freigegeben sind.
- Blatt `Parameter`: `schema_version`, `bilanztoleranz_m2`.

| Bilanzstatus | Bedeutung | Folge in 03 |
|---|---|---|
| `BILANZ_OK` | Neubau und Abriss vorgegeben, Bilanz innerhalb der Toleranz | Rekonstruktion mit expliziten Neubau-/Abrissflüssen (gemeinsames LP) |
| `NUR_NETTO` | keine Bruttoangaben | gleiche NGF: Rekonstruktion ohne Neubau/Abriss; ungleiche NGF: `EINGABEN_UNGUELTIG` („nur Nettoänderung bekannt“) |
| `WIDERSPRUCH` | Vorgaben passen nicht zu A/B (oder Bilanzrest negativ) | `EINGABEN_UNGUELTIG`; nichts wird ausgeglichen |
| `UNVOLLSTAENDIG` | nur eine Größe oder beide als Bilanzrest | `EINGABEN_UNGUELTIG` |

Die Rekonstruktion setzt Abriss nur auf freigegebene Typen in A und Neubau nur auf freigegebene Typen in B; Bestandsflüsse bleiben in den unveränderlichen Blöcken und folgen den Übergangsregeln. Innerhalb der Freigaben ist die Auswahl nicht eindeutig (Ziel: maximale vollständig unveränderte Bestandsfläche, dann minimaler Versorgungswechsel; weitere Präferenzen, etwa Abriss bevorzugt aus ältesten Qualitäten, sind nicht festgelegt). Freigaben (bestätigt 17.11.2026): Abriss aus vor1919 bis 1990-99; Neubau in Neu_20cm/Neu_30cm mit Wärmepumpe, Fernwärme, Biomasse oder Strom direkt, nicht Erdgas/Öl. Neubau und Abriss erscheinen in Tabellen und Sankey als eigene externe Knoten, nie als Gebäudetypen. Bezugsbasen: Änderungsanteile und Raten auf NGF A; in `zusammensetzung` Abriss auf A der Kategorie, Neubau auf B der Kategorie.

Vor dem LP wird geprüft (ohne Solver): Bilanz, Abriss-/Neubaukapazität der freigegebenen Typen, Blockbilanz und Merkmalshüllen (eine Kategorie ohne zulässigen Zufluss kann nur aus sich selbst oder aus freigegebenem Neubau wachsen, analog für Abnahmen). Ein gespeichertes Ergebnis gilt nur, solange Zustände **und** Neubau-/Abrissvorgaben (Mengen, Freigaben) unverändert sind.

### Maßnahmenraten und Maßnahmenkombinationen (ab AP5)

Abschnitt 8 von `03_Flaechenstroeme` leitet aus gültigen Flüssen (Status `MACHBAR`, geladen oder neu rekonstruiert) Maßnahmenraten ab. Es wird nichts optimiert; die Auswertung liest nur das Ergebnis. Die Abgrenzung steht in `config/flaechenstroeme/massnahmen.json` (Pfad in `config/projekt.json` → `konfiguration.massnahmen`).

Rate einer Maßnahme \(M\) mit betroffener Fläche \(A_M\) (m² im Zeitraum):

\[ r_M = \frac{100 \cdot A_M}{T_A \cdot (J_B - J_A)} \quad [\%\ \text{der Ausgangs-NGF pro Jahr}] \]

Der Nenner \(T_A\) ist die gesamte NGF des Ausgangszustands, für alle Raten gleich (Festlegung E8, 16.11.2026). Die Rate ist eine lineare mittlere Periodenrate, keine beobachtete Jahreszeitreihe.

| Maßnahme | Abgrenzung (Bestandsflüsse) |
|---|---|
| Thermische Sanierungsrate | Qualitätswechsel, der als Verbesserung klassifiziert ist; Festlegung E7: alle in `uebergaenge.json` zulässigen Wechsel (vor1919 … 1980-89 → Neu_20cm/Neu_30cm); aufgeschlüsselt nach Zielqualität |
| Versorgungswechselrate | Wechsel der Versorgungskategorie; aufgeschlüsselt nach Ziel- und Herkunftsgruppe (Wärmepumpe, Fernwärme, Biomasse, Fossil, Strom direkt). Festlegung E9: Dieser Begriff ersetzt „Kesseltauschrate“. Ein Kesseltausch innerhalb derselben Kategorie ist im Typenschema nicht erkennbar. |
| Dekarbonisierungsrate (ab 1.6.1) | Wechsel von fossil (Erdgas, Öl) zu erneuerbar bzw. nicht fossil (Biomasse, Fernwärme, Wärmepumpe, Strom direkt); Teilmenge der Versorgungswechselrate; aufgeschlüsselt nach Zielgruppe und fossilem Ausgangsträger. Nicht enthalten: Erdgas ↔ Öl, Abriss fossil versorgter Fläche, Neubau. Wechsel erneuerbar → fossil getrennt (`Rückwärts`). Fernwärme und Strom gelten nach Festlegung (17.11.2026) als erneuerbar; ihr Erzeugungsmix ist nicht abgebildet. |
| PV-Ausbaurate | höhere PV-Kategorie; betroffene NGF, **nicht kWp**; davon Erstausstattung PV0 → PV > 0 |
| Flexibilisierungsrate | noFlex → Flex |
| Rückwärtsentwicklungen | nicht klassifizierte Qualitätswechsel, PV-Rückbau, Flex → noFlex: getrennte Zeilen, nie mit den Raten verrechnet |
| Mindestens eine Änderung | Fläche mit mindestens einer Merkmalsänderung, ohne Doppelzählung; dazu „ohne Änderung“ |
| Neubaurate, Abrissrate | externe Flüsse (Bereich `Extern`), getrennt vom Bestand; Merkmale von Neubau/Abriss in eigenen Tabellen |

Lesart:

- Einzelraten **nicht addieren**: Dieselbe Fläche kann mehrere Maßnahmen zugleich erhalten. Überschneidungen zeigt die Tabelle der Maßnahmenkombinationen (jede Bestandsfläche genau einmal).
- Die Raten beruhen auf **einer** zulässigen Zuordnung zwischen zwei Endzuständen (maximale unveränderte Fläche). Zwischenzeitliche Mehrfachwechsel, wiederholte Sanierungen oder Neubau mit späterem Abriss sind nicht identifizierbar. Es sind **keine beobachteten Bruttomaßnahmenraten**.
- Eindeutig ist die Summe „mindestens eine Änderung“ (minimal) und, seit 1.5.1, die Versorgungswechselfläche (kleinste mit der maximal unveränderten Fläche verträgliche). Die Aufteilung auf Sanierung, PV-Ausbau und Flexibilisierung sowie auf Herkunfts- und Zielgruppen kann weiterhin zwischen gleichwertigen Lösungen variieren. Verbleibt eine Kategorie zugleich als Herkunft und Ziel (z. B. Fernwärme), ist dieser Wechsel unter den Regeln nötig, um die unveränderte Fläche zu halten.
- Maßnahmen im Neubau (z. B. Wärmepumpe, PV) zählen nicht zu den Bestandsraten; sie stehen in der Neubau-Merkmalstabelle.
- **Fossilbilanz** (ab 1.6.1): Verbleib der fossil versorgten Ausgangsfläche \(F_A\) = Abriss + Dekarbonisierung + Wechsel innerhalb fossil + fossil unverändert; Herkunft der fossilen Zielfläche \(F_B\) = innerhalb fossil + unverändert + Wechsel erneuerbar → fossil + Neubau fossil. Der Rückgang \(F_A - F_B\) entsteht aus Dekarbonisierung **und** Abriss. Neben der Rate in % der Ausgangs-NGF steht jeweils der Anteil an \(F_A\) (`Anteil_fossile_Ausgangsflaeche_pct`, `Rate_fossil_pct_pro_Jahr`). Welche Abrissfläche fossil versorgt war, folgt aus der gewählten Zuordnung innerhalb der Freigaben und ist nicht eindeutig.

Ein Export (`EXPORTIEREN=True`) schreibt zusätzlich `Massnahmenraten.csv`, `Massnahmenkombinationen.csv`, `Fossilbilanz.csv` (ab 1.6.1), `massnahmen_verwendet.json` sowie die Excel-Blätter `Massnahmenraten`, `Massnahmenkombinationen`, `Versorgungswechsel_Gruppen`, `Fossilbilanz`, `Massnahmen_Kontrollen`, `Neubau_Merkmale`, `Abriss_Merkmale`. Schlägt eine Maßnahmenkontrolle fehl, bricht der Export ab.

## Lokale Gesamtprüfung (AP7)

Die Abnahme folgt `docs/AP7/AP7_Abnahmeprotokoll.md`. Zwei Hilfen lesen und vergleichen nur (`modell/abnahme.py`):

- `00_Start`, Abschnitt „Abnahmestand“ (`ABNAHMESTAND_PRUEFEN=True`): je registriertem Szenario, Vergleich und Flächenstrompaar `OK`, `FEHLT`, `HINWEIS` oder `FEHLERHAFT`/`FEHLER`; prüft Integrität, Zugehörigkeit der Flüsse zu den aktuellen Zuständen und wertet die Maßnahmenraten aus den gespeicherten Flüssen erneut aus (Abnahmeschritt 8).
- `03_Flaechenstroeme`, Abschnitt 9 „Wiederholbarkeit“: nach einer neuen Rekonstruktion (vor dem Ersetzen) Vergleich mit dem gespeicherten Ergebnis. Toleranz \(\max(1\ \text{m}^2,\ 10^{-7} \cdot T_A)\). Maßgeblich sind Status, Zielwerte und Neubau/Abriss; abweichende Einzelflüsse bei gleichen Zielwerten sind eine gleichwertige alternative Zuordnung (`HINWEIS`).

## Neues Szenario anlegen

1. Excel-Verteilung nach Vorlage unter `data/eingaben/verteilungen/` ablegen.
2. Eintrag in `config/szenarien.json` ergänzen (ID nur aus Buchstaben, Ziffern, `_`, `-`; `jahr`, `statistikjahr`, `verteilungen`, optional `ziel_ngf_m2`, `typ`, `beschreibung`).
3. `00_Start` ausführen (Datei vorhanden?), dann `01_Szenario` mit der neuen ID.

## Zustands-ID

Die Zustands-ID ist ein SHA-256 über Eingabe-Fingerprint (Szenarioprofil, Bilanzdefinition, aufgelöste Verteilungen, Prüfsummen der Eingabedateien mit projektrelativen Pfaden, Parquet-Name und -Größe), Rechenkern und Kalibrierung. Sie ist damit unabhängig vom Speicherort des Projekts und (ab AP3) unabhängig davon, welche weiteren Szenarien registriert sind. Gleiche ID bedeutet gleicher Zustand.

## Bekannte Windows-Besonderheit

Python ab 3.12.4 legt unter Windows mit `tempfile.mkdtemp` Ordner mit Rechten nur für den aktuellen Benutzer an. Dadurch waren frühere Ergebnisordner für andere Prozesse nicht lesbar. Seit AP1 werden Arbeitsordner ohne `mkdtemp` angelegt und erben die Rechte des Zielordners.
