"""Regelbasierte Flussrekonstruktion zwischen gespeicherten NGF-Zuständen.

Konstanter Bestand (AP3) oder mit explizitem Neubau/Abriss aus der Bestandsbilanz (AP4, modell/bestandsbilanz.py).
Keine Neukalibrierung, keine Jahresdynamik, kein impliziter Neubau/Abriss. Zustände A und B werden nur gelesen.
Einstieg: analysiere_rekonstruktion(rek_id, projekt, modus, rekonstruieren, ...). Status: STATUSWERTE.
"""
from pathlib import Path
from itertools import product
import json, hashlib, copy, shutil, uuid
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import coo_matrix,csr_matrix
import plotly.graph_objects as go
from distribution_to_json import DOMAENEN

DIMS=['geometry','quality','energy','pv','flex','weather','mass']
DOM={'geometry':DOMAENEN['geometrie'],'quality':DOMAENEN['qualitaet'],
     'energy':DOMAENEN['versorgung'],'pv':DOMAENEN['pv'],'flex':DOMAENEN['flex'],
     'weather':['Wien','Innsbruck'],'mass':DOMAENEN['masse']}
WP=set(DOMAENEN['versorgung'][:4])
WP_QUALITY={'1990-99','Neu_10cm','Neu_20cm','Neu_30cm'}
LABEL={'quality':'Qualität','energy':'Versorgung','pv':'PV','flex':'Flexibilität',
       'geometry':'Geometrie','weather':'Wetter','mass':'Speichermasse'}
SCHEMA='1.0'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def _rel(root,path):
    if root is None:return str(path)
    try:return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:return str(path)

def lade_regeln(path='uebergaenge.json'):
    cfg=json.loads(Path(path).read_text(encoding='utf-8'))
    validiere_regeln(cfg)
    return cfg

def validiere_regeln(cfg):
    if cfg.get('schema_version')!=SCHEMA:raise ValueError('Unbekanntes Regelschema.')
    if cfg.get('optimierung')!='maximale_unveraenderte_typenflaeche':raise ValueError('Unbekanntes Zuordnungsziel.')
    if not isinstance(cfg.get('unveraendert_erlaubt'),bool):raise ValueError('unveraendert_erlaubt muss boolesch sein.')
    fixed=cfg.get('unveraenderlich',[])
    if len(set(fixed))!=len(fixed) or not set(fixed)<=set(DIMS):raise ValueError('Ungültige unveränderliche Eigenschaften.')
    rules=cfg.get('regeln',{})
    if set(rules)&set(fixed):raise ValueError('Eigenschaft zugleich unveränderlich und mit Änderungsregel.')
    if set(rules)|set(fixed)!=set(DIMS):raise ValueError('Jede Eigenschaft braucht eine Regel oder muss unveränderlich sein.')
    tol=cfg.get('toleranz_m2')
    if isinstance(tol,bool) or not isinstance(tol,(int,float)) or not np.isfinite(tol) or not 0<tol<=0.1:raise ValueError('Flächentoleranz muss >0 und <=0.1 m² sein.')
    limit=cfg.get('max_kanten_je_block',2000000)
    if isinstance(limit,bool) or not isinstance(limit,int) or limit<1:raise ValueError('Ungültiges Kantenlimit.')
    for dim,r in rules.items():
        if r.get('typ')=='gruppen':
            if set(r)-{'typ','gruppen'}:raise ValueError('Unbekanntes Gruppenfeld.')
            for group in r.get('gruppen',[]):
                if set(group)!={'pre','post'}:raise ValueError('Gruppe braucht pre und post.')
                for side in ['pre','post']:
                    vals=group[side]
                    if not isinstance(vals,list) or not vals or len(vals)!=len(set(vals)) or not set(vals)<=set(DOM[dim]):raise ValueError(f'Ungültige Kategorien: {dim}/{side}')
        elif r.get('typ')=='aufstieg':
            if set(r)!={'typ','folge'} or len(r['folge'])!=len(set(r['folge'])) or set(r['folge'])!=set(DOM[dim]):raise ValueError('Aufstiegsfolge muss alle Kategorien genau einmal enthalten.')
        else:raise ValueError('Regeltyp muss gruppen oder aufstieg sein.')
    return True

def erlaubte_paare(dim,cfg):
    cats=DOM[dim]
    if dim in cfg['unveraenderlich']:return {(v,v) for v in cats}
    allowed={(v,v) for v in cats} if cfg['unveraendert_erlaubt'] else set()
    rule=cfg['regeln'][dim]
    if rule['typ']=='gruppen':
        for group in rule['gruppen']:allowed.update(product(group['pre'],group['post']))
    else:
        seq=rule['folge'];allowed.update((a,b) for i,a in enumerate(seq) for b in seq[i+1:])
    return allowed

def regeltabelle(cfg):
    validiere_regeln(cfg)
    return pd.DataFrame([{'Eigenschaft':d,'Pre':a,'Post':b,'Unveraendert':a==b}
                         for d in DIMS for a,b in sorted(erlaubte_paare(d,cfg))])

def validiere_zustand(df,tol=0.01):
    needed=set(DIMS)|{'NGF_m2'}
    if not needed<=set(df):raise ValueError(f'Fehlende Zustandsfelder: {needed-set(df)}')
    f=df.copy()
    f['NGF_m2']=pd.to_numeric(f.NGF_m2,errors='raise')
    if not np.isfinite(f.NGF_m2).all() or (f.NGF_m2<0).any() or f.NGF_m2.sum()<=0:raise ValueError('Ungültige NGF.')
    for d in DIMS:
        if f[d].isna().any():raise ValueError('Fehlende Kategorie.')
        f[d]=f[d].astype(str).str.strip()
    wrong=f.energy.isin(['FW_Wien','FW_erneu']) & f.energy.ne(f.weather.map({'Wien':'FW_Wien','Innsbruck':'FW_erneu'}))
    if (wrong & f.NGF_m2.gt(0)).any():raise ValueError('Fernwärme passt nicht zum Wetter auf belegter Fläche.')
    f['Typ']=f[DIMS].agg('|'.join,axis=1)
    if f.Typ.duplicated().any():raise ValueError('Doppelte Typen; Batchauswahl zuerst auflösen.')
    if 'Archetype' in f:
        parsed=f.Archetype.astype(str).map(lambda s:'|'.join(p.strip() for p in s.split('|')))
        if not parsed.eq(f.Typ).all():raise ValueError('Archetype widerspricht den Dimensionen.')
    f['energy']=f.energy.replace({'FW_Wien':'DH','FW_erneu':'DH'})
    for d in DIMS:
        if not set(f[d])<=set(DOM[d]):raise ValueError(f'Unbekannte Kategorie in {d}.')
    if f.loc[f.NGF_m2.gt(0)].duplicated(DIMS).any():raise ValueError('Doppelte Plan-Typen.')
    if (f.energy.isin(WP)&~f.quality.isin(WP_QUALITY)&f.NGF_m2.gt(0)).any():raise ValueError('WP in ausgeschlossener Qualität.')
    return f.loc[f.NGF_m2.gt(0)].reset_index(drop=True)

def lade_zustand(folder,root=None):
    folder=Path(folder);path=folder/'Verteilung.csv'
    df=pd.read_csv(path,sep=';',encoding='utf-8-sig')
    f=validiere_zustand(df)
    if df.Szenario.nunique()!=1 or df.Jahr.nunique()!=1:raise ValueError('Genau ein Szenario/Jahr erforderlich.')
    year=float(df.Jahr.iloc[0])
    if not np.isfinite(year) or year%1:raise ValueError('Jahr muss ganzzahlig sein.')
    logpath=folder/'laufprotokoll.json'
    log=json.loads(logpath.read_text(encoding='utf-8')) if logpath.exists() else {}
    return {'name':str(df.Szenario.iloc[0]),'jahr':int(year),'df':df,'datei':_rel(root,path),'sha256':sha(path),
            'zustand_id':log.get('zustand_id'),'protokoll_sha256':sha(logpath) if logpath.exists() else None}

def _marginal_conflicts(a,b,cfg):
    tol=cfg['toleranz_m2'];rows=[]
    ta=float(a.NGF_m2.sum());tb=float(b.NGF_m2.sum())
    if abs(ta-tb)>tol:
        rows.append({'Ebene':'Gesamt','Eigenschaft':'NGF','Kategorie':'Gesamt','Meldung':'Ungleiche Gesamt-NGF: ohne Bruttoangaben zu Neubau/Abriss (Bestandsentwicklung.xlsx) nicht rekonstruierbar.','Defizit_m2':abs(ta-tb)})
    for d in DIMS:
        x=a.groupby(d).NGF_m2.sum();y=b.groupby(d).NGF_m2.sum();allowed=erlaubte_paare(d,cfg)
        for cat,area in x.items():
            cap=float(y.reindex([v for u,v in allowed if u==cat],fill_value=0).sum())
            if area>cap+tol:rows.append({'Ebene':'Global','Eigenschaft':d,'Kategorie':cat,'Meldung':'Ausgangsfläche übersteigt erreichbare Zielfläche.','Ausgang_m2':float(area),'Kapazitaet_m2':cap,'Defizit_m2':float(area-cap)})
        for cat,area in y.items():
            cap=float(x.reindex([u for u,v in allowed if v==cat],fill_value=0).sum())
            if area>cap+tol:rows.append({'Ebene':'Global','Eigenschaft':d,'Kategorie':cat,'Meldung':'Zielfläche übersteigt zulässige Herkunftsfläche.','Ziel_m2':float(area),'Kapazitaet_m2':cap,'Defizit_m2':float(area-cap)})
    return rows

def _groups(frame,fixed):
    if not fixed:return {():frame}
    return {key if isinstance(key,tuple) else (key,):g for key,g in frame.groupby(fixed,sort=True,dropna=False)}

def _graph(a,b,cfg):
    if len(a)*len(b)>max(5000000,cfg.get('max_kanten_je_block',2000000)):raise MemoryError('Zu viele Kandidaten; unveränderliche Gruppen enger wählen.')
    mask=np.ones((len(a),len(b)),bool)
    for d in DIMS:
        pairs=erlaubte_paare(d,cfg)
        cats=DOM[d];idx={v:i for i,v in enumerate(cats)}
        support=np.array([[(u,v) in pairs for v in cats] for u in cats],bool)
        mask &= support[np.array([idx[v] for v in a[d]])[:,None],np.array([idx[v] for v in b[d]])[None,:]]
    i,j=np.where(mask)
    if len(i)>cfg.get('max_kanten_je_block',2000000):raise MemoryError('Kantenlimit überschritten; unveränderliche Gruppen enger wählen.')
    n=len(i)
    mat=coo_matrix((np.ones(2*n),(np.r_[i,len(a)+j],np.r_[np.arange(n),np.arange(n)])),shape=(len(a)+len(b),n)).tocsr()
    return i,j,mat

ZIELFUNKTION='2: max. unveränderte Fläche, dann min. Versorgungswechsel'
ZIELFUNKTION_TEXT=('Stufe 1: maximale vollständig unveränderte Bestandsfläche. Stufe 2 (Entscheidung 17.11.2026): bei gleicher '
                   'unveränderter Fläche (Toleranz toleranz_m2) minimale Bestandsfläche mit Versorgungswechsel.')

def _zweistufig(c1,c2,mat,rhs,opt,eps):
    """Lexikografisches LP: Stufe 1 minimiert c1; Stufe 2 minimiert c2 unter c1·x ≤ Optimum + eps.
    Gibt (Ergebnis Stufe 1, Ergebnis Stufe 2 oder None) zurück; Stufe 2 nur verwendet, wenn erfolgreich und Stufe-1-Wert gehalten."""
    r1=linprog(c1,A_eq=mat,b_eq=rhs,bounds=(0,None),method='highs',options=opt)
    if not r1.success:return r1,None
    if not np.any(c2):return r1,r1   # kein Versorgungswechsel möglich: Stufe 2 trivial erfüllt
    r2=linprog(c2,A_ub=csr_matrix(c1[None,:]),b_ub=[r1.fun+eps],A_eq=mat,b_eq=rhs,bounds=(0,None),method='highs',options=opt)
    if not r2.success or float(c1@r2.x)>r1.fun+2*eps:return r1,None
    return r1,r2

