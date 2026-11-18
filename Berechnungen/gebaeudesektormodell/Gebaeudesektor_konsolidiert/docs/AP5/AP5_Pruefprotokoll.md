# AP5 – Prüfprotokoll Maßnahmenraten

Stand 17.11.2026 · Modell 1.5.1-AP5 (Nachtrag zu 1.5.0 vom 16.11.2026) · Prüfumgebung Python 3.14 / pandas 3.1.1 (lokale Referenz 3.12.4 / 3.0.0 wird in AP7 bestätigt)

## Auftrag und Festlegungen

Arbeitspaket 5 (Arbeitsauftrag Abschnitt 9 und 11): Änderungsraten und Maßnahmenkombinationen aus gültigen Flüssen, mit einheitlichem Nenner und korrekter Behandlung von Überschneidungen.

| Nr. | Festlegung (16.11.2026) | Umsetzung |
|---|---|---|
| E7 | Thermische Sanierung = alle zulässigen Qualitätswechsel | `massnahmen.json`: vor1919, 1919-44, 1945-59, 1960-79, 1980-89 → Neu_20cm/Neu_30cm (10 Paare). Notebook 03 prüft gegen `uebergaenge.json`: 10 klassifiziert, 10 zulässig (OK) |
| E8 | Nenner = Ausgangs-NGF | \(r_M = 100 \cdot A_M / (T_A \cdot (J_B - J_A))\), für alle Raten gleich; andere Nenner werden abgelehnt |
| E9 | Begriff „Versorgungswechselrate“ | Erläuterung: umgangssprachlich „Kesseltauschrate“; umfasst auch Wechsel zu WP/Fernwärme; Kesseltausch innerhalb einer Kategorie nicht erkennbar |

## Nachtrag 17.11.2026 (1.5.1)

### Entscheidungen

| Thema | Entscheidung | Umsetzung |
|---|---|---|
| Neubau-Freigaben | Wärmepumpe, Fernwärme, Biomasse und Elektro; Qualität Neu_20cm/Neu_30cm | `Bestandsentwicklung.xlsx`: Bio und Elektro freigegeben; Erdgas/Öl gesperrt |
| Abriss-Freigaben | vor1919, 1919-44, 1945-59, 1960-79, 1980-89, 1990-99 | 1990-99 freigegeben |
| Abrissmenge | Bilanzrest 19 872 558 m² in Ordnung | unverändert |
| Mehrdeutigkeit | bei gleicher unveränderter Fläche geringerer Versorgungswechsel | zweistufiges LP (`ZIELFUNKTION`) im Block-LP und im gemeinsamen LP mit Neubau/Abriss |

### Blockdiagnose: 300 Einzelmerkmalkonflikte beim Wachstumspaar

Nachgestellt in der Prüfumgebung: 300 Meldungen = 60 unveränderliche Blöcke (Geometrie × Wetter × Speichermasse) × 5 Meldungen. Je Block meldet die Diagnose eine ungleiche Gesamt-NGF und je eine Zielfläche über der Herkunftsfläche für Geometrie, Wetter, Speichermasse und Flex. Ursache: Die Zelle prüfte nur die Bedingungen für einen konstanten Bestand und ignorierte Neubau und Abriss. Da jeder Block durch Neubau wächst, ist seine B-Fläche ohne Neubau zwangsläufig nicht erreichbar. Die Meldungen waren also Scheinkonflikte und kein Hinweis auf Unmachbarkeit; die Rekonstruktion selbst prüft vorab bereits die richtigen Bedingungen und war `MACHBAR`.

Korrektur: `blockdiagnose(a, b, regeln, bilanz)` verwendet bei `BILANZ_OK` dieselben notwendigen Bedingungen wie die Rekonstruktion (Bilanz, Kapazität der freigegebenen Typen, Blockbilanz, Merkmalshüllen). Ergebnis Wachstumspaar: **0 Konflikte** (Grundlage „mit Neubau/Abriss“); ohne Bilanz weiterhin 300 (Grundlage „konstanter Bestand“, ausgewiesen). Transition 2040: 0.

### Wirkung der zweiten Zielstufe (Prüfumgebung, neu rekonstruiert)

| Kennzahl (Mio. m²) | Transition Stufe 1 | Transition Stufe 2 | Wachstum Stufe 1 | Wachstum Stufe 2 |
|---|---|---|---|---|
| Geänderte Bestandsfläche | 478,29 | 478,29 | 443,59 | 443,59 |
| Versorgungswechsel | 460,65 | **409,71** | 423,93 | **374,33** |

