# AP4 – Prüfprotokoll Neubau-/Abrissbilanz

Stand: 16.11.2026 · Paketversion 1.4.0-AP4 (Rechenkern `gebaeudesektor.py` unverändert, 1.3.0-AP3) · Prüfumgebung Python 3.14 / pandas 3.1

## Ergebnis

AP4 ist technisch umgesetzt. Neubau und Abriss werden als explizite Bruttoflüsse bilanziert und in der Rekonstruktion als eigene externe Flüsse geführt. Aus A und B allein (nur \(N - D\)) wird nichts abgeleitet, auch nicht \(N = D = 0\). Alle 60 automatischen Tests und der Selbsttest der Excel-Einlesung (19) sind bestanden (`AP4_Testlauf.txt`).

Mit den beiden neuen Versorgungsregeln (Bio → WP, Erdgas/Öl → Elektro) ist `Bestand_2024__Transition_2040` jetzt `MACHBAR`: 30 780 Flüsse, 46,25 % der Fläche bleiben vollständig unverändert, die beliebige Änderung beträgt 53,75 %. Das entspricht der minimalen Umverteilung aus AP2.

Nach der fachlichen Entscheidung vom 16.11.2026 („im Wachstumsszenario bzw. für Neubauten keine zusätzlichen Flächen für 1990-99 und Neu_10cm“) wurde Szenario 3 angepasst. `Bestand_2024__Transition_2040_Wachstum` ist jetzt mit den Standardfreigaben `MACHBAR`: 29 932 Flüsse, alle 29 Pflichtprüfungen OK, Neubau 80 Mio. m² nur in Neu_20cm/Neu_30cm, Abriss 19,87 Mio. m² nur aus vor1919–1980-89.

## Bilanz des Wachstumspaars

| Größe | m² NGF | % von NGF A | %/a |
|---|---:|---:|---:|
| Ausgangsbestand T_A (2024) | 889 872 558 | 100 | – |
| Abriss D (Bilanzrest) | 19 872 558 | 2,23 | 0,140 |
| Neubau N (Vorgabe) | 80 000 000 | 8,99 | 0,562 |
| Zielbestand T_B (2040) | 950 000 000 | 106,76 | – |
| Nettoänderung N − D | 60 127 442 | 6,76 | 0,423 |

Die Vorgabe „Abriss 19,9 Mio. m²“ hätte \(T_A - D + N\) um 27 442 m² verfehlt (Bilanztoleranz 1 m²). Der Abriss ist deshalb ausdrücklich als `Bilanzrest` eingetragen. Das ist in der Excel-Bemerkung dokumentiert. Ein fester Wert von 19,9 Mio. m² ergäbe `WIDERSPRUCH` (Test `test_vorgaben_widersprechen_bilanz`).

## Anpassung von Szenario 3

Vorher übernahm Szenario 3 die Anteile von Transition 2040 und skalierte sie auf 950 Mio. m². Dadurch lagen 1990-99 (+5,32 Mio. m²) und Neu_10cm (+3,91 Mio. m²) absolut über dem Bestand. Für diese Qualitäten gibt es weder Zufluss aus dem Bestand noch eine Neubaufreigabe, daher war das Paar `NICHT_MACHBAR` (9,23 Mio. m², durch Hüllendiagnose und Schlupf-LP bestätigt).

Neu ist die eigene Verteilungsdatei `Verteilung_Transition_2040_Wachstum.xlsx`. Sie ist eine Kopie von Transition 2040; geändert sind nur die Zielzeile im Blatt `Qualitaet` und die Hinweise.

| Qualität | Zielanteil Transition 2040 | Zielanteil Wachstum (neu) | Fläche Wachstum 2040 | Bestand 2024 |
|---|---:|---:|---:|---:|
| 1990-99 | 8,84 % | 8,2805 % | 78 664 734 m² | 78 664 734 m² |
| Neu_10cm | 6,51 % | 6,0980 % | 57 930 704 m² | 57 930 704 m² |
| Neu_20cm | 33,65 % | 34,1636 % | 324 554 415 m² | 245 248 877 m² |
| Neu_30cm | 30,00 % | 30,4579 % | 289 350 147 m² | 123 514 311 m² |
| übrige (vor1919 … 1980-89) | 21,00 % | 21,00 % | unverändert anteilig | – |