def _zielwerte(r1,r2,c1,c2,skala):
    s=r2 if r2 is not None else r1
    return {'zielfunktion':ZIELFUNKTION,'stufe2_geloest':r2 is not None,
            'geaendert_stufe1_m2':float(c1@r1.x)*skala,'geaendert_m2':float(c1@s.x)*skala,
            'versorgungswechsel_stufe1_m2':float(c2@r1.x)*skala,'versorgungswechsel_m2':float(c2@s.x)*skala}

def rekonstruiere(a,b,cfg,zeitlimit_s=None,extern=None):
    """LP je unveränderlichem Block (ohne Bruttovorgaben) bzw. gemeinsames LP mit Neubau/Abriss; Zielfunktion siehe ZIELFUNKTION_TEXT. Status: MACHBAR, NICHT_MACHBAR, NICHT_ABSCHLIESSEND_GELOEST (Zeit-/Iterationslimit), BERECHNUNGSFEHLER.
    Ungültige Eingaben lösen ValueError aus (in analysiere_rekonstruktion als EINGABEN_UNGUELTIG ausgewiesen)."""
    validiere_regeln(cfg)
    x=validiere_zustand(a['df']);y=validiere_zustand(b['df'])
    if b['jahr']<=a['jahr']:raise ValueError('Zeitreihenfolge: Zieljahr muss nach dem Ausgangsjahr liegen.')
    if extern is not None:return _rekonstruiere_extern(a,b,cfg,x,y,extern,zeitlimit_s)
    conflicts=_marginal_conflicts(x,y,cfg)
    base={'szenario_a':a['name'],'szenario_b':b['name'],'jahr_a':a['jahr'],'jahr_b':b['jahr'],
          'eingaben':{k:{z:v for z,v in s.items() if z!='df'} for k,s in [('A',a),('B',b)]},
          'regeln':copy.deepcopy(cfg),'regel_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
          'methode':'LP je unveränderlichem Block; '+ZIELFUNKTION_TEXT+' Direkte Gruppenübergänge; keine automatische Verkettung',
          'mehrdeutigkeit':'Eine optimale Zuordnung; gleichwertige Lösungen können existieren. Keine beobachteten Bruttomaßnahmen.',
          'solver':{'verfahren':'scipy.optimize.linprog, HiGHS, zweistufig','primal_feasibility_tolerance':1e-10,'dual_feasibility_tolerance':1e-10,'zeitlimit_s':zeitlimit_s},
          'schema_version':SCHEMA}
    if conflicts:return {**base,'status':'NICHT_MACHBAR','diagnose':pd.DataFrame(conflicts),'fluesse':pd.DataFrame(),'kontrollen':pd.DataFrame()}
    ga=_groups(x,cfg['unveraenderlich']);gb=_groups(y,cfg['unveraenderlich']);solutions=[];checks=[];stufen=[]
    for key in sorted(set(ga)|set(gb)):
        aa=ga.get(key,x.iloc[:0]).reset_index(drop=True);bb=gb.get(key,y.iloc[:0]).reset_index(drop=True)
        sa=float(aa.NGF_m2.sum());sb=float(bb.NGF_m2.sum());tol=cfg['toleranz_m2']
        block=' | '.join(map(str,key)) or 'Gesamt'
        if abs(sa-sb)>tol or not len(aa) or not len(bb):
            conflicts.append({'Ebene':'Block','Eigenschaft':'unveraenderlich','Kategorie':block,'Meldung':'Unveränderliche Blockrandsummen stimmen nicht überein.','Defizit_m2':abs(sa-sb)});continue
        i,j,mat=_graph(aa,bb,cfg)
        if not len(i):
            conflicts.append({'Ebene':'Block','Kategorie':block,'Meldung':'Keine zulässigen Kanten.'});continue
        row=aa.NGF_m2.to_numpy()/sa;col=bb.NGF_m2.to_numpy()/sa
        correction=1.-col.sum();col[np.argmax(col)]+=correction
        same=aa.Typ.to_numpy()[i]==bb.Typ.to_numpy()[j];c1=(~same).astype(float)
        c2=(aa.energy.to_numpy()[i]!=bb.energy.to_numpy()[j]).astype(float)
        r1,r2=_zweistufig(c1,c2,mat,np.r_[row,col],{'primal_feasibility_tolerance':1e-10,'dual_feasibility_tolerance':1e-10,**({'time_limit':float(zeitlimit_s)} if zeitlimit_s else {})},tol/sa)
        result=r2 if r2 is not None else r1
        if result.success:
            zw=_zielwerte(r1,r2,c1,c2,sa);stufen.append(zw)
        if not result.success:
            conflicts.append({'Ebene':'Block','Kategorie':block,'Meldung':'Gemeinsame Übergänge nicht erfüllbar oder Solverfehler.','Solverstatus':int(result.status),'Solvermeldung':result.message});continue
        values=result.x*sa
        re=float(np.max(np.abs(np.bincount(i,weights=values,minlength=len(aa))-aa.NGF_m2.to_numpy())))
        ce=float(np.max(np.abs(np.bincount(j,weights=values,minlength=len(bb))-bb.NGF_m2.to_numpy())))
        if min(values)<0 or max(re,ce)>tol:
            conflicts.append({'Ebene':'Numerik','Kategorie':block,'Meldung':'Abschlussprüfung fehlgeschlagen.','Max_Randfehler_m2':max(re,ce)});continue
        keep=values>0;i=i[keep];j=j[keep];values=values[keep]
        part=pd.DataFrame({'Herkunft_Typ':aa.Typ.to_numpy()[i],'Ziel_Typ':bb.Typ.to_numpy()[j],'NGF_m2':values})
        for d in DIMS:
            part['pre_'+d]=aa[d].to_numpy()[i];part['post_'+d]=bb[d].to_numpy()[j]
            part['Aenderung_'+d]=part['pre_'+d].ne(part['post_'+d])
        solutions.append(part)
        checks.append({'Block':block,'NGF_m2':sa,'Kanten_zulaessig':int(mat.shape[1]),'Kanten_belegt':len(part),'Max_Herkunftsfehler_m2':re,'Max_Zielfehler_m2':ce,'Numerische_Zielkorrektur_m2':correction*sa,'Status':'OK'})
    if conflicts:
        return {**base,'status':_status_aus_konflikten(conflicts),'diagnose':pd.DataFrame(conflicts),'fluesse':pd.DataFrame(),'kontrollen':pd.DataFrame(checks)}
    f=pd.concat(solutions,ignore_index=True)
    for d in DIMS:
        if any((u,v) not in erlaubte_paare(d,cfg) for u,v in set(zip(f['pre_'+d],f['post_'+d]))):raise AssertionError('Unzulässige Kante.')
    if (f.post_energy.isin(WP)&~f.post_quality.isin(WP_QUALITY)).any():raise AssertionError('WP-Zielkombination verletzt.')
    for col,node in [('Herkunft_Typ',x),('Ziel_Typ',y)]:
        err=(f.groupby(col).NGF_m2.sum().reindex(node.Typ,fill_value=0).to_numpy()-node.NGF_m2.to_numpy())
        if np.max(np.abs(err))>cfg['toleranz_m2']:raise AssertionError('Gesamtrandsumme verletzt.')
    f['Unveraendert']=f.Herkunft_Typ.eq(f.Ziel_Typ)
    base['zielwerte']={'zielfunktion':ZIELFUNKTION,'stufe2_geloest':all(s['stufe2_geloest'] for s in stufen),
                       **{k:float(sum(s[k] for s in stufen)) for k in ['geaendert_stufe1_m2','geaendert_m2','versorgungswechsel_stufe1_m2','versorgungswechsel_m2']}}
    return {**base,'status':'MACHBAR','diagnose':pd.DataFrame(columns=['Meldung']),'fluesse':f,'kontrollen':pd.DataFrame(checks)}

def aggregiere(result,dims):
    if result['status']!='MACHBAR':raise ValueError('Keine gültigen Flüsse verfügbar.')
    if not dims or not set(dims)<=set(DIMS):raise ValueError('Unbekannte Auswahl.')
    f=result['fluesse'];pre=['pre_'+d for d in dims];post=['post_'+d for d in dims]
    a=f.groupby(pre+post,as_index=False).NGF_m2.sum()
    a['Herkunftsanteil_pct']=100*a.NGF_m2/a.groupby(pre).NGF_m2.transform('sum')
    a['Zielanteil_pct']=100*a.NGF_m2/a.groupby(post).NGF_m2.transform('sum')
    return a

def sankey(result,dims):
    """Sankey der Bestandsflüsse; explizite externe Flüsse erscheinen als eigene Knoten 'Neubau' (links) und 'Abriss' (rechts).
    Diese Knoten sind reine Darstellungen expliziter Neubau-/Abrissflüsse, keine Gebäudetypen."""
    a=aggregiere(result,dims);pre=['pre_'+d for d in dims];post=['post_'+d for d in dims]
    t=pd.DataFrame({'q':a[pre].astype(str).agg(' | '.join,axis=1).to_numpy(),'z':a[post].astype(str).agg(' | '.join,axis=1).to_numpy(),'NGF_m2':a.NGF_m2.to_numpy()})
    n,d=_extern_tabellen(result);NEU='Neubau (Zeitraum)';ABR='Abriss (Zeitraum)'
    if len(d):t=pd.concat([t,pd.DataFrame({'q':d[pre].astype(str).agg(' | '.join,axis=1).to_numpy(),'z':ABR,'NGF_m2':d.NGF_m2.to_numpy()})])
    if len(n):t=pd.concat([t,pd.DataFrame({'q':NEU,'z':n[post].astype(str).agg(' | '.join,axis=1).to_numpy(),'NGF_m2':n.NGF_m2.to_numpy()})])
    t=t.groupby(['q','z'],as_index=False,sort=True).NGF_m2.sum()
    t['hq']=100*t.NGF_m2/t.groupby('q').NGF_m2.transform('sum');t['hz']=100*t.NGF_m2/t.groupby('z').NGF_m2.transform('sum')
    sl=sorted(set(t.q)-{NEU})+([NEU] if NEU in set(t.q) else []);tl=sorted(set(t.z)-{ABR})+([ABR] if ABR in set(t.z) else [])
    si={v:i for i,v in enumerate(sl)};ti={v:len(sl)+i for i,v in enumerate(tl)}
    lab=lambda v,j:v if v in (NEU,ABR) else v+' · '+str(j)
    fig=go.Figure(go.Sankey(node={'label':[lab(v,result['jahr_a']) for v in sl]+[lab(v,result['jahr_b']) for v in tl],'pad':16,'thickness':18},
        link={'source':[si[v] for v in t.q],'target':[ti[v] for v in t.z],'value':t.NGF_m2/1e6,
              'customdata':t[['hq','hz']].to_numpy(),
              'hovertemplate':'%{source.label} → %{target.label}<br>%{value:.4f} Mio. m² NGF<br>%{customdata[0]:.2f} % der Herkunft<br>%{customdata[1]:.2f} % des Ziels<extra></extra>'}))
    fig.update_layout(title=' → '.join([result['szenario_a'],result['szenario_b']])+' · '+' × '.join(LABEL[d] for d in dims),template='plotly_white',height=800)
    return fig

