# AP6.1 – Nachtrag Dekarbonisierungsrate und Vorbereitung AP7

Stand 17.11.2026, Fassung 1.6.1-AP6. Nachtrag zu AP6 (1.6.0). Vorfassungen auf dem Gerät gesichert unter `archiv/vor_AP61_20261117/`.

## Fachliche Ergänzung

Dekarbonisierungsrate = Fläche, die zwischen A und B von fossil versorgt (Erdgas, Öl) auf erneuerbar versorgt (Wärmepumpen aller Arten, Fernwärme, Bio, Strom/Elektro) wechselt, bezogen auf die Ausgangs-NGF \(T_A\); Jahresrate = Gesamtwert / Zeitspanne (16 Jahre). Die Gruppenzuordnung steht in `config/flaechenstroeme/massnahmen.json` (Schema 1.1, Abschnitt `dekarbonisierung`) und wird validiert (jeder Versorgungsträger genau einer Gruppe, keine unbekannten Träger).

Neue Ausgaben:

- Maßnahmenraten: „Dekarbonisierungsrate“, „davon fossil → WP/FW/Bio/Strom“, „davon aus Erdgas/Öl“, Gegenrichtung „Wechsel erneuerbar → fossil“.
- `Fossilbilanz.csv` und Excel-Blatt „Fossilbilanz“: fossile Ausgangsfläche \(F_A\) = bleibt fossil + dekarbonisiert + abgerissen; fossile Endfläche \(F_B\); Anteile an \(F_A\) und Raten je Jahr.
- Kontrollen: Fossilbilanz geschlossen; Dekarbonisierung ≤ Versorgungswechsel; Gruppenzuordnung vollständig.

## Ergebnisse (Prüfumgebung, gespeicherte Rekonstruktionen)

| Kennzahl | Transition_2040 | Transition_2040_Wachstum |
|---|---|---|
| Versorgungswechselrate | 46,042 % / 2,878 %/a | 42,066 % / 2,629 %/a |
| Dekarbonisierungsrate | 293,658 Mio m² = 33,000 % / 2,062 %/a | 273,294 Mio m² = 30,712 % / 1,919 %/a |
| davon fossil → WP | 24,571 % | 21,042 % |
| davon fossil → FW | 4,619 % | 5,282 % |
| davon fossil → Bio | 3,801 % | 4,378 % |
| davon fossil → Strom | 0,009 % | 0,009 % |
| davon aus Erdgas / Öl | 20,0 % / 13,0 % | 18,485 % / 12,227 % |
| fossile Fläche A / B | 311,455 / 17,797 Mio m² | 311,455 / 19,000 Mio m² |
| fossil abgerissen | 0 | 19,162 Mio m² |
| Dekarbonisierung bezogen auf \(F_A\) | 94,29 % (5,89 %/a) | 87,75 % (5,48 %/a) |

Alle Kontrollen OK. Die Zahl hängt an der ausgewählten zulässigen Zuordnung (max. unveränderte Fläche, dann min. Versorgungswechsel); sie ist eine rekonstruktionsbasierte Kennzahl, keine beobachtete Rate.

## AP7-Vorbereitung

- Neues Modul `modell/abnahme.py` (nur lesend): `abnahmestand()` listet je gespeichertem Szenario, Vergleich und Flussergebnis Status OK/FEHLT/HINWEIS/FEHLERHAFT; `wiederholbarkeit()` vergleicht eine neue Rekonstruktion mit der gespeicherten (Status, Zielwerte, Neubau/Abriss, Maßnahmenraten, Flüsse je Typpaar; Toleranz \(\max(1\ \text{m}^2, 10^{-7} T_A)\)).
- Notebook 00: Abschnitt „Abnahmestand (AP7)“, Schalter `ABNAHMESTAND_PRUEFEN = False`.
- Notebook 03: Abschnitt 8 mit Dekarbonisierung und Fossilbilanz; neuer Abschnitt 9 „Wiederholbarkeit (Abnahme)“; Speichern jetzt Abschnitt 10.
- `docs/AP7/AP7_Abnahmeprotokoll.md`: Ablauf Schritte 0–9 gemäß Arbeitsauftrag §12, Abgleich §14, Sollwerte, Felder für Ist-Werte und Abzeichnung.

## Prüfungen

| Prüfung | Ergebnis |
|---|---|
| Testsuite `python -m unittest discover -s tests -v` | 87 Tests OK (488,8 s), `AP61_Testlauf.txt` |
| `distribution_to_json.py self-test` | 19 Tests OK |
| Notebook 00 mit `ABNAHMESTAND_PRUEFEN=True` | läuft, Fassung 1.6.1-AP6 erkannt |
| Notebook 03 Standardlauf | nur Lesen, keine Optimierung |
| Notebook 03 mit `MODUS='Rekonstruktion'`, `REKONSTRUIEREN=True` (Transition) | Wiederholbarkeit: alle 7 Prüfungen OK, Differenz 0,00 m²; nichts gespeichert (`EXPORTIEREN=False`) |
| Wiederholbarkeit Wachstum (Skript) | bitidentisch |

## Abgrenzung / offene Punkte

- Gespeicherte Flussergebnisse aus 1.5.x/1.6.0 bleiben gültig; sie enthalten die Dekarbonisierungszeilen erst nach erneutem Export (Status HINWEIS im Abnahmestand). Keine Neuberechnung nötig, Raten werden beim Laden neu ausgewertet.
- Wachstumsszenario: Energieberechnung lokal noch ausständig (AP7 Schritt 2).
- Vollabnahme AP7 lokal durch den Nutzer; synthetische Tests ersetzen sie nicht.