Die unveränderte Fläche bleibt gleich (Abweichung 0,6 m² bzw. 0,01 m², innerhalb `toleranz_m2` je Block). Laufzeit: Transition ca. 31 s, Wachstum ca. 103 s (vorher ca. 45 s). Alle Pflichtprüfungen und Maßnahmenkontrollen `OK`; Wiederladen ohne Solver `MACHBAR`.

| Maßnahme | Transition: Fläche | Anteil | %/a | Wachstum: Fläche | Anteil | %/a |
|---|---|---|---|---|---|---|
| Thermische Sanierungsrate | 197,64 | 22,21 % | 1,388 | 165,14 | 18,56 % | 1,160 |
| Versorgungswechselrate | 409,71 | 46,04 % | 2,878 | 374,33 | 42,07 % | 2,629 |
| davon nach Wärmepumpe | 329,25 | 37,00 % | 2,312 | 283,45 | 31,85 % | 1,991 |
| davon nach Fernwärme | 46,55 | 5,23 % | 0,327 | 51,84 | 5,83 % | 0,364 |
| davon nach Biomasse | 33,83 | 3,80 % | 0,238 | 38,96 | 4,38 % | 0,274 |
| davon aus Fossil (Erdgas/Öl) | 293,66 | 33,00 % | 2,062 | 273,29 | 30,71 % | 1,919 |
| PV-Ausbaurate (NGF) | 296,61 | 33,33 % | 2,083 | 285,44 | 32,08 % | 2,005 |
| Flexibilisierungsrate | 20,72 | 2,33 % | 0,146 | 19,75 | 2,22 % | 0,139 |
| Mindestens eine Änderung | 478,29 | 53,75 % | 3,359 | 443,59 | 49,85 % | 3,116 |
| Neubaurate / Abrissrate | – | – | – | 80,00 / 19,87 | 8,99 / 2,23 % | 0,562 / 0,140 |

Häufigste Kombinationen (Stufe 2): keine Maßnahme 46,25 % bzw. 47,92 %; Versorgungswechsel + PV-Ausbau 14,16 % bzw. 14,24 %; Sanierung + Versorgungswechsel + PV-Ausbau 10,62 % bzw. 9,18 %; Sanierung + Versorgungswechsel 9,49 % bzw. 7,55 %; nur Versorgungswechsel 9,45 % bzw. 8,88 %; nur PV-Ausbau 7,10 % bzw. 7,09 %. Kombinationen mit 0,00 Mio. m² sind numerische Restflüsse (Transition: 19 Flüsse < 0,01 m², zusammen 0,19 m²).

Wachstumspaar mit den neuen Freigaben: Neubau 93,3 % Wärmepumpe, 5,1 % Fernwärme, 1,5 % Biomasse, 0 % Strom direkt; 31,5 % Neu_20cm, 68,5 % Neu_30cm. Abriss 96,4 % fossil; 54,0 % aus 1960-79, 23,2 % vor1919, 13,4 % 1980-89; aus 1990-99 kein Abriss, weil 1990-99 in Szenario 3 absolut wie im Bestand festgelegt ist und nur aus sich selbst entstehen kann.

Verbleibende Mehrdeutigkeit: Die Aufteilung auf Sanierung, PV und Flex sowie die Auswahl innerhalb der Freigaben kann zwischen gleichwertigen Lösungen variieren. Fernwärme erscheint weiterhin zugleich als Herkunft und Ziel (Transition je 46,55 Mio. m²). Dieser Anteil ist mit der maximal unveränderten Fläche nicht weiter reduzierbar.

## Anforderungen aus Abschnitt 9

| Anforderung | Nachweis |
|---|---|
| Gemeinsame Definition, Einheit % der Ausgangs-NGF pro Jahr, lineare mittlere Periodenrate | `massnahmenraten`, Spalten `Anteil_Ausgangs_NGF_pct` und `Rate_pct_pro_Jahr`; Kontrolle „Nenner T_A = NGF des Ausgangszustands“ |
| Sanierung nur bei klassifizierter Verbesserung | andere Qualitätswechsel als eigene Zeile „nicht als Sanierung klassifiziert“ (Test `test_rueckentwicklung_und_nicht_klassifiziert_getrennt`) |
| Versorgungswechsel mit Erläuterung „Kesseltauschrate“ | Zeile mit Aufschlüsselung nach Ziel- und Herkunftsgruppe; Erläuterung in Definition, Notebook und `BEDIENUNG.md` |
| PV = betroffene NGF, nicht kWp | Hinweis an jeder Tabelle; Bezeichnung „PV-Ausbaurate“ mit Flächenbasis |
| Maßnahmen im Neubau getrennt | Bestandsraten nur aus Bestandsflüssen; Neubau-/Abrissrate im Bereich `Extern`, Merkmale in `Neubau_Merkmale`/`Abriss_Merkmale` (Test `test_neubau_abriss_getrennt_und_ausgangswert_null`) |
| Rückwärtsentwicklungen getrennt | Zeilen PV-Rückbau, Flex → noFlex, nicht klassifizierte Qualitätswechsel (Ebene `Rückwärts`); nie verrechnet |
| Einzelraten nicht addieren; Kombinationen; „mindestens eine Änderung“ | `massnahmenkombinationen` (jede Bestandsfläche genau einmal); Zeile „mindestens eine Änderung (ohne Doppelzählung)“; Kontrollen Abdeckung und Überschneidung (Test `test_mehrfachmassnahme_ohne_doppelzaehlung`) |
| Aussagegrenze | Text `HINWEIS` an jeder Tabelle, im Notebook vor den Tabellen und in `BEDIENUNG.md`: rekonstruktionsbasierte Raten einer ausgewählten zulässigen Zuordnung, keine beobachteten Bruttomaßnahmenraten |