def exportiere(result,cfg,root='.',ersetzen=False):
    root=Path(root);target=root/cfg['ausgabe']
    _pruefe_exportziel(result,cfg,root,target)
    if target.exists() and not ersetzen:raise FileExistsError(f'{_rel(root,target)} existiert bereits. Zum Ersetzen ERSETZEN = True setzen.')
    target.parent.mkdir(parents=True,exist_ok=True);stage=target.parent/('.fluss_'+uuid.uuid4().hex[:12]);stage.mkdir()  # bewusst ohne tempfile.mkdtemp (Windows-ACL)
    try:
        result['diagnose'].to_csv(stage/'Machbarkeit.csv',sep=';',index=False,encoding='utf-8-sig')
        result['kontrollen'].to_csv(stage/'Kontrollen.csv',sep=';',index=False,encoding='utf-8-sig')
        result.get('pruefungen',pd.DataFrame(columns=['Pruefung','Status','Detail'])).to_csv(stage/'Pruefungen.csv',sep=';',index=False,encoding='utf-8-sig')
        regeltabelle(cfg).to_csv(stage/'Erlaubte_Uebergaenge.csv',sep=';',index=False,encoding='utf-8-sig')
        (stage/'uebergaenge_verwendet.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
        if isinstance(result.get('bestandsbilanz'),pd.DataFrame) and len(result['bestandsbilanz']):
            result['bestandsbilanz'].to_csv(stage/'Bestandsbilanz.csv',sep=';',index=False,encoding='utf-8-sig',float_format='%.17g')
        md=result.get('massnahmen_definition') if result['status']=='MACHBAR' else None
        if md is not None:
            import massnahmen as ms
            mtab={'Massnahmenraten':ms.massnahmenraten(result,md),'Massnahmenkombinationen':ms.massnahmenkombinationen(result,md),
                  'Versorgungswechsel_Gruppen':ms.versorgungswechsel_matrix(result,md),'Fossilbilanz':ms.fossilbilanz(result,md),'Massnahmen_Kontrollen':ms.kontrollen(result,md)}
            if result.get('extern') is not None:
                mtab['Neubau_Merkmale']=ms.extern_merkmale(result,md,'Neubau');mtab['Abriss_Merkmale']=ms.extern_merkmale(result,md,'Abriss')
            if (mtab['Massnahmen_Kontrollen'].Status=='FEHLER').any():raise AssertionError('Maßnahmenkontrollen fehlgeschlagen.')
            mtab['Massnahmenraten'].to_csv(stage/'Massnahmenraten.csv',sep=';',index=False,encoding='utf-8-sig',float_format='%.17g')
            mtab['Fossilbilanz'].to_csv(stage/'Fossilbilanz.csv',sep=';',index=False,encoding='utf-8-sig',float_format='%.17g')
            mtab['Massnahmenkombinationen'].to_csv(stage/'Massnahmenkombinationen.csv',sep=';',index=False,encoding='utf-8-sig',float_format='%.17g')
            (stage/'massnahmen_verwendet.json').write_text(json.dumps(md,ensure_ascii=False,indent=2),encoding='utf-8')
        if result['status']=='MACHBAR':
            f=result['fluesse'];f.to_csv(stage/'Fluesse.csv',sep=';',index=False,float_format='%.17g')
            if result.get('extern') is not None:
                for name in ['neubau','abriss']:result[name].to_csv(stage/(name.capitalize()+'.csv'),sep=';',index=False,float_format='%.17g')
            sankey_auswahl(result).write_html(stage/'Sankey_Auswahl.html',include_plotlyjs=True,full_html=True)
            views={'Qualitaet':['quality'],'Versorgung':['energy'],'Qualitaet_Versorgung':['quality','energy'],'PV_Flex':['pv','flex']}
            with pd.ExcelWriter(stage/'Flussanalyse.xlsx',engine='openpyxl') as writer:
                result['kontrollen'].to_excel(writer,sheet_name='Kontrollen',index=False)
                if isinstance(result.get('bestandsbilanz'),pd.DataFrame) and len(result['bestandsbilanz']):result['bestandsbilanz'].to_excel(writer,sheet_name='Bestandsbilanz',index=False)
                aenderungsanteile(result).to_excel(writer,sheet_name='Aenderungsanteile',index=False)
                if result.get('extern') is not None:
                    result['neubau'].to_excel(writer,sheet_name='Neubau',index=False);result['abriss'].to_excel(writer,sheet_name='Abriss',index=False)
                    for dname,dim in [('Qualitaet','quality'),('Versorgung','energy')]:zusammensetzung(result,dim).to_excel(writer,sheet_name='Zusammensetzung_'+dname,index=False)
                if md is not None:
                    for sheet,tab in mtab.items():
                        tab.to_excel(writer,sheet_name=sheet,index=(sheet=='Versorgungswechsel_Gruppen'))
                for name,dims in views.items():
                    tab=aggregiere(result,dims);tab.to_excel(writer,sheet_name=name,index=False)
                    pre=['pre_'+d for d in dims];post=['post_'+d for d in dims]
                    tab.pivot_table(index=pre,columns=post,values='NGF_m2',aggfunc='sum',fill_value=0).to_excel(writer,sheet_name=name+'_Matrix')
                    sankey(result,dims).write_html(stage/('Sankey_'+name+'.html'),include_plotlyjs=True,full_html=True)
        else:
            (stage/'KEINE_FLUESSE.txt').write_text(result['status']+': '+statusbedeutung(result['status'])+' Keine gültige Flusstabelle oder Sankey-Grafik erzeugt. Siehe Machbarkeit.csv und Pruefungen.csv. Keine automatische Lockerung.',encoding='utf-8')
        protocol={k:v for k,v in result.items() if k not in ['diagnose','fluesse','kontrollen','pruefungen','ausgabe','quelle','ordner','neubau','abriss','bestandsbilanz','massnahmen_definition']}
        if md is not None:protocol['massnahmen_sha256']=hashlib.sha256(json.dumps(md,sort_keys=True).encode()).hexdigest()
        protocol['eingaben']={k:{z:v for z,v in e.items() if z not in ('df','ordner')} for k,e in result.get('eingaben',{}).items()}
        protocol['modul_sha256']=sha(__file__)
        import platform, fassung
        protocol['software']={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':__import__('scipy').__version__,'projektfassung':fassung.FASSUNG}
        protocol['module_sha256']={n:sha(Path(__file__).with_name(n)) for n in ['flaechenstroeme.py','bestandsbilanz.py','massnahmen.py','fassung.py'] if Path(__file__).with_name(n).is_file()}
        if result['status']==MACHBAR:
            ab=result.get('abriss');ta=float(result['fluesse'].NGF_m2.sum())+(float(ab.NGF_m2.sum()) if isinstance(ab,pd.DataFrame) and len(ab) else 0.0)
            protocol['raten']={'nenner':'Ausgangs-NGF T_A','nenner_m2':ta,'zeitspanne_jahre':result['jahr_b']-result['jahr_a'],
                               'formel':'r_M = 100 · A_M / (T_A · (J_B − J_A)) in % der Ausgangs-NGF pro Jahr (lineare mittlere Periodenrate)'}
        protocol['ausgaben']={n.name:sha(n) for n in sorted(stage.iterdir()) if n.is_file()}
        (stage/'flussprotokoll.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2,allow_nan=False,default=str),encoding='utf-8')
        backup=None
        if target.exists():
            backup=target.with_name('.'+target.name+'_backup_'+uuid.uuid4().hex[:8])
            if backup.exists():raise FileExistsError(backup)
            target.rename(backup)
        try:stage.rename(target)
        except Exception:
            if backup is not None:backup.rename(target)
            raise
        if backup is not None:shutil.rmtree(backup)
        return target
    finally:
        if stage.exists():shutil.rmtree(stage)

def sankey_auswahl(result):
    views=[('Qualität',['quality']),('Versorgung',['energy']),('Qualität × Versorgung',['quality','energy']),('PV × Flex',['pv','flex'])]
    fig=go.Figure()
    for i,(label,dims) in enumerate(views):
        trace=sankey(result,dims).data[0]
        trace.visible=(i==0)
        fig.add_trace(trace)
    fig.update_layout(template='plotly_white',height=850,title='Flächenströme · Qualität',
        updatemenus=[dict(x=0,y=1.12,buttons=[dict(label=label,method='update',args=[{'visible':[j==i for j in range(len(views))]},{'title':'Flächenströme · '+label}]) for i,(label,dims) in enumerate(views)])])
    return fig


# Integration 1: gemeinsame Auswertung bereits berechneter Flüsse, ohne neues LP.
# pandas < 3.1: 'round_trip' für bitgenaues Einlesen; ab 3.1 ist das der Standard und die Option veraltet.
_CSV_GENAU={} if tuple(int(v) for v in pd.__version__.split('.')[:2] if v.isdigit())>=(3,1) else {'float_precision':'round_trip'}

def blockdiagnose(a,b,cfg,bilanz=None):
    """Notwendige (nicht hinreichende) Bedingungen je unveränderlichem Block, ohne Solver.
    Mit Bruttovorgaben (bilanz mit Status BILANZ_OK) dieselben Bedingungen wie vor dem gemeinsamen LP mit Neubau/Abriss
    (Bilanz, Kapazitäten, Blockbilanz, Merkmalshüllen). Ohne Bruttovorgaben bei gleicher NGF Bedingungen für konstanten
    Bestand; bei ungleicher NGF eine einzige Meldung „nur Nettoänderung bekannt“ (ab 1.6.0, keine Scheinkonflikte je Block)."""
    validiere_regeln(cfg)
    x=validiere_zustand(a['df']);y=validiere_zustand(b['df']);rows=[]
    import bestandsbilanz as bb
    ext=bb.extern_fuer(bilanz) if bilanz else None
    if ext is not None:
        for r in _extern_konflikte(x,y,cfg,ext,bb.maske(x,ext['freigabe_abriss']).to_numpy(),bb.maske(y,ext['freigabe_neubau']).to_numpy()):
            rows.append({'Block':r['Kategorie'].split(' · ')[0] if r['Ebene']=='Block' else 'Gesamt',**r})
        grundlage='mit Neubau/Abriss (Bestandsentwicklung, Status BILANZ_OK)'
    elif abs(float(x.NGF_m2.sum())-float(y.NGF_m2.sum()))>cfg['toleranz_m2']:
        # Ohne Bruttovorgaben ist bei ungleicher NGF nur N − D bekannt: keine Blockprüfung (sonst Scheinkonflikte je Block).
        st=(bilanz or {}).get('status','keine Bestandsbilanz übergeben')
        rows.append({'Block':'Gesamt','Ebene':'Gesamt','Eigenschaft':'NGF','Kategorie':'Bilanz',
                     'Meldung':f'NGF A ≠ NGF B und keine gültigen Bruttovorgaben ({st}): nur die Nettoänderung ist bekannt; '
                               'Blockdiagnose nicht möglich. Bestandsbilanz mit Status BILANZ_OK übergeben: blockdiagnose(a, b, regeln, bilanz).',
                     'Defizit_m2':abs(float(y.NGF_m2.sum())-float(x.NGF_m2.sum()))})
        grundlage='keine (NGF A ≠ NGF B ohne Bruttovorgaben)'
    else:
        ga=_groups(x,cfg['unveraenderlich']);gb=_groups(y,cfg['unveraenderlich'])
        for key in sorted(set(ga)|set(gb)):
            aa=ga.get(key,x.iloc[:0]);bb_=gb.get(key,y.iloc[:0])
            blk=' | '.join(map(str,key)) or 'Gesamt'
            for row in _marginal_conflicts(aa,bb_,cfg):rows.append({'Block':blk,**row})
            for row in _kombinations_konflikte(aa,bb_,cfg,np.zeros(len(aa),bool),np.zeros(len(bb_),bool),'Block'):rows.append({'Block':blk,**row})
        grundlage='konstanter Bestand (ohne Neubau/Abriss)'
    out=pd.DataFrame(rows)
    out=out.sort_values('Defizit_m2',ascending=False).reset_index(drop=True) if len(out) else pd.DataFrame(columns=['Block','Ebene','Eigenschaft','Kategorie','Meldung','Defizit_m2'])
    out.attrs['grundlage']=grundlage
    out.attrs['bloecke']=int(out.Block.nunique()) if len(out) else 0
    return out

def _typenschluessel(value):
    if not isinstance(value,str) or len(value.split('|'))!=len(DIMS):raise ValueError('Typenschlüssel benötigt sieben Merkmale.')
    return '|'.join(v.strip() for v in value.split('|'))

def _ids_als_text(values):
    if values.map(lambda v:isinstance(v,(bool,np.bool_))).any():raise ValueError('Boolesche Typen-ID.')
    v=pd.to_numeric(values,errors='raise')
    if not np.isfinite(v).all() or (v<0).any() or (v%1!=0).any() or (v>np.iinfo(np.int64).max).any():raise ValueError('Ungültige Typen-ID.')
    return v.astype(np.int64)

def lade_berechnete_fluesse(datei,systemordner=None):
    """Semantisches Fluesse.csv oder ID-basierter Zeuge plus Part-2B-Knotenregister."""
    path=Path(datei);f=pd.read_csv(path,sep=';',encoding='utf-8-sig',**_CSV_GENAU)
    quellen={'fluesse':{'datei':str(path),'sha256':sha(path)}}
    if not {'Herkunft_Typ','Ziel_Typ'}<=set(f):
        if not {'Herkunft_ID','Ziel_ID','NGF_m2'}<=set(f) or systemordner is None:raise ValueError('ID-Flusstabelle benötigt Herkunft_ID, Ziel_ID, NGF_m2 und systemordner mit Part-2B-Knotenregistern.')
        for side,name,key in [('Herkunft','Herkunftstypen.csv','Herkunft_ID'),('Ziel','Erreichbare_Zieltypen.csv','Ziel_ID')]:
            p=Path(systemordner)/name;nodes=pd.read_csv(p,sep=';',encoding='utf-8-sig',**_CSV_GENAU)
            if not {'Typ_ID','Typ'}<=set(nodes):raise ValueError('Knotenregister ohne Typ_ID/Typ.')
            ids=_ids_als_text(nodes.Typ_ID)
            if ids.duplicated().any():raise ValueError('Doppelte Register-ID.')
            mapping=pd.Series(nodes.Typ.map(_typenschluessel).to_numpy(),index=ids)
            f[side+'_Typ']=_ids_als_text(f[key]).map(mapping)
            if f[side+'_Typ'].isna().any():raise ValueError('Fluss enthält unbekannte '+side+'-ID.')
            quellen[side+'_register']={'datei':str(p),'sha256':sha(p)}
    return f,quellen

def pruefe_berechnete_fluesse(a,b,cfg,fluesse,quellen=None):
    """Übernimmt keine Solver-/Eindeutigkeitsbehauptung. Prüft die konkrete Tabelle."""
    validiere_regeln(cfg);x=validiere_zustand(a['df']);y=validiere_zustand(b['df']);tol=cfg['toleranz_m2']
    if b['jahr']<a['jahr']:raise ValueError('Zieljahr liegt vor Ausgangsjahr.')
    f=fluesse.copy(deep=True)
    if not {'Herkunft_Typ','Ziel_Typ','NGF_m2'}<=set(f):raise ValueError('Flusstabelle braucht Herkunft_Typ, Ziel_Typ und NGF_m2.')
    if f.NGF_m2.map(lambda v:isinstance(v,(bool,np.bool_))).any():raise ValueError('Boolesche Flussfläche.')
    f['NGF_m2']=pd.to_numeric(f.NGF_m2,errors='raise')
    if not np.isfinite(f.NGF_m2).all() or (f.NGF_m2<0).any():raise ValueError('Flussflächen müssen endlich und nichtnegativ sein; keine automatische Reparatur.')
    for side in ['Herkunft_Typ','Ziel_Typ']:f[side]=f[side].map(_typenschluessel)
    inputrows=len(f);zero=int(f.NGF_m2.eq(0).sum());f=f.loc[f.NGF_m2.gt(0)].copy()
    if f.empty:raise ValueError('Keine positive Flussfläche.')
    if not set(f.Herkunft_Typ)<=set(x.Typ) or not set(f.Ziel_Typ)<=set(y.Typ):raise ValueError('Positive Flüsse verweisen auf nicht belegte oder unbekannte Zustands-Typen.')
    for side,node,col in [('pre',x,'Herkunft_Typ'),('post',y,'Ziel_Typ')]:
        lookup=node.set_index('Typ')
        for dim in DIMS:
            expected=f[col].map(lookup[dim])
            stored=side+'_'+dim
            if stored in f:
                supplied=f[stored].astype(str).str.strip()
                if dim=='energy':supplied=supplied.replace({'FW_Wien':'DH','FW_erneu':'DH'})
                if not supplied.eq(expected).all():raise ValueError('Gespeichertes Merkmal widerspricht Zustandsregister: '+stored)
            f[stored]=expected
    same=f.Herkunft_Typ.eq(f.Ziel_Typ)
    if 'Unveraendert' in f:
        if not f.Unveraendert.map(lambda v:isinstance(v,(bool,np.bool_))).all() or not np.array_equal(f.Unveraendert.to_numpy(),same.to_numpy()):raise ValueError('Unveraendert-Kennzeichen widerspricht Typen.')
    for dim in DIMS:
        allowed=erlaubte_paare(dim,cfg)
        if not set(zip(f['pre_'+dim],f['post_'+dim]))<=allowed:raise ValueError('Unzulässiger Übergang: '+dim)
        computed=f['pre_'+dim].ne(f['post_'+dim])
        old='Aenderung_'+dim
        if old in f and (not f[old].map(lambda v:isinstance(v,(bool,np.bool_))).all() or not np.array_equal(f[old].to_numpy(),computed.to_numpy())):raise ValueError('Änderungskennzeichen widerspricht Typen: '+dim)
    if (f.post_energy.isin(WP)&~f.post_quality.isin(WP_QUALITY)).any():raise ValueError('WP-Zielkombination verletzt.')
    # Only identical pairs are combined; no alternative pairing is selected.
    import math
    counts=f.groupby(['Herkunft_Typ','Ziel_Typ'],sort=True).NGF_m2.agg(lambda v:math.fsum(v))
    out=counts.rename('NGF_m2').reset_index()
    for side,node,col in [('pre',x,'Herkunft_Typ'),('post',y,'Ziel_Typ')]:
        lookup=node.set_index('Typ')
        for dim in DIMS:out[side+'_'+dim]=out[col].map(lookup[dim])
    for dim in DIMS:out['Aenderung_'+dim]=out['pre_'+dim].ne(out['post_'+dim])
    out['Unveraendert']=out.Herkunft_Typ.eq(out.Ziel_Typ)
    errors={}
    for label,col,node in [('Herkunft','Herkunft_Typ',x),('Ziel','Ziel_Typ',y)]:
        actual=out.groupby(col).NGF_m2.sum().reindex(node.Typ,fill_value=0).to_numpy();err=float(np.max(np.abs(actual-node.NGF_m2.to_numpy())))
        errors[label]=err
        if err>tol:raise ValueError(label+'-Randsummen verletzt: '+str(err)+' m².')
    total_a=math.fsum(x.NGF_m2);total_b=math.fsum(y.NGF_m2);total_f=math.fsum(out.NGF_m2)
    if max(abs(total_a-total_b),abs(total_a-total_f),abs(total_b-total_f))>tol:raise ValueError('Gesamtflächenbilanz verletzt; keine implizite Skalierung.')
    return {'schema_version':SCHEMA,'status':'MACHBAR','szenario_a':a['name'],'szenario_b':b['name'],'jahr_a':a['jahr'],'jahr_b':b['jahr'],
            'eingaben':{k:{z:v for z,v in s.items() if z!='df'} for k,s in [('A',a),('B',b)]},'flussquellen':copy.deepcopy(quellen or {}),
            'regeln':copy.deepcopy(cfg),'regel_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
            'methode':'Vorhandene berechnete Flüsse übernommen und geprüft; kein Solver, keine Neuzuordnung.',
            'mehrdeutigkeit':'Auswahl aus vorgelagertem Lauf unverändert übernommen; Eindeutigkeit, Optimalität und Reproduzierbarkeit werden hier nicht neu nachgewiesen.',
            'validierung':{'eingabezeilen':inputrows,'nullzeilen':zero,'identische_paare_zusammengefasst':inputrows-zero-len(out),
                           'optimalitaet_neu_geprueft':False,'reproduzierbarkeit_neu_geprueft':False},
            'diagnose':pd.DataFrame(columns=['Meldung']),'fluesse':out,
            'kontrollen':pd.DataFrame([{'Block':'Gesamt','NGF_m2':total_f,'Kanten_belegt':len(out),'Max_Herkunftsfehler_m2':errors['Herkunft'],'Max_Zielfehler_m2':errors['Ziel'],'Status':'OK'}])}

def uebernehme_berechnete_fluesse(a,b,cfg,datei,systemordner=None):
    f,sources=lade_berechnete_fluesse(datei,systemordner)
    return pruefe_berechnete_fluesse(a,b,cfg,f,quellen=sources)


def _pruefe_exportziel(result,cfg,root,target):
    """Ein Ergebnisordner darf keine Zustands- oder importierten Quelldateien ersetzen."""
    target=Path(target).resolve();root=Path(root)
    paths=[]
    for key in ['szenario_a','szenario_b']:
        if cfg.get(key):paths.append(root/cfg[key]/'Verteilung.csv')
    for s in result.get('eingaben',{}).values():
        if isinstance(s,dict) and s.get('datei'):paths.append(root/s['datei'])
    for s in result.get('flussquellen',{}).values():
        if isinstance(s,dict) and s.get('datei'):paths.append(root/s['datei'])
    for source in paths:
        if Path(source).resolve().is_relative_to(target):raise ValueError('Ausgabe würde eine Eingabedatei oder ihren Ordner ersetzen: '+str(source))


# AP1: Projektstruktur. Zustände aus results/szenarien/<ID>, Ausgabe nach results/flaechenstroeme/<ID>.
def lade_rekonstruktion(rek_id,projekt):
    """Setzt Regeln (config/flaechenstroeme/uebergaenge.json) und Paar (rekonstruktionen.json) zusammen. Startet nichts."""
    root=Path(projekt['root'])
    reg=json.loads(Path(projekt['konfiguration']['rekonstruktionen']).read_text(encoding='utf-8'))
    if reg.get('schema_version')!=SCHEMA:raise ValueError('Unbekanntes Schema in rekonstruktionen.json.')
    if rek_id not in reg['rekonstruktionen']:raise KeyError('Rekonstruktion nicht registriert: '+str(rek_id))
    r=reg['rekonstruktionen'][rek_id]
    regeln=root/r['regeln'] if r.get('regeln') else Path(projekt['konfiguration']['uebergaenge'])
    cfg=lade_regeln(regeln)
    szen=_rel(root,projekt['ergebnisse']['szenarien']);aus=_rel(root,projekt['ergebnisse']['flaechenstroeme'])
    cfg.update({'szenario_a':szen+'/'+r['szenario_a'],'szenario_b':szen+'/'+r['szenario_b'],'ausgabe':aus+'/'+rek_id,
                'flussdatei':r.get('flussdatei'),'systemordner':r.get('systemordner'),'regeldatei':_rel(root,regeln),'rekonstruktion_id':rek_id})
    return cfg

def lade_zustaende(cfg,projekt):
    root=Path(projekt['root'])
    return lade_zustand(root/cfg['szenario_a'],root),lade_zustand(root/cfg['szenario_b'],root)


# ---------------------------------------------------------------------------
# AP3: Statusbehandlung, Pflichtprüfungen, unveränderliche Zustände, gespeicherte Flüsse
# ---------------------------------------------------------------------------
NICHT_AUSGEFUEHRT='NICHT_AUSGEFUEHRT'
EINGABEN_UNGUELTIG='EINGABEN_UNGUELTIG'
MACHBAR='MACHBAR'
NICHT_MACHBAR='NICHT_MACHBAR'
NICHT_ABSCHLIESSEND='NICHT_ABSCHLIESSEND_GELOEST'
BERECHNUNGSFEHLER='BERECHNUNGSFEHLER'
STATUSWERTE=[NICHT_AUSGEFUEHRT,EINGABEN_UNGUELTIG,MACHBAR,NICHT_MACHBAR,NICHT_ABSCHLIESSEND,BERECHNUNGSFEHLER]
STATUSBEDEUTUNG={
    NICHT_AUSGEFUEHRT:'Keine Rekonstruktion gestartet bzw. keine vorhandenen Flüsse geladen.',
    EINGABEN_UNGUELTIG:'Zustände, Regeln, Zeitreihenfolge oder Flussdatei ungültig; es wurde nichts gelöst.',
    MACHBAR:'Gültige Flüsse; alle Pflichtprüfungen bestanden.',
    NICHT_MACHBAR:'Nachweislich keine zulässige Zuordnung unter den Regeln (Randsummen- oder Blockkonflikt bzw. Solver: unzulässig).',
    NICHT_ABSCHLIESSEND:'Solver hat Zeit- oder Iterationslimit erreicht. Kein Unmachbarkeitsnachweis.',
    BERECHNUNGSFEHLER:'Numerischer oder technischer Fehler; Ergebnis nicht verwendbar.'}
FLUSSAUSGABEN=['Machbarkeit.csv','Kontrollen.csv','Pruefungen.csv','Erlaubte_Uebergaenge.csv','uebergaenge_verwendet.json']

def _status_aus_konflikten(conflicts):
    """NICHT_MACHBAR, sobald ein Block nachweislich unzulässig ist (Randsummen-/Blockkonflikt, keine Kanten, Solver: unzulässig);
    sonst Zeit-/Iterationslimit → NICHT_ABSCHLIESSEND_GELOEST; sonst BERECHNUNGSFEHLER."""
    solver=[c['Solverstatus'] for c in conflicts if 'Solverstatus' in c]
    bewiesen=any('Solverstatus' not in c and c.get('Ebene')!='Numerik' for c in conflicts) or 2 in solver
    if bewiesen:return NICHT_MACHBAR
    if 1 in solver:return NICHT_ABSCHLIESSEND
    return BERECHNUNGSFEHLER

def statusbedeutung(status):
    return STATUSBEDEUTUNG.get(status,'Unbekannter Status')

def _leeres_ergebnis(status,meldung,cfg=None,a=None,b=None,pruefungen=None):
    r={'schema_version':SCHEMA,'status':status,'meldung':meldung,'szenario_a':a['name'] if a else (cfg or {}).get('szenario_a'),
       'szenario_b':b['name'] if b else (cfg or {}).get('szenario_b'),'jahr_a':a['jahr'] if a else None,'jahr_b':b['jahr'] if b else None,
       'eingaben':{k:{z:v for z,v in s.items() if z!='df'} for k,s in [('A',a),('B',b)] if s},
       'diagnose':pd.DataFrame([{'Meldung':meldung}]),'fluesse':pd.DataFrame(),'kontrollen':pd.DataFrame(),'neubau':pd.DataFrame(),'abriss':pd.DataFrame(),
       'pruefungen':pruefungen if pruefungen is not None else pd.DataFrame(columns=['Pruefung','Status','Detail'])}
    if cfg is not None:r['regeln']=copy.deepcopy(cfg)
    return r

def _p(rows,name,ok,detail=''):
    rows.append({'Pruefung':name,'Status':'OK' if ok else 'FEHLER','Detail':detail})
    return ok

def pruefe_eingaben(a,b,cfg,bilanz=None):
    """Pflichtprüfungen vor jeder Rekonstruktion oder Übernahme. Gibt Tabelle (Pruefung, Status, Detail) zurück; löst nichts."""
    rows=[]
    try:validiere_regeln(cfg);_p(rows,'Regeln gültig und dokumentiert',True,cfg.get('regeldatei',''))
    except Exception as e:_p(rows,'Regeln gültig und dokumentiert',False,str(e))
    for k,z in [('A',a),('B',b)]:
        try:validiere_zustand(z['df']);_p(rows,f'Zustand {k} gültig (Typen, Nichtnegativität, FW/Wetter, WP-Qualität)',True,z['name'])
        except Exception as e:_p(rows,f'Zustand {k} gültig (Typen, Nichtnegativität, FW/Wetter, WP-Qualität)',False,str(e))
        integ=z.get('integritaet')
        _p(rows,f'Zustand {k} gespeichert und unverändert (Ausgabehashes)',integ is None or str(integ).startswith('OK'),str(integ or 'nicht geprüft'))
    _p(rows,'Zeitreihenfolge (Jahr B > Jahr A)',b['jahr']>a['jahr'],f"{a['jahr']} → {b['jahr']}")
    ta=float(pd.to_numeric(a['df'].NGF_m2).sum());tb=float(pd.to_numeric(b['df'].NGF_m2).sum());tol=cfg.get('toleranz_m2',0.01)
    name='Gesamtbilanz T_A − D + N = T_B'
    st=(bilanz or {}).get('status')
    if st in (None,'NUR_NETTO'):
        if abs(ta-tb)<=tol:rows.append({'Pruefung':name,'Status':'OK','Detail':f'konstanter Bestand {ta:,.2f} m²; keine Bruttoangaben registriert – Rekonstruktion ohne Neubau/Abriss'})
        else:_p(rows,name,False,f'Nur Nettoänderung bekannt (N − D = {tb-ta:,.2f} m²); Neubau und Abriss sind daraus nicht bestimmbar. Bruttoangaben in Bestandsentwicklung.xlsx erforderlich.')
    elif st=='BILANZ_OK':
        _p(rows,name,True,f"A {ta:,.2f} m² − Abriss {bilanz['abriss_m2']:,.2f} m² + Neubau {bilanz['neubau_m2']:,.2f} m² = B {tb:,.2f} m² (Toleranz {bilanz['toleranz_m2']:g} m²)")
    else:
        _p(rows,name,False,f"{st}: {bilanz['meldung']}")
    return pd.DataFrame(rows)

def _extern_tabellen(result):
    leer=pd.DataFrame(columns=['NGF_m2'])
    n=result.get('neubau');d=result.get('abriss')
    return (n if isinstance(n,pd.DataFrame) and len(n) else leer),(d if isinstance(d,pd.DataFrame) and len(d) else leer)

def pruefe_fluesse(result,a,b,cfg):
    """Pflichtprüfungen an einer Flusstabelle (rekonstruiert oder übernommen), einschließlich expliziter Neubau-/Abrissflüsse."""
    rows=[];f=result['fluesse'];tol=cfg['toleranz_m2'];ext=result.get('extern')
    x=validiere_zustand(a['df']);y=validiere_zustand(b['df'])
    n,d=_extern_tabellen(result)
    _p(rows,'Nichtnegativität der Flüsse',bool((f.NGF_m2>=0).all()),f'min {float(f.NGF_m2.min()):.6g} m²')
    for dim in cfg['unveraenderlich']:
        _p(rows,f'Unveränderliche Eigenschaft {LABEL[dim]}',bool(f['pre_'+dim].eq(f['post_'+dim]).all()))
    for dim in DIMS:
        allowed=erlaubte_paare(dim,cfg);bad=set(zip(f['pre_'+dim],f['post_'+dim]))-allowed
        _p(rows,f'Zulässige Einzelübergänge {LABEL[dim]}',not bad,'; '.join(f'{u}→{v}' for u,v in sorted(bad)))
    _p(rows,'Gemeinsame Zielkombination nur als belegter Zieltyp',set(f.Ziel_Typ)<=set(y.Typ))
    _p(rows,'WP-Zielqualität',not bool((f.post_energy.isin(WP)&~f.post_quality.isin(WP_QUALITY)).any()))
    _p(rows,'Fernwärme/Wetter (Wetter unverändert, Zustände geprüft)',bool(f.pre_weather.eq(f.post_weather).all()))
    for lab,col,node,extra,key in [('Herkunftsrandsummen (Flüsse + Abriss)','Herkunft_Typ',x,d,'Herkunft_Typ'),('Zielrandsummen (Flüsse + Neubau)','Ziel_Typ',y,n,'Ziel_Typ')]:
        summe=f.groupby(col).NGF_m2.sum().reindex(node.Typ,fill_value=0).to_numpy()
        if len(extra):summe=summe+extra.groupby(key).NGF_m2.sum().reindex(node.Typ,fill_value=0).to_numpy()
        err=float(np.max(np.abs(summe-node.NGF_m2.to_numpy())))
        _p(rows,lab,err<=tol,f'max. Abweichung {err:.3g} m² (Toleranz {tol} m²)')
    tf=float(f.NGF_m2.sum());ta=float(x.NGF_m2.sum());tb=float(y.NGF_m2.sum());sn=float(n.NGF_m2.sum());sd=float(d.NGF_m2.sum())
    _p(rows,'Gesamtbilanz (Σ Flüsse + Abriss = NGF A; Σ Flüsse + Neubau = NGF B)',max(abs(tf+sd-ta),abs(tf+sn-tb))<=tol+1e-12*ta,
       f'Σ Flüsse {tf:,.2f} m², Abriss {sd:,.2f} m², Neubau {sn:,.2f} m², NGF A {ta:,.2f} m², NGF B {tb:,.2f} m²')
    zw=result.get('zielwerte')
    if zw:
        ist_g=float(f.NGF_m2[~f.Unveraendert].sum());ist_v=float(f.NGF_m2[f.pre_energy.ne(f.post_energy)].sum())
        _p(rows,'Zielwerte = Flüsse (geänderte Fläche, Versorgungswechsel)',max(abs(ist_g-zw['geaendert_m2']),abs(ist_v-zw['versorgungswechsel_m2']))<=1.0,
           f"geändert {ist_g:,.2f} m², Versorgungswechsel {ist_v:,.2f} m²")
        rows.append({'Pruefung':'Zweite Zielstufe: minimaler Versorgungswechsel bei gleicher unveränderter Fläche','Status':'OK' if zw['stufe2_geloest'] else 'HINWEIS',
                     'Detail':(f"Versorgungswechsel {zw['versorgungswechsel_stufe1_m2']:,.0f} → {zw['versorgungswechsel_m2']:,.0f} m²; geänderte Fläche {zw['geaendert_stufe1_m2']:,.2f} → {zw['geaendert_m2']:,.2f} m²"
                               if zw['stufe2_geloest'] else 'Stufe 2 nicht gelöst; Ergebnis der Stufe 1 verwendet')})
    if ext is None:
        _p(rows,'Keine externen Flüsse ohne Bruttoangaben',len(n)==0 and len(d)==0)
    else:
        import bestandsbilanz as bb
        btol=ext['bilanztoleranz_m2']+tol
        _p(rows,'Nichtnegativität Neubau/Abriss',bool((n.NGF_m2>=0).all() and (d.NGF_m2>=0).all()))
        _p(rows,'Abriss = Vorgabe',abs(sd-ext['abriss_m2'])<=btol,f"Σ Abriss {sd:,.2f} m², Vorgabe {ext['abriss_m2']:,.2f} m²")
        _p(rows,'Neubau = Vorgabe',abs(sn-ext['neubau_m2'])<=btol,f"Σ Neubau {sn:,.2f} m², Vorgabe {ext['neubau_m2']:,.2f} m²")
        okd=True if not len(d) else bool(bb.maske(d.rename(columns={'pre_'+k:k for k in DIMS}),ext['freigabe_abriss']).all())
        okn=True if not len(n) else bool(bb.maske(n.rename(columns={'post_'+k:k for k in DIMS}),ext['freigabe_neubau']).all())
        _p(rows,'Abriss nur aus freigegebenen Typen',okd);_p(rows,'Neubau nur in freigegebene Typen',okn)
    return pd.DataFrame(rows)

def _huelle(start,paare,rueckwaerts):
    """Kategorienmenge, die unter direkten zulässigen Übergängen abgeschlossen ist (Vorgänger bzw. Nachfolger)."""
    t=set(start);neu=True
    while neu:
        n={u for u,v in paare if v in t} if rueckwaerts else {v for u,v in paare if u in t}
        neu=not n<=t;t|=n
    return t

def _merkmal_huellen_konflikte(x,y,cfg,ma,mb,ebene):
    """Notwendige Bedingung je Merkmal: Fläche einer vorgängerabgeschlossenen Kategoriemenge T kann in B nur aus A_T oder
    freigegebenem Neubau in T stammen (B_T ≤ A_T + N_frei,T); analog A_U ≤ B_U + D_frei,U für nachfolgerabgeschlossene U."""
    rows=[];tol=cfg['toleranz_m2']
    for dim in DIMS:
        if dim in cfg['unveraenderlich']:continue
        paare=erlaubte_paare(dim,cfg)
        for c in DOM[dim]:
            t=_huelle({c},paare,True)
            if t!=set(DOM[dim]):
                inb=y[dim].isin(t).to_numpy();ina=x[dim].isin(t).to_numpy()
                bt=float(y.NGF_m2[inb].sum());at=float(x.NGF_m2[ina].sum());nt=float(y.NGF_m2[inb&mb].sum())
                if bt>at+nt+tol:rows.append({'Ebene':ebene,'Kategorie':f"{LABEL[dim]}: {', '.join(sorted(t))}",
                    'Meldung':'Zunahme nicht erreichbar: Fläche dieser Kategorien kann nur aus sich selbst oder aus freigegebenem Neubau stammen.',
                    'A_m2':at,'B_m2':bt,'Neubau_frei_m2':nt,'Defizit_m2':bt-at-nt})
            u=_huelle({c},paare,False)
            if u!=set(DOM[dim]):
                ina=x[dim].isin(u).to_numpy();inb=y[dim].isin(u).to_numpy()
                au=float(x.NGF_m2[ina].sum());bu=float(y.NGF_m2[inb].sum());du=float(x.NGF_m2[ina&ma].sum())
                if au>bu+du+tol:rows.append({'Ebene':ebene,'Kategorie':f"{LABEL[dim]}: {', '.join(sorted(u))}",
                    'Meldung':'Abnahme nicht erreichbar: Fläche dieser Kategorien kann nur in sich selbst übergehen oder freigegeben abgerissen werden.',
                    'A_m2':au,'B_m2':bu,'Abriss_frei_m2':du,'Defizit_m2':au-bu-du})
    return pd.DataFrame(rows).drop_duplicates(subset=['Kategorie','Meldung']).to_dict('records') if rows else []

def _kombinations_konflikte(x,y,cfg,ma,mb,ebene,max_merkmale=None):
    """Notwendige Bedingung für Kombinationen veränderlicher Merkmale (ab 1.6.2): Für vorgängerabgeschlossene
    Kategoriemengen T_d mehrerer Merkmale kann B-Fläche in T_1 × … × T_k nur aus A-Fläche derselben Kombination oder aus
    freigegebenem Neubau stammen (B_T ≤ A_T + N_frei,T); analog A_U ≤ B_U + D_frei,U für nachfolgerabgeschlossene U.
    Gemeldet werden nur minimale Kombinationen (keine Teilkombination verletzt). Einzelmerkmale prüft
    _merkmal_huellen_konflikte. Weiterhin nicht hinreichend."""
    from itertools import combinations
    tol=cfg['toleranz_m2'];dims=[d for d in DIMS if d not in cfg['unveraenderlich']];rows=[]
    if not len(x) and not len(y):return rows
    wa=x.NGF_m2.to_numpy(float);wb=y.NGF_m2.to_numpy(float)
    ma=np.asarray(ma,bool) if len(x) else np.zeros(0,bool);mb=np.asarray(mb,bool) if len(y) else np.zeros(0,bool)
    for rueck,(Q,Z,wq,wz,mz,text,frei) in [(True,(y,x,wb,wa,mb,'Zunahme nicht erreichbar: Fläche dieser Merkmalskombination kann nur aus derselben Kombination oder aus freigegebenem Neubau stammen.','Neubau_frei_m2')),
                                              (False,(x,y,wa,wb,ma,'Abnahme nicht erreichbar: Fläche dieser Merkmalskombination kann nur in dieselbe Kombination übergehen oder freigegeben abgerissen werden.','Abriss_frei_m2'))]:
        h={}
        for d in dims:
            paare=erlaubte_paare(d,cfg);seen=set()
            for c in DOM[d]:
                t=frozenset(_huelle({c},paare,rueck))
                if t!=frozenset(DOM[d]) and t not in seen:
                    seen.add(t);h.setdefault(d,[]).append((t,Q[d].isin(t).to_numpy(),Z[d].isin(t).to_numpy()))
        verletzt=set()
        kmax=len(dims) if max_merkmale is None else min(max_merkmale,len(dims))
        for k in range(1,kmax+1):
            for ds in combinations([d for d in dims if d in h],k):
                for wahl in product(*[range(len(h[d])) for d in ds]):
                    key=tuple(zip(ds,wahl))
                    if k>1 and any(sub in verletzt for sub in combinations(key,k-1)):verletzt.add(key);continue   # Oberkombination: nicht melden
                    mq=np.ones(len(Q),bool);mz_=np.ones(len(Z),bool)
                    for d,w in key:mq&=h[d][w][1];mz_&=h[d][w][2]
                    q=float(wq[mq].sum());z=float(wz[mz_].sum());f=float(wq[mq&mz].sum())
                    if q>z+f+tol:
                        verletzt.add(key)
                        if k>1:
                            kat=' × '.join(f"{LABEL[d]}: {', '.join(sorted(h[d][w][0]))}" for d,w in key)
                            rows.append({'Ebene':ebene,'Eigenschaft':'Kombination','Kategorie':kat,'Meldung':text,
                                         'A_m2':z if rueck else q,'B_m2':q if rueck else z,frei:f,'Defizit_m2':q-z-f})
    return rows

def _extern_konflikte(x,y,cfg,ext,ma,mb):
    """Notwendige Bedingungen mit externen Flüssen (global und je unveränderlichem Block). Nicht hinreichend."""
    tol=ext['bilanztoleranz_m2']+cfg['toleranz_m2'];rows=[];D=ext['abriss_m2'];N=ext['neubau_m2']
    ta=float(x.NGF_m2.sum());tb=float(y.NGF_m2.sum())
    if abs(ta-D+N-tb)>tol:rows.append({'Ebene':'Gesamt','Kategorie':'Bilanz','Meldung':'T_A − D + N ≠ T_B.','Defizit_m2':abs(ta-D+N-tb)})
    cd=float(x.NGF_m2[ma].sum());cn=float(y.NGF_m2[mb].sum())
    if D>cd+tol:rows.append({'Ebene':'Gesamt','Kategorie':'Abriss','Meldung':'Abrissvorgabe übersteigt die Fläche freigegebener Abrisstypen in A.','Kapazitaet_m2':cd,'Defizit_m2':D-cd})
    if N>cn+tol:rows.append({'Ebene':'Gesamt','Kategorie':'Neubau','Meldung':'Neubauvorgabe übersteigt die Fläche freigegebener Neubautypen in B.','Kapazitaet_m2':cn,'Defizit_m2':N-cn})
    rows+=_merkmal_huellen_konflikte(x,y,cfg,ma,mb,'Gesamt')
    rows+=_kombinations_konflikte(x,y,cfg,ma,mb,'Gesamt')
    fixed=cfg['unveraenderlich']
    xa=x.assign(_frei=ma);yb=y.assign(_frei=mb)
    ga=_groups(xa,fixed);gb=_groups(yb,fixed)
    for key in sorted(set(ga)|set(gb)):
        aa=ga.get(key,xa.iloc[:0]);bb_=gb.get(key,yb.iloc[:0]);block=' | '.join(map(str,key)) or 'Gesamt'
        sa=float(aa.NGF_m2.sum());sb=float(bb_.NGF_m2.sum())
        da=float(aa.NGF_m2[aa._frei].sum());nb=float(bb_.NGF_m2[bb_._frei].sum())
        if sa-sb>da+cfg['toleranz_m2']:rows.append({'Ebene':'Block','Kategorie':block,'Meldung':'Flächenabnahme im Block größer als freigegebene Abrissfläche.','Defizit_m2':sa-sb-da})
        if sb-sa>nb+cfg['toleranz_m2']:rows.append({'Ebene':'Block','Kategorie':block,'Meldung':'Flächenzunahme im Block größer als freigegebene Neubaufläche.','Defizit_m2':sb-sa-nb})
        if len(aa) or len(bb_):
            for r in _merkmal_huellen_konflikte(aa,bb_,cfg,aa._frei.to_numpy().astype(bool),bb_._frei.to_numpy().astype(bool),'Block'):
                r['Kategorie']=block+' · '+r['Kategorie'];rows.append(r)
            for r in _kombinations_konflikte(aa,bb_,cfg,aa._frei.to_numpy().astype(bool),bb_._frei.to_numpy().astype(bool),'Block'):
                r['Kategorie']=block+' · '+r['Kategorie'];rows.append(r)
    return rows

SKALA_M2=1e4   # LP-Einheit (10 000 m²): Solver-Toleranz 1e-10 entspricht 1e-6 m²

def _fehlmengen(mat,rhs,x,y,cfg,nA,nB,opt,anzahl=20):
    """Fehlmengenanalyse bei Solverstatus 2 (ab 1.6.2): dasselbe LP mit Fehlmengen je Typ (A: nicht zuordenbar, B: nicht
    erreichbar), minimiert deren Summe. Ortet die Typen, an denen die Unzulässigkeit entsteht; ändert nichts am Status."""
    from scipy.sparse import hstack,identity
    n=mat.shape[0];m=hstack([mat,identity(n,format='csr')[:,:nA+nB]]).tocsr()
    c=np.r_[np.zeros(mat.shape[1]),np.ones(nA+nB)]
    r=linprog(c,A_eq=m,b_eq=rhs,bounds=(0,None),method='highs',options={k:v for k,v in opt.items() if k!='primal_feasibility_tolerance'})
    if not r.success:return [{'Ebene':'Fehlmengen','Kategorie':'alle Blöcke','Meldung':'Fehlmengenanalyse nicht lösbar: '+str(r.message)}]
    s=r.x[mat.shape[1]:]*SKALA_M2;rows=[]
    for seite,z,w,text in [('A',x,s[:nA],'Ausgangsfläche dieses Typs ist unter den Regeln keinem Zieltyp und keinem freigegebenen Abriss zuordenbar.'),
                           ('B',y,s[nA:],'Zielfläche dieses Typs ist unter den Regeln aus keinem Ausgangstyp und keinem freigegebenen Neubau erreichbar.')]:
        for k in np.argsort(-w)[:anzahl]:
            if w[k]>cfg['toleranz_m2']:rows.append({'Ebene':'Fehlmengen '+seite,'Eigenschaft':'Typ','Kategorie':str(z.Typ.iat[k]),'Meldung':text,'Defizit_m2':float(w[k])})
    if not rows:rows=[{'Ebene':'Fehlmengen','Kategorie':'alle Blöcke','Meldung':'Fehlmengen unter Toleranz: numerische Unzulässigkeit, kein Regelkonflikt.','Defizit_m2':float(s.sum())}]
    return rows

def _rekonstruiere_extern(a,b,cfg,x,y,ext,zeitlimit_s):
    """Ein gemeinsames LP über alle Blöcke: A_i = Σ_j F_ij + D_i, B_j = Σ_i F_ij + N_j, Σ D_i = D.
    F nur innerhalb unveränderlicher Blöcke und nur über zulässige Kanten; D_i nur auf freigegebenen Abrisstypen,
    N_j nur auf freigegebenen Neubautypen. Ziel: maximale vollständig unveränderte Bestandsfläche."""
    import bestandsbilanz as bb
    base={'szenario_a':a['name'],'szenario_b':b['name'],'jahr_a':a['jahr'],'jahr_b':b['jahr'],
          'eingaben':{k:{z:v for z,v in s.items() if z!='df'} for k,s in [('A',a),('B',b)]},
          'regeln':copy.deepcopy(cfg),'regel_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
          'extern':copy.deepcopy(ext),
          'methode':'Gemeinsames LP über alle Blöcke mit expliziten Neubau-/Abrissflüssen (Bruttovorgaben); '+ZIELFUNKTION_TEXT+' Direkte Gruppenübergänge; keine automatische Verkettung',
          'mehrdeutigkeit':'Eine optimale Zuordnung; Auswahl der Abriss- und Neubautypen innerhalb der Freigaben und Aufteilung auf Sanierung/PV/Flex sind bei gleichen Zielwerten nicht eindeutig. Keine beobachteten Bruttomaßnahmen.',
          'solver':{'verfahren':'scipy.optimize.linprog, HiGHS, zweistufig','primal_feasibility_tolerance':1e-10,'dual_feasibility_tolerance':1e-10,'zeitlimit_s':zeitlimit_s},
          'schema_version':SCHEMA}
    leer={'fluesse':pd.DataFrame(),'neubau':pd.DataFrame(),'abriss':pd.DataFrame()}
    ma=bb.maske(x,ext['freigabe_abriss']).to_numpy();mb=bb.maske(y,ext['freigabe_neubau']).to_numpy()
    conflicts=_extern_konflikte(x,y,cfg,ext,ma,mb)
    if conflicts:return {**base,**leer,'status':NICHT_MACHBAR,'diagnose':pd.DataFrame(conflicts),'kontrollen':pd.DataFrame()}
    ga=_groups(x,cfg['unveraenderlich']);gb=_groups(y,cfg['unveraenderlich']);I=[];J=[];checks=[]
    for key in sorted(set(ga)|set(gb)):
        aa=ga.get(key,x.iloc[:0]);bb_=gb.get(key,y.iloc[:0])
        if len(aa) and len(bb_):
            i,j,_=_graph(aa,bb_,cfg);I.append(aa.index.to_numpy()[i]);J.append(bb_.index.to_numpy()[j])
        else:i=[]
        checks.append({'Block':' | '.join(map(str,key)) or 'Gesamt','NGF_A_m2':float(aa.NGF_m2.sum()),'NGF_B_m2':float(bb_.NGF_m2.sum()),'Kanten_zulaessig':int(len(i))})
    I=np.concatenate(I) if I else np.array([],int);J=np.concatenate(J) if J else np.array([],int)
    nA,nB,E=len(x),len(y),len(I);da=np.where(ma)[0];nb=np.where(mb)[0];nD,nN=len(da),len(nb)
    rows=np.r_[I,nA+J,da,nA+nb,np.full(nD,nA+nB)]
    cols=np.r_[np.arange(E),np.arange(E),E+np.arange(nD),E+nD+np.arange(nN),E+np.arange(nD)]
    mat=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(nA+nB+1,E+nD+nN)).tocsr()
    rhs=np.r_[x.NGF_m2.to_numpy(),y.NGF_m2.to_numpy(),ext['abriss_m2']]/SKALA_M2
    same=x.Typ.to_numpy()[I]==y.Typ.to_numpy()[J]
    cost=np.r_[(~same).astype(float),np.zeros(nD+nN)]
    cost2=np.r_[(x.energy.to_numpy()[I]!=y.energy.to_numpy()[J]).astype(float),np.zeros(nD+nN)]
    eps=cfg['toleranz_m2']/SKALA_M2
    opt={'primal_feasibility_tolerance':1e-10,'dual_feasibility_tolerance':1e-10,**({'time_limit':float(zeitlimit_s)} if zeitlimit_s else {})}
    r1,r2=_zweistufig(cost,cost2,mat,rhs,opt,eps)
    base['solver_toleranz']=opt['primal_feasibility_tolerance']
    if r1.status==2:
        # Kalibrierte Zustände treffen Zielsummen nur bis auf Rundungsreste (<< toleranz_m2). Ein zweiter Lauf mit der
        # aus toleranz_m2 abgeleiteten Zulässigkeitstoleranz unterscheidet echte Konflikte von Rundungsresten;
        # die Rand- und Bilanzkontrollen unten prüfen das Ergebnis weiterhin gegen toleranz_m2.
        opt={**opt,'primal_feasibility_tolerance':cfg['toleranz_m2']/SKALA_M2/10}
        r1,r2=_zweistufig(cost,cost2,mat,rhs,opt,eps)
        base['solver_toleranz']=opt['primal_feasibility_tolerance']
    res=r2 if r2 is not None else r1
    if res.success:base['zielwerte']=_zielwerte(r1,r2,cost,cost2,SKALA_M2)
    if not res.success:
        c=[{'Ebene':'Gesamt-LP','Kategorie':'alle Blöcke','Meldung':'Bilanz mit Neubau/Abriss und Übergangsregeln nicht erfüllbar oder Solverfehler.','Solverstatus':int(res.status),'Solvermeldung':res.message}]
        if int(res.status)==2:c+=_fehlmengen(mat,rhs,x,y,cfg,nA,nB,opt)
        return {**base,**leer,'status':_status_aus_konflikten(c),'diagnose':pd.DataFrame(c),'kontrollen':pd.DataFrame(checks)}
    v=res.x*SKALA_M2;fv=v[:E];dv=v[E:E+nD];nv=v[E+nD:]
    if min(v.min(),0)<-cfg['toleranz_m2']:
        c=[{'Ebene':'Numerik','Kategorie':'alle Blöcke','Meldung':'Negative Lösungswerte.'}]
        return {**base,**leer,'status':BERECHNUNGSFEHLER,'diagnose':pd.DataFrame(c),'kontrollen':pd.DataFrame(checks)}
    fv=np.clip(fv,0,None);dv=np.clip(dv,0,None);nv=np.clip(nv,0,None)
    keep=fv>0;I=I[keep];J=J[keep];fv=fv[keep]
    f=pd.DataFrame({'Herkunft_Typ':x.Typ.to_numpy()[I],'Ziel_Typ':y.Typ.to_numpy()[J],'NGF_m2':fv})
    for d in DIMS:
        f['pre_'+d]=x[d].to_numpy()[I];f['post_'+d]=y[d].to_numpy()[J];f['Aenderung_'+d]=f['pre_'+d].ne(f['post_'+d])
    f['Unveraendert']=f.Herkunft_Typ.eq(f.Ziel_Typ)
    ab=pd.DataFrame({'Herkunft_Typ':x.Typ.to_numpy()[da],**{'pre_'+d:x[d].to_numpy()[da] for d in DIMS},'NGF_m2':dv});ab=ab[ab.NGF_m2>0].reset_index(drop=True)
    nu=pd.DataFrame({'Ziel_Typ':y.Typ.to_numpy()[nb],**{'post_'+d:y[d].to_numpy()[nb] for d in DIMS},'NGF_m2':nv});nu=nu[nu.NGF_m2>0].reset_index(drop=True)
    re=np.abs(np.bincount(I,weights=fv,minlength=nA)+np.bincount(da,weights=dv,minlength=nA)-x.NGF_m2.to_numpy())
    ce=np.abs(np.bincount(J,weights=fv,minlength=nB)+np.bincount(nb,weights=nv,minlength=nB)-y.NGF_m2.to_numpy())
    k=pd.DataFrame(checks)
    blk=lambda frame,pre:frame[[pre+c for c in cfg['unveraenderlich']]].astype(str).agg(' | '.join,axis=1) if len(frame) else pd.Series(dtype=str)
    k['Bestandsfluss_m2']=k.Block.map(f.groupby(blk(f,'pre_')).NGF_m2.sum()).fillna(0)
    k['Abriss_m2']=k.Block.map(ab.groupby(blk(ab,'pre_')).NGF_m2.sum() if len(ab) else {}).fillna(0)
    k['Neubau_m2']=k.Block.map(nu.groupby(blk(nu,'post_')).NGF_m2.sum() if len(nu) else {}).fillna(0)
    k['Kanten_belegt']=k.Block.map(f.groupby(blk(f,'pre_')).size()).fillna(0).astype(int)
    k['Status']='OK'
    gesamt={'Block':'GESAMT','NGF_A_m2':float(x.NGF_m2.sum()),'NGF_B_m2':float(y.NGF_m2.sum()),'Kanten_zulaessig':E,'Bestandsfluss_m2':float(fv.sum()),
            'Abriss_m2':float(dv.sum()),'Neubau_m2':float(nv.sum()),'Kanten_belegt':len(f),'Max_Herkunftsfehler_m2':float(re.max()),'Max_Zielfehler_m2':float(ce.max()),'Status':'OK'}
    k=pd.concat([k,pd.DataFrame([gesamt])],ignore_index=True)
    if max(re.max(),ce.max())>cfg['toleranz_m2']:
        c=[{'Ebene':'Numerik','Kategorie':'alle Blöcke','Meldung':'Abschlussprüfung Randsummen fehlgeschlagen.','Max_Randfehler_m2':float(max(re.max(),ce.max()))}]
        return {**base,**leer,'status':BERECHNUNGSFEHLER,'diagnose':pd.DataFrame(c),'kontrollen':k}
    return {**base,'status':MACHBAR,'diagnose':pd.DataFrame(columns=['Meldung']),'fluesse':f,'neubau':nu,'abriss':ab,'kontrollen':k}

def _dateihashes(z):
    ordner=Path(z['ordner']);return {n:sha(ordner/n) for n in ['Verteilung.csv','laufprotokoll.json'] if (ordner/n).is_file()}

def lade_zustaende_geprueft(cfg,projekt):
    """Lädt A und B aus results/szenarien mit Integritätsprüfung (gebaeudesektor.lade_gespeichertes_szenario). Nur lesen."""
    import gebaeudesektor as gs
    root=Path(projekt['root']);out=[]
    for key in ['szenario_a','szenario_b']:
        ordner=root/cfg[key];z=lade_zustand(ordner,root)
        g=gs.lade_gespeichertes_szenario(ordner.name,projekt)
        if g['zustand_id']!=z['zustand_id']:raise ValueError('Zustands-ID widersprüchlich: '+ordner.name)
        z.update({'integritaet':g['integritaet'],'energiestatus':g.get('energiestatus'),'ordner':ordner})
        out.append(z)
    return out[0],out[1]

def lade_flussergebnis(rek_id,projekt,ordner=None):
    """Lädt ein gespeichertes Rekonstruktionsergebnis (results/flaechenstroeme/<ID>/) mit Hashprüfung. Kein Solveraufruf."""
    root=Path(projekt['root']);ordner=Path(ordner) if ordner else Path(projekt['ergebnisse']['flaechenstroeme'])/rek_id
    log=json.loads((ordner/'flussprotokoll.json').read_text(encoding='utf-8'))
    if 'ausgaben' not in log:raise ValueError('Gespeichertes Ergebnis im Altformat (vor AP3, ohne Ausgabehashes); bitte neu rekonstruieren oder Flussdatei registrieren.')
    bad=[n for n,h in log['ausgaben'].items() if not (ordner/n).is_file() or sha(ordner/n)!=h]
    if bad:raise ValueError('Gespeichertes Flussergebnis verändert oder unvollständig: '+', '.join(bad))
    def lies(n):
        try:return pd.read_csv(ordner/n,sep=';',encoding='utf-8-sig',**_CSV_GENAU)
        except pd.errors.EmptyDataError:return pd.DataFrame()
    r={k:v for k,v in log.items() if k not in ['ausgaben']}
    r.update({'diagnose':lies('Machbarkeit.csv'),'kontrollen':lies('Kontrollen.csv'),'pruefungen':lies('Pruefungen.csv'),
              'fluesse':lies('Fluesse.csv') if (ordner/'Fluesse.csv').is_file() else pd.DataFrame(),'quelle':'gespeichert','ordner':_rel(root,ordner)})
    for k,n in [('neubau','Neubau.csv'),('abriss','Abriss.csv'),('bestandsbilanz','Bestandsbilanz.csv')]:
        r[k]=lies(n) if (ordner/n).is_file() else pd.DataFrame()
    return r

def extern_signatur(ext):
    """Inhaltlicher Fingerabdruck der Brutto-Vorgaben (ohne Dateiherkunft): ändert sich nur, wenn sich Mengen oder Freigaben ändern."""
    if ext is None:return None
    k={z:ext[z] for z in ['neubau_m2','abriss_m2','freigabe_neubau','freigabe_abriss']}
    return hashlib.sha256(json.dumps(k,sort_keys=True,default=str).encode()).hexdigest()

def _quellen_aktuell(r,a,b,ext=None):
    if not all(r.get('eingaben',{}).get(k,{}).get('sha256')==z['sha256'] for k,z in [('A',a),('B',b)]):return False
    if r.get('quelle')=='gespeichert' and r.get('status')==MACHBAR and (r.get('zielwerte') or {}).get('zielfunktion')!=ZIELFUNKTION:return False
    return extern_signatur(r.get('extern'))==extern_signatur(ext)

def _bilanz_laden(rek_id,projekt,a,b):
    """Bestandsbilanz der Verbindung; ohne konfigurierte Bestandsentwicklung None (= nur Nettoänderung bekannt)."""
    if not (projekt.get('konfiguration') or {}).get('bestandsentwicklung'):return None
    if b['jahr']<=a['jahr']:return None
    import bestandsbilanz as bb
    return bb.bilanz_fuer(rek_id,projekt,float(pd.to_numeric(a['df'].NGF_m2).sum()),float(pd.to_numeric(b['df'].NGF_m2).sum()),a['jahr'],b['jahr'])

def analysiere_rekonstruktion(rek_id,projekt,modus='VorhandeneFluesse',rekonstruieren=False,exportieren=False,ersetzen=False,zeitlimit_s=None):
    """Einheitlicher Einstieg (AP3). Gibt immer ein Ergebnis mit Status aus STATUSWERTE zurück.

    modus='VorhandeneFluesse': liest nur – registrierte Flussdatei prüfen oder gespeichertes Ergebnis laden; kein Solver.
    modus='Rekonstruktion': LP nur mit rekonstruieren=True, sonst NICHT_AUSGEFUEHRT.
    Zustände A und B werden gelesen und nie verändert (Hashvergleich vor/nach dem Lauf)."""
    root=Path(projekt['root'])
    if modus not in ('VorhandeneFluesse','Rekonstruktion'):raise ValueError('Unbekannter Flächenstrommodus: '+str(modus))
    try:
        cfg=lade_rekonstruktion(rek_id,projekt);a,b=lade_zustaende_geprueft(cfg,projekt)
    except Exception as e:
        return _leeres_ergebnis(EINGABEN_UNGUELTIG,f'{type(e).__name__}: {e}')
    vorher={k:_dateihashes(z) for k,z in [('A',a),('B',b)]}
    try:bil=_bilanz_laden(rek_id,projekt,a,b)
    except Exception as e:
        return _leeres_ergebnis(EINGABEN_UNGUELTIG,f'Bestandsentwicklung ungültig: {type(e).__name__}: {e}',cfg,a,b)
    import bestandsbilanz as bb
    ext=bb.extern_fuer(bil) if bil else None
    pr=pruefe_eingaben(a,b,cfg,bil)
    if (pr.Status=='FEHLER').any():
        r=_leeres_ergebnis(EINGABEN_UNGUELTIG,'Pflichtprüfung fehlgeschlagen: '+'; '.join(pr.loc[pr.Status=='FEHLER','Pruefung']),cfg,a,b,pr)
    elif modus=='Rekonstruktion' and not rekonstruieren:
        r=_leeres_ergebnis(NICHT_AUSGEFUEHRT,'Rekonstruktion nicht gestartet (REKONSTRUIEREN=False).',cfg,a,b,pr)
    elif modus=='Rekonstruktion':
        try:r=rekonstruiere(a,b,cfg,zeitlimit_s=zeitlimit_s,extern=ext);r['quelle']='rekonstruiert'
        except (MemoryError,AssertionError) as e:r=_leeres_ergebnis(BERECHNUNGSFEHLER,f'{type(e).__name__}: {e}',cfg,a,b)
        except ValueError as e:r=_leeres_ergebnis(EINGABEN_UNGUELTIG,str(e),cfg,a,b)
        r['pruefungen']=pr
    elif cfg.get('flussdatei') and ext is not None:
        r=_leeres_ergebnis(EINGABEN_UNGUELTIG,'Übernahme vorhandener Flussdateien mit Neubau/Abriss ist noch nicht unterstützt (offener Punkt); MODUS=\'Rekonstruktion\' verwenden.',cfg,a,b,pr)
    elif cfg.get('flussdatei'):
        try:
            system=root/cfg['systemordner'] if cfg.get('systemordner') else None
            r=uebernehme_berechnete_fluesse(a,b,cfg,root/cfg['flussdatei'],system);r['quelle']='flussdatei'
        except Exception as e:r=_leeres_ergebnis(EINGABEN_UNGUELTIG,f'Flussdatei abgewiesen: {e}',cfg,a,b)
        r['pruefungen']=pr
    else:
        ziel=Path(projekt['ergebnisse']['flaechenstroeme'])/rek_id
        if not ziel.exists():
            r=_leeres_ergebnis(NICHT_AUSGEFUEHRT,'Keine Flussdatei registriert und kein gespeichertes Ergebnis vorhanden. Rekonstruktion mit MODUS=\'Rekonstruktion\', REKONSTRUIEREN=True starten.',cfg,a,b,pr)
        else:
            try:
                r=lade_flussergebnis(rek_id,projekt)
                if not _quellen_aktuell(r,a,b,ext):
                    r=_leeres_ergebnis(EINGABEN_UNGUELTIG,'Gespeichertes Flussergebnis gehört zu anderen Zuständen A/B, anderen Neubau-/Abrissvorgaben oder einer älteren Zielfunktion; neu rekonstruieren.',cfg,a,b,pr)
            except Exception as e:
                r=_leeres_ergebnis(NICHT_AUSGEFUEHRT,f'Gespeichertes Ergebnis nicht lesbar: {type(e).__name__}: {e}',cfg,a,b,pr)
            exportieren=False if r.get('quelle')=='gespeichert' else exportieren
    if r['status']==MACHBAR and r.get('quelle')!='gespeichert':
        r['pruefungen']=pd.concat([r['pruefungen'],pruefe_fluesse(r,a,b,cfg)],ignore_index=True)
        if (r['pruefungen'].Status=='FEHLER').any():
            r['status']=BERECHNUNGSFEHLER;r['diagnose']=r['pruefungen'][r['pruefungen'].Status=='FEHLER']
    nachher={k:_dateihashes(z) for k,z in [('A',a),('B',b)]}
    if nachher!=vorher:raise RuntimeError('Zustände A/B wurden während der Analyse verändert.')
    r['zustaende_unveraendert']=True;r['zustand_hashes']=vorher
    for k in ['neubau','abriss']:
        if not isinstance(r.get(k),pd.DataFrame):r[k]=pd.DataFrame()
    r['rekonstruktion_id']=rek_id;r['modus']=modus;r['statusbedeutung']=statusbedeutung(r['status'])
    r['zeitspanne_jahre']=(b['jahr']-a['jahr'])
    if bil is not None:
        konst=abs(bil['ngf_b']-bil['ngf_a'])<=cfg.get('toleranz_m2',0.01)
        r['bilanzstatus']='KONSTANT' if bil['status']=='NUR_NETTO' and konst else bil['status'];r['bilanzmeldung']=bil['meldung']
        if r.get('quelle')!='gespeichert' or not isinstance(r.get('bestandsbilanz'),pd.DataFrame) or not len(r['bestandsbilanz']):r['bestandsbilanz']=bil['tabelle']
    else:r['bilanzstatus']='NUR_NETTO' if abs(float(pd.to_numeric(a['df'].NGF_m2).sum())-float(pd.to_numeric(b['df'].NGF_m2).sum()))>cfg.get('toleranz_m2',0.01) else 'KONSTANT'
    if exportieren:r['ausgabe']=speichere_ergebnis(r,projekt,ersetzen)
    return r

def matrix(result,dim):
    """Übergangsmatrix Herkunft × Ziel (m² NGF) für ein Merkmal."""
    if result['status']!=MACHBAR:raise ValueError('Keine gültigen Flüsse verfügbar.')
    f=result['fluesse']
    return f.pivot_table(index='pre_'+dim,columns='post_'+dim,values='NGF_m2',aggfunc='sum',fill_value=0).reindex(index=DOM[dim],columns=DOM[dim],fill_value=0)

def aenderungsanteile(result):
    """Geänderte Fläche je Typmerkmal (ohne Richtung) und insgesamt, bezogen auf die Ausgangs-NGF T_A = Σ Flüsse + Abriss.
    Maßnahmenraten mit Richtung, Sanierungsklassifikation und Kombinationen: modell/massnahmen.py (AP5).
    Jede Bestandsfläche zählt je Merkmal höchstens einmal; 'Beliebige Änderung' ohne Doppelzählung. Neubau und Abriss werden
    gesondert ausgewiesen und nie als Merkmalsänderung gezählt. Mittelwerte pro Jahr nur bei positiver Zeitspanne."""
    if result['status']!=MACHBAR:raise ValueError('Keine gültigen Flüsse verfügbar.')
    f=result['fluesse'];n,d=_extern_tabellen(result);total=float(f.NGF_m2.sum())+float(d.NGF_m2.sum());jahre=int(result['jahr_b']-result['jahr_a'])
    rows=[]
    for dim in DIMS:
        m=float(f.loc[f['pre_'+dim].ne(f['post_'+dim]),'NGF_m2'].sum())
        rows.append({'Merkmal':LABEL[dim],'Geaenderte_NGF_m2':m})
    m=float(f.loc[~f.Herkunft_Typ.eq(f.Ziel_Typ),'NGF_m2'].sum())
    rows.append({'Merkmal':'Beliebige Änderung (ohne Doppelzählung)','Geaenderte_NGF_m2':m})
    if result.get('extern') is not None:
        rows.append({'Merkmal':'Abriss (explizit)','Geaenderte_NGF_m2':float(d.NGF_m2.sum())})
        rows.append({'Merkmal':'Neubau (explizit)','Geaenderte_NGF_m2':float(n.NGF_m2.sum())})
    out=pd.DataFrame(rows)
    out['Anteil_Ausgangs_NGF_pct']=100*out.Geaenderte_NGF_m2/total
    out['Mittel_pct_pro_Jahr']=out.Anteil_Ausgangs_NGF_pct/jahre if jahre>0 else np.nan
    return out

def zusammensetzung(result,dim):
    """Herkunft und Verbleib je Kategorie eines Merkmals: A = Abriss + verbleibend, B = aus Bestand + Neubau (m² NGF).
    Bezugsbasis der Anteile: Abriss_pct bezogen auf A der Kategorie, Neubau_pct bezogen auf B der Kategorie."""
    if result['status']!=MACHBAR:raise ValueError('Keine gültigen Flüsse verfügbar.')
    if dim not in DIMS:raise ValueError('Unbekanntes Merkmal: '+str(dim))
    f=result['fluesse'];n,d=_extern_tabellen(result);idx=DOM[dim]
    g=lambda frame,col:(frame.groupby(col).NGF_m2.sum() if len(frame) else pd.Series(dtype=float)).reindex(idx,fill_value=0.0)
    out=pd.DataFrame({LABEL[dim]:idx,'A_verbleibend_m2':g(f,'pre_'+dim).to_numpy(),'Abriss_m2':g(d,'pre_'+dim).to_numpy(),
                      'B_aus_Bestand_m2':g(f,'post_'+dim).to_numpy(),'Neubau_m2':g(n,'post_'+dim).to_numpy()})
    out.insert(1,'A_gesamt_m2',out.A_verbleibend_m2+out.Abriss_m2);out['B_gesamt_m2']=out.B_aus_Bestand_m2+out.Neubau_m2
    with np.errstate(invalid='ignore',divide='ignore'):
        out['Abriss_pct_von_A']=np.where(out.A_gesamt_m2>0,100*out.Abriss_m2/out.A_gesamt_m2,np.nan)
        out['Neubau_pct_von_B']=np.where(out.B_gesamt_m2>0,100*out.Neubau_m2/out.B_gesamt_m2,np.nan)
    out=out[(out.A_gesamt_m2>0)|(out.B_gesamt_m2>0)].reset_index(drop=True)
    return out

def zusammenfassung(result):
    """Kurzübersicht eines Ergebnisses für Notebook und Protokoll."""
    f=result.get('fluesse',pd.DataFrame())
    d={'Rekonstruktion':result.get('rekonstruktion_id'),'Status':result['status'],'Bedeutung':statusbedeutung(result['status']),
       'Quelle':result.get('quelle','–'),'A':result.get('szenario_a'),'B':result.get('szenario_b'),
       'Jahre':(result['jahr_b']-result['jahr_a']) if result.get('jahr_a') is not None and result.get('jahr_b') is not None else None,
       'Fluesse':len(f),'NGF_m2':float(f.NGF_m2.sum()) if len(f) else np.nan,
       'Unveraendert_m2':float(f.loc[f.Herkunft_Typ.eq(f.Ziel_Typ),'NGF_m2'].sum()) if len(f) else np.nan,
       'Abriss_m2':float(_extern_tabellen(result)[1].NGF_m2.sum()) if result.get('extern') is not None and len(f) else (0.0 if len(f) else np.nan),
       'Neubau_m2':float(_extern_tabellen(result)[0].NGF_m2.sum()) if result.get('extern') is not None and len(f) else (0.0 if len(f) else np.nan),
       'Bilanzstatus':result.get('bilanzstatus','–'),
       'Zustaende_unveraendert':result.get('zustaende_unveraendert'),'Meldung':result.get('meldung','')}
    return pd.DataFrame([d])

def registrierte_rekonstruktionen(projekt):
    reg=json.loads(Path(projekt['konfiguration']['rekonstruktionen']).read_text(encoding='utf-8'))
    return pd.DataFrame([{'Rekonstruktion_ID':k,'A':v['szenario_a'],'B':v['szenario_b'],'Regeln':v.get('regeln'),
                          'Flussdatei':v.get('flussdatei') or '','Beschreibung':v.get('beschreibung','')} for k,v in reg['rekonstruktionen'].items()])

def speichere_ergebnis(result,projekt,ersetzen=False):
    """Speichert ein Ergebnis nach results/flaechenstroeme/<ID>/ (Arbeitsordner, Ausgabehashes, Ersetzungsschutz)."""
    if result['status']==NICHT_AUSGEFUEHRT:raise ValueError('Nichts zu speichern: Status NICHT_AUSGEFUEHRT.')
    if result.get('quelle')=='gespeichert':raise ValueError('Ergebnis wurde aus dem Ergebnisordner geladen; erneutes Speichern nicht nötig.')
    root=Path(projekt['root'])
    if result['status']==MACHBAR and projekt['konfiguration'].get('massnahmen'):
        import massnahmen as ms
        result={**result,'massnahmen_definition':ms.lade_definition(projekt)}
    return _rel(root,exportiere(result,result['regeln'],root,ersetzen))
