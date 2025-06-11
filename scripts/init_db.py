# scripts/init_db.py
from src.models.base import Base, engine
from src.models.error_history import ErrorHistory, CorrectionHistory

if __name__ == "__main__":
    print("[init_db] 正在建立所有資料表...")
    Base.metadata.create_all(engine)
    print("[init_db] 資料表建立完成！") 