# AP6.2 – Kombinationsdiagnose (Wachstumsszenario, Solverstatus 2)

Stand 17.11.2026, Fassung 1.6.2-AP6. Vorfassungen auf dem Gerät gesichert unter `archiv/vor_AP62_20261117/`.

## Befund

Lokal geändert (17.11.2026, 15:32/15:45):

- `Verteilung_Transition_2040_Wachstum.xlsx`: Qualität ZIEL 1960-79 7 %, Neu_20cm 30,62 %, Neu_30cm 35 %; Versorgung ZIEL DH 38 %, Bio 20 %, Öl 1 %, Elektro 6 %, WP gesamt 33 %.
- `uebergaenge.json`: Qualität 1990-99 → Neu_20cm/Neu_30cm; neu vor1919, 1919-44, 1945-59 → Neu_10cm.

In der Prüfumgebung (Modell 1.6.1, lokale Verteilung und Regeln) nachgestellt: Zustand-ID `e3ac469b4eb250b1`, Bestandsbilanz `BILANZ_OK`, Blockdiagnose „0 Konflikte in 0 Blöcken“, Rekonstruktion `NICHT_MACHBAR` (HiGHS Status 2, unzulässig).

Ursache (Fehlmengen-LP, Gesamtfehlmenge 39 147 m²): Die bisherige Diagnose prüfte jedes Merkmal einzeln. Unzulässig ist aber eine Kombination zweier Merkmale:

| Konflikt | Blöcke | Defizit | Erklärung |
|---|---|---|---|
| Qualität 1990-99 × Versorgung Öl (Zunahme) | GWB_7G, alle 6 Wetter-/Massenblöcke | 38 672 m² | 1990-99 entsteht nur aus 1990-99, Öl nur aus Öl; Neubau mit Öl nicht freigegeben. A hat in GWB_7G/1990-99 kein Öl (Prior 0 in Verteilung_Bestand_2024), die Wachstumsverteilung hat dort den Prior 0,0519 und verteilt bei 1 % Öl-Ziel Fläche darauf. |
| Qualität Neu_20cm × Versorgung {Bio, WP} (Abnahme) | EFH_2G · Innsbruck · mittel, schwer | 2 × 237,7 m² | Neu_20cm bleibt Neu_20cm, Bio/WP bleiben Bio/WP; Neu_20cm darf nicht abgerissen werden. B hat in diesen Blöcken weniger Neu_20cm mit Bio/WP als A. |

## Änderung

- `flaechenstroeme._kombinations_konflikte`: notwendige Bedingung für Kombinationen veränderlicher Merkmale (Produkte abgeschlossener Kategoriemengen; Zunahme ≤ A + freigegebener Neubau, Abnahme ≤ B + freigegebener Abriss), global und je Block; nur minimale Kombinationen. Eingebunden in `blockdiagnose` und in die Vorprüfung der Rekonstruktion mit Neubau/Abriss.
- `flaechenstroeme._fehlmengen`: bei Solverstatus 2 nennt die Diagnose die Typen mit nicht zuordenbarer Fläche (Ebene „Fehlmengen A/B“).
- Zulässige Fälle: Rechenweg und Ergebnisse unverändert (Tests Transition/Wachstum in voller Größe, Wiederholbarkeit).

## Prüfungen

| Prüfung | Ergebnis |
|---|---|
| Testsuite (92 Tests, davon 5 neu `Kombinationsdiagnose`) | OK (503,9 s), `AP62_Testlauf.txt` |
| Notebook 03 mit lokalem Stand, Standardlauf | Blockdiagnose „8 Konflikte in 8 Blöcken“, Eigenschaft „Kombination“; Dauer der Diagnose ≈ 8 s |
| Diagnose = Fehlmengen-LP | 6 Blöcke 1990-99 × Öl = 38 672 m²; 2 Blöcke Neu_20cm × Bio/WP = 475 m² (deckungsgleich) |
| Test: nur Öl-Prior GWB_7G/1990-99 → 0 (Wert auf Erdgas) | weiterhin `NICHT_MACHBAR`, Diagnose: nur noch Neu_20cm × Bio/WP (2 Blöcke) |
| Test: zusätzlich Regel Neu_20cm → Neu_30cm | `MACHBAR` (Abriss 19,873 Mio m², Neubau 80,0 Mio m²) |

## Offene fachliche Entscheidung

Möglichkeiten zur Auflösung (Nutzerentscheidung; nichts davon ist in den gelieferten Dateien umgesetzt):

1. Öl: in `Verteilung_Transition_2040_Wachstum.xlsx`, Blatt Versorgung, Zeile GWB_7G/1990-99 den Öl-Prior auf 0 setzen (Zeilensumme 1 erhalten, z. B. Wert zu Erdgas), oder Öl-Ziel 0 %.
2. Neu_20cm × Bio/WP in EFH_2G/Innsbruck: entweder Übergang Neu_20cm → Neu_30cm in `uebergaenge.json` zulassen (getestet, machbar), oder Neu_20cm-Ziel bzw. Prioren so anpassen, dass B dort nicht unter A fällt.

Die AP7-Sollwerte für das Wachstumspaar sind nach der Entscheidung neu zu bestimmen. Das Hinweisblatt der Wachstumsverteilung nennt noch die alten Versorgungsziele (nur Text).
