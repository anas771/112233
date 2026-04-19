import os
import shutil
from datetime import datetime
from ui.constants import DB_PATH, BASE_DIR

def make_backup():
    if not os.path.exists(DB_PATH): 
        return None
    
    backup_dir = os.path.join(BASE_DIR, "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f"poultry_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    
    # Optional: Keep only last 10 backups
    backups = sorted([f for f in os.listdir(backup_dir) if f.endswith(".db")])
    if len(backups) > 10:
        for old_b in backups[:-10]:
            try: os.remove(os.path.join(backup_dir, old_b))
            except: pass
            
    return dest
