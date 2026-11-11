# THG-Zielwert: interne Arbeitsrechnung mit Senkenvergleich

- `03_zielwert_thg_intern_senkenvergleich.ipynb` in JupyterLab / VS Code öffnen; alle Zellen ausführen.
- Python-Abhängigkeiten: `numpy`, `pandas`, `matplotlib`, `ipykernel`.
- Bei Ablage des Notebooks mit den vier CSV-Dateien im selben Verzeichnis werden CSV-Eingaben genutzt; ohne Dateien greifen die eingebetteten Ausgangsdaten.
- Stellschrauben in Abschnitt **2. Stellschrauben**: globales Budget, EPC-Faktor, Welt-/AT-Bevölkerung, Bevölkerung für Senken, Senkenstufen, Sektoranteil, BGF, Jahre.
- Vergleich **Lamboll / Alaux**: Globalbudgets ab 2023 mit Alaux-EPC (0,10 %) und Bevölkerungsanteil aus World Bank 2023, jeweils Zielwerte mit 0 und 1 t CO₂e/(Person·a) bis 2025/2026.
- Die ursprüngliche historische Referenz 320 kg CO₂e/m² BGF ist weiterhin prüfbar.
- Vorsicht: UBA-Gesamt-THG (CO₂e) von CO₂-Budget abgezogen; Arbeitshypothese. Der 2025-NowCast ist vorläufig. CO₂-Senken sind zusätzliche, zu diskutierende Annahmen.

**Quellen:** Lamboll et al. (2023) doi:10.1038/s41558-023-01848-5; Alaux et al. (2023) doi:10.1088/1742-6596/2600/15/152004; Schneider et al. (2025) doi:10.3390/designs9060123; World Bank Population total (SP.POP.TOTL) 2023 Austria und World; Umweltbundesamt Österreich THG-Inventar 2026 und NowCast 2025.