## Ergebnisse 1.5.0 (Stufe 1, überholt durch den Nachtrag)

Zeitraum 2024–2040 (16 Jahre), Nenner \(T_A\) = 889,873 Mio. m². Fläche in Mio. m² im Zeitraum.

| Maßnahme | Transition 2040: Fläche | Anteil | %/a | Wachstum 2040: Fläche | Anteil | %/a |
|---|---|---|---|---|---|---|
| Thermische Sanierungsrate | 197,64 | 22,21 % | 1,388 | 165,14 | 18,56 % | 1,160 |
| davon Zielqualität Neu_20cm | 54,19 | 6,09 % | 0,381 | 55,86 | 6,28 % | 0,392 |
| davon Zielqualität Neu_30cm | 143,45 | 16,12 % | 1,008 | 109,28 | 12,28 % | 0,768 |
| Versorgungswechselrate | 460,65 | 51,77 % | 3,235 | 424,05 | 47,65 % | 2,978 |
| davon nach Wärmepumpe | 329,25 | 37,00 % | 2,312 | 286,53 | 32,20 % | 2,012 |
| davon nach Fernwärme | 79,06 | 8,88 % | 0,555 | 79,63 | 8,95 % | 0,559 |
| davon nach Biomasse | 50,30 | 5,65 % | 0,353 | 55,62 | 6,25 % | 0,391 |
| davon nach Strom direkt | 2,04 | 0,23 % | 0,014 | 2,27 | 0,25 % | 0,016 |
| davon aus Fossil (Erdgas/Öl) | 293,66 | 33,00 % | 2,062 | 275,88 | 31,00 % | 1,938 |
| PV-Ausbaurate (NGF) | 302,94 | 34,04 % | 2,128 | 287,87 | 32,35 % | 2,022 |
| davon Erstausstattung PV0 → PV > 0 | 266,96 | 30,00 % | 1,875 | 257,56 | 28,94 % | 1,809 |
| Flexibilisierungsrate | 20,72 | 2,33 % | 0,146 | 19,65 | 2,21 % | 0,138 |
| Rückwärtsentwicklungen (alle) | 0,00 | 0 % | 0 | 0,00 | 0 % | 0 |
| Mindestens eine Änderung (ohne Doppelzählung) | 478,29 | 53,75 % | 3,359 | 443,59 | 49,85 % | 3,116 |
| Bestandsfläche ohne Änderung | 411,58 | 46,25 % | – | 426,41 | 47,92 % | – |
| Neubaurate (extern) | – | – | – | 80,00 | 8,99 % | 0,562 |
| Abrissrate (extern) | – | – | – | 19,87 | 2,23 % | 0,140 |

Die Summe der Einzelraten (Transition: 197,64 + 460,65 + 302,94 + 20,72 = 981,95 Mio. m²) übersteigt die Fläche mit mindestens einer Änderung (478,29 Mio. m²) deutlich; das zeigt die Überschneidung.

Häufigste Kombinationen (Anteil an \(T_A\)):

| Kombination | Transition | Wachstum |
|---|---|---|
| keine Maßnahme | 46,25 % | 47,92 % |
| Versorgungswechsel + PV-Ausbau | 17,79 % | 18,42 % |
| Sanierung + Versorgungswechsel + PV-Ausbau | 13,18 % | 10,75 % |
| nur Versorgungswechsel | 10,64 % | 9,74 % |
| Sanierung + Versorgungswechsel | 7,82 % | 6,54 % |
| nur PV-Ausbau | 1,77 % | 1,89 % |
| übrige 6 Kombinationen | 2,54 % | 2,52 % |

