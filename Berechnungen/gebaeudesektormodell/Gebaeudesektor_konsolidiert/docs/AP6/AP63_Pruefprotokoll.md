# AP6.3 – Prioren aus globalen Zielen und Erreichbarkeitsprüfung

Stand 17.11.2026, Fassung 1.6.3-AP6. Auftrag: Stufe A (Szenarioeingabe nur über globale Ziele, Prior-Verteilungen optional, leere Zellen regelbasiert befüllen) und Stufe B (Erreichbarkeitsprüfung beim Bilden eines Zustands). Vorfassungen auf dem Gerät gesichert unter `archiv/vor_AP63_20261117/`.

## Plan und Abgrenzung

| Schritt | Inhalt | Ergebnis |
|---|---|---|
| A1 | Eingabe lesen: ZIEL-Zeilen Pflicht, leere Prior-Zellen/-Zeilen erlaubt | `prioren.lies_eingabe` |
| A2 | Globale Verschiebung Basis → Ziele nach Regeln, Neubau, Abriss | `prioren._transport` (Qualität × Versorgung gemeinsam, PV getrennt) |
| A3 | Leere Zellen befüllen, Eingaben behalten | `prioren.leite_ab`, `_fuelle` |
| A4 | Vollständige Verteilungsdatei schreiben, Status und Veralten erkennen | `schreibe_abgeleitet`, `status` |
| A5 | Bedienung in 00/01 mit Schalter `PRIOREN_ABLEITEN=False` | Notebooks 1.6.3 |
| B1 | Zustand gegen gespeicherte Gegenzustände aller Paare prüfen (ohne Solver) | `prioren.erreichbarkeit` (nutzt `flaechenstroeme.blockdiagnose`) |

Nicht verändert: `gebaeudesektor.py` und `distribution_to_json.py`. Beide gehen mit ihrem SHA-256 in die Zustands-ID ein. Meine frühere Aussage, eine Änderung nur an `distribution_to_json.py` lasse die IDs unverändert, war falsch. Deshalb ist die Ableitung eine Vorstufe: Sie schreibt eine vollständige Excel-Verteilung, die der Kern wie jede andere liest (Kalibrierung auf die ZIEL-Zeilen unverändert). Kein zweiter Szenariorechenkern; `bestandsbilanz.py` wird nur gelesen (N, D, Freigaben).

## Methode (1.0)

1. Basis: gespeicherter Zustand (`prioren.basis`), Flächen je Typ und wirksame Verteilungen aus dem Laufprotokoll.
2. Gemeinsame Transportmatrix Qualität × Versorgung von der Basis zu den Zielanteilen, mit Neubauzeile und Abrissspalte (Mengen und Freigaben aus `Bestandsentwicklung.xlsx` für das Paar Basis → Szenario). Zulässig: Verbleib, Übergänge nach `uebergaenge.json`, WP nur in WP-Qualitäten. Startwert \(\theta^{\text{Zahl geänderter Merkmale}}\) mit \(\theta = 0{,}05\); Maximum-Entropie-Lösung durch iteratives proportionales Anpassen.
3. Vorab: LP-Machbarkeitsprüfung (Fehlmengen; nicht erreichbare Ziele werden mit den größten Fehlmengen abgewiesen) und LP-Trägerbestimmung (Übergänge, die in keiner zulässigen Lösung positiv sein können, werden auf 0 gesetzt). Letzteres beseitigte in der ersten Fassung 34 Kleinstkonflikte (51 m², Neu_10cm).
4. Prior-Zeilen als Herkunftsmischung: Versorgung je (Geometrie, Qualität) aus der Basisfläche dieser Geometrie, die in die Qualität gelangt, mit ihrer verschobenen Versorgung, plus Neubau; Qualität je Baujahrband = Basiszeile · Qualitätsverschiebung plus Neubau; PV je Geometrie analog. Geometrie, Speichermasse, Flexibilität aus der Basis.
5. Eingegebene Zellen haben Vorrang; leere Zellen teilweise befüllter Zeilen erhalten den Rest im Verhältnis der abgeleiteten Werte. Zellen ohne zulässige Herkunft = 0.

## Prüfungen