Die Anteile für 1990-99 und Neu_10cm sind Bestandsfläche / 950 Mio. m² in voller Genauigkeit. Die frei werdenden ≈0,97 %-Punkte sind im Verhältnis 33,65 : 30 auf Neu_20cm und Neu_30cm verteilt (Annahme, im Hinweisblatt dokumentiert). Versorgung, PV, Flexibilität, Geometrie und Speichermasse sind unverändert. Die Zustands-ID von Szenario 3 ändert sich; es muss lokal neu gespeichert werden.

Numerischer Hinweis: Nach der Kalibrierung liegt 1990-99 um 0,001 m² über dem Bestand (Rundungsrest, Toleranz 0,01 m²). Das LP mit der strengen Solvertoleranz (1e-10, skaliert) meldete deshalb „unzulässig“, ein Schlupf-LP zeigte aber keinen Konflikt. `flaechenstroeme.py` führt jetzt in diesem Fall einen zweiten Lauf mit der aus `toleranz_m2` abgeleiteten Toleranz (1e-7 ≙ 0,001 m²) aus. Die Rand- und Bilanzprüfungen bleiben unverändert streng (größter Herkunftsfehler 0,00004 m², größter Zielfehler 0,000003 m²).

## Ergebnis Wachstumspaar

| Kennzahl | m² NGF | % von NGF A | %/a |
|---|---:|---:|---:|
| Vollständig unverändert | 426 405 464 | 47,92 | – |
| Beliebige Änderung (ohne Doppelzählung) | 443 594 536 | 49,85 | 3,12 |
| Abriss (explizit) | 19 872 558 | 2,23 | 0,14 |
| Neubau (explizit) | 80 000 000 | 8,99 | 0,56 |
| Qualitätswechsel | 165,14 Mio. | 18,56 | 1,16 |
| Versorgungswechsel | 424,05 Mio. | 47,65 | 2,98 |
| PV-Wechsel | 287,87 Mio. | 32,35 | 2,02 |
| Flex-Wechsel | 19,65 Mio. | 2,21 | 0,14 |

| Qualität | Abriss | Neubau | B gesamt |
|---|---:|---:|---:|
| vor1919 | 4 364 356 | 0 | 38 000 000 |
| 1919-44 | 585 402 | 0 | 19 000 000 |
| 1945-59 | 923 265 | 0 | 28 500 000 |
| 1960-79 | 9 868 186 | 0 | 76 000 000 |
| 1980-89 | 4 131 350 | 0 | 38 000 000 |
| 1990-99 | 0 | 0 | 78 664 734 |
| Neu_10cm | 0 | 0 | 57 930 704 |
| Neu_20cm | 0 | 23 448 597 | 324 554 415 |
| Neu_30cm | 0 | 56 551 403 | 289 350 147 |

Die Aufteilung von Abriss und Neubau auf Typen ist eine zulässige Zuordnung mit maximal unveränderter Fläche, nicht eindeutig (keine weiteren Präferenzen festgelegt). Rechenzeit in der Prüfumgebung rund 45 s.

## Abnahme AP4 (Arbeitsauftrag Abschnitte 6, 10, 11, 12)

| Anforderung | Umsetzung | Nachweis |
|---|---|---|
| \(T_B = T_A - D + N\); \(A_i = \sum_j F_{ij} + D_i\); \(B_j = \sum_i F_{ij} + N_j\) | gemeinsames LP mit Variablen F, D, N; Randsummenprüfung inkl. D/N | `pruefe_fluesse`: Herkunfts-/Zielrandsummen, Gesamtbilanz, Abriss/Neubau = Vorgabe |
| Keine Netto-Identifikation, kein automatisches N = D = 0 | ohne Bruttoangaben `NUR_NETTO`; ungleiche NGF → FEHLER; gleiche NGF → Rekonstruktion ohne externe Flüsse, ausdrücklich so gekennzeichnet | `test_nur_nettoaenderung_bekannt`, `test_gleicher_gesamtbestand_mit_neubau_und_abriss` |
| Unveränderliche Eigenschaften nur für Bestandsübergänge | Blockbindung nur für F; D/N nur über Freigaben | Pflichtprüfungen, `test_rueckgang_nur_durch_abriss` |
| Bezugsbasis dokumentiert | Raten: NGF A; `zusammensetzung`: Abriss bezogen auf A der Kategorie, Neubau auf B | `BEDIENUNG.md`, Notebook 03 Abschnitt 7 |
| Weitere Präferenzen nur nach Entscheidung | keine; Auswahl innerhalb der Freigaben durch maximale unveränderte Fläche, als nicht eindeutig gekennzeichnet | Protokollfeld `mehrdeutigkeit` |
| `bestandsbilanz.py` ohne zweiten Rechenkern | liest nur Vorgaben und Gesamtflächen gespeicherter Zustände | Modulinhalt; keine Zustandserzeugung |
| Neubau/Abriss nicht als Gebäudetypen; externe Sankey-Knoten nur Darstellung | eigene Dateien `Neubau.csv`/`Abriss.csv`; Knoten „Neubau (Zeitraum)“/„Abriss (Zeitraum)“ | `test_mehrere_massnahmen_ohne_doppelzaehlung_mit_neubau` |
| Laden/Analysieren startet keine Optimierung | Standardmodus liest nur; Diagnose vor dem LP | Solveraufruf führt in `Wachstumspaar.test_1/2/3` zum Abbruch |
| Gespeichertes Ergebnis nur bei gleichen Vorgaben | `extern_signatur` (Mengen, Freigaben) | `test_2_standardfreigaben_machbar_export_laden` |
| Keine absoluten Pfade | Bestandsentwicklung projektrelativ im Protokoll | `test_projektpfade_relativ`, `test_projektdatei_gueltig` |

