"""Plausibilitätsrechnungen zu Kapitel 3; keine Implementierung von PEExcel.

Quellen: Schneider et al. (2025), Designs 9(6), 123, Tabellen 2/A1;
Schneider et al. (2023), Buildings 13(5), 1210, Tabellen 6/8/9.
Aufruf: python Berechnungen/allokation.py (nur Standardbibliothek).
"""
from decimal import Decimal as D


def thg_budget(restbudget_mt, personen_mio, senke_t_pro_person_jahr,
               jahre, sektoranteil, bgf_mio_m2):
    """kg CO2e/m² BGF gemäß publizierter Allokationskonvention.

    Mt / Mio. m² = t/m²; Faktor 1000 ergibt kg/m².
    Prüft nicht die wissenschaftliche CO2/CO2e-Budgetübertragung.
    """
    brutto_mt = restbudget_mt + personen_mio * senke_t_pro_person_jahr * jahre
    return brutto_mt * sektoranteil / bgf_mio_m2 * D(1000)


def mobilitaetsgutschrift(budget_twh, ngf_mio_m2):
    """Jährliches Budget TWh/(Mio. m²) in kWh/(m² a)."""
    return budget_twh / ngf_mio_m2 * D(1000)


if __name__ == "__main__":
    for name, senke, publiziert in [
        ("L1", "0", 72), ("L2", "0.5", 196), ("L3", "1", 320)
    ]:
        wert = thg_budget(D(130), D(9), D(senke), D(50), D("0.5"), D("906.7"))
        assert round(wert) == publiziert, (name, wert, publiziert)
        print(f"{name}: {wert:.2f} kg CO2e/m² BGF; publiziert {publiziert}")
    zeilen = [
        ("Wohnen", "5.30", "375.6", "14.11"),
        ("Büro/Gewerbe", "2.20", "53.1", "41.47"),
        ("Bildung", "0.29", "22.5", "12.93"),
        ("Handel/sonstige", "2.89", "96.5", "29.97"),
    ]
    for name, budget, flaeche, publiziert in zeilen:
        wert = mobilitaetsgutschrift(D(budget), D(flaeche))
        print(f"{name}: {wert:.4f}; publiziert {publiziert}; "
              f"Differenz {wert-D(publiziert):+.4f} kWh PE/(m² NGF a)")
    print("Mobilitätsbudget [TWh PE/a]:", sum(D(z[1]) for z in zeilen))
    print("Teilflächen [Mio. m² NGF]:", sum(D(z[2]) for z in zeilen),
          "; publizierte Summe 547.8")
    print("Stromsaldo aus gedruckten Zahlen [PJ/a]:",
          D("114.8") - D("137.6"), "; publizierter Saldo -22.7")
