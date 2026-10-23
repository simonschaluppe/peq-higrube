"""Execute the editorial notebook and save outputs only after successful execution."""
import asyncio
import argparse
import sys
import nbformat
from nbclient import NotebookClient
from .model import ROOT


def main():
    # pyzmq needs the selector loop on Windows; avoids a cleanup crash on Python 3.13.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notebook', choices=['transition', 'allokation'], default='transition')
    args = parser.parse_args()
    path = ROOT / ('Berechnungen/sektorenmodell/allokation.ipynb' if args.notebook == 'allokation'
                   else 'Redaktion/transitionsszenarien/Berechnungen/Transition_2040.ipynb')
    notebook = nbformat.read(path, as_version=4)
    NotebookClient(notebook, timeout=180, kernel_name='python3',
                   resources={'metadata': {'path': str(ROOT)}}).execute()
    nbformat.write(notebook, path)
    print(path)


if __name__ == '__main__':
    main()
