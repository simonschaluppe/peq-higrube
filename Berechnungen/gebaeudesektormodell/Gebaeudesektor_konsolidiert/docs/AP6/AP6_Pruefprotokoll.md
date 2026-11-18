# AP6 – Prüfprotokoll Notebook-Texte, Export und Bedienung

Stand 17.11.2026, Fassung 1.6.0-AP6. Abnahmekriterium (Abschnitt 11): vollständig nachvollziehbarer Standardworkflow.

## Anlass: 300 Einzelmerkmalkonflikte erneut gemeldet

Befund auf dem Gerät nach der Übertragung von 1.5.1:

| Prüfung | Ergebnis |
|---|---|
| `notebooks/03_Flaechenstroeme.ipynb` | SHA-256 57A1CE73D3C5 = gelieferte Fassung 1.5.1; Datei seit der Übertragung (10:36) nicht gespeichert |
| `modell/flaechenstroeme.py` | CECD8EB9A214 = Fassung 1.5.1 |
| `results/flaechenstroeme/Bestand_2024__Transition_2040_Wachstum` (10:51) | `MACHBAR`, Zielfunktion 2, alle Pflichtprüfungen `OK`; Bilanz `BILANZ_OK` (Neubau 80 000 000 m², Abriss 19 872 558 m²); geänderte Fläche 443 594 535,54 m², Versorgungswechsel 374 333 216 m², identisch mit der Prüfumgebung |
| Wortlaut der Meldung | „… Einzelmerkmalkonflikte“ gibt nur die Zelle der Fassung 1.5.0 aus (`print(len(diagnose), 'Einzelmerkmalkonflikte')`, Aufruf ohne `bilanz`). Die Zelle 1.5.1 gibt „N Konflikte in X Blöcken \| Grundlage: …“ aus. |

**Ursache:** Das Notebook war beim Aktualisieren geöffnet. Ausgeführt wurde der alte Zelleninhalt aus dem Editorfenster, nicht die neue Datei. Der Aufruf ohne Bilanz prüfte deshalb für konstanten Bestand, und jeder wachsende Block meldete Scheinkonflikte. Rekonstruktion und Export liefen trotzdem richtig, denn sie bilden die Bilanz unabhängig von dieser Zelle.

Nachgestellt in der Prüfumgebung mit den Modulen 1.6.0: Der alte Aufruf `blockdiagnose(a, b, regeln)` ergibt jetzt **eine** Meldung „nur Nettoänderung bekannt … Bestandsbilanz mit Status BILANZ_OK übergeben“. Mit Bilanz sind es 0 Konflikte.

**Maßnahmen gegen eine Wiederholung:**

1. Die Startzelle entfernt alle bereits geladenen Module aus `modell/` und lädt sie neu.
2. Die Startzelle prüft die Notebook-Fassung gegen `modell/fassung.py` und bricht bei einer Abweichung mit einer Abhilfe ab.
3. Die Blockdiagnose ohne Bruttovorgaben meldet bei ungleicher NGF nur noch einen Hinweis.
4. Die Bedienung erklärt das richtige Vorgehen nach einer Aktualisierung.

## Abnahme nach Abschnitt 4