Wachstumspaar: Bestandsflüsse (870,00 Mio. m²) + Abriss (19,87 Mio. m²) = \(T_A\). Neubau: 89,5 % Wärmepumpe, 10,5 % Fernwärme, 29,3 % Neu_20cm, 70,7 % Neu_30cm. Abriss: 83,4 % Fossil, 49,7 % aus 1960-79.

Maßnahmenkontrollen beider Paare: alle `OK` (Nenner = Bestandsflüsse + Abriss = NGF A, Kombinationen decken den Bestand genau einmal ab, mindestens eine Änderung + ohne Änderung = Bestandsflüsse, jede Einzelmaßnahme ≤ mindestens eine Änderung, unveränderliche Merkmale ohne Wechsel, Zeitspanne > 0). Auswertung ca. 0,7 s, ohne Solver.

## Grenzen der Aussage

- Eindeutig sind die Summe „mindestens eine Änderung“ (Stufe 1) und seit 1.5.1 die Versorgungswechselfläche (Stufe 2). Die Aufteilung auf Sanierung, PV und Flex sowie die Auswahl innerhalb der Freigaben hängt weiter von der gewählten gleichwertigen Lösung ab. (Stand 1.5.0: Fernwärme zugleich Herkunft und Ziel mit 79,06 Mio. m²; mit Stufe 2 46,55 Mio. m².)
- Zwischenzeitliche Mehrfachwechsel und Neubau mit späterem Abriss sind aus zwei Endzuständen nicht identifizierbar.
- Die Ergebnisse stammen aus der Prüfumgebung. Lokal entstehen die Maßnahmendateien erst beim nächsten Export in Notebook 03.

## Tests

`python -m unittest discover -s tests -v`: **71 Tests OK** (487 s, Stand 1.5.1). Behobener Fehler im ersten 1.5.1-Lauf: Stufe 2 wurde ohne möglichen Versorgungswechsel (Kostenvektor null) übersprungen und als nicht gelöst gemeldet; jetzt wird das Ergebnis von Stufe 1 direkt übernommen. Selbsttest `distribution_to_json.py`: **19 OK**. Protokoll: `AP5_Testlauf.txt`.

| Testfall nach Abschnitt 12 | Test |
|---|---|
| identische Zustände → keine Maßnahme | `test_massnahmen.Raten.test_identisch_keine_massnahme` |
| einzelne Maßnahmen, Nenner und Annualisierung (bekannte Werte) | `test_einzelmassnahmen_nenner_und_annualisierung` |
| mehrere gleichzeitige Maßnahmen ohne Doppelzählung | `test_mehrfachmassnahme_ohne_doppelzaehlung` |
| gleiche Vergleichsjahre → keine Jahresrate | `test_gleiche_jahre_keine_jahresrate` |
| Ausgangswert null → keine erfundene relative Änderung; Neubau/Abriss getrennt | `test_neubau_abriss_getrennt_und_ausgangswert_null` |
| Rückwärtsentwicklung und nicht klassifizierter Wechsel getrennt | `test_rueckentwicklung_und_nicht_klassifiziert_getrennt` |
| ohne gültige Flüsse keine Raten | `test_ohne_gueltige_fluesse_keine_raten` |
| Definition gültig bzw. Fehler erkannt | `test_massnahmen.Definition.*` |
| Export, Wiederladen ohne Solver, gleiche Raten | `test_flaechenstroeme` (test_3), `test_bestandsbilanz.Wachstumspaar.test_2` |
| Notebook-Defaults ohne Berechnung/Export; nur öffentliche Funktionen | `test_notebook_sicherheit` |
| zweite Zielstufe: minimaler Versorgungswechsel bei gleicher unveränderter Fläche (Block-LP und gemeinsames LP) | `test_massnahmen.Zielstufe.*` |
| Blockdiagnose mit/ohne Bilanz; neue Freigaben; Abweisung älterer Zielfunktion | `test_bestandsbilanz.Wachstumspaar.test_1`, `test_2` |

Zusätzlich wurde Notebook 03 vollständig mit beiden Paaren ausgeführt (gespeicherte Flüsse 1.5.1, ohne Fehler; Blockdiagnose 0 Konflikte). Abschnitt 8 zeigt Hinweis, Raten, Kombinationen, Versorgungsmatrix, Neubau-/Abrissmerkmale und Kontrollen.

## Sperrende Fehler

Keine. Freigaben und Bilanzrest sind seit 17.11.2026 bestätigt. Offen (nicht sperrend): weitere Präferenzen für Sanierung/PV/Flex und die Abrissauswahl, lokale Vollabnahme (AP7).
