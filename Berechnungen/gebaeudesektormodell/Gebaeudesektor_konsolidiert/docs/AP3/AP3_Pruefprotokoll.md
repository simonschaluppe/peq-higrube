# AP3 – Prüfprotokoll Flussrekonstruktion konstanter Bestand

Stand: 16.11.2026 · Modellversion 1.3.0-AP3 · Prüfumgebung Python 3.14 / pandas 3.1

## Ergebnis

AP3 ist technisch umgesetzt. Die Rekonstruktion für konstanten Bestand liefert immer einen der sechs Statuswerte. Die Zustände A und B werden nur gelesen; vor und nach jedem Lauf wird über Dateihashes nachgewiesen, dass sie unverändert sind. Im Standardlauf von Notebook 03 werden nur vorhandene Flüsse gelesen. Es startet kein Solver und es wird nichts geschrieben. Alle 47 automatischen Tests und der Selbsttest der Excel-Einlesung (19) sind bestanden (`AP3_Testlauf.txt`).

Zusätzlich: drittes Szenario `Transition_2040_Wachstum` (950 Mio. m² NGF) und Vergleich `Bestand_Transition_Wachstum_2040` registriert. Damit ist die AP2-Abnahme mit drei echten Szenarien möglich.

## Abnahme AP3 (Arbeitsauftrag Abschnitte 9 und 15)

| Anforderung | Umsetzung | Nachweis |
|---|---|---|
| A/B bleiben unverändert | Laden mit Integritätsprüfung (`lade_zustaende_geprueft`); Hashvergleich von `Verteilung.csv` und `laufprotokoll.json` vor/nach jedem Lauf | `Projektablauf.assertZustaendeUnveraendert` in allen Projekttests |
| Gültige Flüsse oder korrekter Fehlerstatus | `analysiere_rekonstruktion` gibt immer `status` aus `STATUSWERTE` und `statusbedeutung` zurück | alle Tests in `test_flaechenstroeme.py` |
| Timeout ist kein Unmachbarkeitsnachweis | Solverstatus 1 → `NICHT_ABSCHLIESSEND_GELOEST`; 2 → `NICHT_MACHBAR`; 4/Numerik → `BERECHNUNGSFEHLER`; Zeitlimit `ZEITLIMIT_S` | `test_statuszuordnung_solver` |
| Keine Nachkalibrierung, kein automatischer Flächenausgleich, keine zusätzlichen Übergänge, Ziel unverändert | Zielfunktion: maximale vollständig unveränderte Fläche; ungleiche NGF → `NICHT_MACHBAR` mit HINWEIS | `test_zeitreihenfolge_und_gesamtbilanz`, `test_verbotene_uebergaenge` |
| Laden/Analysieren startet keine Optimierung | Standard `MODUS='VorhandeneFluesse'`; Solver nur mit `MODUS='Rekonstruktion'` und `REKONSTRUIEREN=True` | `test_1_…`, `test_3_…`, `test_4_…` (Solveraufruf führt zu Testabbruch), `test_5_notebook_03_standardlauf_schreibt_nichts` |
| Notebook-Ablauf 1–8, Standardwerte `False`, nur Modulaufrufe, Markdown vor jedem Abschnitt | Notebook 03 neu | `test_standardwerte`, `test_03_nur_modulfunktionen`, `test_keine_verbotenen_muster_und_markdown` |
| Speichern nur bewusst, Ersetzungsschutz, Wiederladen | `speichere_ergebnis` mit Arbeitsordner, `FileExistsError` ohne `ERSETZEN`, Ausgabehashes; Manipulation erkannt | `test_3_nicht_machbar_export_wiederladen_ohne_solver` |
| Keine absoluten Pfade | Protokolle projektrelativ, Eingaben ohne Datenrahmen und Ordnerpfade | `test_3_…`, `test_modell` |

## Pflichtprüfungen

Vor jeder Rekonstruktion oder Übernahme (`pruefe_eingaben`): Regeln gültig, Zustand A und B gültig (Typen, Nichtnegativität, Fernwärme/Wetter, WP-Qualität), A und B gespeichert und unverändert, Zeitreihenfolge, Gesamtbilanz.

An jeder Flusstabelle (`pruefe_fluesse`, 17 Prüfungen): Nichtnegativität, unveränderliche Eigenschaften (Geometrie, Wetter, Speichermasse), zulässige Einzelübergänge je Merkmal (7), gemeinsame Zielkombination nur als belegter Zieltyp, WP-Zielqualität, Fernwärme/Wetter, Herkunfts- und Zielrandsummen, Gesamtbilanz.

## Testfälle nach Arbeitsauftrag

