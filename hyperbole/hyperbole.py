r"""Point d'entrée : python D:\Super_Toolbox\hyperbole\hyperbole.py <commande>   (aide : -h)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from popo.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