| Prüfung | Ergebnis |
|---|---|
| `test_prioren` (9 Tests: Füllregel, exakte Summen, Status FEHLT → AKTUELL, kein Schreiben ohne Änderung, Bytegleichheit, Ziele exakt erreicht, Erreichbarkeit ohne Solver und Erkennung eines unerreichbaren Zustands, Vorrang der Eingabe, unerreichbare Ziele und Konfigurationsfehler, VERALTET bei Eingabe-/Regel-/Handänderung, bestehende Szenarien und Zustands-IDs unberührt) | OK |
| `test_notebook_sicherheit` (Schalter `PRIOREN_ABLEITEN=False`, Alias `pr`, Notebooks 00–03 ausführbar ohne Berechnung) | OK |
| Gesamte Testsuite (101 Tests, 543 s) | OK (`AP63_Testlauf.txt`) |
| `distribution_to_json.py self-test` | OK |
| Kerndateien `gebaeudesektor.py` (`0e11cc7e6d0b`), `distribution_to_json.py` (`afc031681543`) | unverändert gegenüber 1.6.2 und Gerät |

## Wachstumsszenario nur aus Zielen (Prüfumgebung)

Nachgestellt mit dem lokalen Stand vom 17.11.2026: lokale Übergangsregeln **ohne** Biomasse → Fernwärme, Ziele der lokalen Wachstumsverteilung (Qualität 1960-79 7 %, Neu_20cm 30,62 %, Neu_30cm 35 %; Versorgung DH 38 %, Bio 20 %, Erdgas 2 %, Öl 1 %, Elektro 6 %, WP gesamt 33 %; PV 50/25/15/10 %), alle Prior-Zellen leer, Basis `Bestand_2024`.

| Größe | Wert |
|---|---|
| Ableitung | ca. 3 s; 77 Iterationen (Qualität × Versorgung), 26 (PV); Restfehler < 1e-10; 177 erzwungene Nullflüsse; 1 655 Zellen abgeleitet, davon 894 strukturell 0 |
| Neubau / Abriss | 80 000 000 m² / 19 872 558 m² (Bestandsentwicklung) |
| Zustand | ID `ce43a7121bf5b531`, NGF 950 Mio. m², alle Bilanzkontrollen OK |
| Erreichbarkeit (Stufe B) | `KEINE_KONFLIKTE`, `BILANZ_OK` (8,9 s, ohne Solver) |
| Rekonstruktion Bestand_2024 → Wachstum | `MACHBAR` (96 s); geänderte Fläche 380,06 Mio. m², Versorgungswechsel 271,49 Mio. m² |

Die beiden Konflikte aus AP6.2 (GWB_7G · 1990-99 × Öl; EFH_2G · Innsbruck · Neu_20cm × Bio/WP) entstehen bei abgeleiteten Prioren nicht, weil Prior-Anteile nur dort entstehen, wo die Basis eine zulässige Herkunft hat. Die lokale Freigabe Biomasse → Fernwärme ist für diese Ziele daher nicht nötig. Welcher Weg gilt, ist fachlich zu entscheiden (`docs/OFFENE_PUNKTE.md`).

## Bedienung

`docs/BEDIENUNG.md`, Abschnitt „Szenario nur über globale Ziele“; Schema `docs/DATENSCHEMATA.md`, Abschnitt „Abgeleitete Prioren“; Vorlage `data/eingaben/verteilungen/Vorlage_Verteilung_nur_Ziele.xlsx` (Beispielziele Wachstum).

Registrierung, z. B. für eine Zielvariante des Wachstumsszenarios (lokal einzutragen; `config/szenarien.json` wurde nicht überschrieben):

```json
"Transition_2040_Wachstum": {
  "...": "bisherige Felder",
  "verteilungen": "data/eingaben/verteilungen/abgeleitet/Verteilung_Transition_2040_Wachstum.xlsx",
  "prioren": {"eingabe": "data/eingaben/verteilungen/Verteilung_Transition_2040_Wachstum.xlsx", "basis": "Bestand_2024"}
}
```

Hinweis: Als Eingabe kann auch die bisherige, vollständig befüllte Wachstumsdatei dienen; dann haben alle ihre Werte Vorrang und es wird nichts abgeleitet. Für die reine Zielvariante die Prior-Zellen leeren oder die Vorlage verwenden. Die Umstellung ändert die Zustands-ID; Vergleich und Flüsse des Paars sind danach neu zu erzeugen.

## Offene Punkte

- Fachliche Festlegung, ob das Wachstumsszenario für AP7 über Zielvorgaben (abgeleitete Prioren) oder mit eigenen Prioren und Freigabe Biomasse → Fernwärme geführt wird.
- Wechselgewicht 0,05 ist eine Setzung (Verbleib bevorzugt); andere Präferenzen sind nicht abgebildet.
- Qualitätsverschiebung je Baujahrband global, nicht je Geometrie; Typkonflikte zeigt Stufe B.
- Lokaler Lauf (Ableitung, 01, 03) steht aus.
