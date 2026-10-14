# Interner Reviewvermerk: Kapitel 3 und redaktionelle Gesamtüberarbeitung

Stand: 14.10.2026. Lesefassung: [Kapitel 3](../Kapitel/03-allokation.qmd).

## Was der Entwurf leistet

Nationale Energieallokation, Dichteprinzip und Bestandskalibrierung, nutzungsbezogenes Mobilitätsbudget sowie Herleitung der drei THG-Budgets sind ausgearbeitet. Normative Entscheidungen, angewendete Parametrisierung und Fortschreibung sind getrennt. Die Rückrechnungen dienen ausschließlich der internen Kontrolle. Die Rechnung zu L1/L2/L3 ist mit den gedruckten nationalen Größen reproduziert; das ist keine vollständige Validierung der zugrunde liegenden Allokationsmethode.

Der Rechenweg liegt in [Berechnungen/allokation.py](../Berechnungen/allokation.py). Er verwendet nur die Python-Standardbibliothek und muss beim Rendern nicht ausgeführt werden. Die Dichteformeln erläutern das Prinzip und die Flächengewichtung; sie sind keine neue Kalibrierung.

## Erste Durchsicht und Perspektivkorrektur eingearbeitet

Klarstellung von Simon Schneider vom 14.10.2026:

- **Flächenprojektion und Ableitung:** 2040 ist das ursprüngliche Ziel- und Prognosejahr; die 906,7 Mio. m² BGF beziehen sich auf 2040. Die abweichende Jahresangabe im Artikel bleibt ausschließlich hier und im Quellenregister vermerkt; im Bericht gilt eindeutig 2040.
- **2050:** Vorsorglich späterer Dekarbonisierungszeitpunkt wegen einer möglichen Verzögerung gegenüber dem ursprünglichen Ziel. Keine bereits beschlossene Verschiebung der Flächenprognose oder des nationalen Klimaziels. Eine spätere Umstellung bleibt eine gesonderte Fortschreibung.
- **Sonstige Darstellung:** Der Auftraggeber hat die bisher erläuterte Vorgehensweise grundsätzlich bestätigt. Die publizierte Kombination aus 50-jähriger Senkenannahme und Dekarbonisierung ab 2050 bleibt bestehen; daraus wird keine weitere Rückfrage gemacht.

Die erste Durchsicht hat zur beauftragten Perspektivkorrektur geführt. Alle vorhandenen Kapitel, Kurzfassung, Startseite und Redaktionsdokumente sind angepasst. Die fachliche Schlussfreigabe bleibt offen. Aktuell keine zusätzlichen Entscheidungsfragen; Rundungs- und Quellenprüfungen benötigen kein Nutzerreview.

## Redaktionell erfasst, keine zusätzlichen Entscheidungen nötig

- Historischer sektoraler Saldo: 114,8 − 137,6 = −22,8 PJ/a, publiziert sind −22,7. Quellenwert nicht eigenmächtig korrigiert.
- Mobilität: Teilbudgets summieren sich zu 10,68 TWh PE/a. Teilflächen ergeben 547,7 statt 547,8 Mio. m². Rückrechnung einzelner Gutschriften weicht geringfügig ab; ungerundete Ausgangsdaten fehlen.
- Dichteparameter: Flächen-/Energiebezüge noch nicht konsistent genug für eine geprüfte numerische Kurve. Kein Ersatz durch erfundene Parameter. Die angekündigten Notebooks und 1.13.1-Daten bleiben ausstehend.
- „Auf dem Weg“ wird hinsichtlich der zeitlichen Budgetwirkung angebunden. Ausarbeitung von Etappen und europäischen Studien bleibt ein eigenes Arbeitspaket.
- Keine neuen Szenarien, Tooldefaults oder Fallzahlen eingesetzt. Kapitel 1 und 2 sowie die Kurzfassung wurden redaktionell angepasst.

## Aus der öffentlichen Fassung entfernte Prüfdetails

- THG-Rückrechnung: L1 71,69, L2 195,76, L3 319,84 kg CO₂e/m² BGF. Im Bericht stehen die übernommenen Werte 72/196/320; die erklärende L3-Herleitung bleibt.
- Die Formeln zum Dichteprinzip und zur Aggregation sind erläuternde, einheitlich formulierte Beziehungen. Gleichung 9 der Veröffentlichung ist verkürzt; BGF-/NGF- und Energiebezüge der Parameter bleiben vor numerischer Neukalibrierung abzugleichen. Bis dahin Grafikübernahme oder Platzhalter, keine erfundene Kurve.
- Die Übertragung des nationalen CO₂-Budgets auf einen THG-Kennwert ist eine methodische Konvention. Ein erfolgreicher Rechenabgleich validiert nicht das gesamte Bilanzmodell.
- Einzelbelege zu Lebenszyklusmodulen/Normfassung, Übergangsregeln und freigegebenen Presets bleiben den Punkten M05/M06/M08/M11 zugeordnet.

Maßstab für weitere Redaktion: nachvollziehbare Methodenerklärung mit passenden Eigenzitaten; kein öffentliches Protokoll der Quellenprüfung. Tabellen und Abbildungen müssen für die Arbeitsfassung nicht neu berechnet oder gezeichnet werden.
