# AP1 – Prüfprotokoll

Arbeitspaket: Szenario-API und Notebook konsolidieren, Zielstruktur mit relativen Pfaden.
Abnahmekriterium: Ein Zustand wird prüfbar erstellt, analysiert, gespeichert und wiedergeladen.
Datum: 16.11.2026 · Prüfumgebung: Python 3.14.8, numpy 2.5.4, pandas 3.1.1, scipy 1.18.1, pyarrow 26.0.1 (lokale Abnahme unter Windows steht aus, siehe unten).

## Automatische Tests

`python -m unittest discover -s tests -v` → **20 Tests, alle OK** (Laufzeit ca. 60 s, Einzelergebnisse in `AP1_Testlauf.txt`).
`python modell/distribution_to_json.py self-test` → **19 Tests, alle OK**.

| Bereich | Test | Ergebnis |
|---|---|---|
| Struktur | alle Pfade in `projekt.json` relativ; `pruefe_projekt` ohne fehlende Pflichtdateien | OK |
| Struktur | kein benutzerspezifischer absoluter Pfad und kein `mkdtemp` im Modellcode | OK |
| Zustand | Typenflächen Bestand 2024 und Transition 2040 = Referenz (rtol 1e-10) | OK |
| Zustand | 43 200 Typen, 889 872 558 m² NGF, positiv belegt 14 640 / 16 320, keine negativen Flächen, alle Bilanzkontrollen OK | OK |
| Zustand | WP-Anteil in ausgeschlossener Qualität wird abgewiesen | OK |
| Zustand | Wiederholbarkeit (identische Flächen und Zustands-ID) | OK |
| Zustand | Zustands-ID unabhängig vom Speicherort (Projektkopie in anderem Ordner) | OK |
| Zustand | Änderung einer Eingabedatei nach dem Laden wird erkannt | OK |
| Zustand | unregistriertes Szenario wird abgewiesen | OK |
| Kennwerte | Schema `Kennwerte.csv`, NGF und Typenzahl, getrennte Vergleichsbasis F-/E- | OK |
| Energie | ohne Anforderung „Nicht ausgeführt“; mit Anforderung „Ausgeführt“; GWh/a = gespeicherte Ergebnisse vor AP1 (rtol 1e-9, 33 Kennwerte je Szenario) | OK |
| Export | Speichern, Überschreibschutz, Ersetzen ohne Reste, keine absoluten Pfade im Protokoll | OK |
| Wiederladen | Integrität über SHA-256, gleiche Zustands-ID, gleiche Flächen; veränderte Ausgabe wird erkannt | OK |
| Notebooks | genau 00–03; einheitliche Startzelle; Standardwerte `False` bzw. `VorhandeneFluesse`; Markdown vor jeder Codezelle; keine privaten Funktionen/absoluten Pfade | OK |
| Notebooks | 00 und 01 im Standardlauf ausgeführt: keine Datei erzeugt oder verändert | OK |
| Flächenströme | Zustände aus `results/szenarien`, Ausgabe `results/flaechenstroeme`; relative Pfade; Lesemodus ohne Flussdatei bricht ohne Rechnung und ohne Ausgabe ab | OK |

## Abnahmelauf über die Notebooks (Projektkopie, leere results/)

| Schritt | Ergebnis |
|---|---|
| 01 Bestand_2024 mit BERECHNEN, ENERGIE_BERECHNEN, EXPORTIEREN | gespeichert, Integrität OK, Energie Ausgeführt, wiedergeladene Zustands-ID = berechnete |
| 01 Transition_2040 ebenso | ebenso |
| 00 Start | beide Ergebnisse LESBAR, Integrität OK |
| 02 Szenarienvergleich mit EXPORTIEREN | Vergleich gespeichert, Energiebasis kompatibel, Selbsttest OK, keine absoluten Pfade |
| 03 mit MODUS='Rekonstruktion', REKONSTRUIEREN, EXPORTIEREN | Status NICHT_MACHBAR (60 Blockkonflikte), Diagnose gespeichert; wie vor AP1 |

## Gleichheit mit dem Stand vor AP1

- Flächen: maximale Abweichung zu den gespeicherten `Verteilung.csv` 5,8·10⁻¹¹ m².
- Energiekennwerte: maximale relative Abweichung 6·10⁻¹⁶.
- Zustands-IDs ändern sich beabsichtigt (projektrelative Pfade, Parquet nur Name/Größe, geänderter Rechenkern): Bestand_2024 `587b6456…`, Transition_2040 `00197295…` (in der Prüfumgebung; lokal identisch, sofern Dateien gleich).

## Lokal noch durchzuführen

1. `00_Start.ipynb` ausführen (Pfade, Pakete, insbesondere `pyarrow`).
2. `01_Szenario.ipynb` für beide Szenarien mit allen Schaltern `True` (inkl. `ERSETZEN=True`), damit die Ergebnisse im neuen Format mit Ausgabehashes vorliegen.
3. `python -m unittest discover -s tests -v` im Projektordner.
