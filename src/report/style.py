from pathlib import Path
from matplotlib import pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]


def setup():
    plt.style.use('classic')


def save(fig, name, dpi=200):
    out_dir = REPO_ROOT / 'reports' / 'figures'
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'{name}.png'
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    return str(path)
