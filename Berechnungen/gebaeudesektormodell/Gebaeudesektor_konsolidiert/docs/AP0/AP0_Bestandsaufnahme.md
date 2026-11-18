# AP0 – Sicherung, Versionsmanifest und Bestandsaufnahme

Stand: 16.11.2026 · Projektordner: `Gebaeudesektor_konsolidiert\Gebaeudesektor`

## 1 Sicherung

| Element | Wert |
|---|---|
| Sicherung | `archiv/sicherungen/Sicherung_20261116_AP0.zip` |
| Inhalt | 68 Dateien, unverändert (nur gelesen, nichts verschoben oder gelöscht) |
| Größe | 20.298.686 Byte |
| SHA-256 der ZIP | `7D0B6ADBF2CE211E5C67FAA46E0A20F0CBB24863E3E4A3E0637AF1B7DCB26B97` |
| Hashliste je Datei | `archiv/sicherungen/Sicherung_20261116_AP0.sha256.csv` |

Ergänzende Sicherung der zunächst gesperrten Ergebnisordner (vom Nutzer nach `archiv/sicherungen/results_kopie/` kopiert, Stand 16.11.2026):

| Element | Wert |
|---|---|
| Sicherung | `archiv/sicherungen/Sicherung_20261116_AP0_results.zip` |
| Inhalt | 43 Dateien aus `results/szenarien/Bestand_2024`, `results/szenarien/Transition_2040`, `results/flaechenstroeme/Bestand_2024__Transition_2040`, `results/flaechenstroeme/SYNTHETISCH_Demo`, `Integration_2_2/results/szenarien/SynthetischesZiel` |
| Größe | 20.406.732 Byte |
| SHA-256 der ZIP | `4DB676418A212BC91E5C893538DC51E4D30D8F451F532DC790CD7E8F7008F794` |
| Hashliste je Datei | `archiv/sicherungen/Sicherung_20261116_AP0_results.sha256.csv` |

Ursache der Sperre: `tempfile.mkdtemp` legt unter Windows Ordner an, die nur der Ersteller lesen darf. Wird in AP1 behoben.

## 2 Versionsnachweis

Der Nachweis erfolgt über SHA-256 gegen das alte Manifest vom 13.11.2026 (`manifest.json`) und über Inhaltsvergleiche, nicht über Dateinamen.

