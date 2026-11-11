# Zielwert THG – reproduzierbare Budgetableitung (FAIR)

Öffnen: `03_zielwert_thg_fair_v2.ipynb` in JupyterLab / VS Code; `Restart & Run All`.
Python-Pakete: pandas, numpy, matplotlib, ipykernel.

## Bearbeitbare Tabellen
- `thg_nationale_klimabudgets.csv`: nationale CO2-Budgets, Quelle, Referenzjahr; Lamboll-AT-Werte offen.
- `thg_historische_emissionen_AT.csv`: jährliche Emissionen und Herkunft; THG-CO2e-Inventar von CO2-only getrennt.
- `thg_historische_aggregatannahmen.csv`: 150 Mt für 2022–2024 zur Reproduktion der S1-Originalrechnung.
- `thg_globale_budgets_kontext.csv`: globale Lamboll-Budgets in Gt CO2, **nicht** für nationale Allokation.

## Methodische Warnung
S1, Tab. A1 und Tabelle 2 reproduzieren den veröffentlichten L3-Wert von 320 kg/m² bei 1,5°C mit 66 % **ohne** temporäre Überschreitung. Bei **mit** Overshoot sind es bei sonst gleichen Annahmen ca. 353 kg/m². Die revidierte 2026-Berechnung verlangt jährliche CO2-only-Emissionen bis einschließlich 2025. Vorliegende UBA-NowCast-Gesamt-THG-Werte (CO2e) sind dafür nicht automatisch austauschbar.

## Quellen
- Schneider et al. (2025): https://doi.org/10.3390/designs9060123
- Steininger et al. (2022): https://doi.org/10.1038/s41467-022-31204-8
- Lamboll et al. (2023): https://doi.org/10.1038/s41558-023-01848-5
- UBA (2026), REP-1016: https://www.umweltbundesamt.at/fileadmin/site/publikationen/rep1016.pdf
- UBA (2026) NowCast: https://www.umweltbundesamt.at/news260902-treibhausgas-emissionen-2025

Dieses Paket hat keine externe Abhängigkeit von der ursprünglich hochgeladenen QMD- oder PDF-Datei; die ursprünglichen Quellen werden referenziert, nicht dupliziert.
