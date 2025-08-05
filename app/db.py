from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Purchase
from datetime import datetime

# SQLite DB connection
DATABASE_URL = "sqlite:///./receipts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Create all tables
Base.metadata.create_all(bind=engine)

# ----------- Purchase Operations -----------

def insert_purchases(data, receipt_title, image_filename):
    session = SessionLocal()

    for p in data["purchases"]:
        exists = session.query(Purchase).filter_by(
            receipt_title=receipt_title,
            purchase_date=data["date"],
            item=p["item"]
        ).first()

        if not exists:
            purchase = Purchase(
                receipt_title=receipt_title,
                image_filename=image_filename,
                purchase_date=data["date"],
                item=p["item"],
                quantity=float(p.get("qty", 1)),
                price=float(p.get("price", 0).replace("$", "").strip())
            )
            session.add(purchase)

    session.commit()
    session.close()


def drop_all_purchases():
    session = SessionLocal()
    # First delete purchases
    session.query(Purchase).delete()
    session.commit()
    session.close()



