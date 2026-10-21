# Integration und Methodenstand, 21.10.2026

## Auftrag und Umfang

Grundlage: `Redaktion/sektormodell/arbeitsauftrag.md` und die anschließenden Nutzeranweisungen. Phase 1 und 3 umgesetzt. Phase 2 wird nur dokumentiert, ohne methodische Nachbearbeitungs- oder Sensitivitätsschleife. Die Ersatzregel ist ausdrücklich freigegeben. Abweichungen von ungefähr 1–3 % und fehlende Daten sind für diesen Arbeitsstand akzeptiert; sie werden nicht durch erfundene Werte geschlossen. Phase 4 (2040-Kalibrierung, PEExcel-Anbindung) bleibt entsprechend dem unmittelbaren Startauftrag unberührt.

Branch: `feature/gfz-bundesland-hochrechnung`. Die Originalanlieferung wird weder umbenannt noch überschrieben. Original-Exceldateien werden nur gelesen; lokale Arbeitskopien unter `data/` sind nicht versioniert.

## Rekonstruktion der Anlieferung

Die entpackten Dateien lagen vor, jedoch mit verschobenen Dateinamen. Zuordnung anhand von Textinhalt, CSV-Spalten und Dateisignatur:

| Gelieferter Name in Redaktion/sektormodell | Tatsächlicher Inhalt / Integrationsziel |
|---|---|
| `test_gfz_hydrator.py` | `gfz_hydrator.py` |
| `README.md` | `test_gfz_hydrator.py` (fünf Tests) |
| `requirements.txt` | `GFZ_AT_Analyse.ipynb` |
| `GFZ_AT_Analyse.ipynb` | Python-Plotmodul; als Grundlage für `plot_gfz.py` verwendet |
| `download` | Ursprüngliche README; inhaltlich in neue Dokumentation übernommen |
| `gfz_oesterreich_nutzung.png` | `outputs/gfz_distribution_by_province_use_storeys.csv` |
| `fallback_bundeslaender.png` | `outputs/allocation_audit.csv` |
| `validation.json` | `outputs/reference_coverage.csv` |
| `reference_coverage.csv` | `outputs/province_totals.csv` |
| `gfz_distribution_by_province_use_storeys.csv` | `outputs/gfz_distribution_by_province.csv` |
| `gfz_distribution_by_province.csv` | `outputs/gfz_distribution_austria_by_use.csv` |
| `gfz_distribution_austria_by_use.csv`, `province_totals.csv` | PNG-Dateien; Berichtsgrafiken stattdessen aus Tabellen neu erzeugt |

Eine echte `validation.json` und eine Paketliste waren in der Anlieferung nicht vorhanden. Deshalb werden das technische Prüfprotokoll `validation_delivered.json` und die Abhängigkeiten neu erstellt, ohne sie als angelieferte Dateien auszugeben.

## Originaldaten und Reproduktion

Der Auftraggeber hat im Verlauf drei Originaldateien aus dem Verzeichnis `OneDrive/PhD/Paper/unfinished/3Jb Building sector RES potential - STUB` bereitgestellt:

| Datei | Verwendung | SHA-256 |
|---|---|---|
| `rohdaten_python.xlsx` | Blatt `Rohdaten`: Gebäudestichprobe | `c1c5b3d9e78384465c18e2bf83364cec5e2fb345b6075badcd14ad939dd74a91` |
| `GFZ_Analyse_AT.xlsx` | Blatt `python`: statistische NGF | `dfd871b2e143dba421e39d3b13296e55ac5a952cc2c3b0ccef5641ce4bbc4b33` |
| `statistics.xlsx` | Ergänzende Archivquelle; nicht zusätzlich eingerechnet | `9ccc33c527beb837fe9cb6955438787bb81fccd6fca929e5337cc7fdac766ee0` |

Das Blatt `python` enthält 78 Zeilen: 63 Bundesland-/Geschosszeilen, sieben AT-Kontrollzeilen und acht historische Aggregatzeilen. Der ursprüngliche Refactor erwartete bereits bereinigte Eingaben. Die Integration entfernt gezielt die sieben Zeilen `AT ohne Wien und Salzburg` und die Zeile `Alles`, protokolliert diese und behält die Prüfung unbekannter Regionen bei. Dies ist eine Importkorrektur, keine neue Modellannahme.

