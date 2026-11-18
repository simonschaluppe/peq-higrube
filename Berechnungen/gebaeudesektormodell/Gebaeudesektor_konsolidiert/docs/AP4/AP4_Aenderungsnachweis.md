# AP4 – Änderungsnachweis

| Datei | Art | Änderung |
|---|---|---|
| `modell/bestandsbilanz.py` | neu | Nur Bilanzierung Bestand/Neubau/Abriss (\(T_B = T_A - D + N\)): Einlesen und Prüfen von `Bestandsentwicklung.xlsx`, Umrechnung Rate → Periodenfläche, Bilanzrest, Bilanzstatus, Freigaben, `bilanz_fuer`, `extern_fuer`, `szenariobilanz`. Kein Szenariorechenkern. |
| `data/eingaben/bestandsentwicklung/Bestandsentwicklung.xlsx` | neu | Schema 1.0; Verbindung Wachstum (Neubau 80 Mio. m², Abriss Bilanzrest); Standardfreigaben |
| `config/projekt.json` | geändert | `konfiguration.bestandsentwicklung` (nicht im Zustands-Fingerprint) |
| `config/flaechenstroeme/uebergaenge.json` | geändert | Versorgungsregeln Bio → WP (4 WP-Arten) und Erdgas/Öl → Elektro |
| `modell/flaechenstroeme.py` | geändert | zweiter LP-Lauf mit Toleranz aus `toleranz_m2` bei Rundungsresten; `rekonstruiere(..., extern)` mit gemeinsamem LP (Bestandsflüsse, Abriss, Neubau); Vorabdiagnose ohne Solver (Bilanz, Kapazitäten, Blockbilanz, Merkmalshüllen); `pruefe_eingaben(..., bilanz)` (nur Nettoänderung → FEHLER); `pruefe_fluesse` mit externen Flüssen (bis 22 Prüfungen); `analysiere_rekonstruktion` lädt die Bilanz, prüft Aktualität auch gegen Neubau-/Abrissvorgaben, sperrt Flussdatei + Neubau/Abriss; Export `Neubau.csv`, `Abriss.csv`, `Bestandsbilanz.csv`, Excel-Blätter; Sankey mit externen Knoten; `aenderungsanteile` (Nenner T_A, Zeilen Neubau/Abriss); neu `zusammensetzung`, `extern_signatur`; `zusammenfassung` mit Neubau/Abriss/Bilanzstatus |
| `notebooks/03_Flaechenstroeme.ipynb` | ersetzt | Abschnitt Bestandsbilanz; Bilanztabelle des Paares vor den Pflichtprüfungen; Zusammensetzung und Neubau-/Abrisssummen; Schalter und Standardwerte unverändert |
| `tests/test_bestandsbilanz.py` | neu | 13 Tests (8 synthetische Bilanzfälle, 2 Eingabedatei, 3 Wachstumspaar in voller Größe: Bilanz/nur lesen; Standardfreigaben `MACHBAR` mit Export, Laden ohne Solver und Aktualitätsprüfung; eingeschränkte Neubaufreigabe `NICHT_MACHBAR`) |
| `data/eingaben/verteilungen/Verteilung_Transition_2040_Wachstum.xlsx` | neu | Szenario 3: Kopie von Transition 2040; Zielzeile Qualität (1990-99 und Neu_10cm absolut wie Bestand, Rest auf Neu_20cm/Neu_30cm) und Hinweise angepasst |
| `config/szenarien.json` | geändert | `Transition_2040_Wachstum`: eigene Verteilungsdatei, Beschreibung |
| `tests/test_szenario.py` | geändert | `test_drittes_szenario_wachstum`: 1990-99/Neu_10cm wie Bestand (≤ 0,01 m²) |
| `tests/test_flaechenstroeme.py` | geändert | Bestand → Transition jetzt `MACHBAR` (Export/Laden ohne Solver); ungleiche NGF ohne Bruttoangaben → FEHLER |
| `tests/test_notebook_sicherheit.py` | geändert | 03: Import `bestandsbilanz`, Verbot `bb._` und `.to_excel` |
| `README.md`, `CHANGELOG.md` | geändert | AP4-Stand (1.4.0-AP4) |
| `docs/BEDIENUNG.md`, `docs/DATENSCHEMATA.md`, `docs/OFFENE_PUNKTE.md` | geändert | Neubau/Abriss, Bilanzstatus, Excel-Schema, neue Ausgabedateien, offene Entscheidungen |
| `docs/AP4/*` | neu | Prüfprotokoll, Änderungsnachweis, Testlauf |

Nicht geändert: `modell/gebaeudesektor.py` (Zustands-IDs bleiben gültig), `modell/distribution_to_json.py`, `modell/szenarienvergleich.py`, Notebooks 00–02, `config/vergleiche.json`, `config/flaechenstroeme/rekonstruktionen.json`, die bestehenden Verteilungen `Verteilung_Bestand_2024.xlsx` und `Verteilung_Transition_2040.xlsx`.

Vorherige Fassungen liegen unter `archiv/vor_AP4_20261116/` (Dateinamen mit `__` statt Ordnertrenner).
