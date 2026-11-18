# AP6.3 – Änderungsnachweis

Stand 17.11.2026, Fassung 1.6.3-AP6. Vorfassungen auf dem Gerät: `archiv/vor_AP63_20261117/`. Hash = erste 12 Stellen SHA-256.

| Datei | vorher (Gerät) | nachher | Änderung |
|---|---|---|---|
| `modell/prioren.py` | neu | `78298eec71e3` | Stufe A (Ableitung, Schreiben, Status) und Stufe B (Erreichbarkeit) |
| `modell/fassung.py` | `340acc067775` | `68e9b7f91f8e` | FASSUNG 1.6.3-AP6 |
| `notebooks/00_Start.ipynb` | `daf1152efb84` | `5f28fdbe8117` | Abschnitt „Abgeleitete Prioren“ (nur lesen), Fassung |
| `notebooks/01_Szenario.ipynb` | `92f0e65519db` | `584f25de45c3` | Schalter `PRIOREN_ABLEITEN=False`, Abschnitte „Prioren aus globalen Zielen“, „Erreichbarkeit“, Warnung beim Speichern, Fassung |
| `notebooks/02_Szenarienvergleich.ipynb` | `a799a842f14e` | `348c966b8c47` | nur Fassung |
| `notebooks/03_Flaechenstroeme.ipynb` | `79e3691645a2` | `efd596f57683` | nur Fassung |
| `tests/test_prioren.py` | neu | `abb430e273d5` | 9 Tests |
| `tests/test_notebook_sicherheit.py` | `f4c4ae16e80a` | `d9d76a0a711c` | neuer Schalter, Alias `pr` |
| `data/eingaben/verteilungen/Vorlage_Verteilung_nur_Ziele.xlsx` | neu | `c2fa1a8e5ecc` | Vorlage nur ZIEL-Zeilen |
| `README.md` | `b01b88538460` | `fb9fd2ee0b09` | Modul, Fassung |
| `CHANGELOG.md` | `b3835dc7c8ac` | `e739c18b8471` | Eintrag 1.6.3-AP6 |
| `docs/BEDIENUNG.md` | `1942f6c48219` | `ad4fe6ba244e` | Schalter, Ablauf „Szenario nur über globale Ziele“ |
| `docs/DATENSCHEMATA.md` | `172c48672872` | `83628c262e8d` | Profilfeld `prioren`, abgeleitete Datei |
| `docs/OFFENE_PUNKTE.md` | `3457fcb995cc` | `ba00ef871b3c` | Stand 1.6.3 |
| `docs/AP7/AP7_Abnahmeprotokoll.md` | `a3e437a19c1a` | `0f5f205d3c1f` | Fassung 1.6.3, Hinweis |
| `docs/AP6/AP63_Pruefprotokoll.md`, `AP63_Testlauf.txt` | neu | `3a791852988e`, `3de0a611c245` | Protokolle |

Unverändert (Hash gleich auf Gerät und in der Prüfumgebung): `gebaeudesektor.py` `0e11cc7e6d0b`, `distribution_to_json.py` `afc031681543`, `flaechenstroeme.py` `918020d82b78`, `bestandsbilanz.py` `9fb67c2571c2`, `massnahmen.py` `adb39c70d402`, `szenarienvergleich.py` `973205f710ec`, `abnahme.py` `0c9a92814c3d`, übrige Tests. Zustands-IDs und gespeicherte Ergebnisse bleiben gültig.

Nicht übertragen (lokale Fassungen bleiben): `config/szenarien.json`, `config/flaechenstroeme/uebergaenge.json`, alle Verteilungen und `Bestandsentwicklung.xlsx`, `results/`.
