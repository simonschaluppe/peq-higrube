# AP7 – Abnahmeprotokoll lokale Gesamtprüfung

Vorlage, Stand 17.11.2026, Fassung 1.6.3-AP6. Abnahmekriterium (Abschnitt 11): dokumentierte fachlich-technische Abnahme. Grundlage: Abschnitt 12 („Lokale Vollabnahme“) und Abschnitt 14 („Projekt finalisiert“) des Arbeitsauftrags.

> Hinweis 1.6.3 (17.11.2026): Optionaler Eingabeweg über globale Ziele (`modell/prioren.py`). Wird das Wachstumsszenario darauf umgestellt, ändert sich seine Zustands-ID; die Wachstum-Sollwerte sind dann aus dem lokalen Lauf zu übernehmen. In 00 zusätzlich: Abschnitt „Abgeleitete Prioren“ meldet `AKTUELL` bzw. `NICHT_KONFIGURIERT`.
>
> Hinweis 1.6.2 (17.11.2026): Die Wachstumsverteilung und die Übergangsregeln wurden lokal geändert. Die Wachstum-Sollwerte unten (Zustand-ID `c88c0d629dd09b32`, Rekonstruktions- und Ratenwerte) gelten für den Stand davor. Mit der geänderten Verteilung ergibt sich in der Prüfumgebung die Zustand-ID `e3ac469b4eb250b1`; die Rekonstruktion ist mit den lokalen Regeln `NICHT_MACHBAR` (Kombinationskonflikte, siehe `docs/AP6/AP62_Pruefprotokoll.md`). Nach der fachlichen Entscheidung werden die Wachstum-Sollwerte neu bestimmt.

Die Spalten „Ergebnis lokal“ und „Status“ werden bei der Ausführung auf dem Arbeitsrechner ausgefüllt. Die Referenzwerte stammen aus der Prüfumgebung (Python 3.14, pandas 3.1, HiGHS über scipy 1.18). Synthetische Tests ersetzen diese Abnahme nicht.

Status: `OK` = Kriterium erfüllt · `ABW` = Abweichung (Bemerkung) · `n. a.` = nicht anwendbar.

## 0 Voraussetzungen

| Nr. | Prüfung | Kriterium | Ergebnis lokal | Status |
|---|---|---|---|---|
| 0.1 | Fassung | Startzellen aller vier Notebooks melden „Fassung 1.6.3-AP6 (Notebook und Modell passen zusammen)“ | | |
| 0.2 | Umgebung (E10) | Python- und Paketversionen notieren (00, Projektprüfung, Bereich `python`): Python, numpy, pandas, scipy, openpyxl, plotly, pyarrow | | |
| 0.3 | Projektprüfung (00) | alle Pflichtdateien vorhanden; `scenarios.parquet` und `pyarrow` vorhanden | | |
| 0.4 | Abnahmestand (00, `ABNAHMESTAND_PRUEFEN=True`) | alle Szenarien `OK`; Flächenströme `OK` oder `HINWEIS` „vor 1.6.0 gespeichert … Fossilbilanz.csv erst nach Neu-Speichern“; keine Zeile `FEHLERHAFT`/`FEHLER` | | |
| 0.5 | Automatische Tests | im Projektordner `python -m unittest discover -s tests -v` → alle Tests `OK` (Prüfumgebung: 92 Tests) | | |
| 0.6 | Selbsttest Excel-Einlesung | `python modell/distribution_to_json.py self-test` → alle Fälle `OK` | | |

Ablaufhinweis: Vor jedem Schritt mit `ERSETZEN=True` zuerst die Wiederholbarkeit prüfen (Schritte 1, 4, 5, 9). Wird ein Szenario neu gespeichert, bleiben darauf beruhende Flüsse gültig, solange `Verteilung.csv` bitgleich ist (Zustand-ID unverändert); Vergleiche sind danach neu zu exportieren.

## 1 Referenzbestand validieren (01_Szenario)

Einstellungen: `SZENARIO='Bestand_2024'`, `BERECHNEN=True`, `ENERGIE_BERECHNEN=True`, `EXPORTIEREN=False`.

| Nr. | Prüfung | Kriterium / Referenz | Ergebnis lokal | Status |
|---|---|---|---|---|
| 1.1 | Bilanzkontrollen | alle `OK` | | |
| 1.2 | Gesamt-NGF | 889 872 558 m² | | |
| 1.3 | Zustand-ID | beginnt mit `a8a7262a30bba10f`; „Gleicher Zustand wie in dieser Sitzung: True“ | | |
| 1.4 | Energieanalyse | Status „Ausgeführt“; Kennwerte plausibel (Endenergie, Abdeckung) | | |

