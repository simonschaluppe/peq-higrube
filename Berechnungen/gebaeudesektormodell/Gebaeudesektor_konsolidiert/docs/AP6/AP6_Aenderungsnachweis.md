# AP6 – Änderungsnachweis

Stand 17.11.2026, Fassung 1.6.0-AP6. Sicherung der Vorfassungen auf dem Gerät: `archiv/vor_AP6_20261117/` (Pfadtrenner als `__`). SHA-256 (erste 12 Zeichen) der gelieferten Fassung.

| Datei | Art | Änderung | SHA-256 (12) |
|---|---|---|---|
| `modell/fassung.py` | neu | Projektfassung 1.6.0-AP6, erwartete Notebook-Fassungen, `pruefe_notebook` | 2F008828D980 |
| `modell/flaechenstroeme.py` | geändert | Blockdiagnose ohne Bruttovorgaben bei ungleicher NGF: eine Meldung; CSV-Einlesung ohne veraltete Option ab pandas 3.1; Protokoll: Software/Projektfassung, `module_sha256`, `solver`, `raten`, Energiestatus A/B; klarere Meldung beim Ersetzungsschutz | 59C3F26CDAAC |
| `modell/szenarienvergleich.py` | geändert | `software.projektfassung` im Vergleichsprotokoll | 973205F710EC |
| `notebooks/00_Start.ipynb` | geändert | Startzelle (Module neu laden, Fassungsprüfung); Zweck und Grenzen, Standardworkflow, Aktualisierung; Statustext | 7D2BB7CD04B6 |
| `notebooks/01_Szenario.ipynb` | geändert | Startzelle; Ablaufzeile; `gs._relativ` ersetzt | DAB66EA42155 |
| `notebooks/02_Szenarienvergleich.ipynb` | geändert | nur Startzelle | E875240BE2ED |
| `notebooks/03_Flaechenstroeme.ipynb` | geändert | Startzelle; Ablaufzeile; Text Blockdiagnose | 5A2BD3563DB4 |
| `tests/test_notebook_sicherheit.py` | geändert | 6 neue Tests (Fassung, Abschnittstexte, 00-Inhalte, private Funktionen, Abbruch, Neuladen) | B2FEF924C5B9 |
| `tests/test_bestandsbilanz.py` | geändert | Blockdiagnose ohne Bilanz; Protokollangaben | 99DD35D495C8 |
| `README.md` | geändert | `fassung.py`, Startzelle | 00AC7A06BE41 |
| `CHANGELOG.md` | geändert | 1.6.0-AP6 | A815716AF080 |
| `docs/BEDIENUNG.md` | geändert | Standardworkflow, Aktualisierung, Fehlermeldungen und Abhilfe, Blockdiagnose | AFA10E63EBFA |
| `docs/DATENSCHEMATA.md` | geändert | Zuordnung Abschnitt 10, Dokumentation je Export, Nachweisstärke, neue Protokollfelder | 613055C0B402 |
| `docs/OFFENE_PUNKTE.md` | geändert | bereinigt, Stand AP6 | 458B15304273 |
| `docs/AP6/AP6_Testlauf.txt` | neu | Testprotokoll | 1B80A1CC64B3 |
| `docs/AP6/AP6_Pruefprotokoll.md` | neu | Prüfprotokoll | 096B4E6284C0 |

Unverändert: `gebaeudesektor.py` (Zustands-IDs gültig), `bestandsbilanz.py`, `massnahmen.py`, `distribution_to_json.py`, `config/`, `data/`, übrige Tests. Gespeicherte Ergebnisse 1.5.1 bleiben gültig.

Notebook-Generator (Prüfumgebung): alle vier Notebooks werden aus einer Quelle erzeugt; Startzelle gemeinsam, Fassungszeile je Notebook.

Der Hash dieses Nachweises steht im Abschlussbericht.
