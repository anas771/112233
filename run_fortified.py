from pathlib import Path
import sys

# إضافة المسارات اللازمة
base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir / "src"))

from core.database import DBManager
from ui.main_window import MainWindow

if __name__ == "__main__":
    db_path = base_dir / "poultry_data.db"
    db = DBManager(str(db_path))
    
    app = MainWindow(db)
    app.mainloop()