## 2 Zukunftsszenarien (01_Szenario)

`Transition_2040`: wie Schritt 1 (nur prüfen, `EXPORTIEREN=False`). `Transition_2040_Wachstum`: zusätzlich Energieanalyse speichern (`ENERGIE_BERECHNEN=True`, `EXPORTIEREN=True`, `ERSETZEN=True`), denn das gespeicherte Ergebnis enthält bisher nur die Flächenanalyse.

| Nr. | Prüfung | Kriterium / Referenz | Ergebnis lokal | Status |
|---|---|---|---|---|
| 2.1 | Transition_2040 NGF, Zustand-ID | 889 872 558 m² (konstanter Bestand); `e1a12c1d6c911112`; gleicher Zustand | | |
| 2.2 | Transition_2040_Wachstum NGF, Zustand-ID | 950 000 000 m²; `c88c0d629dd09b32`; gleicher Zustand | | |
| 2.3 | Bilanzkontrollen beider | alle `OK`; WP nur in zulässigen Qualitäten | | |
| 2.4 | Wachstum Energie gespeichert | 00 zeigt Energie „Ausgeführt“ | | |

## 3 Mehrszenarienvergleich (02_Szenarienvergleich)

Einstellungen: `VERGLEICH='Bestand_Transition_Wachstum_2040'`, `EXPORTIEREN=True`; danach ebenso `Bestand_2024__Transition_2040`.

| Nr. | Prüfung | Kriterium | Ergebnis lokal | Status |
|---|---|---|---|---|
| 3.1 | Gemeinsame Kennwerttabelle | drei Szenarien in einer Tabelle | | |
| 3.2 | Vergleichbarkeit | Flächenkennwerte vergleichbar; Energie vergleichbar, wenn für alle Szenarien berechnet | | |
| 3.3 | Referenzvergleich | Differenzen zur Referenz `Bestand_2024`; identische Zustände Δ = 0 | | |
| 3.4 | Paarvergleich gleichjährig | Transition ↔ Wachstum: keine Jahresrate | | |
| 3.5 | Export und Wiederladen | Ordner unter `results/vergleiche/`; Integrität `OK` | | |

## 4 Paar mit konstantem Bestand (03_Flaechenstroeme)

Erst lesen (Standard), dann `MODUS='Rekonstruktion'`, `REKONSTRUIEREN=True`, Abschnitt 9 prüfen, dann `EXPORTIEREN=True`, `ERSETZEN=True`. `REKONSTRUKTION='Bestand_2024__Transition_2040'`.

| Nr. | Prüfung | Kriterium / Referenz | Ergebnis lokal | Status |
|---|---|---|---|---|
| 4.1 | Bilanzgrundlage | Bilanzstatus konstant; Blockdiagnose 0 Konflikte, Grundlage „konstanter Bestand“ | | |
| 4.2 | Status | `MACHBAR`; alle Pflichtprüfungen `OK`; A/B unverändert | | |
| 4.3 | Zielwerte | geänderte Fläche 478 291 170,82 m²; Versorgungswechsel 409 712 579,60 m² | | |
| 4.4 | Laufzeit | notieren (Prüfumgebung ca. 30 s) | | |
| 4.5 | Wiederholbarkeit (Abschnitt 9) | Status, Zielwerte `OK`; Flüsse je Typpaar `OK` oder `HINWEIS` | | |

## 5 Paar mit explizitem Neubau und Abriss (03_Flaechenstroeme)

Wie Schritt 4 mit `REKONSTRUKTION='Bestand_2024__Transition_2040_Wachstum'`.

| Nr. | Prüfung | Kriterium / Referenz | Ergebnis lokal | Status |
|---|---|---|---|---|
| 5.1 | Bestandsbilanz | `BILANZ_OK`: \(T_B = T_A - D + N\); Neubau 80 000 000 m², Abriss (Bilanzrest) 19 872 558 m² | | |
| 5.2 | Blockdiagnose | 0 Konflikte; Grundlage mit Neubau/Abriss innerhalb der Freigaben | | |
| 5.3 | Status | `MACHBAR`; Pflichtprüfungen `OK`; Neubau nur Neu_20cm/Neu_30cm mit WP, Fernwärme, Biomasse, Strom direkt; Abriss nur vor1919 … 1990-99 | | |
| 5.4 | Zielwerte | geänderte Fläche 443 594 535,54 m²; Versorgungswechsel 374 333 216,43 m² | | |
| 5.5 | Laufzeit | notieren (Prüfumgebung ca. 100 s) | | |
| 5.6 | Wiederholbarkeit (Abschnitt 9) | Status, Zielwerte, Neubau/Abriss `OK` | | |

