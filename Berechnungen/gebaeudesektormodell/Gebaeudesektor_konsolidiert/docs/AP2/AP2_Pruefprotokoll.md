# AP2 – Prüfprotokoll Mehrszenarienvergleich

Stand: 16.11.2026 · Modellversion 1.2.0-AP2 · Rechenkern `gebaeudesektor.py` unverändert (SHA-256 `76e72fbb…5252`)

## Ergebnis

AP2 ist technisch umgesetzt. Der Vergleich liest ausschließlich gespeicherte Szenarioergebnisse, rechnet keine Zustände neu und startet keine Flussrekonstruktion. Alle 33 automatischen Tests und der Selbsttest der Excel-Einlesung (19) sind bestanden.

Für die fachliche Abnahme „mindestens drei Szenarien über gemeinsame Kennwerttabelle vergleichen“ fehlt im Projekt noch ein drittes, fachlich gewünschtes Szenario. Die Funktion ist mit drei Szenarien getestet (Testszenario `Transition_2040_Wachstum`, nur im Testprojekt registriert).

## Abnahmekriterien Arbeitsauftrag Abschnitt 6

| Anforderung | Umsetzung | Nachweis |
|---|---|---|
| Ablauf: auswählen → Kennwerttabelle → Vergleichbarkeit → Übersicht → Referenz → optional Paar → optional Export | Notebook 02 in genau dieser Reihenfolge, je Abschnitt Markdown (Was, Eingaben, Rechnet/liest, Annahmen, Interpretation, sperrende Fehler) | `test_keine_verbotenen_muster_und_markdown`, `test_02_nur_modulfunktionen` |
| Keine Flussrekonstruktion beim vollständigen Ausführen | 02 importiert nur `gebaeudesektor` und `szenarienvergleich`; kein `flaechenstroeme`, kein `linprog` | `test_02_nur_modulfunktionen`, `test_notebook_02_standardlauf_schreibt_nichts` |
| Mindestens drei Szenarien über gemeinsame Kennwerttabelle | `sv.vergleiche([...])` mit beliebig vielen Szenarien | `test_drei_szenarien_gemeinsame_tabelle` |
| Status VERGLEICHBAR / BEDINGT / NICHT / KENNWERT_FEHLT | `status_paar`, Regeln in `docs/DATENSCHEMATA.md` | `test_status_paar` (11 Fälle) |
| Nicht vergleichbare Energiewerte sperren den Flächenvergleich nicht | Flächen- und Energiekennwerte getrennt bewertet | `test_flaeche_trotz_fehlender_energie` |
| Drei Ansichten | `uebersicht`, `referenzvergleich`, `paarvergleich` | Tests oben |
| Absolute Differenz; relative Änderung nur bei Basis ≠ 0; pp für Anteile; Jahresrate nur bei positiver Zeitspanne | `_differenz`, `differenzen` | `test_differenzregeln` |
| Gleichjährige Alternativszenarien vergleichbar, ohne Jahresrate | `Jahre = 0` → `Netto_pro_Jahr` leer, Hinweis „gleiches Jahr: keine Jahresrate“ | `test_gleichjaehrig_keine_jahresrate_und_zerlegung` |
| Exportdateien | `Kennwerte_Alle_Szenarien.csv`, `Vergleichbarkeit.csv`, `Referenzvergleich.csv`, `Paarvergleich.csv`, `Vergleich.xlsx`, `Vergleich.html`, `vergleichsprotokoll.json` (zusätzlich `Typenvergleich.csv`) | `test_export_schutz_und_wiederladen` |
| Export nur bewusst, kein stilles Überschreiben | `EXPORTIEREN=False`, `ERSETZEN=False`; `FileExistsError` ohne `ERSETZEN`; Arbeitsordner, dann Veröffentlichung | `test_export_schutz_und_wiederladen`, `test_standardwerte` |
| Keine absoluten Pfade | Protokoll nur projektrelativ | `test_export_schutz_und_wiederladen`, `test_modell` |

## Kontrollrechnungen

| Prüfung | Ergebnis |
|---|---|
| Lokale Ergebnisse (vom Gerät übernommen) Bestand_2024 → Transition_2040 | Integrität beider Szenarien OK; 126 Flächen- und 87 Energiekennwerte VERGLEICHBAR |
| Minimale Umverteilung Bestand → Transition | Geometrie, Wetter, Speichermasse 0; Qualität 22,21 %; Planversorgung 37,00 %; PV 30,00 %; Flexibilität 2,33 %; vollständiger Typenschlüssel 53,75 % der NGF |
| Testszenario Wachstum (950 Mio. m², ohne Energie) gegen Bestand | NGF-Δ 60 127 442 m², 3 757 965 m²/a über 16 Jahre; alle 87 Energiekennwerte KENNWERT_FEHLT, alle 126 Flächenkennwerte VERGLEICHBAR |
| Paar Transition 2040 → Wachstum 2040 (gleichjährig, skaliert) | keine Jahresraten; Δ = Flächeneffekt + Struktureffekt exakt; Struktureffekt < 1 m²; minimale Umverteilung nicht ausgewiesen (NGF verschieden) |
| Plotly 5.22.0 (lokale Version) | alle Grafiken und `Vergleich.html` erzeugt |
| Export, Wiederladen, Manipulation | Hashes geprüft; geänderte Ausgabedatei wird beim Laden abgewiesen; nach `ERSETZEN=True` keine Arbeits- oder Sicherungsordner übrig |

## Festgestellt und behoben

- Summenzeilen der Endenergieträger (`SUMME ohne Umgebungswärme`) haben in `Kennwerte.csv` keine Abdeckung und wurden daher zunächst als NICHT_VERGLEICHBAR eingestuft. Der Vergleich übernimmt jetzt die kleinste Abdeckung der Einzelträger. Der Rechenkern bleibt unverändert, weil jede Änderung an `gebaeudesektor.py` alle Zustands-IDs ändert.

## Annahmen

- Mindestabdeckung 95 % (in `config/vergleiche.json`, je Vergleich überschreibbar).
- Paarvergleich auf Planversorgung (Fernwärme Wien und erneuerbare Fernwärme zusammengefasst als DH).

## Offene Punkte

1. Drittes fachliches Szenario für die Abnahme festlegen, in `config/szenarien.json` registrieren, in 01 speichern und in `config/vergleiche.json` aufnehmen.
2. `02_Szenarienvergleich` lokal ausführen (Standard: kein Export). Der vorhandene Ordner `results/vergleiche/Bestand_2024__Transition_2040/` hat das alte Format; zum Ersetzen `EXPORTIEREN=True` und `ERSETZEN=True` setzen.
3. Zustands-ID hängt am Hash der gesamten Kerndatei (Vorschlag: explizite Kernversion), siehe `docs/OFFENE_PUNKTE.md`.
4. `01_Szenario` nutzt noch `gs._relativ` (AP6).

## Testlauf

Vollständige Ausgabe: `docs/AP2/AP2_Testlauf.txt`. Befehle im Projektordner:

```
python -m unittest discover -s tests -v      # 33 Tests, OK
python modell/distribution_to_json.py self-test   # 19 Tests, OK
```

Prüfumgebung: Python 3.14.8, pandas 3.1.1, numpy 2.5.4, plotly 7.1.0 (zusätzlich Grafiken mit plotly 5.22.0).