| Datei | gegenüber Manifest 13.11. |
|---|---|
| gebaeudesektor.py, distribution_to_json.py, szenarien.json, README.md, requirements.txt, Pruefbericht.md | gleich |
| data/annahmen.json, typologien_43200.csv, Statistik_Austria_2024.xlsx, Verteilungen_Gebaeudesektor.xlsx | gleich |
| tests/test_regression.py, referenz_*.csv, pruefprotokoll.txt | gleich |
| Gebaeudesektor_Szenario.ipynb, Gebaeudesektor_Szenarienvergleich.ipynb | geändert |
| **data/Verteilungen_Transition_2040.xlsx** | **geändert** (17 Zellen, siehe unten) |
| results/vergleiche/Bestand_2024__Transition_2040/* | geändert (neu exportiert) |
| results/szenarien/* | nicht im alten Manifest prüfbar; Eingabe-Excel im Ergebnis = aktuelle `data`-Excel (SHA-256 gleich) |

Inhaltliche Änderung in `Verteilungen_Transition_2040.xlsx` gegenüber dem Konsolidierungsstand:

| Blatt | Zeile | Spalte | alt → neu |
|---|---|---|---|
| Qualitaet | ZIEL/GLOBAL | vor1919 / 1919-44 / 1945-59 / 1960-79 / 1980-89 | 0,03→0,04 / 0,01→0,02 / 0,02→0,03 / 0,05→0,08 / 0,03→0,04 |
| Qualitaet | ZIEL/GLOBAL | 1990-99 / Neu_10cm / Neu_20cm | 0,06→0,0884 / 0,05→0,0651 / 0,45→0,3365 |
| Versorgung | ZIEL/GLOBAL | DH / Bio / Elektro / WP_gesamt | 0,25→0,30 / 0,08→0,18 / 0→0,02 / 0,65→0,48 |
| PV | ZIEL | PV0 / PV30 / PV70 | 0,30→0,50 / 0,30→0,25 / 0,30→0,15 |
| Hinweise | – | Beschreibungstexte | angepasst |

Dazu wurden Prüfsummenspalten der Geometrie mit 1 befüllt (keine Wirkung auf die Rechnung).

## 3 Rekonstruktionstest der aktiven Basis

Ausgeführt in der Sandbox (Python 3.14.8, pandas 3.0.1, numpy 2.5.4, scipy 1.18.1). Das ist kein Ersatz für die lokale Abnahme mit Python 3.12.8.

| Prüfung | Ergebnis |
|---|---|
| `distribution_to_json.py self-test` | 19/19 OK |
| `tests/test_regression.py` | 7/8 OK, 1 Fehler |
| Bestand_2024 gegen Referenz | max. Abweichung 5·10⁻⁶ m², 14.640 belegte Typen, 889.872.558 m² NGF – reproduziert |
| Transition_2040 gegen Referenz | max. Abweichung 1.567.311 m², **16.320** statt 14.160 belegte Typen, Summe gleich |

Folgerung: `tests/referenz_Transition_2040.csv` und `testdaten/Reale_Zustaende/Transition_2040/Verteilung.csv` beschreiben den Zustand aus der **alten** Transition-Excel.

Nachprüfung mit den gesicherten Ergebnissen:

| Prüfung | Ergebnis |
|---|---|
| Eingabe-Excel in `results/szenarien/*/eingaben/` | SHA-256-gleich mit aktueller `data`-Excel (beide Szenarien) |
| Neuberechnung vs. gespeicherte `Verteilung.csv` | max. 6·10⁻¹¹ m² (Bestand 14.640, Transition 16.320 belegte Typen) |
| Flussrekonstruktion `Bestand_2024__Transition_2040` | Status NICHT_MACHBAR; die `zustand_id` von A und B stimmen mit den gespeicherten Zuständen überein, beruhen also auf der aktuellen Excel |

**Entscheidung (Nutzer, 16.11.2026):** Gültig ist die aktuelle Fassung der Transition-Excel (Bio 0,18). Neue Regressionsreferenzen sind die gespeicherten Zustände:

| Zustand | Referenzdatei | SHA-256 | zustand_id |
|---|---|---|---|
| Bestand_2024 | `results/szenarien/Bestand_2024/Verteilung.csv` | `40b3ee4b…de142` | `cb97226c…20dff` |
| Transition_2040 | `results/szenarien/Transition_2040/Verteilung.csv` | `88ffe2a8…8ce54` | `aa2f08fe…0f913a` |

Die alte Transition-Referenz wird in AP1 als veraltet archiviert und durch diese Referenz ersetzt (`tests/daten/`).

## 4 Kennzeichnung (Kurzfassung)

Vollständige Liste mit Pfad, SHA-256, Status, Rolle und Zielpfad: `Versionsmanifest_AP0.csv`.

| Status | Anzahl | Bedeutung |
|---|---|---|
| AKTIV | 13 | Grundlage der Finalisierung |
| AKTIV_BASIS_UEBERARBEITEN | 3 | Grundlage, muss vor Nutzung angepasst werden (Notebooks) |
| VERALTET | 4 | ersetzt; wird archiviert (u. a. alte Transition-Referenzen) |
| EXPERIMENTELL_ZURUECKGESTELLT | 22 | zielgeführte Entwicklung → `archiv/zielgefuehrte_entwicklung/Integration_2_2_20261116/` |
| ARCHIV_ORIGINAL | 14 | unveränderte Übergabedateien |
| DUPLIKAT | 2 | inhaltsgleiche Kopien |
| ERGEBNIS_REFERENZ | 31 | gespeicherte Zustände, Vergleich und Flussdiagnose |
| TESTDATEN | 17 | synthetische und Referenzzustände |
| DOKU_HISTORISCH | 5 | Berichte und Anleitungen vom 13.11. |

Wesentliche Zuordnungen:

- `modell/gebaeudesektor.py` ← Wurzel-`gebaeudesektor.py` (ohne die zielgeführten Hooks aus Integration_2_2).
- `modell/flaechenstroeme.py` ← `Integration_2_2/flaechenstroeme.py` (neueste Fassung mit Blockdiagnose, Übernahme vorhandener Flüsse und Exportzielschutz; keine Abhängigkeit zu zielgeführten Modulen). Die Wurzelfassung ist veraltet.
- `notebooks/02_Szenarienvergleich.ipynb` ← `Integration_2_2/Gebaeudesektor_Szenarienvergleich.ipynb` (ohne automatische Rekonstruktion). Die Wurzelfassung startet in der letzten Zelle `analysiere_fluesse(ersetzen=True)` und ist veraltet.
- Zurückgestellt: `zielszenario_*.py`, `zielprofil_import.py`, `Globale_Ziele_Transition2040.xlsx`, zielgeführtes Notebook und Tests aus `Integration_2_2`.

## 5 Abweichungen vom Arbeitsauftrag (Ist-Zustand)

| Thema | Befund |
|---|---|
| Struktur | flach im Wurzelordner; `config/`, `modell/`, `notebooks/`, `docs/` fehlen |
| Notebook-Defaults | Szenario: `SPEICHERN=True`, `ERSETZEN=True`; Vergleich: `EXPORTIEREN=True`, `EXPORT_ERSETZEN=True`, startet Rekonstruktion; Flächenströme: `EXPORTIEREN=True`, `ERSETZEN=True`, nutzt private Funktionen |
| Vergleich | nur paarweise, Logik inline im Notebook; kein `szenarienvergleich.py`, keine Kennwerttabelle nach Schema |
| Neubau/Abriss | nicht vorhanden; Rekonstruktion verlangt gleiche Gesamtflächen |
| Änderungsraten | nicht vorhanden |
| Absolute Pfade | in `vergleichsprotokoll.json` und Laufprotokollen (Ergebnisse, nicht Modellcode) |
| Ergebnisablage | `Blockdiagnose.csv` im Wurzelordner |
| Export-ACL | `tempfile.mkdtemp` erzeugt unter Windows nur für den Ersteller lesbare Ordner |
| Tests | `test_flaechenstroeme.py`, `requirements_flaechenstroeme.txt` und Beispielregeln (Referenz/Demo/Großtest) werden in `README_Flaechenstroeme.md` genannt, fehlen aber |
| Umgebung | kein `requirements_getestet.txt`; `pyarrow` nur als Kommentar, ist aber für `scenarios.parquet` zwingend |
| Regression | Transition-Referenz im Testordner veraltet; gültige Referenz festgelegt (Abschnitt 3) |

## 6 Fehlende Eingaben und Entscheidungen

Sperrend für einzelne Arbeitspakete:

| Nr. | Fehlt | betrifft | sperrt |
|---|---|---|---|
| E1 | ~~Lesezugriff auf gesperrte Ergebnisordner~~ | erledigt 16.11. (Kopie gesichert) | – |
| E2 | ~~Gültige Transition-Excel~~ | entschieden 16.11.: aktuelle Fassung (Bio 0,18) | – |
| E3 | `Bestandsentwicklung.xlsx` (Neubau/Abriss je Periode) | Bestandsbilanz | AP3 externe Flüsse |
| E4 | Neubau/Abriss als Periodenflächen oder als Raten | Bestandsbilanz | AP3 |
| E5 | Zuordnung des Abrisses (nach Bauperiode, Typ, proportional) | Bestandsbilanz | AP3 |
| E6 | Welche Tabellen Gesamtbestand, verbleibender Bestand bzw. Neubau beschreiben | Zustand B | AP3 |
| E7 | Welche Qualitätsübergänge als „thermische Sanierung“ zählen | Raten | AP5 |
| E8 | Bezug „Ausgangs-NGF“ (T_A) als Nenner bestätigen | Raten | AP5 |
| E9 | Bezeichnung „Kesseltauschrate“ vs. „Versorgungstauschrate“ | Raten, Doku | AP5 |
| E10 | Lokaler Python-Interpreter für Abnahme (Pfad zur Jupyter-Umgebung) | lokale Abnahme | AP7 |

Nicht sperrend: weitere Szenarien in `config/szenarien.json`, Referenzszenario für den Mehrszenarienvergleich (Vorschlag: Bestand_2024).

## 7 Status und nächste Schritte

AP0 ist abgeschlossen. Es wurden keine Projektdateien verändert, verschoben oder gelöscht; neu sind nur die Sicherungen unter `archiv/sicherungen/` und die Dokumente unter `docs/AP0/`.

Nächster Schritt AP1: Zielstruktur anlegen, `config/projekt.json` mit relativen Pfaden, Module nach `modell/`, sichere Exporte ohne restriktive ACL, Regressionsreferenzen gemäß Abschnitt 3, `requirements_getestet.txt`, Archivierung der zielgeführten Stände.
