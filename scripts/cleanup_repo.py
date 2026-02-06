import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Directories to remove
for name in ("build", "dist", ".pytest_cache", ".cache"):
    path = ROOT / name
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)

# Remove __pycache__ directories and compiled python files
for p in ROOT.rglob('__pycache__'):
    shutil.rmtree(p, ignore_errors=True)
for ext in ('*.pyc', '*.pyo'):
    for f in ROOT.rglob(ext):
        try:
            f.unlink()
        except Exception:
            pass

print('Cleanup complete')
