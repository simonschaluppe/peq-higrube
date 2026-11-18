# Offene Punkte (Stand 1.6.3-AP6, 17.11.2026)

## Lokal auszuführen (vor bzw. in AP7)

- Wachstumsszenario: Lösungsweg zu den Kombinationskonflikten lokal gewählt (Freigabe Biomasse → Fernwärme). Alternativ (1.6.3) Eingabe nur über globale Ziele: In der Prüfumgebung ergaben die abgeleiteten Prioren aus den Zielen vom 17.11.2026 mit den lokalen Regeln **ohne** Biomasse → Fernwärme 0 Konflikte und eine machbare Rekonstruktion (`docs/AP6/AP63_Pruefprotokoll.md`). Welcher Weg für AP7 gilt, ist fachlich festzulegen; die AP7-Sollwerte des Wachstumspaars danach neu eintragen.
- Umstellung eines Szenarios auf `prioren` ändert seine Verteilungsdatei und damit die Zustands-ID; gespeicherte Vergleiche und Flüsse dieses Szenarios sind danach neu zu erzeugen.
- Wachstumsszenario (Änderung vom 17.11.2026: Öl 1 %, DH 38 %, Bio 20 %, Elektro 6 %, WP 33 %, Neu_20cm/Neu_30cm 30,6/35 %; Regeln 1990-99 → Neu_20/30cm, vor1919–1945-59 → Neu_10cm): mit den lokalen Regeln `NICHT_MACHBAR` wegen zweier Kombinationskonflikte (GWB_7G · 1990-99 × Öl, 38 672 m²; EFH_2G · Innsbruck · Neu_20cm × Biomasse/WP, 475 m²). Fachliche Entscheidung zur Auflösung offen (siehe `docs/AP6/AP62_Pruefprotokoll.md`). Die AP7-Sollwerte für das Wachstumspaar gelten für den Stand vor dieser Änderung und sind nach der Neuberechnung zu ersetzen.
- Hinweisblatt der Wachstumsverteilung (Zeile „Versorgung“) nennt noch die alten Zielwerte (65 % WP, 25 % DH, 8 % Bio, 0 % Öl, 0 % Elektro); nur Text, ohne Rechenwirkung.
- Nach der Übertragung von 1.6.2 alle geöffneten Notebooks **ohne Speichern schließen**, neu öffnen und den Kernel neu starten (`docs/BEDIENUNG.md`, „Nach einer Aktualisierung“).
- Ergebnisse 1.5.1 bleiben gültig und ladbar; Dekarbonisierungsrate und Fossilbilanz werden aus den gespeicherten Flüssen ausgewertet. `Fossilbilanz.csv` und die neuen Protokollangaben entstehen beim nächsten Export (in AP7 nach der Wiederholbarkeitsprüfung mit `ERSETZEN=True`).
- AP7 – lokale Vollabnahme nach `docs/AP7/AP7_Abnahmeprotokoll.md` (Abschnitt 12, Schritte 0–9, Abschnitt 14); dazu `python -m unittest discover -s tests -v` in der lokalen Umgebung (bisher nur in der Prüfumgebung mit Python 3.14 und pandas 3.1 ausgeführt).
- `Transition_2040_Wachstum` ist ohne Energieanalyse gespeichert; für die Energievergleichbarkeit in AP7 mit `ENERGIE_BERECHNEN=True` neu speichern (Zustand-ID bleibt gleich).

## Fachlich (nicht sperrend)

