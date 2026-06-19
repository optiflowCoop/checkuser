import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Cleanup old script since logic is merged
old_script = ROOT / 'scripts' / 'generate_excel.py'
if old_script.exists():
    old_script.unlink()