| Vorgabe | Umsetzung |
|---|---|
| 00: Zweck und Grenzen, Gesamtworkflow, Pfade/Abhängigkeiten, registrierte Szenarien, Ergebnisstatus, Hinweise auf 01–03; rechnet nicht | Abschnitte „Zweck und Grenzen des Modells“, „Standardworkflow“ (Tabelle 01–03), „Nach einer Aktualisierung“, „Projektprüfung“, „Registrierte Szenarien“, „Vorhandene Ergebnisse“ (Statustext auf LESBAR/FEHLERHAFT/NICHT_LESBAR korrigiert); Test `test_00_rechnet_nicht`, `test_00_zweck_workflow` |
| 01: Szenario wählen … optional speichern; Defaults `False` | Steuerung → Eingaben → Zustand bilden/Bilanzkontrollen → Eigenschaften und Energie → Speichern → Wiederladen; Ablaufzeile im Kopf; interne Funktion `gs._relativ` ersetzt |
| 02: Auswahl … optional Export; keine Flussrekonstruktion | unverändert seit AP2 (nur Startzelle) |
| 03: Modi, Defaults, Schritte 1–8 | Abschnitte 1–9 (Schritt 7 „Änderungsraten“ = Abschnitte 7 und 8; Schritt 8 „Speichern“ = Abschnitt 9); Ablaufzeile im Kopf; Blockdiagnose-Text |
| Markdown mit sechs Angaben vor jedem Abschnitt | Test `test_abschnittstexte_vollstaendig`: vor **jeder** Codezelle Was / Eingaben / Rechnet oder liest / Annahmen / Interpretation / Sperrende Fehler |
| Logik in Modulen | Tests `test_02_/test_03_nur_modulfunktionen`, `test_keine_privaten_modulfunktionen` |
| Notebooks ohne Codeeingriffe konfigurierbar | je Notebook eine Steuerzelle, Tests `test_standardwerte` |

## Abnahme nach Abschnitt 10

Dateinamen und Protokollangaben sind in `docs/DATENSCHEMATA.md` den Vorgaben zugeordnet: „Zuordnung zu Abschnitt 10“, „Dokumentation in jedem Export“ und „Nachweisstärke von Referenzen“. Neu im Flussprotokoll sind Python-Version und Projektfassung, die Modulhashes, die Solveroptionen, Rate/Nenner/Zeitspanne und der Energiestatus von A und B. Diese Angaben sind durch einen Test abgesichert. Abweichende Dateinamen (`Machbarkeit.csv`, `Massnahmenraten.csv`, `Sankey_*.html`) sind begründet beibehalten, damit gespeicherte Ergebnisse ladbar bleiben.

## Notebook-Läufe (Prüfumgebung, gespeicherte Ergebnisse 1.5.1)

| Notebook | Einstellung | Ergebnis |
|---|---|---|
| 00 | Standard | Fassung passt, keine Datei geschrieben |
| 01 | Standard | kein Zustand gebildet; gespeichertes Ergebnis geladen, Integrität OK |
| 02 | Standard | Vergleich ohne Export |
| 03 | Standard, Transition | `NUR_NETTO` bei gleicher NGF, Blockdiagnose 0 (konstanter Bestand), Flüsse geladen, kein Solver |
| 03 | Standard, Wachstum | `BILANZ_OK`, Blockdiagnose 0 (mit Neubau/Abriss), Abriss 19,873 / Neubau 80,0 Mio. m², kein Solver |

## Wirkung auf vorhandene Ergebnisse

`gebaeudesektor.py`, `bestandsbilanz.py`, `massnahmen.py`, Eingaben und Regeln sind unverändert. Zustands-IDs, der Vergleich und beide Flussergebnisse 1.5.1 bleiben gültig und werden ohne Solver geladen. Lokal muss nichts neu berechnet werden.

## Tests

`python -m unittest discover -s tests -v`: **77 Tests OK** (490 s). Selbsttest `distribution_to_json.py`: **19 OK**. Die Veraltungswarnung zu `float_precision` tritt nicht mehr auf. Protokoll: `AP6_Testlauf.txt`. Neu hinzugekommen:

- `test_notebook_sicherheit`: `test_fassung_je_notebook`, `test_abschnittstexte_vollstaendig`, `test_00_zweck_workflow`, `test_keine_privaten_modulfunktionen`, `Fassungspruefung.test_abweichende_fassung_bricht_ab`, `Fassungspruefung.test_startzelle_entfernt_veraltete_module`.
- `test_bestandsbilanz.Wachstumspaar`: test_1 prüft die Blockdiagnose ohne Bilanz (eine Meldung), test_2 die Protokollangaben.

## Sperrende Fehler

Keine. Offene Punkte stehen in `docs/OFFENE_PUNKTE.md`: lokale Vollabnahme (AP7), Mehrdeutigkeit der Maßnahmenaufteilung, E6 vorläufig, `flussdatei` mit Neubau/Abriss gesperrt.
