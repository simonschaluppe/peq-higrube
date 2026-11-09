"""Extract the supplied workbook into an editable, values-only input edition.

No energy aggregation or scientific mapping is performed here. Run before the
artifact-tool workbook builder; it never overwrites the supplied workbook.
"""
from pathlib import Path
import json, shutil
import pandas as pd
from utils import read_source, sha256

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
SOURCE = ROOT/'Redaktion/sektormodell/Building-Sector_Pool 1.xlsx'
SNAPSHOT = BASE/'data/Building-Sector_Pool_1.xlsx'
SNAPSHOT.parent.mkdir(exist_ok=True)
if SNAPSHOT.exists() and sha256(SNAPSHOT)!=sha256(SOURCE):
    raise ValueError('Existing versioned source differs; explicitly version a new snapshot.')
shutil.copy2(SOURCE, SNAPSHOT)
t=read_source(SNAPSHOT)
types=t['Strombed_estim'].copy()
types['BGF_2020_m2']=None
types['PEQ_Anteil_2040']=None
types['Quelle_Ergaenzung']=None
types['Unsicherheit_Notiz']=None
metrics=['EUI_plugloads','EUI_auxiliary','EUI_lighting','EUIh_el','EUIh_el_aux',
 'EUIc_el','EUIc_el_aux','EUIdhw_el','EUIv_el','Edhw_aux_el','EUIdhwdirect_el',
 'EUIev_el','Batt_total_charge_input','EUI_el_total','PV_total','PV_total_flex',
 'VRGrid_to_building','EUIh_district_heating','EUIdhw_district_heating',
 'EUIh_natural_gas','EUIdhw_natural_gas','EUIh_biomass','EUIdhw_biomass',
 'EUIh_other','EUIc_other','EUIdhw_other','fPE_grid','fPE_eff',
 'PEI_district_heating','PEI_natural_gas','PEI_biomass','PEI_other']
simulation=t['simulation'][['var_name',*metrics]].copy()
simulation=simulation.rename(columns={'var_name':'Archetype'})
dictionary=t['dictionary'].loc[t['dictionary'].metric.isin([*metrics,*t['Strombed_estim'].columns[9:]])]
parameters=pd.DataFrame([
 ['ngf_bgf',0.8,None,'Modellannahme aus Berechnungen/gfz_at; einheitlich, typologiespezifisch zu prüfen'],
 ['jahr_heute',None,None,'Quelldatei nennt heute ohne explizites Statistikjahr; nicht automatisch 2020'],
 ['jahr_pe_bewertung',None,None,'Heutiger Bewertungsstand aus gelieferten PEI; Faktorversion noch zu bestätigen'],
 ['single_target_missing_share',1,None,'Vom Auftraggeber bestätigt: einzige GFZ-Zielklasse erhält 100 %; zweite Zielspalte nur bei Aufteilung'],
 ['density_f_res',30.4,2023,'Schneider et al. 2023, Tabelle 5: elektrische Referenz je Grundstücksfläche'],
 ['density_f_ed',26.4,2023,'Schneider et al. 2023, Tabelle 5: elektrische Referenz je BGF'],
 ['density_dx',0.15,2023,'Schneider et al. 2023, Gleichung 7 und Tabelle 5'],
 ['density_cutoff',62,2023,'Tabelle 5 PED-Typen; vorläufige EE-Lesart der gemischt beschrifteten Quellentabelle, keine neue PE-Umrechnung'],
 ],columns=['Parameter','Wert','Bezugsjahr','Quelle_Status'])
pe=pd.DataFrame([[y,e,None,None,None] for y in [2020,2040] for e in ['Netzstrom','PV_Export','Fernwaerme','Gas','Biomasse','Oel','Sonstige']],columns=['Szenariojahr','Energietraeger','f_PE','Faktor_Bezugsjahr','Quelle'])
notes=pd.DataFrame([
 ['Quelle','Building-Sector_Pool 1.xlsx, Lieferung 23.10.2026'],
 ['SHA256',sha256(SNAPSHOT)],
 ['Reinschrift','Gespeicherte Quellwerte, keine erneute PEExcel-Simulation. Wissenschaftliche Rechnung im Notebook.'],
 ['Flaechen','Nationale BGF in m²; Energiekennwerte laut Tabelle2 in kWh/(m² NGF a).'],
 ['Leerwerte','Leer bleibt unbekannt. Null bleibt explizite Null. BGF_2020 und PEQ_Anteil sind ergänzbar.'],
 ['Mapping','Nur A:F aus zuordnung_gfz. Breite Hilfsbereiche rechts sind keine zusätzlichen Zuordnungen.'],
 ['Ergaenzungen','Quelle_Ergaenzung und Unsicherheit_Notiz bei Änderungen ausfüllen; Originalquelle bleibt unverändert.'],
 ['Kennwerte','Anwendungen aus Tabelle2 per Archetype; Quellbezeichnungen und Einheiten im Woerterbuch.'],
 ],columns=['Thema','Hinweis'])
sheets={'Typen':types,'Anwendungen':simulation,'GFZ_Zuordnung':t['zuordnung_gfz'], 'Parameter':parameters,'PE_Faktoren':pe,'Woerterbuch':dictionary,'Hinweise':notes}
payload={k:json.loads(v.to_json(orient='split',index=False,force_ascii=False)) for k,v in sheets.items()}
(ROOT/'.local/building-inputs.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
print('Extracted',len(types),'types; source SHA256',sha256(SNAPSHOT))
