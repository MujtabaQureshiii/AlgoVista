from pathlib import Path
from daa_app.datasets import generate_all
if __name__=='__main__':
    files=generate_all(Path(__file__).resolve().parent/'datasets')
    print(f'Created {len(files)} reproducible JSON datasets across 4 algorithms.')