## 6 Flächen- und Ratenbilanzen (03, Abschnitte 7 und 8)

| Nr. | Prüfung | Kriterium / Referenz (Transition · Wachstum) | Ergebnis lokal | Status |
|---|---|---|---|---|
| 6.1 | Maßnahmenkontrollen | alle `OK` (Nenner, Abdeckung, Überschneidung, Fossilbilanz geschlossen, Dekarbonisierung ≤ Versorgungswechsel) | | |
| 6.2 | Nenner T_A | 889 872 558 m² · 889 872 558 m² | | |
| 6.3 | Versorgungswechselrate | 46,042 % / 2,878 %/a · 42,066 % / 2,629 %/a | | |
| 6.4 | Dekarbonisierungsrate | 33,000 % / 2,062 %/a · 30,712 % / 1,919 %/a | | |
| 6.5 | Fossilbilanz | F_A 311,455 Mio. m² · 311,455 Mio. m²; F_B 17,797 · 19,000 Mio. m²; davon abgerissen 0 · 19,162 Mio. m² | | |
| 6.6 | Kombinationen | Summe = Bestandsflüsse; Einzelraten nicht addiert | | |
| 6.7 | Fachliche Plausibilität | Raten, Zielgruppen und Neubau-/Abrissmerkmale fachlich bestätigt (Bemerkung) | | |

Die Referenzwerte unter 6.3–6.5 sind aus den gespeicherten Flüssen der Prüfumgebung ausgewertet. Die Aufteilung innerhalb gleichwertiger Lösungen (z. B. welche Abrissfläche fossil war) ist nicht eindeutig. Kleine Abweichungen sind dann kein Fehler, solange 4.3/5.4 innerhalb der Toleranz liegen.

## 7 Energieanalyse und Vergleichbarkeit (separat)

| Nr. | Prüfung | Kriterium | Ergebnis lokal | Status |
|---|---|---|---|---|
| 7.1 | Parquet-Nachweis | Name und Größe von `scenarios.parquet` im Laufprotokoll (schwacher Nachweis, `DATENSCHEMATA.md`) | | |
| 7.2 | Abdeckung | Abdeckungsgrad je Szenario notieren; Summenträger nach kleinster Einzelabdeckung | | |
| 7.3 | Vergleichbarkeit | Status in `Vergleichbarkeit.csv` fachlich bestätigt | | |

## 8 Speichern und erneut auswerten

| Nr. | Prüfung | Kriterium | Ergebnis lokal | Status |
|---|---|---|---|---|
| 8.1 | Wiederladen ohne Solver | 03 im Standard (`VorhandeneFluesse`) lädt beide Paare `MACHBAR`, kein Solveraufruf | | |
| 8.2 | Abnahmestand (00) | alle Zeilen `OK`; Raten „identisch neu ausgewertet“ | | |
| 8.3 | Neue Exportdateien | `Fossilbilanz.csv` vorhanden; `flussprotokoll.json` mit `software.projektfassung = 1.6.3-AP6` | | |

## 9 Wiederholbarkeit innerhalb der Toleranzen

Toleranz \(\max(1\ \text{m}^2,\ 10^{-7} \cdot T_A)\) ≈ 89 m² (relative HiGHS-Toleranz 1e-7). Zustände: identische Zustand-ID.

| Nr. | Prüfung | Kriterium | Ergebnis lokal | Status |
|---|---|---|---|---|
| 9.1 | Zustände | Zustand-IDs 1.3, 2.1, 2.2 identisch | | |
| 9.2 | Flüsse | 4.5 und 5.6 ohne `FEHLER` | | |
| 9.3 | Plattform | Abweichungen gegenüber den Referenzwerten der Prüfumgebung notieren | | |

## Abschnitt 14 – Projekt finalisiert

| Kriterium | Nachweis | Status |
|---|---|---|
| Ordnerstruktur und aktive Dateiversion eindeutig | AP0/AP1; `fassung.py`; Schritt 0.1 | |
| Drei Arbeitsnotebooks ohne Codeeingriffe konfigurierbar | nur Schalterzellen geändert (Schritte 1–5) | |
| Wesentliche Abschnitte verständlich erklärt | Abschnittstexte (Was/Eingaben/Rechnet/Annahmen/Interpretation/Fehler) | |
| Szenarien einschließlich explizitem Neubau/Abriss bilanziert | Schritt 5.1 | |
| Mehrere Szenarien über denselben Kennwertworkflow vergleichbar | Schritt 3 | |
| Rekonstruktionen lassen feste Zustände unverändert | 4.2, 5.3 (Hashvergleich A/B) | |
| Maßnahmenraten korrekt bezeichnet, bilanziert, annualisiert | Schritt 6 | |
| Keine versteckten Optimierungen oder Exporte | Standardläufe 00–03 schreiben nichts (Test `NotebookAusfuehrung`, 8.1) | |
| Fehlerzustände aussagekräftig | `BEDIENUNG.md`, „Fehlermeldungen und Abhilfe“ | |
| Lokale Vollprüfungen dokumentiert, Einschränkungen benannt | dieses Protokoll; `OFFENE_PUNKTE.md` | |

