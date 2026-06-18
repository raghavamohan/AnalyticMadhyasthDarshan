"""Import path setup for Scripts/archive/ one-off tools."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
