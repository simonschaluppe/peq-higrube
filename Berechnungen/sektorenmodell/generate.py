"""Generate reviewable tables and Plotly-compatible structure; --check detects drift."""
import argparse
import json
from model import DATA, artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    parameters = json.loads((DATA / 'allocation_parameters.json').read_text(encoding='utf-8'))
    for path, content in artifacts(parameters).items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content:
                raise ValueError(f'Generated artifact out of date: {path}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        print(('Checked ' if args.check else 'Generated ') + path.name)


if __name__ == '__main__':
    main()