Der Originaldatenlauf liest 170.163 Gebäudezeilen; 158.350 bleiben für die Zielnutzungen verwendbar. 11.811 Zeilen fallen unter andere Nutzungen, zwei Gebäude liegen über GFZ 20. Die ausgeschlossene Stichproben-BGF beträgt zusammen 3.843.501,6 m². Das ist keine fehlende nationale Ziel-Fläche: Die nationale Allokation verwendet weiterhin die vollständigen positiven statistischen Zielzellen.

Die neun Bundesländer ergeben exakt 847.147.914 m² NGF beziehungsweise 1.058.934.892,5 m² BGF bei Faktor 0,8. Der Abgleich mit den AT-Kontrollzeilen schließt. Der numerische Residualwert der neu berechneten nationalen BGF liegt bei etwa −0,00000012 m². Alle 516 positiven Zielkombinationen werden flächenerhaltend berechnet. Sechs automatisierte Tests bestehen (fünf übernommene Tests plus Test gegen Doppelzählung historischer Sammelzeilen).

Der neue Lauf liegt unter `outputs/recalculated/`, die Anlieferung bleibt unter `outputs/`. `comparison.json` quantifiziert den Vergleich bis auf die einzelnen GFZ-Bins: Beide Fassungen enthalten 83.703 Zeilen und stimmen innerhalb numerischer Toleranz überein. Die größte absolute Abweichung eines Bins beträgt rund 0,0000000056 m². Die prüfbare Reproduktion ist damit nicht auf die Auswertung gespeicherter Notebook-Ausgaben beschränkt.

Getestete Umgebung: Python 3.13, NumPy 2.3.2, pandas 2.3.2, SciPy 1.16.1, Matplotlib 3.10.6. Der erste Testaufruf scheiterte ausschließlich am nicht beschreibbaren Windows-Sandbox-Tempverzeichnis; mit lokalem `TEMP`/`TMP` bestehen alle Tests. Excel-Lesewarnungen über nicht unterstützte Formatierungserweiterungen betreffen keine gespeicherten Änderungen: Die Arbeitsmappen werden nicht zurückgeschrieben.

## Freigegebene Ersatzregel

Freigabe durch den Auftraggeber am 21.10.2026: vorhandene Ersatzhierarchie beibehalten, fachliche Restfragen dokumentieren. 91 von 516 positiven Zielzellen benötigen Ersatzreferenzen; ihr Flächenanteil beträgt 17.960.405 m² beziehungsweise 1,696082 %. 425 Zielzellen und 98,303918 % der BGF verwenden die primäre Referenz.

| Ersatztyp | BGF [m²] |
|---|---:|
| Wien, gleiche Nutzung und Geschossklasse | 17.361.748,75 |
| Salzburg, gleiche Nutzung und nächste Geschossklasse | 66.302,50 |
| Wien, gleiche Nutzung und nächste Geschossklasse | 532.353,75 |

Die Freigabe betrifft den Einsatz dieser Schätzregel für den Arbeitsstand. Sie bestätigt weder eine unabhängige Repräsentativitätsprüfung noch einen fertig kalibrierten PEQ-Standard. Der Ersatzanteil ist auch kein statistisches Fehlerintervall. Tirol hat mit rund 3,21 % einen etwas höheren Ersatzanteil als der nationale Wert; das ist ausdrücklich dokumentiert und kein Anlass für eine neue Schleife.

## Phase 2 – nur dokumentiert

