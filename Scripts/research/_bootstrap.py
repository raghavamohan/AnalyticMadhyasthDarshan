"""Import path setup for Scripts/research/ one-off tools."""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
RESEARCH = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