## Zuordnung der kleinen automatischen Tests (Abschnitt 12)

| Testfall | Test |
|---|---|
| identische Zustände → unveränderter Bestand | `test_flaechenstroeme.Regelfaelle.test_identisch_unveraendert`, `Projektablauf.test_4_identische_zustaende_volle_groesse` |
| einzelner erlaubter Qualitäts-, Versorgungs-, PV-, Flex-Wechsel | `test_flaechenstroeme.Regelfaelle.test_einzelne_erlaubte_wechsel`, `test_massnahmen.Raten.test_einzelmassnahmen_nenner_und_annualisierung` |
| verbotener Übergang | `test_flaechenstroeme.Regelfaelle.test_verbotene_uebergaenge` |
| unzulässige WP-Zielqualität; falsche Fernwärme-/Wetterkombination | `test_flaechenstroeme.Regelfaelle.test_wp_zielqualitaet_und_fernwaerme_wetter`, `test_szenario.SzenarioAPI.test_wp_eingabe_abgewiesen` |
| gleicher Gesamtbestand mit Neubau und Abriss | `test_bestandsbilanz.Bilanzfaelle.test_gleicher_gesamtbestand_mit_neubau_und_abriss` |
| Wachstum nur durch Neubau; Rückgang nur durch Abriss | `test_bestandsbilanz.Bilanzfaelle.test_wachstum_nur_durch_neubau_rate`, `.test_rueckgang_nur_durch_abriss` |
| fehlende Bruttoangaben bei bekannter Nettoänderung | `test_bestandsbilanz.Bilanzfaelle.test_nur_nettoaenderung_bekannt` |
| Vorgaben widersprechen A/B-Bilanz | `test_bestandsbilanz.Bilanzfaelle.test_vorgaben_widersprechen_bilanz` |
| mehrere Maßnahmen ohne Doppelzählung | `test_massnahmen.Raten.test_mehrfachmassnahme_ohne_doppelzaehlung`, `test_bestandsbilanz.Bilanzfaelle.test_mehrere_massnahmen_ohne_doppelzaehlung_mit_neubau`, `test_flaechenstroeme.Regelfaelle.test_mehrfachmassnahme_ohne_doppelzaehlung` |
| gleiche Vergleichsjahre → keine Jahresrate | `test_massnahmen.Raten.test_gleiche_jahre_keine_jahresrate`, `test_vergleich.Mehrszenarienvergleich.test_gleichjaehrig_keine_jahresrate_und_zerlegung` |
| Ausgangswert null → keine erfundene relative Änderung | `test_massnahmen.Raten.test_neubau_abriss_getrennt_und_ausgangswert_null` |
| fehlende oder inkompatible Energiekennwerte | `test_vergleich.Mehrszenarienvergleich.test_flaeche_trotz_fehlender_energie`, `.test_energie_vergleichbar_wenn_berechnet` |
| Laden vorhandener Flüsse ohne Solveraufruf | `test_flaechenstroeme.Projektablauf.test_3_machbar_export_wiederladen_ohne_solver` |
| Notebook-Defaults ohne Berechnung und Export | `test_notebook_sicherheit.NotebookAusfuehrung.test_standardlauf_schreibt_nichts`, `.NotebookStatisch.test_standardwerte` |
| Überschreibschutz und Wiederladen | `test_szenario.SzenarioAPI.test_speichern_schutz_wiederladen`, `test_vergleich.Mehrszenarienvergleich.test_export_schutz_und_wiederladen` |
| Dekarbonisierung und Fossilbilanz (Ergänzung 17.11.2026) | `test_massnahmen.Dekarbonisierung` (4 Tests) |
| Abnahmehilfen lesen nur | `test_abnahme` (6 Tests) |

## Abnahme

| | |
|---|---|
| Datum | |
| Durchgeführt von | |
| Ergebnis | ☐ abgenommen ☐ abgenommen mit Auflagen ☐ nicht abgenommen |
| Auflagen / Bemerkungen | |