| Prüfthema | Befund / verbleibende Einschränkung |
|---|---|
| Vollständigkeit | Alle neun Bundesländer und 516 positive Zielkombinationen vorhanden. 51 der insgesamt 567 möglichen Kombinationen haben keine positive Zielfläche und erscheinen nicht im Audit. |
| Region und Stichprobengröße | Audit enthält tatsächliche Region/Geschossklasse, Zahl der Referenzgebäude und Ersatzstatus. Mindestfallzahl fünf. Ersatzzuordnungen sind freigegeben. |
| Flächengewichtung | KDE nutzt BGF als Gewichte; Verteilungen und Aggregationen erhalten die statistische BGF. Keine unabhängige Gegenrechnung mit gebäudeanzahlgewichteter KDE durchgeführt. |
| GFZ-Rand und Bandbreite | Scott-Bandbreite, Raster 0–20. Normierung entfernt KDE-Masse außerhalb dieses Bereichs. Keine Bandbreiten-/Rand-Sensitivitätsrunde. |
| Ausreißer und Zuordnung | Zwei Referenzgebäude über GFZ 20 ausgeschlossen. Auffällige Nutzungs-/Geschosskombinationen (etwa EZFH mit 11+) nicht im Einzelnen fachlich bereinigt. |
| Salzburg als Referenz | Räumliche Repräsentativität für die acht Bundesländer bleibt Annahme; keine zusätzlichen regionalen Daten beschafft. |
| NGF/BGF | Einheitlicher Faktor 0,8 aus Altmodell übernommen, nicht typologiespezifisch neu kalibriert. |
| Fehlende Statistikwerte | Übernommener Import setzt leere numerische Zellen auf null. Quellenbedeutung leer/null bleibt offen; keine künstlichen Ergänzungen. |
| Quellenjahr und Rechte | Referenzjahr 2021 gemäß übergebener Methodendokumentation. Ursprüngliche Statistik-Austria-Abfrage und Weitergaberechte nicht unabhängig recherchiert. Rohdateien bleiben lokal. |
| Originalmethodik | Alte Notebooks, `utils.py`, Paper und Präsentation liegen nicht in der aktuellen Anlieferung. Deren beschriebene Fehler/Annahmen werden als Handoff-Befund geführt, nicht als neu unabhängig bestätigte Codeprüfung. |
| 2040 | Kein Neubau-/Abriss-/Sanierungspfad und keine PEExcel-Kennwerte integriert. Das ist Phase 4. |

Die technischen Bilanzkontrollen gehören zur Reproduktion (Phase 1). Sie sind keine nachträglich eingeschobene methodische Phase-2-Schleife. Fehlende Informationen werden für diesen Arbeitsstand akzeptiert und bleiben sichtbar.

## Unterschiede zur früheren Implementierung

Laut Handoff wurden zuvor Geschossklassen uneinheitlich bezeichnet, Flächen teilweise mit `pivot_table()` gemittelt, Restösterreich als Sammelregion behandelt, hohe Geschossklassen gesondert Wien zugeordnet und KDEs ohne BGF-Gewichtung erstellt. Die übernommene Refactor-Fassung vereinheitlicht Klassen, summiert Flächen, berechnet jedes Bundesland separat, gewichtet nach BGF und dokumentiert jede Ersatzreferenz. Diese fachlichen Änderungen stammen aus dem bereitgestellten Refactor.

Neu in dieser Integration: Wiederherstellung der Dateizuordnung, Unterstützung der Originalstatistik mit historischen Summenzeilen, Eingabe-Hashes, unabhängige Ergebnisaggregation und Vergleich, ergänzte Grafiken, Notebook-Pfade und Methodenabschnitt in Kapitel 3. Keine erneute Modellentwicklung oder Änderung der freigegebenen Ersatzhierarchie.

## Phase 3 und Übergabe

Vier Darstellungen sind in Kapitel 3 enthalten: Methodikschema, Wien/Salzburg-Vergleich, nationale BGF nach Nutzung und statistische Abdeckung. Der Regionalvergleich zeigt die hochgerechneten Landesverteilungen einschließlich ihrer jeweiligen Struktur und Ersatzreferenzen. Er wird ausdrücklich nicht als Vergleich unveränderter Rohstichproben ausgegeben. Die drei PNGs werden aus dem Originaldatenlauf reproduzierbar erzeugt; das Schema steht in Quarto als Mermaid.

`allocation_audit.csv` ist die vollständige verlangte Tabelle nach Bundesland/Nutzung/Geschossklasse einschließlich Prüfwerten. Der Bericht zeigt zusätzlich die Bundeslandsummen. Das Kapitel wurde als HTML mit Quarto gerendert; ein PDF-/Word-Neubau und eine Veröffentlichung gehören nicht zu diesem Arbeitsschritt.
