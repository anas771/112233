from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os

# المسار لقاعدة البيانات الجديدة
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_URL = f"sqlite:///{os.path.join(os.path.dirname(BASE_DIR), 'poultry_v5.db')}"

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# إنشاء جلسة معزولة (Thread-safe) للواجهة الرسومية
db_session = scoped_session(SessionLocal)

def init_db():
    from v5.database.models import Base
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
