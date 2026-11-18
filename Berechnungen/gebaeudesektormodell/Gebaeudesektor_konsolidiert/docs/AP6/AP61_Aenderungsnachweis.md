# AP6.1 – Änderungsnachweis

Stand 17.11.2026, Fassung 1.6.1-AP6. Sicherung der Vorfassungen auf dem Gerät: `archiv/vor_AP61_20261117/` (Pfadtrenner als `__`). SHA-256 (erste 12 Zeichen) der gelieferten Fassung.

| Datei | Art | Änderung | SHA-256 (12) |
|---|---|---|---|
| `modell/massnahmen.py` | geändert | Schema 1.1; Merkmale Dekarbonisierung/Refossilisierung; Ratenzeilen Dekarbonisierung; `fossilbilanz()`; 3 Kontrollen | ADB39C70D402 |
| `modell/flaechenstroeme.py` | geändert | Export `Fossilbilanz.csv` und Excel-Blatt „Fossilbilanz“ | 29F773A8A526 |
| `modell/fassung.py` | geändert | Projektfassung 1.6.1-AP6 | 1719EBF2C245 |
| `modell/abnahme.py` | neu | Abnahmestand und Wiederholbarkeitsprüfung (nur lesend) | 0C9A92814C3D |
| `config/flaechenstroeme/massnahmen.json` | geändert | Schema 1.1, Abschnitt `dekarbonisierung` | 3170C7BB245D |
| `config/flaechenstroeme/rekonstruktionen.json` | geändert | Beschreibung Wachstumspaar | 031BCA9B17A3 |
| `notebooks/00_Start.ipynb` | geändert | Fassungszeile; Abschnitt „Abnahmestand (AP7)“ | 90F43FCD64C3 |
| `notebooks/01_Szenario.ipynb` | geändert | nur Fassungszeile | 6F5A5C6979F5 |
| `notebooks/02_Szenarienvergleich.ipynb` | geändert | nur Fassungszeile | 17B5430ED407 |
| `notebooks/03_Flaechenstroeme.ipynb` | geändert | Abschnitt 8 Dekarbonisierung/Fossilbilanz; Abschnitt 9 Wiederholbarkeit; Speichern Abschnitt 10; Formelsatz korrigiert | F15B885CDBAC |
| `tests/test_massnahmen.py` | geändert | Klasse Dekarbonisierung, Validierungsfälle | 3EC8F7B83EF0 |
| `tests/test_abnahme.py` | neu | 6 Tests | D2DC1EAAB1AB |
| `tests/test_notebook_sicherheit.py` | geändert | Standardwert `ABNAHMESTAND_PRUEFEN`; private Funktionen von `abnahme` | F4C4AE16E80A |
| `tests/test_flaechenstroeme.py` | geändert | Exportdatei `Fossilbilanz.csv` | CDBE32E73C34 |
| `README.md` | geändert | 1.6.1, `abnahme.py` | 284BB1C12E9D |
| `CHANGELOG.md` | geändert | 1.6.1-AP6 | AA5F6EF09DD0 |
| `docs/BEDIENUNG.md` | geändert | Dekarbonisierungsrate, Fossilbilanz, lokale Gesamtprüfung | FE174C346E2B |
| `docs/DATENSCHEMATA.md` | geändert | `Fossilbilanz.csv`, Schema 1.1 | F6D01186FB13 |
| `docs/OFFENE_PUNKTE.md` | geändert | Stand AP6.1 | 74C7D4D686C5 |
| `docs/AP7/AP7_Abnahmeprotokoll.md` | neu | Vorlage lokale Gesamtprüfung | A5DFBB015C1B |
| `docs/AP6/AP61_Testlauf.txt` | neu | Testprotokoll (87 Tests OK) | 7FE4FA348149 |
| `docs/AP6/AP61_Pruefprotokoll.md` | neu | Prüfprotokoll Nachtrag | 975F7071A3B6 |

Unverändert: `gebaeudesektor.py` (Zustands-IDs gültig), `bestandsbilanz.py`, `szenarienvergleich.py`, `distribution_to_json.py`, `data/`, übrige Tests. Gespeicherte Ergebnisse bleiben gültig.

Der Hash dieses Nachweises steht im Abschlussbericht.