## Testfälle nach Arbeitsauftrag (Abschnitt 12)

| Fall | Ergebnis | Test |
|---|---|---|
| Gleicher Gesamtbestand mit gleichzeitigem Neubau und Abriss | `BILANZ_OK`, je 10 m² Neubau und Abriss, 90 m² unverändert | `test_gleicher_gesamtbestand_mit_neubau_und_abriss` |
| Wachstum nur durch Neubau (Rate 1,25 %/a) | 20 m² Neubau, kein Abriss, Bestand unverändert | `test_wachstum_nur_durch_neubau_rate` |
| Rückgang nur durch Abriss | 15 m² Abriss aus vor1919, kein Neubau | `test_rueckgang_nur_durch_abriss` |
| Nur Nettoänderung bekannt | `NUR_NETTO`, Pflichtprüfung FEHLER, keine Mengen behauptet | `test_nur_nettoaenderung_bekannt` |
| Vorgaben widersprechen A/B | `WIDERSPRUCH` (auch 80/19,9 Mio.), negativer Bilanzrest, `UNVOLLSTAENDIG` | `test_vorgaben_widersprechen_bilanz` |
| Mehrere Maßnahmen ohne Doppelzählung | je Merkmal 25 m², beliebige Änderung 25 m² (nicht 75), Neubau gesondert | `test_mehrere_massnahmen_ohne_doppelzaehlung_mit_neubau` |
| Freigaben verletzt / Hüllenkonflikt | `NICHT_MACHBAR` ohne Solver, Defizit beziffert; mit Freigabe machbar | `test_freigaben_und_huellendiagnose` |
| Manipulierte externe Flüsse | Pflichtprüfungen FEHLER | `test_pruefe_fluesse_erkennt_manipulierte_externe_fluesse` |
| Ungültige Excel-Eingaben | abgewiesen mit Meldung | `test_validierungsfehler` |
| Wachstumspaar volle Größe | Bilanz OK; Standardfreigaben `MACHBAR` (1990-99/Neu_10cm unverändert, Neubau nur Neu_20/30, WP/DH), Export, Laden ohne Solver, veraltet nach Änderung der Vorgaben; Neubau ohne Neu_30cm `NICHT_MACHBAR` mit Diagnose | `Wachstumspaar.test_1–3` |
| Szenario 3 ohne Zuwachs bei 1990-99/Neu_10cm | Abweichung zum Bestand ≤ 0,01 m² | `test_drittes_szenario_wachstum` |

## Lokale Abnahme

1. In `01_Szenario` Szenario 3 neu speichern (`SZENARIO='Transition_2040_Wachstum'`, `BERECHNEN`, `ENERGIE_BERECHNEN`, `EXPORTIEREN`, `ERSETZEN` jeweils `True`); Bestand 2024 und Transition 2040 bleiben gültig.
2. `02_Szenarienvergleich` mit `VERGLEICH='Bestand_Transition_Wachstum_2040'`.
3. `03_Flaechenstroeme` im Standardlauf; danach für beide Paare mit `MODUS='Rekonstruktion'`, `REKONSTRUIEREN=True` (optional `EXPORTIEREN=True`). Erwartung: beide Paare `MACHBAR`; Wachstum mit 29 932 Flüssen, 47,92 % unverändert, Neubau 80 000 000 m², Abriss 19 872 558 m² (Flusszahl kann je nach Solverversion leicht abweichen; die Bilanzsummen nicht).