| Fall | Ergebnis | Test |
|---|---|---|
| Identische Zustände | `MACHBAR`, alle Flüsse unverändert (synthetisch und volle Größe 889,87 Mio. m²) | `test_identisch_unveraendert`, `test_4_identische_zustaende_volle_groesse` |
| Einzelne erlaubte Änderung Qualität, Versorgung, PV, Flex | je `MACHBAR`, genau 25 m² geändert, alle Prüfungen OK | `test_einzelne_erlaubte_wechsel` |
| Mehrfachmaßnahme | je Merkmal 25 %, „beliebige Änderung“ 25 % ohne Doppelzählung | `test_mehrfachmassnahme_ohne_doppelzaehlung` |
| Verbotener Übergang (PV-Rückschritt, Speichermasse) | `NICHT_MACHBAR`, keine Flüsse, Diagnose | `test_verbotene_uebergaenge` |
| WP in unzulässiger Qualität; falsche Fernwärme/Wetter | Zustand abgewiesen, Pflichtprüfung FEHLER | `test_wp_zielqualitaet_und_fernwaerme_wetter` |
| Zieljahr ≤ Ausgangsjahr | abgewiesen | `test_zeitreihenfolge_und_gesamtbilanz` |
| Vorhandene Flüsse laden ohne Solver | gespeichertes Ergebnis und registrierte Flussdatei; manipulierte Datei abgewiesen | `test_3_…`, `test_4_…` |
| Fehlender Zustand B | `EINGABEN_UNGUELTIG` | `test_2_fehlender_zustand_eingaben_ungueltig` |
| Register ändert Zustands-IDs nicht | ein weiteres Szenario lässt Fingerprint und ID unverändert | `test_zustand_id_unabhaengig_vom_register` |

## Kontrollrechnungen (volle Größe)

| Paar | Ergebnis |
|---|---|
| Bestand 2024 → Transition 2040 | `NICHT_MACHBAR` in ca. 6 s; alle 60 unveränderlichen Blöcke vom Solver als unzulässig erkannt (Status 2). Blockdiagnose: Transition enthält rund 55,1 Mio. m² mehr Biomasse; ein Wechsel nach `Bio` ist in `uebergaenge.json` nicht vorgesehen. |
| Bestand 2024 → Transition 2040 Wachstum | `NICHT_MACHBAR`; Pflichtprüfung Gesamtbilanz: HINWEIS (Differenz ca. 60,1 Mio. m², externe Flüsse erst in AP4) |
| Konstruiertes Zielbild (30 % der alten Erdgas-/Öl-Flächen → Neu_20cm + WP_Luft, 20 % PV0 → PV30) | `MACHBAR` in ca. 7 s; 20 352 Flüsse; 79,53 % der Fläche vollständig unverändert; alle 17 Prüfungen OK; „beliebige Änderung“ 20,47 % ≤ konstruiert 22,29 % (Mindestzuordnung) |
| Transition 2040 Wachstum | 950 000 000 m² NGF, Bilanzkontrollen OK; im Vergleich alle 213 Kennwerte VERGLEICHBAR |

## Festgestellt und behoben

- Der Eingabe-Fingerprint enthielt den Hash von `config/szenarien.json`. Jedes neu registrierte Szenario hätte die Zustands-IDs aller bereits gespeicherten Szenarien geändert. Das Register ist jetzt ausgenommen. Weil `gebaeudesektor.py` geändert wurde, ändern sich alle Zustands-IDs **einmalig**; Flächen und Kennwerte bleiben gleich.
- In `flaechenstroeme.py` gab es zwei Fassungen von `analysiere_rekonstruktion` und die Altfunktion `analysiere_fluesse`; beide entfernt.

## Annahmen

- Zielfunktion: maximale vollständig unveränderte Typenfläche; gleichwertige Lösungen können existieren. Die Flüsse sind eine zulässige Zuordnung, keine beobachteten Maßnahmen.
- Änderungsanteile vorläufig, Nenner Ausgangs-NGF (E8 offen); vollständige Raten in AP5.
- `Transition_2040_Wachstum` ist ein illustratives Zielbild (Verteilung wie Transition 2040, skaliert auf 950 Mio. m²).

## Offene Punkte

1. Lokal alle drei Szenarien neu speichern (neue Zustands-IDs), dann 02 und 03 ausführen.
2. Fachliche Entscheidung zum Biomasseübergang (Regel ergänzen oder Zielbild anpassen); erst dann kann Bestand → Transition `MACHBAR` werden.
3. Gesperrte Altordner unter `results/flaechenstroeme/` im Explorer entfernen.
4. AP4: externe Flüsse (Neubau/Abriss) für das Wachstumspaar.
