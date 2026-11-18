# AP6.2 – Änderungsnachweis

Stand 17.11.2026, Fassung 1.6.2-AP6. Sicherung der Vorfassungen auf dem Gerät: `archiv/vor_AP62_20261117/` (Pfadtrenner als `__`). SHA-256 (erste 12 Zeichen).

| Datei | Art | Änderung | SHA-256 (12) |
|---|---|---|---|
| `modell/flaechenstroeme.py` | geändert | `_kombinations_konflikte`, `_fehlmengen`; Einbindung in Blockdiagnose und Vorprüfung | 918020D82B78 |
| `modell/fassung.py` | geändert | Projektfassung 1.6.2-AP6 | 340ACC067775 |
| `notebooks/00_Start.ipynb` | geändert | nur Fassungszeile | DAF1152EFB84 |
| `notebooks/01_Szenario.ipynb` | geändert | nur Fassungszeile | 92F0E65519DB |
| `notebooks/02_Szenarienvergleich.ipynb` | geändert | nur Fassungszeile | A799A842F14E |
| `notebooks/03_Flaechenstroeme.ipynb` | geändert | Fassungszeile; Text Blockdiagnose | 79E3691645A2 |
| `tests/test_bestandsbilanz.py` | geändert | Klasse `Kombinationsdiagnose` (5 Tests) | D7F389CB69D0 |
| `README.md` | geändert | Fassung | B01B88538460 |
| `CHANGELOG.md` | geändert | 1.6.2-AP6 | B3835DC7C8AC |
| `docs/BEDIENUNG.md` | geändert | Blockdiagnose Kombinationen, Fehlerbilder | 1942F6C48219 |
| `docs/DATENSCHEMATA.md` | geändert | `Machbarkeit.csv`: Ebenen Fehlmengen, Eigenschaft Kombination | 172C48672872 |
| `docs/OFFENE_PUNKTE.md` | geändert | Wachstum: offene Entscheidung | 3457FCB995CC |
| `docs/AP7/AP7_Abnahmeprotokoll.md` | geändert | Fassung, Testanzahl, Hinweis Wachstum-Sollwerte | A3E437A19C1A |
| `docs/AP6/AP62_Testlauf.txt` | neu | Testprotokoll (92 Tests OK) | BAEDBC75815D |
| `docs/AP6/AP62_Pruefprotokoll.md` | neu | Prüfprotokoll | FBAB292DE0D6 |

Nicht übertragen und unverändert: lokale `config/flaechenstroeme/uebergaenge.json` und `Verteilung_Transition_2040_Wachstum.xlsx` (Stand des Nutzers). Unverändert: `gebaeudesektor.py` (Zustands-IDs gültig), `bestandsbilanz.py`, `massnahmen.py`, `abnahme.py`, `data/`.
