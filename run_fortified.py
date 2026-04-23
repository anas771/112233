from pathlib import Path
import subprocess
import sys


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    main_file = base_dir / "main.py"
    subprocess.run([sys.executable, str(main_file)], check=False)