- Prioren-Ableitung (1.6.3): Der Startwert bevorzugt Verbleib mit einem festen Wechselgewicht (0,05 je geändertem Merkmal). Andere fachliche Präferenzen (etwa bevorzugte Wechselpfade oder regionale Unterschiede) sind nicht abgebildet; Wetter (Region) geht nur über die Herkunftsmischung der Basis ein. Ergebnis ist eine regelkonforme Startverteilung, keine Prognose.
- Prioren-Ableitung: Qualitätsverschiebung je Baujahrband ist global (nicht je Geometrie); Konflikte, die nur auf Typebene entstehen, zeigt Abschnitt „Erreichbarkeit“ in 01.
- Dekarbonisierung: Fernwärme und Strom gelten als erneuerbar (Festlegung 17.11.2026); ihr Erzeugungsmix ist im Typenschema nicht abgebildet. Welche Abrissfläche fossil versorgt war, ist innerhalb der Freigaben nicht eindeutig (Fossilbilanz-Zeile „davon abgerissen“); der Saldo F_A − F_B ist eindeutig.
- Mehrdeutigkeit: Eindeutig sind „mindestens eine Änderung“ (Stufe 1) und die Versorgungswechselfläche (Stufe 2). Offen sind die Aufteilung auf Sanierung, PV und Flex sowie die Auswahl der Abriss- und Neubautypen innerhalb der Freigaben. Weitere Präferenzen (etwa Abriss bevorzugt aus den ältesten Qualitäten) wären eine neue fachliche Entscheidung.
- E6 `zusammensetzung` (Tabellen Gesamt/verbleibend/Neubau): vorläufig.
- Übernahme vorhandener Flussdateien (`flussdatei`) zusammen mit Neubau/Abriss ist nicht umgesetzt und mit Meldung gesperrt.
- Numerische Restflüsse unter 0,01 m² (insgesamt < 1 m²) können als Kleinstkombinationen erscheinen.

## Entschiedene Festlegungen (Abschnitt 13)

- E3 Bestandsentwicklung.xlsx: Aufbau Schema 1.0; Mengen und Freigaben am 17.11.2026 bestätigt. Abriss vor1919 bis 1990-99; Neubau Neu_20cm/Neu_30cm mit WP, Fernwärme, Biomasse oder Strom direkt. Abriss als Bilanzrest 19 872 558 m².
- E4 Neubau/Abriss: Raten (%/a, Bezug NGF A, linear) oder Periodenflächen; Bilanzrest nur ausdrücklich.
- E5 Abrisszuordnung: regelgebunden über Freigaben; bei gleicher unveränderter Fläche minimaler Versorgungswechsel (17.11.2026).
- E7 Sanierung = alle zulässigen Qualitätswechsel; E8 Nenner = Ausgangs-NGF; E9 „Versorgungswechselrate“ (alle 16.11.2026).
- E11 Dekarbonisierungsrate: Wechsel fossil (Erdgas, Öl) → erneuerbar bzw. nicht fossil (Biomasse, Fernwärme, Wärmepumpe, Strom direkt), Nenner Ausgangs-NGF, zusätzlich Bezug auf die fossile Ausgangsfläche (17.11.2026).
- E10 lokaler Python-Interpreter: in AP7 zu bestätigen.

## Technisch

- Die Zustands-ID enthält den SHA-256 der gesamten Datei `gebaeudesektor.py`; jede Änderung dort ändert alle IDs. Deshalb blieb die Datei seit AP3 unverändert, auch `MODELLVERSION` (`1.3.0-AP3`) und die interne Hilfsfunktion `_relativ` (vom Notebook nicht mehr genutzt). Vorschlag für später: Hash nur über eine explizite Rechenkern-Version.
- `scenarios.parquet` wird nur über Name und Größe nachgewiesen (schwach; `DATENSCHEMATA.md`, „Nachweisstärke“).
- Die Bestandsentwicklung ist nicht Teil des Zustands-Fingerprints. Sie wird im Flussprotokoll mit SHA-256 und inhaltlichem Fingerabdruck geführt.
- Rundungsreste der Kalibrierung (≈ 0,001 m²) können bei strenger Solvertoleranz zu „unzulässig“ führen. Deshalb gibt es einen zweiten Lauf mit der Toleranz aus `toleranz_m2`.
- Laufzeit (Prüfumgebung): Transition ca. 30 s, Wachstum ca. 100 s (gemeinsames LP mit rund 458 000 Variablen, zweistufig).
- Summenzeilen der Endenergieträger haben in `Kennwerte.csv` keine eigene Abdeckung. Der Vergleich verwendet die kleinste Abdeckung der Einzelträger.
- Notebook-Fenster mit Inhalten vor 1.6.0 haben keine Fassungsprüfung. Sie erkennen eine Aktualisierung also nicht selbst.
- Wiederholbarkeit: In der Prüfumgebung sind beide Paare bitgleich reproduziert. Auf anderer Plattform oder HiGHS-Version kann eine gleichwertige alternative Zuordnung entstehen (`HINWEIS`); maßgeblich sind die Zielwerte.
