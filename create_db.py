from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base   # zakładając że modele masz w pliku models.py

def create_database(db_path="baza.db"):
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    Base.metadata.create_all(engine)
    print(f"Baza została utworzona: {db_path}")

if __name__ == "__main__":
    create_database()