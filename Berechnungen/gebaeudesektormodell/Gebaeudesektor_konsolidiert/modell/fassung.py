"""Projektfassung und Fassungsprüfung der Notebooks (AP6).

Jedes Notebook nennt in seiner Startzelle die Fassung, für die es geschrieben ist. Weicht sie von der hier
erwarteten Fassung ab, wurde meist eine aktualisierte Notebook-Datei in einem noch geöffneten Fenster mit dem
alten Zelleninhalt ausgeführt (oder umgekehrt ein altes Notebook mit neuen Modulen). Dann wird mit einer klaren
Meldung abgebrochen, bevor etwas geladen, gerechnet oder gespeichert wird.

Die Datei ist bewusst getrennt von ``gebaeudesektor.py``: Deren Inhalt geht in die Zustands-ID ein; eine
Fassungsänderung soll gespeicherte Zustände nicht ungültig machen.
"""

FASSUNG = '1.6.3-AP6'

NOTEBOOKS = {
    '00_Start': FASSUNG,
    '01_Szenario': FASSUNG,
    '02_Szenarienvergleich': FASSUNG,
    '03_Flaechenstroeme': FASSUNG,
}

ABHILFE = ('Abhilfe: Notebook-Fenster schließen, ohne zu speichern (sonst wird die aktuelle Datei mit dem alten Inhalt '
           'überschrieben), die Datei aus notebooks/ neu öffnen und den Kernel neu starten (Kernel → Restart).')


def pruefe_notebook(name, fassung):
    """Bricht ab, wenn die Notebook-Fassung nicht zur Projektfassung passt. Gibt sonst eine Kurzmeldung zurück."""
    if name not in NOTEBOOKS:
        raise ValueError(f'Unbekanntes Notebook {name!r}; erwartet: {", ".join(NOTEBOOKS)}.')
    soll = NOTEBOOKS[name]
    if fassung != soll:
        raise RuntimeError(f'Notebook {name} hat Fassung {fassung}, das Modell im Projektordner erwartet {soll}. '
                           'Ursache meist: Die Datei wurde aktualisiert, während das Notebook geöffnet war; '
                           'ausgeführt wurde der alte Zelleninhalt. ' + ABHILFE)
    return f'Fassung {soll} (Notebook und Modell passen zusammen)'
