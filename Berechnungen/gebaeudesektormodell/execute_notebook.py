"""Execute all scientific notebook cells from a fresh kernel and retain outputs."""
import asyncio
import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient

if __name__=='__main__':
    if sys.platform=='win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    path=Path(__file__).with_name('Gebaeudesektormodell.ipynb')
    notebook=nbformat.read(path,as_version=4)
    NotebookClient(notebook,timeout=240,kernel_name='python3',resources={'metadata':{'path':str(path.parents[2])}}).execute()
    nbformat.write(notebook,path)
    print(path)
